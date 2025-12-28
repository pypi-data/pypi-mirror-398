"""Scheduler for automatic PyTorchJob discovery and tuning in Kubernetes."""

import concurrent.futures
import logging
import queue
import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

import yaml
from kubernetes import client, config, watch
from optuna.samplers import BaseSampler

from .annotation_based_tuning import (
    _deep_merge,
    annotation_job_converter,
    annotation_value_extractor,
)
from .pytorchjob import PyTorchJob
from .pytorchjob_tuner import PyTorchJobTuner

logger = logging.getLogger("zenith-tune")


@dataclass
class TuningConfig:
    """Configuration for a tuning job."""

    # Function to convert job with trial parameters
    job_converter: Callable[[any, PyTorchJob], PyTorchJob] = annotation_job_converter
    # Function to extract objective value from job logs
    value_extractor: Callable[[str, PyTorchJob], float] = annotation_value_extractor
    # Number of trials to run (None = use annotation or default 10)
    n_trials: Optional[int] = None
    # Directory to store study results
    output_dir: str = "outputs"
    # Optuna sampler for hyperparameter selection
    sampler: Optional[BaseSampler] = None
    # Whether to maximize objective (None = use annotation or default False)
    maximize: Optional[bool] = None
    # Default parameter values for trials
    default_params: Optional[Dict] = None
    # Custom patches to apply to all trial jobs
    default_custom_patches: Optional[Dict] = None
    # Whether to wait for cluster resources before each trial
    wait_resources: bool = False
    # Target namespace for trial job submission (None = inherit from original job)
    submit_namespace: Optional[str] = None


@dataclass
class JobFilter:
    """Filter criteria for selecting PyTorchJobs to tune."""

    # Required labels on the job (key-value pairs must match exactly)
    labels: Optional[Dict[str, str]] = None
    # Required annotations on the job (None value = key existence check only)
    annotations: Optional[Dict[str, str]] = None
    # Regex pattern for job name (e.g., "training-.*")
    name_pattern: Optional[str] = None
    # Regex pattern for namespace (e.g., "production-.*")
    namespace_pattern: Optional[str] = None


@dataclass
class TuningRule:
    """
    A rule that maps a JobFilter to a TuningConfig.

    When a job matches the filter, the associated tuning config is used.
    """

    job_filter: JobFilter
    tuning_config: TuningConfig


class PyTorchJobTuningScheduler:
    """
    Scheduler that discovers PyTorchJobs and automatically creates tuning jobs.

    This scheduler periodically scans for PyTorchJobs matching specified criteria
    and creates PyTorchJobTuner instances to optimize them.
    """

    def __init__(
        self,
        tuning_rules: List[TuningRule],
        max_concurrent_tuning: Optional[int] = None,
        max_concurrent_tuning_per_namespace: Optional[int] = None,
        polling_interval: int = 60,
        timeout_per_trial: int = 1209600,  # 2 weeks
    ):
        """
        Initialize the tuning scheduler.

        Args:
            tuning_rules: List of TuningRule for rule-based config selection (first match wins).
                          Must not be empty. Jobs that match a rule's filter will be tuned using the rule's config.
            max_concurrent_tuning: Maximum number of concurrent tuning jobs (None = unlimited)
            max_concurrent_tuning_per_namespace: Maximum concurrent tuning jobs per namespace (None = unlimited)
            polling_interval: Interval in seconds for polling checks (default: 60)
            timeout_per_trial: Timeout in seconds for each trial (default: 1209600 = 2 weeks)

        Raises:
            ValueError: If tuning_rules is empty
        """
        if not tuning_rules:
            raise ValueError("tuning_rules cannot be empty")

        self.tuning_rules = tuning_rules
        self.max_concurrent_tuning = max_concurrent_tuning
        self.max_concurrent_tuning_per_namespace = max_concurrent_tuning_per_namespace
        self.polling_interval = polling_interval
        self.timeout_per_trial = timeout_per_trial

        # Track active tuning futures
        self._active_futures: Dict[str, concurrent.futures.Future] = {}

        # Track namespace for each active job (job_key -> namespace)
        self._active_job_namespaces: Dict[str, str] = {}

        # Queue for jobs to be tuned
        self._job_queue: queue.Queue = queue.Queue()

        # Shutdown event for graceful termination
        self._shutdown_event = threading.Event()

        # Record scheduler startup time (UTC)
        self._startup_time = datetime.now(timezone.utc).timestamp()

        # Setup ThreadPoolExecutor for concurrent tuning
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_concurrent_tuning
        )

        # Setup Kubernetes API clients
        self._setup_api_clients()

    def _setup_api_clients(self):
        """Setup Kubernetes API clients."""
        try:
            # Try in-cluster config first (for Pod execution)
            try:
                config.load_incluster_config()
                logger.info("Using in-cluster Kubernetes configuration")
            except config.ConfigException:
                # Fallback to kubeconfig (for local development)
                config.load_kube_config()
                logger.info("Using kubeconfig for Kubernetes configuration")

            self.core_api = client.CoreV1Api()
            self.custom_api = client.CustomObjectsApi()
        except config.ConfigException as e:
            logger.error(f"Failed to load Kubernetes config: {e}")
            raise

    @classmethod
    def from_yaml(cls, config_path: str) -> "PyTorchJobTuningScheduler":
        """
        Create a PyTorchJobTuningScheduler from a YAML configuration file.

        Args:
            config_path: Path to the YAML configuration file

        Returns:
            Configured PyTorchJobTuningScheduler instance

        Example YAML structure:
            scheduler:
              max_concurrent_tuning: 5
              max_concurrent_tuning_per_namespace: 2
              polling_interval: 60
              timeout_per_trial: 1209600

            tuning_rules:
              - job_filter:
                  namespace_pattern: "production-.*"
                  labels:
                    team: "ml-team"
                tuning_config:
                  n_trials: 20
                  output_dir: "production_outputs"
                  maximize: true
                  wait_resources: true

              - job_filter:
                  namespace_pattern: ".*"
                tuning_config:
                  n_trials: 10
                  output_dir: "outputs"
        """
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        # Parse scheduler settings
        scheduler_config = config_data.get("scheduler", {})

        # Parse tuning rules
        rules_data = config_data.get("tuning_rules", [])
        if not rules_data:
            raise ValueError("tuning_rules cannot be empty in config file")

        tuning_rules = []
        for rule_data in rules_data:
            # Parse JobFilter
            filter_data = rule_data.get("job_filter", {})
            job_filter = JobFilter(
                labels=filter_data.get("labels"),
                annotations=filter_data.get("annotations"),
                name_pattern=filter_data.get("name_pattern"),
                namespace_pattern=filter_data.get("namespace_pattern"),
            )

            # Parse TuningConfig
            config_data_item = rule_data.get("tuning_config", {})
            tuning_config = TuningConfig(
                # job_converter and value_extractor use defaults (annotation-based)
                n_trials=config_data_item.get("n_trials"),
                output_dir=config_data_item.get("output_dir", "outputs"),
                # sampler cannot be specified via YAML
                maximize=config_data_item.get("maximize"),
                default_params=config_data_item.get("default_params"),
                default_custom_patches=config_data_item.get("default_custom_patches"),
                wait_resources=config_data_item.get("wait_resources", False),
                submit_namespace=config_data_item.get("submit_namespace"),
            )

            tuning_rules.append(
                TuningRule(job_filter=job_filter, tuning_config=tuning_config)
            )

        return cls(
            tuning_rules=tuning_rules,
            max_concurrent_tuning=scheduler_config.get("max_concurrent_tuning"),
            max_concurrent_tuning_per_namespace=scheduler_config.get(
                "max_concurrent_tuning_per_namespace"
            ),
            polling_interval=scheduler_config.get("polling_interval", 60),
            timeout_per_trial=scheduler_config.get("timeout_per_trial", 1209600),
        )

    def _tuning_job_producer(self):
        """
        Producer: Watch for PyTorchJobs and add matching ones to the queue.

        This runs in a separate thread and continuously watches for new/modified jobs.
        """
        w = watch.Watch()
        resource_version = None

        logger.info("Starting tuning job producer (PyTorchJob watcher)")

        while not self._shutdown_event.is_set():
            try:
                # Watch for all PyTorchJob events
                for event in w.stream(
                    self.custom_api.list_cluster_custom_object,
                    group="kubeflow.org",
                    version="v1",
                    plural="pytorchjobs",
                    resource_version=resource_version,
                    timeout_seconds=30,  # Shorter timeout for faster shutdown response
                ):
                    if self._shutdown_event.is_set():
                        break

                    event_type = event["type"]
                    job = event["object"]

                    # Update resource version for reconnection
                    metadata = job.get("metadata", {})
                    if "resourceVersion" in metadata:
                        resource_version = metadata["resourceVersion"]

                    # Only process ADDED events (new jobs created)
                    if event_type == "ADDED":
                        # Check if job was created after scheduler startup
                        creation_timestamp = metadata.get("creationTimestamp")

                        if creation_timestamp:
                            # Parse ISO 8601 timestamp from Kubernetes
                            try:
                                # Convert timestamp to epoch time for comparison
                                creation_time = datetime.fromisoformat(
                                    creation_timestamp.replace("Z", "+00:00")
                                ).timestamp()

                                # Only process jobs created after scheduler startup
                                if (
                                    creation_time > self._startup_time
                                    and self._matches_filter(job)
                                ):
                                    job_name = metadata.get("name", "unknown")
                                    logger.info(
                                        f"[Producer] Queueing newly created job {job_name} for tuning"
                                    )
                                    self._job_queue.put(job)
                            except (ValueError, AttributeError) as e:
                                job_name = metadata.get("name", "unknown")
                                logger.warning(
                                    f"Failed to parse creation timestamp for job {job_name}: {e}"
                                )
                        else:
                            job_name = metadata.get("name", "unknown")
                            logger.error(
                                f"PyTorchJob {job_name} is missing creationTimestamp - this should not happen in a normal Kubernetes cluster"
                            )

            except Exception as e:
                if not self._shutdown_event.is_set():
                    error_message = str(e)
                    if "too old resource version" in error_message:
                        logger.warning(
                            f"[Producer] Resource version too old, resetting: {e}"
                        )
                        # Reset only for "too old resource version" errors
                        resource_version = None
                    else:
                        logger.warning(
                            f"[Producer] Watch disconnected: {e}, reconnecting in 5 seconds..."
                        )
                    time.sleep(5)

        logger.info("[Producer] Shutting down")

    def _matches_filter(self, job: Dict) -> bool:
        """
        Check if a PyTorchJob matches any tuning rule's filter criteria.

        Args:
            job: PyTorchJob dictionary

        Returns:
            True if job matches any rule's filter criteria, False otherwise
        """
        metadata = job.get("metadata", {})
        name = metadata.get("name", "")
        namespace = metadata.get("namespace", "")
        annotations = metadata.get("annotations", {})

        # Check if job has required metadata
        if not name or not namespace:
            return False

        # Skip jobs created by tuning system to prevent recursive tuning
        if annotations.get("zenith-tune/created-by") == "PyTorchJobTuner":
            return False

        # Check if job matches any tuning rule
        for rule in self.tuning_rules:
            if self._matches_job_filter(job, rule.job_filter):
                return True

        return False

    def _matches_job_filter(self, job: Dict, job_filter: JobFilter) -> bool:
        """
        Check if a PyTorchJob matches a specific JobFilter.

        Args:
            job: PyTorchJob dictionary
            job_filter: Filter criteria to check against

        Returns:
            True if job matches filter criteria, False otherwise
        """
        metadata = job.get("metadata", {})
        name = metadata.get("name", "")
        namespace = metadata.get("namespace", "")
        labels = metadata.get("labels", {})
        annotations = metadata.get("annotations", {})

        # Check namespace pattern
        if job_filter.namespace_pattern:
            if not re.match(job_filter.namespace_pattern, namespace):
                return False

        # Check name pattern
        if job_filter.name_pattern:
            if not re.match(job_filter.name_pattern, name):
                return False

        # Check required labels
        if job_filter.labels:
            for key, value in job_filter.labels.items():
                if labels.get(key) != value:
                    return False

        # Check required annotations
        if job_filter.annotations:
            for key, value in job_filter.annotations.items():
                if value is None:
                    # Check for key existence only
                    if key not in annotations:
                        return False
                else:
                    # Check for specific value
                    if annotations.get(key) != value:
                        return False

        return True

    def _get_tuning_config_for_job(self, job: Dict) -> TuningConfig:
        """
        Get the appropriate TuningConfig for a job based on tuning rules.

        Iterates through tuning_rules and returns the config from the first
        matching rule.

        Args:
            job: PyTorchJob dictionary

        Returns:
            TuningConfig to use for this job

        Raises:
            ValueError: If no tuning rule matches the job
        """
        job_name = job.get("metadata", {}).get("name", "unknown")

        for rule in self.tuning_rules:
            if self._matches_job_filter(job, rule.job_filter):
                logger.info(f"Job {job_name} matched tuning rule")
                return rule.tuning_config

        raise ValueError(f"No tuning rule matches job '{job_name}'")

    def _get_job_key(self, job: Dict) -> str:
        """
        Generate a unique key for a PyTorchJob.

        Args:
            job: PyTorchJob dictionary

        Returns:
            Unique key string
        """
        metadata = job.get("metadata", {})
        namespace = metadata.get("namespace")
        name = metadata.get("name")
        uid = metadata.get("uid", "")

        return f"{namespace}_{name}_{uid}"

    def _start_tuning_job(self, job: Dict) -> bool:
        """
        Start a tuning job for a specific PyTorchJob using ThreadPoolExecutor.

        Args:
            job: PyTorchJob dictionary to tune

        Returns:
            True if tuning started successfully, False otherwise
        """
        job_key = self._get_job_key(job)
        metadata = job.get("metadata", {})
        job_name = metadata.get("name")
        namespace = metadata.get("namespace", "default")

        try:
            logger.info(f"Starting tuning for job {job_name}")

            # Get the appropriate tuning config for this job
            tuning_config = self._get_tuning_config_for_job(job)

            # Create PyTorchJob object to pass to tuning job
            pytorch_job = PyTorchJob(job)

            # Submit tuning job to thread pool
            future = self.executor.submit(
                self._run_tuning_job, pytorch_job, tuning_config
            )

            # Mark as active and track namespace
            self._active_futures[job_key] = future
            self._active_job_namespaces[job_key] = namespace

            return True

        except Exception as e:
            logger.error(f"Error starting tuning for job {job_name}: {e}")
            return False

    def _run_tuning_job(
        self,
        job: PyTorchJob,
        tuning_config: TuningConfig,
    ) -> None:
        """
        Run the actual tuning job in a separate thread.

        Args:
            job: PyTorchJob object to tune
            tuning_config: TuningConfig to use for this job
        """
        # Extract namespace and job_name from the PyTorchJob object
        job_name = job.get_name()
        namespace = job._job_dict.get("metadata", {}).get("namespace", "default")
        logger.info(f"Running tuning for job {job_name} in namespace {namespace}")

        # Determine submit_namespace: use TuningConfig's value or inherit from job
        submit_namespace = (
            tuning_config.submit_namespace
            if tuning_config.submit_namespace
            else namespace
        )

        # Extract values from annotation if tuning config values are None
        # Only check annotation if job has tuning config
        has_job_tuning_config = job.has_tuning_config()

        # Handle wait_resources (annotation takes priority)
        wait_resources = tuning_config.wait_resources
        if has_job_tuning_config:
            annotation_wait = job.get_wait_resources()
            if annotation_wait is not None:
                wait_resources = annotation_wait
                logger.info(f"Using wait_resources from annotation: {wait_resources}")

        # Handle n_trials
        n_trials = tuning_config.n_trials
        if n_trials is None and has_job_tuning_config:
            annotation_n_trials = job.get_n_trials()
            if annotation_n_trials is not None:
                n_trials = annotation_n_trials
                logger.info(f"Using n_trials from annotation: {n_trials}")

        if n_trials is not None:
            logger.info(f"Using n_trials: {n_trials}")
        else:
            # Use PyTorchJobTuner's default
            n_trials = 10
            logger.info(f"No n_trials specified, using default: {n_trials}")

        # Handle maximize
        maximize = tuning_config.maximize
        if maximize is None and has_job_tuning_config:
            should_maximize = job.should_maximize()
            if should_maximize is not None:
                maximize = should_maximize
                logger.info(f"Using maximize from annotation: {maximize}")

        if maximize is not None:
            logger.info(f"Using maximize: {maximize}")
        else:
            # Default to minimize if not specified anywhere
            maximize = False
            logger.info("No maximize value specified, defaulting to minimize")

        # Generate study name based on namespace and job name
        study_name = f"tune_{namespace}_{job_name}"

        try:
            tuner = PyTorchJobTuner(
                job_name=job_name,
                get_namespace=namespace,
                submit_namespace=submit_namespace,
                output_dir=tuning_config.output_dir,
                study_name=study_name,
                sampler=tuning_config.sampler,
                maximize=maximize,
                timeout_per_trial=self.timeout_per_trial,
                wait_resources=wait_resources,
                polling_interval=self.polling_interval,
            )
            logger.info(f"Created tuner for job {job_name} in namespace {namespace}")
        except Exception as e:
            logger.error(f"Failed to create tuner for job {job_name}: {e}")
            return

        try:
            # Create job_converter that applies default_custom_patches
            base_job_converter = tuning_config.job_converter
            default_custom_patches = tuning_config.default_custom_patches

            if default_custom_patches:

                def job_converter_with_patches(trial, job):
                    # Apply default_custom_patches first
                    merged = _deep_merge(job._job_dict, default_custom_patches)
                    job._job_dict = merged
                    logger.debug(
                        f"Applied default custom patches: {list(default_custom_patches.keys())}"
                    )
                    # Then call the original job_converter
                    return base_job_converter(trial, job)

                job_converter = job_converter_with_patches
            else:
                job_converter = base_job_converter

            # Run optimization
            best_value, best_params = tuner.optimize(
                job_converter=job_converter,
                value_extractor=tuning_config.value_extractor,
                n_trials=n_trials,
                default_params=tuning_config.default_params,
            )

            if best_value is not None:
                logger.info(
                    f"Tuning completed for {job_name}: best_value={best_value}, best_params={best_params}"
                )
            else:
                logger.warning(
                    f"Tuning completed for {job_name} but no valid results found"
                )
        except Exception as e:
            logger.error(f"Error during optimization of job {job_name}: {e}")

    def _cleanup_completed_tuners(self) -> None:
        """Clean up completed tuning futures."""
        completed_keys = [
            key for key, future in self._active_futures.items() if future.done()
        ]

        for key in completed_keys:
            future = self._active_futures[key]
            try:
                # Get result to handle any exceptions
                future.result()
            except Exception as e:
                logger.error(f"Tuning job {key} failed with exception: {e}")

            # Remove from active futures and namespace tracking
            del self._active_futures[key]
            if key in self._active_job_namespaces:
                del self._active_job_namespaces[key]

        if completed_keys:
            logger.debug(f"Cleaned up {len(completed_keys)} completed tuners")

    def _tuning_job_consumer(self):
        """
        Consumer: Process jobs from the queue and start tuning when capacity is available.

        This runs in the main thread and manages concurrent tuning jobs.
        """
        logger.info("Starting tuning job consumer")

        while not self._shutdown_event.is_set():
            # Clean up completed tuners first
            self._cleanup_completed_tuners()

            # Check current active tuner count
            current_active = len(self._active_futures)

            # Check global concurrency limit (None = unlimited)
            global_limit_ok = (
                self.max_concurrent_tuning is None
                or current_active < self.max_concurrent_tuning
            )

            if global_limit_ok:
                try:
                    # Wait for a job from the queue (timeout to allow periodic cleanup)
                    job = self._job_queue.get(timeout=5)

                    metadata = job.get("metadata", {})
                    job_name = metadata.get("name")
                    namespace = metadata.get("namespace", "default")

                    # Check namespace-level concurrency limit
                    if self.max_concurrent_tuning_per_namespace is not None:
                        ns_count = sum(
                            1
                            for ns in self._active_job_namespaces.values()
                            if ns == namespace
                        )
                        if ns_count >= self.max_concurrent_tuning_per_namespace:
                            # Put job back in queue and wait for capacity
                            self._job_queue.put(job)
                            logger.debug(
                                f"[Consumer] Namespace {namespace} at capacity "
                                f"({ns_count}/{self.max_concurrent_tuning_per_namespace}), "
                                f"requeueing job {job_name}"
                            )
                            # Wait for a job to complete (with timeout for shutdown check)
                            time.sleep(self.polling_interval)
                            continue

                    logger.info(f"[Consumer] Processing job {job_name} from queue")
                    self._start_tuning_job(job)

                except queue.Empty:
                    # No jobs in queue, just continue to check for completed tuners
                    pass

            else:
                # At global capacity, wait for a job to complete
                time.sleep(self.polling_interval)

            # Log status periodically
            if current_active > 0 or not self._job_queue.empty():
                max_str = (
                    str(self.max_concurrent_tuning)
                    if self.max_concurrent_tuning
                    else "unlimited"
                )
                logger.debug(
                    f"[Consumer] Active: {current_active}/{max_str}, Queue: {self._job_queue.qsize()}"
                )

        logger.info("[Consumer] Shutting down")

    def run(self):
        """
        Run the scheduler continuously.
        """
        logger.info("Starting PyTorchJob tuning scheduler")
        if self.max_concurrent_tuning:
            logger.info(f"Max concurrent tuning: {self.max_concurrent_tuning}")
        else:
            logger.info("Max concurrent tuning: unlimited")
        if self.max_concurrent_tuning_per_namespace:
            logger.info(
                f"Max concurrent per namespace: {self.max_concurrent_tuning_per_namespace}"
            )
        logger.info(f"Tuning rules: {len(self.tuning_rules)}")

        # Start the producer thread
        producer_thread = threading.Thread(
            target=self._tuning_job_producer, daemon=True, name="tuning-job-producer"
        )
        producer_thread.start()

        try:
            # Run the consumer in the main thread
            self._tuning_job_consumer()
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            raise
        finally:
            self.shutdown()

    def shutdown(self):
        """
        Gracefully shutdown the scheduler.

        This will:
        1. Signal all threads to stop
        2. Wait for active tuning jobs to complete
        3. Shutdown the executor
        """
        logger.info("Initiating scheduler shutdown...")

        # Signal all threads to shutdown
        self._shutdown_event.set()

        # Wait for active tuning jobs to complete with a timeout
        logger.info(
            f"Waiting for {len(self._active_futures)} active tuning jobs to complete..."
        )

        # Give tuning jobs some time to complete (e.g., 5 minutes)
        max_wait_time = 300  # 5 minutes
        start_time = time.time()

        while self._active_futures and (time.time() - start_time) < max_wait_time:
            self._cleanup_completed_tuners()
            if self._active_futures:
                logger.info(
                    f"Still waiting for {len(self._active_futures)} jobs to complete..."
                )
                time.sleep(10)

        if self._active_futures:
            logger.warning(
                f"Timeout: {len(self._active_futures)} jobs still running, forcing shutdown"
            )

        # Shutdown the executor
        logger.info("Shutting down ThreadPoolExecutor...")
        self.executor.shutdown(wait=True, cancel_futures=True)

        logger.info("Scheduler shutdown complete")

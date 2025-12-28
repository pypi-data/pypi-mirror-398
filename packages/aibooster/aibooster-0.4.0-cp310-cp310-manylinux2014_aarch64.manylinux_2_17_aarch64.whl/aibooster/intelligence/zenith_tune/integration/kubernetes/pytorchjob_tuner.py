import datetime
import hashlib
import logging
import os
import time
from typing import Any, Callable, Dict, Optional

from kubernetes import client, config, watch
from kubernetes.client.exceptions import ApiException
from optuna.samplers import BaseSampler
from optuna.trial import Trial

from ...distributed import get_world_size
from ...tuners import GeneralTuner
from .pytorchjob import PyTorchJob

logger = logging.getLogger("zenith-tune")


class PyTorchJobTuner(GeneralTuner):
    """Kubernetes PyTorchJob tuner that extends GeneralTuner for Kubernetes environments."""

    def __init__(
        self,
        job_name: str,
        get_namespace: Optional[str] = None,
        submit_namespace: Optional[str] = None,
        output_dir: str = "outputs",
        study_name: Optional[str] = None,
        db_path: Optional[str] = None,
        sampler: Optional[BaseSampler] = None,
        maximize: bool = False,
        timeout_per_trial: int = 86400,  # 24 hours default
        wait_resources: bool = False,
        polling_interval: int = 60,
    ):
        """Initialize the Kubernetes PyTorchJob tuning orchestrator.

        Args:
            job_name: Name of the PyTorchJob to use as original
            get_namespace: Namespace to search for the original job (default: None uses current namespace)
            submit_namespace: Target namespace for job submission (default: current namespace from kubeconfig)
            output_dir: Directory to store study results
            study_name: Name for the Optuna study
            db_path: Path to the database file for Optuna study persistence
            sampler: Sampler to use for optimization
            maximize: Whether to maximize the objective function
            timeout_per_trial: Timeout in seconds for each trial (default: 86400 = 24 hours)
            wait_resources: Whether to wait for resources before each trial
            polling_interval: Interval in seconds for polling checks
        """
        # Check if running in a distributed environment and raise an error if so
        if get_world_size() > 1:
            raise RuntimeError(
                "PyTorchJobTuner should not be run in a distributed environment. "
                "It is designed to run on a single process to orchestrate Kubernetes jobs."
            )

        self.job_name = job_name
        self.timeout_per_trial = timeout_per_trial
        self.wait_resources = wait_resources
        self.polling_interval = polling_interval

        # Setup Kubernetes API clients and get namespace
        self.core_api, self.custom_api = self._setup_api_clients()

        # Set get_namespace - if None, use current namespace
        if get_namespace is None:
            self.get_namespace = self._get_current_namespace()
            logger.info(
                f"Searching for original job in current namespace: {self.get_namespace}"
            )
        else:
            self.get_namespace = get_namespace
            logger.info(
                f"Searching for original job in namespace: {self.get_namespace}"
            )

        # Use provided submit_namespace or get current namespace from context
        if submit_namespace is None:
            self.submit_namespace = self._get_current_namespace()
            logger.info(
                f"Using current namespace for job submission: {self.submit_namespace}"
            )
        else:
            self.submit_namespace = submit_namespace
            logger.info(
                f"Using specified namespace for job submission: {self.submit_namespace}"
            )

        # Validate that the job exists and store it as original job definition
        job_dict = self._get_pytorchjob()
        if job_dict is None:
            raise ValueError(
                f"PyTorchJob '{self.job_name}' not found in namespace '{self.get_namespace}'"
            )

        # Create PyTorchJob object (validation happens automatically in constructor)
        self._original_job = PyTorchJob(job_dict)

        # Generate default study_name if not provided
        if study_name is None and db_path is None:
            # Create study name based on job name and timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            study_name = f"{job_name}_{timestamp}"
            logger.info(f"Generated study name: {study_name}")

        super().__init__(
            output_dir=output_dir,
            study_name=study_name,
            db_path=db_path,
            sampler=sampler,
            maximize=maximize,
        )

    def _get_otel_attributes(self):
        """Get additional attributes for OpenTelemetry callback including job-specific info."""
        attributes = super()._get_otel_attributes()
        attributes.update(
            {
                "job.name": self.job_name,
                "k8s.namespace.origin": self.get_namespace,
                "k8s.namespace.submit": self.submit_namespace,
            }
        )
        return attributes

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

            return client.CoreV1Api(), client.CustomObjectsApi()
        except config.ConfigException as e:
            logger.error(f"Failed to load Kubernetes config: {e}")
            raise

    def _get_current_namespace(self) -> str:
        """Get the current namespace from kubeconfig context.

        Returns:
            Current namespace string, defaults to 'default' if not found
        """
        try:
            contexts, active_context = config.list_kube_config_contexts()
            if active_context and "namespace" in active_context.get("context", {}):
                return active_context["context"]["namespace"]
        except Exception as e:
            logger.warning(f"Could not get namespace from kubeconfig: {e}")

        # Default to 'default' namespace if not found
        return "default"

    def _get_pytorchjob(self) -> Optional[Dict[str, Any]]:
        """Get the original PyTorchJob from specified namespace.

        Returns:
            PyTorchJob dictionary if found, None otherwise
        """
        try:
            # Search specific namespace
            job = self.custom_api.get_namespaced_custom_object(
                group="kubeflow.org",
                version="v1",
                namespace=self.get_namespace,
                plural="pytorchjobs",
                name=self.job_name,
            )
            logger.info(
                f"Found PyTorchJob '{self.job_name}' in namespace: {self.get_namespace}"
            )
            return job
        except ApiException as e:
            if e.status == 404:
                logger.error(
                    f"PyTorchJob '{self.job_name}' not found in namespace '{self.get_namespace}'"
                )
                return None
            else:
                logger.error(
                    f"Error accessing PyTorchJob: {e.reason} (status: {e.status})"
                )
                return None

    def _generate_trial_job_name(self, trial_number: int) -> str:
        """Generate Kubernetes job name for a trial based on original job name.

        Args:
            trial_number: The trial number

        Returns:
            Valid Kubernetes job name (max 63 characters) in format:
            {original_job_name}-{hash5}-trial-{number}
        """
        # Create a hash from study_name for uniqueness
        study_hash = hashlib.md5(self.study_name.encode()).hexdigest()[:5]
        trial_suffix = f"-trial-{trial_number}"
        hash_suffix = f"-{study_hash}"

        # Calculate available space for original job name
        suffix_length = len(hash_suffix) + len(trial_suffix)
        max_job_name_length = 63 - suffix_length

        # Truncate original job name if necessary
        original_job_name = self.job_name.replace("_", "-").lower()
        if len(original_job_name) > max_job_name_length:
            original_job_name = original_job_name[:max_job_name_length]

        return f"{original_job_name}{hash_suffix}{trial_suffix}"

    def _create_trial_job(self, base_job: PyTorchJob, trial_number: int) -> PyTorchJob:
        """Create a new job for a specific trial.

        Args:
            base_job: The base PyTorchJob to copy
            trial_number: The trial number

        Returns:
            A PyTorchJob for this trial
        """
        job = PyTorchJob(base_job)  # Copy constructor - no validation needed
        job.set_name(self._generate_trial_job_name(trial_number))

        # Clean up metadata fields
        if "status" in job:
            del job["status"]

        for field in [
            "uid",
            "generateName",
            "managedFields",
            "resourceVersion",
            "creationTimestamp",
            "namespace",  # Remove namespace to allow submitting to different namespace
        ]:
            if field in job["metadata"]:
                del job["metadata"][field]

        # Add annotation to mark this as a tuning job to prevent recursive tuning
        annotations = job["metadata"].get("annotations", {})
        annotations["zenith-tune/created-by"] = "PyTorchJobTuner"
        job["metadata"]["annotations"] = annotations

        return job

    def _submit_job(self, job: PyTorchJob) -> bool:
        """Submit a PyTorchJob to the cluster.

        Args:
            job: The PyTorchJob to submit

        Returns:
            True if submission successful, False otherwise
        """
        try:
            response = self.custom_api.create_namespaced_custom_object(
                group="kubeflow.org",
                version="v1",
                namespace=self.submit_namespace,
                plural="pytorchjobs",
                body=job.to_dict(),
            )
            job_name = response.get("metadata", {}).get("name")
            logger.info(f"Successfully submitted PyTorchJob: {job_name}")
            return True
        except ApiException as e:
            logger.error(
                f"Failed to submit PyTorchJob: {e.reason} (status: {e.status})"
            )
            if e.body:
                try:
                    import json

                    error_body = json.loads(e.body)
                    logger.error(f"Error details: {error_body}")
                except (json.JSONDecodeError, AttributeError):
                    logger.error(f"Error body: {e.body}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error submitting PyTorchJob: {str(e)}")
            return False

    def _wait_for_job_completion(self, job_name: str) -> str:
        """Wait for a job to complete and return its status using Watch API.

        Args:
            job_name: Name of the job to wait for

        Returns:
            Job status: 'Succeeded', 'Failed', or 'Timeout'
        """
        w = watch.Watch()

        try:
            # Watch for changes to the specific PyTorchJob with timeout
            for event in w.stream(
                self.custom_api.list_namespaced_custom_object,
                group="kubeflow.org",
                version="v1",
                namespace=self.submit_namespace,
                plural="pytorchjobs",
                field_selector=f"metadata.name={job_name}",
                timeout_seconds=int(self.timeout_per_trial),
            ):
                # Parse the event
                event_type = event["type"]
                job_object = event["object"]

                # Handle deletion events
                if event_type == "DELETED":
                    logger.warning(f"Job {job_name} was deleted")
                    w.stop()
                    return "Failed"

                # Check job status
                if isinstance(job_object, dict):
                    status = job_object.get("status", {})
                    conditions = status.get("conditions", [])

                    for condition in conditions:
                        if (
                            condition.get("type") == "Succeeded"
                            and condition.get("status") == "True"
                        ):
                            logger.info(f"Job {job_name} succeeded")
                            w.stop()
                            return "Succeeded"
                        elif (
                            condition.get("type") == "Failed"
                            and condition.get("status") == "True"
                        ):
                            reason = condition.get("reason", "Unknown")
                            message = condition.get("message", "")
                            logger.error(f"Job {job_name} failed: {reason} - {message}")
                            w.stop()
                            return "Failed"

        except ApiException as e:
            logger.error(f"Error watching job status: {e.reason} (status: {e.status})")
            return "Failed"
        except Exception as e:
            logger.error(f"Unexpected error watching job: {str(e)}")
            return "Failed"
        finally:
            # Ensure the watch is stopped
            w.stop()

        # If we exit the loop without a clear status, it's a timeout
        logger.warning(
            f"Job {job_name} timed out after {self.timeout_per_trial} seconds"
        )
        return "Timeout"

    def get_logs(self) -> str:
        """Get logs from the original PyTorchJob (public API).

        Returns:
            Job logs as string
        """
        # Get logs from the original job using get_namespace
        return self._get_job_logs(self.job_name, self.get_namespace)

    def _get_job_logs(self, job_name: str, namespace: str) -> str:
        """Get logs from a completed PyTorchJob using Kubernetes API.

        Args:
            job_name: Name of the PyTorchJob
            namespace: Namespace to search for the job

        Returns:
            Job logs as string
        """
        try:
            # Try to confirm the job exists in the expected namespace
            try:
                self.custom_api.get_namespaced_custom_object(
                    group="kubeflow.org",
                    version="v1",
                    namespace=namespace,
                    plural="pytorchjobs",
                    name=job_name,
                )
                logger.info(f"Found job {job_name} in namespace: {namespace}")
            except ApiException as e:
                if e.status == 404:
                    logger.error(f"Job {job_name} not found in namespace {namespace}")
                    return ""
                else:
                    logger.error(f"Error getting job: {e.reason}")
                    return ""

            # Try different label selector formats for PyTorchJob pods
            pods = None

            # Try training.kubeflow.org labels (newer versions)
            label_selectors = [
                f"training.kubeflow.org/job-name={job_name},training.kubeflow.org/replica-type=worker",
                f"pytorch-job-name={job_name},pytorch-replica-type=worker",
                f"pytorch-job-name={job_name}",
                f"job-name={job_name}",
            ]

            for label_selector in label_selectors:
                pods = self.core_api.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=label_selector,
                )
                if pods.items:
                    # Filter for worker pods
                    worker_pods = [
                        p for p in pods.items if "worker" in p.metadata.name.lower()
                    ]
                    if worker_pods:
                        pods.items = worker_pods
                        break

            # If still not found, try without label selector and filter by name
            if not pods or not pods.items:
                all_pods = self.core_api.list_namespaced_pod(namespace=namespace)
                matching_pods = [
                    p
                    for p in all_pods.items
                    if job_name in p.metadata.name
                    and "worker" in p.metadata.name.lower()
                ]
                if matching_pods:
                    pods = type("obj", (object,), {"items": matching_pods})()
                    logger.info(f"Found pod by name matching for job {job_name}")

            if not pods or not pods.items:
                logger.error(
                    f"No worker pods found for PyTorchJob {job_name} in namespace {namespace}"
                )
                return ""

            # Get the first worker pod
            pod_name = pods.items[0].metadata.name
            logger.info(f"Getting logs from pod: {pod_name}")

            # Get logs using Kubernetes API
            logs = self.core_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
            )

            return logs

        except ApiException as e:
            logger.error(
                f"API error getting logs for {job_name}: {e.reason} (status: {e.status})"
            )
            return ""
        except Exception as e:
            logger.error(f"Unexpected error getting logs for {job_name}: {e}")
            return ""

    def _cleanup_job(self, job_name: str):
        """Delete a completed job.

        Args:
            job_name: Name of the job to delete
        """
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="kubeflow.org",
                version="v1",
                namespace=self.submit_namespace,
                plural="pytorchjobs",
                name=job_name,
            )
            logger.info(f"Cleaned up job: {job_name}")
        except ApiException as e:
            logger.warning(f"Failed to cleanup job {job_name}: {e.reason}")

    def _check_resources_available(self, job: PyTorchJob) -> bool:
        """Check if cluster has enough nodes for the job.

        Args:
            job: PyTorchJob to check resources for

        Returns:
            True if resources are available, False otherwise
        """
        try:
            replicas = job.get_worker_replicas()

            # Get all nodes
            nodes = self.core_api.list_node()

            # Count available nodes
            total_nodes = sum(
                1
                for node in nodes.items
                if not node.spec.unschedulable
                and any(
                    condition.type == "Ready" and condition.status == "True"
                    for condition in node.status.conditions or []
                )
            )

            # Get all running PyTorchJobs to calculate used nodes
            pytorchjobs = self.custom_api.list_cluster_custom_object(
                group="kubeflow.org",
                version="v1",
                plural="pytorchjobs",
            )

            used_nodes = sum(
                pj.get("spec", {})
                .get("pytorchReplicaSpecs", {})
                .get("Worker", {})
                .get("replicas", 1)
                for pj in pytorchjobs.get("items", [])
                if any(
                    c.get("type") == "Running" and c.get("status") == "True"
                    for c in pj.get("status", {}).get("conditions", [])
                )
            )

            available_nodes = total_nodes - used_nodes

            if available_nodes < replicas:
                logger.info(
                    f"Insufficient nodes: available={available_nodes}, "
                    f"required={replicas} (total={total_nodes}, used={used_nodes})"
                )
                return False

            logger.debug(f"Nodes available for job: {available_nodes} >= {replicas}")
            return True

        except Exception as e:
            logger.warning(f"Error checking resources: {e}, allowing job to proceed")
            return True

    def _wait_resources(self, job: PyTorchJob) -> None:
        """Wait until cluster has enough resources for the job.

        Args:
            job: PyTorchJob to wait for resources
        """
        job_name = job.get_name()
        interval = self.polling_interval
        wait_count = 0
        start_time = time.monotonic()

        while True:
            if self._check_resources_available(job):
                if wait_count > 0:
                    elapsed_time = time.monotonic() - start_time
                    logger.info(
                        f"Resources now available for job {job_name} after {elapsed_time:.1f}s"
                    )
                return

            wait_count += 1
            logger.info(
                f"Waiting for resources for job {job_name} "
                f"(attempt {wait_count}, next check in {interval}s)"
            )
            time.sleep(interval)

    def _save_trial_logs(
        self,
        job_name: str,
        trial_id: int,
        status: str,
        logs: str = "",
        trial_params: Dict = None,
    ) -> str:
        """Save trial logs to file.

        Args:
            job_name: Name of the Kubernetes job
            trial_id: Trial number
            status: Job status (Succeeded, Failed, etc.)
            logs: Job logs content
            trial_params: Trial parameters dict

        Returns:
            Path to the saved log file
        """
        log_filename = f"trial_{trial_id}.txt"
        log_path = os.path.join(self.study_dir, log_filename)

        try:
            with open(log_path, "w") as f:
                f.write(f"# Job: {job_name}\n")
                f.write(f"# Trial: {trial_id}\n")
                f.write(f"# Status: {status}\n")
                if trial_params:
                    f.write(f"# Parameters: {trial_params}\n")
                if status == "Succeeded" and logs:
                    f.write("# --- Log Output ---\n")
                    f.write(logs)
                elif status != "Succeeded":
                    f.write(f"# Job failed with status: {status}\n")
            logger.info(f"Saved logs for trial {trial_id} to {log_path}")
        except Exception as e:
            logger.error(f"Failed to save logs for trial {trial_id}: {e}")

        return log_path

    def _process_completed_job(
        self,
        job_name: str,
        trial_id: int,
        status: str,
        value_extractor: Callable,
        trial_job: PyTorchJob,
        trial_params: Dict = None,
    ) -> Optional[float]:
        """Process a completed job: get logs, save to file, extract value, cleanup.

        Args:
            job_name: Name of the Kubernetes job
            trial_id: Trial number
            status: Job completion status
            value_extractor: Function to extract objective value
            trial_job: PyTorchJob object for this trial
            trial_params: Trial parameters dict

        Returns:
            Extracted objective value, or None if failed
        """
        value = None

        if status == "Succeeded":
            # Get logs and save to file
            logs = self._get_job_logs(job_name, self.submit_namespace)
            log_path = self._save_trial_logs(
                job_name, trial_id, status, logs, trial_params
            )

            # Extract value from log file
            try:
                value = value_extractor(log_path, trial_job)
                logger.info(f"Trial {trial_id} completed with value: {value}")
            except Exception as e:
                logger.error(f"Error extracting value for trial {trial_id}: {e}")
        else:
            # Save error status to log file
            log_path = self._save_trial_logs(
                job_name, trial_id, status, trial_params=trial_params
            )
            logger.warning(f"Trial {trial_id} failed with status: {status}")

        # Cleanup job
        self._cleanup_job(job_name)

        return value

    def _update_and_submit_job(
        self,
        trial: Trial,
        trial_job: PyTorchJob,
        job_converter: Callable,
        trial_id: int,
    ) -> Optional[PyTorchJob]:
        """Update job with trial parameters and submit to Kubernetes.

        Args:
            trial: Optuna trial object
            trial_job: PyTorchJob to update and submit
            job_converter: Function to update job with trial parameters
            trial_id: Trial number for logging

        Returns:
            Updated PyTorchJob if successful, None if failed
        """
        try:
            trial_job = job_converter(trial, trial_job)
            if not isinstance(trial_job, PyTorchJob):
                raise TypeError(
                    f"job_converter must return PyTorchJob, got {type(trial_job)}"
                )
        except Exception as e:
            logger.error(f"Error in job_converter for trial {trial_id}: {e}")
            return None

        # Submit job
        job_name = trial_job.get_name()
        logger.debug(f"Submitting job with name: {job_name}")
        if not self._submit_job(trial_job):
            logger.error(f"Failed to submit job for trial {trial_id}")
            return None

        logger.info(f"Submitted trial {trial_id} as job {job_name}")
        return trial_job

    def _check_existing_job(self, job_name: str) -> Optional[str]:
        """Check if a job already exists and return its status.

        Args:
            job_name: Name of the job to check

        Returns:
            Job status if exists, None otherwise
            Possible values: "Succeeded", "Failed", "InProgress", None
        """
        try:
            job = self.custom_api.get_namespaced_custom_object(
                group="kubeflow.org",
                version="v1",
                namespace=self.submit_namespace,
                plural="pytorchjobs",
                name=job_name,
            )

            status = job.get("status", {})
            conditions = status.get("conditions", [])

            for condition in conditions:
                if (
                    condition.get("type") == "Succeeded"
                    and condition.get("status") == "True"
                ):
                    return "Succeeded"
                elif (
                    condition.get("type") == "Failed"
                    and condition.get("status") == "True"
                ):
                    return "Failed"

            # Job exists but not completed (could be Pending, Running, etc.)
            return "InProgress"

        except ApiException as e:
            if e.status == 404:
                return None  # Job doesn't exist
            else:
                logger.error(f"Error checking job status: {e.reason}")
                return None

    def _create_objective(self, job_converter: Callable, value_extractor: Callable):
        """Create objective function compatible with GeneralTuner.

        Args:
            job_converter: Function to update job definition
            value_extractor: Function to extract objective value from logs

        Returns:
            Objective function for GeneralTuner.optimize()
        """

        def objective(trial, trial_id: int, dist_info, study_dir: str):
            """Single trial execution for GeneralTuner compatibility."""
            logger.info(f"Starting trial {trial_id}")

            # Check if original job still exists and is in valid state
            original_job = self._get_pytorchjob()
            if original_job is None:
                error_msg = f"Original job '{self.job_name}' no longer exists in namespace '{self.get_namespace}'. Aborting trial."
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            # Check if original job is in Failed state
            original_job_obj = PyTorchJob(original_job)
            job_status = original_job_obj.get_status()
            if job_status == "Failed":
                error_msg = f"Original job '{self.job_name}' is in Failed state. Cannot continue tuning based on failed job. Aborting trial."
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            # Create job for this trial
            trial_job = self._create_trial_job(self._original_job, trial_id)
            job_name = trial_job.get_name()

            # Check if job already exists (e.g., from previous run)
            existing_status = self._check_existing_job(job_name)

            if existing_status is not None:
                # This should not happen - any existing jobs should be handled by optimize() for resumption
                raise RuntimeError(
                    f"Trial {trial_id} job already exists with status '{existing_status}'. "
                    f"This indicates a bug in trial management or duplicate execution."
                )
            # Job doesn't exist, wait for resources and submit new job
            if self.wait_resources:
                self._wait_resources(trial_job)

            trial_job = self._update_and_submit_job(
                trial, trial_job, job_converter, trial_id
            )
            if trial_job is None:
                return None

            # Wait for job completion and process result
            logger.info(f"Waiting for trial {trial_id} job {job_name} to complete...")
            status = self._wait_for_job_completion(job_name)
            return self._process_completed_job(
                job_name, trial_id, status, value_extractor, trial_job, trial.params
            )

        return objective

    def optimize(
        self,
        job_converter: Callable[[Trial, PyTorchJob], PyTorchJob],
        value_extractor: Callable[[str, PyTorchJob], float],
        n_trials: int = 10,
        default_params: Optional[Dict[str, Any]] = None,
    ):
        """Execute Kubernetes PyTorchJob tuning using GeneralTuner framework.

        Args:
            job_converter: Function to update job definition based on trial parameters
                        Takes (Trial, PyTorchJob) and returns PyTorchJob
            value_extractor: Function to extract objective value from log file
                           Takes (log_file_path, job) and returns float value
            n_trials: Number of trials to run
            default_params: Default parameters for the first trial

        Returns:
            Tuple of (best_value, best_params) if successful, (None, None) otherwise
        """
        logger.info(f"Starting Kubernetes PyTorchJob tuning for: {self.job_name}")

        # Check for incomplete job from the last trial when resuming
        if self.is_load_study:
            last_trial_number = len(self.study.trials) - 1
            if last_trial_number >= 0:
                job_name = self._generate_trial_job_name(last_trial_number)
                existing_status = self._check_existing_job(job_name)

                if existing_status in ["InProgress", "Succeeded", "Failed"]:
                    if existing_status == "InProgress":
                        logger.info(
                            f"Found job in progress from previous session: {job_name}, waiting for completion..."
                        )
                        status = self._wait_for_job_completion(job_name)
                    else:
                        logger.info(
                            f"Found uncleaned job from previous session: {job_name} (status: {existing_status})"
                        )
                        status = existing_status

                    # Process the recovered job
                    # Recreate the trial job for value extraction
                    trial_job = self._create_trial_job(
                        self._original_job, last_trial_number
                    )
                    value = self._process_completed_job(
                        job_name, last_trial_number, status, value_extractor, trial_job
                    )
                    if value is not None:
                        logger.info(
                            f"Recovered trial {last_trial_number} completed with value: {value}"
                        )

        # Create objective function compatible with GeneralTuner
        objective_func = self._create_objective(job_converter, value_extractor)

        # Use GeneralTuner's optimize method
        return super().optimize(objective_func, n_trials, default_params)

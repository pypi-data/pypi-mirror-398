"""PyTorchJob wrapper for convenient job definition manipulation."""

import logging
from copy import deepcopy
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("zenith-tune")


class PyTorchJob:
    """
    A convenient interface for modifying PyTorchJob definitions.

    This class wraps the standard Kubernetes PyTorchJob dictionary format
    and provides methods for common modifications during hyperparameter tuning.

    Supports zenith-tune optimization configuration via annotations:

    ```yaml
    metadata:
      annotations:
        zenith-tune/optimization-config: |
          variables:
            - name: "learning_rate"
              type: "float"
              range: [0.001, 0.1]
              log: true
              target_env: "LEARNING_RATE"
            - name: "batch_size"
              type: "int"
              range: [16, 128]
              step: 16
              target_env: "BATCH_SIZE"
            - name: "optimizer"
              type: "categorical"
              choices: ["adam", "sgd"]
              target_env: "OPTIMIZER"
          objective:
            name: "loss"
            regex: "Loss: ([0-9]+\\.?[0-9]*)"
            direction: "minimize"
          n_trials: 100
    ```

    Note: This is not the actual Kubernetes PyTorchJob CRD object, but a
    user-friendly wrapper for job definition manipulation.
    """

    def __init__(self, job_dict_or_job: Union[Dict[str, Any], "PyTorchJob"]):
        """Initialize with a PyTorchJob dictionary or another PyTorchJob.

        Args:
            job_dict_or_job: Dictionary representation of a PyTorchJob or another PyTorchJob instance

        Raises:
            ValueError: If job_dict has invalid PyTorchJob structure
        """
        if isinstance(job_dict_or_job, PyTorchJob):
            # Copy constructor: copy from another PyTorchJob (already validated)
            self._job_dict = deepcopy(job_dict_or_job._job_dict)
        else:
            # Dictionary constructor: validate structure
            self._job_dict = deepcopy(job_dict_or_job)
            self._validate_structure()

    def _validate_structure(self):
        """Validate that the PyTorchJob has the expected structure.

        Raises:
            ValueError: If the job structure is invalid
        """
        try:
            containers = self._job_dict["spec"]["pytorchReplicaSpecs"]["Worker"][
                "template"
            ]["spec"]["containers"]
        except (KeyError, IndexError) as e:
            raise ValueError(
                f"Invalid PyTorchJob structure: missing containers path - {e}"
            )

        if not isinstance(containers, list) or len(containers) == 0:
            raise ValueError(
                f"Invalid containers format: expected non-empty list, got {containers}"
            )

    def set_env(
        self,
        key: str,
        value: str,
        replica_type: str = "Worker",
        container_index: int = 0,
    ) -> "PyTorchJob":
        """Set environment variable for specified replica type.

        Args:
            key: Environment variable name
            value: Environment variable value
            replica_type: Replica type (Worker, Master, etc.)
            container_index: Container index (default: 0)

        Returns:
            Self for method chaining
        """
        try:
            containers = self._job_dict["spec"]["pytorchReplicaSpecs"][replica_type][
                "template"
            ]["spec"]["containers"]

            if container_index >= len(containers):
                raise ValueError(
                    f"Container index {container_index} out of range. Available containers: {len(containers)}"
                )

            # Get or create env list
            env_list = containers[container_index].get("env", [])

            # Update existing environment variable or add new one
            env_found = False
            for env_var in env_list:
                if env_var["name"] == key:
                    env_var["value"] = str(value)
                    env_found = True
                    break

            if not env_found:
                env_list.append({"name": key, "value": str(value)})

            containers[container_index]["env"] = env_list

        except (KeyError, IndexError) as e:
            raise ValueError(
                f"Invalid PyTorchJob structure when setting env {key}={value}: {e}"
            )

        return self

    def set_name(self, name: str) -> "PyTorchJob":
        """Set job name.

        Args:
            name: Job name

        Returns:
            Self for method chaining
        """
        self._job_dict["metadata"]["name"] = str(name)
        return self

    def get_name(self) -> Optional[str]:
        """Get job name.

        Returns:
            Job name or None if not set
        """
        return self._job_dict.get("metadata", {}).get("name")

    def set_command(
        self,
        command: list,
        replica_type: str = "Worker",
        container_index: int = 0,
    ) -> "PyTorchJob":
        """Set command for specified replica type.

        Args:
            command: Command list (e.g., ["python", "train.py"])
            replica_type: Replica type (Worker, Master, etc.)
            container_index: Container index (default: 0)

        Returns:
            Self for method chaining
        """
        try:
            containers = self._job_dict["spec"]["pytorchReplicaSpecs"][replica_type][
                "template"
            ]["spec"]["containers"]

            if container_index >= len(containers):
                raise ValueError(
                    f"Container index {container_index} out of range. Available containers: {len(containers)}"
                )

            containers[container_index]["command"] = command

        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid PyTorchJob structure when setting command: {e}")

        return self

    def get_command(
        self, replica_type: str = "Worker", container_index: int = 0
    ) -> Optional[list]:
        """Get command for specified replica type.

        Args:
            replica_type: Replica type (Worker, Master, etc.)
            container_index: Container index (default: 0)

        Returns:
            Command list or None if not set
        """
        try:
            containers = self._job_dict["spec"]["pytorchReplicaSpecs"][replica_type][
                "template"
            ]["spec"]["containers"]

            if container_index >= len(containers):
                return None

            return containers[container_index].get("command")

        except (KeyError, IndexError):
            return None

    def set_worker_replicas(self, replicas: int) -> "PyTorchJob":
        """Set number of worker replicas.

        Args:
            replicas: Number of worker replicas

        Returns:
            Self for method chaining
        """
        try:
            self._job_dict["spec"]["pytorchReplicaSpecs"]["Worker"]["replicas"] = int(
                replicas
            )
        except KeyError as e:
            raise ValueError(
                f"Invalid PyTorchJob structure when setting worker replicas: {e}"
            )

        return self

    def get_env(
        self, key: str, replica_type: str = "Worker", container_index: int = 0
    ) -> Optional[str]:
        """Get environment variable value.

        Args:
            key: Environment variable name
            replica_type: Replica type (Worker, Master, etc.)
            container_index: Container index (default: 0)

        Returns:
            Environment variable value or None if not found
        """
        env_dict = self.get_env_list(
            replica_type=replica_type, container_index=container_index
        )
        return env_dict.get(key)

    def get_env_list(
        self, replica_type: str = "Worker", container_index: int = 0
    ) -> Dict[str, str]:
        """Get all environment variables as a dictionary.

        Args:
            replica_type: Replica type (Worker, Master, etc.)
            container_index: Container index (default: 0)

        Returns:
            Dictionary of environment variables
        """
        try:
            containers = self._job_dict["spec"]["pytorchReplicaSpecs"][replica_type][
                "template"
            ]["spec"]["containers"]

            if container_index >= len(containers):
                return {}

            env_list = containers[container_index].get("env", [])
            return {env_var["name"]: env_var["value"] for env_var in env_list}

        except (KeyError, IndexError):
            return {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert back to dictionary format.

        Returns:
            Dictionary representation of the PyTorchJob
        """
        return deepcopy(self._job_dict)

    # Tuning annotation support
    def has_tuning_config(self) -> bool:
        """Check if job has tuning optimization config annotation.

        Returns:
            True if zenith-tune/optimization-config annotation exists
        """
        annotations = self.get("metadata", {}).get("annotations", {})
        return "zenith-tune/optimization-config" in annotations

    def get_tuning_config(self) -> Optional[Dict[str, Any]]:
        """Get parsed tuning optimization config from annotations.

        Returns:
            Parsed config dictionary or None if not found/invalid
        """
        annotations = self.get("metadata", {}).get("annotations", {})
        config_yaml = annotations.get("zenith-tune/optimization-config")

        if not config_yaml:
            return None

        try:
            import yaml

            config = yaml.safe_load(config_yaml)
            if isinstance(config, dict):
                return config
        except (ImportError, yaml.YAMLError):
            pass

        return None

    def get_optimization_variables(self) -> List[Dict[str, Any]]:
        """Get optimization variables from tuning config.

        Returns:
            List of variable configurations, empty if not found
        """
        config = self.get_tuning_config()
        if config is None:
            return []
        return config.get("variables", [])

    def get_objective_config(self) -> Optional[Dict[str, Any]]:
        """Get objective configuration from tuning config.

        Returns:
            Objective config dictionary or None if not found
        """
        config = self.get_tuning_config()
        if config is None:
            return None
        return config.get("objective")

    def get_objective_direction(self) -> str:
        """Get objective direction (minimize/maximize) from tuning config.

        Returns:
            "minimize" or "maximize", defaults to "minimize"
        """
        objective = self.get_objective_config()
        if objective is None:
            return "minimize"
        direction = objective.get("direction", "minimize")
        return direction if direction in ["minimize", "maximize"] else "minimize"

    def should_maximize(self) -> bool:
        """Check if objective should be maximized.

        Returns:
            True if should maximize, False if should minimize
        """
        return self.get_objective_direction() == "maximize"

    def get_n_trials(self) -> Optional[int]:
        """Get number of trials from tuning config.

        Returns:
            Number of trials or None if not specified
        """
        config = self.get_tuning_config()
        if config is None:
            return None
        n_trials = config.get("n_trials")
        if isinstance(n_trials, int) and n_trials > 0:
            return n_trials
        return None

    def get_wait_resources(self) -> Optional[bool]:
        """Get wait_resources setting from tuning config.

        Returns:
            True/False if specified, None if not specified
        """
        config = self.get_tuning_config()
        if config is None:
            return None
        wait_resources = config.get("wait_resources")
        if isinstance(wait_resources, bool):
            return wait_resources
        return None

    def get_worker_replicas(self) -> int:
        """Get number of worker replicas.

        Returns:
            Number of worker replicas (default: 1)
        """
        try:
            return self._job_dict["spec"]["pytorchReplicaSpecs"]["Worker"].get(
                "replicas", 1
            )
        except KeyError:
            return 1

    def get_status(self) -> str:
        """Get the status of this PyTorchJob.

        Returns:
            Job status: "Succeeded", "Failed", "InProgress", or "Unknown"
        """
        status = self._job_dict.get("status", {})
        conditions = status.get("conditions", [])

        for condition in conditions:
            if (
                condition.get("type") == "Succeeded"
                and condition.get("status") == "True"
            ):
                return "Succeeded"
            elif (
                condition.get("type") == "Failed" and condition.get("status") == "True"
            ):
                return "Failed"

        # Check if job has started (has any conditions)
        if conditions:
            return "InProgress"

        return "Unknown"

    def validate_tuning_config(self) -> List[str]:
        """Validate tuning configuration format.

        Returns:
            List of validation error messages, empty if valid
        """
        errors = []

        if not self.has_tuning_config():
            return ["No zenith-tune/optimization-config annotation found"]

        config = self.get_tuning_config()
        if config is None:
            return ["Invalid YAML in zenith-tune/optimization-config annotation"]

        # Validate variables
        variables = config.get("variables", [])
        if not isinstance(variables, list):
            errors.append("variables must be a list")
        else:
            for i, var in enumerate(variables):
                if not isinstance(var, dict):
                    errors.append(f"variables[{i}] must be a dictionary")
                    continue

                # Required fields
                for field in ["name", "type", "target_env"]:
                    if field not in var:
                        errors.append(f"variables[{i}] missing required field: {field}")

                # Type-specific validation
                var_type = var.get("type")
                if var_type in ["float", "int"]:
                    if "range" not in var:
                        errors.append(
                            f"variables[{i}] with type {var_type} missing 'range' field"
                        )
                    elif (
                        not isinstance(var.get("range"), list)
                        or len(var.get("range", [])) != 2
                    ):
                        errors.append(
                            f"variables[{i}] 'range' must be a list of 2 elements"
                        )
                elif var_type == "categorical":
                    if "choices" not in var:
                        errors.append(
                            f"variables[{i}] with type categorical missing 'choices' field"
                        )
                    elif not isinstance(var.get("choices"), list):
                        errors.append(f"variables[{i}] 'choices' must be a list")
                elif var_type is not None:
                    errors.append(
                        f"variables[{i}] invalid type: {var_type} (must be float, int, or categorical)"
                    )

        # Validate objective
        objective = config.get("objective")
        if objective is not None:
            if not isinstance(objective, dict):
                errors.append("objective must be a dictionary")
            else:
                for field in ["name", "regex"]:
                    if field not in objective:
                        errors.append(f"objective missing required field: {field}")

                direction = objective.get("direction", "minimize")
                if direction not in ["minimize", "maximize"]:
                    errors.append(
                        f"objective direction must be 'minimize' or 'maximize', got: {direction}"
                    )

        # Validate n_trials
        n_trials = config.get("n_trials")
        if n_trials is not None:
            if not isinstance(n_trials, int) or n_trials <= 0:
                errors.append("n_trials must be a positive integer")

        return errors

    def is_tuning_config_valid(self) -> bool:
        """Check if tuning configuration is valid.

        Returns:
            True if configuration is valid
        """
        return len(self.validate_tuning_config()) == 0

    # Dict-like interface support
    def __getitem__(self, key):
        """Support dict-like access: job['spec']"""
        return self._job_dict[key]

    def __setitem__(self, key, value):
        """Support dict-like assignment: job['spec'] = value"""
        self._job_dict[key] = value

    def __delitem__(self, key):
        """Support dict-like deletion: del job['status']"""
        del self._job_dict[key]

    def __contains__(self, key):
        """Support 'in' operator: 'spec' in job"""
        return key in self._job_dict

    def __len__(self):
        """Support len() function: len(job)"""
        return len(self._job_dict)

    def __iter__(self):
        """Support iteration: for key in job"""
        return iter(self._job_dict)

    def keys(self):
        """Support dict.keys(): job.keys()"""
        return self._job_dict.keys()

    def values(self):
        """Support dict.values(): job.values()"""
        return self._job_dict.values()

    def items(self):
        """Support dict.items(): job.items()"""
        return self._job_dict.items()

    def get(self, key, default=None):
        """Support dict.get(): job.get('spec')"""
        return self._job_dict.get(key, default)

    def update(self, other):
        """Support dict.update(): job.update(other_dict)"""
        self._job_dict.update(other)

    def __repr__(self):
        """String representation for debugging."""
        job_name = self._job_dict.get("metadata", {}).get("name", "unknown")
        return f"PyTorchJob(name='{job_name}')"

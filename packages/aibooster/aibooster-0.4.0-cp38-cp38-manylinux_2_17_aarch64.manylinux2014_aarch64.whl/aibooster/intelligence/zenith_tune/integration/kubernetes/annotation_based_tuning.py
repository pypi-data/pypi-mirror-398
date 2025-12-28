"""Annotation-based tuning converters for PyTorchJob."""

import logging
import re
import statistics
from typing import Any, Dict

from optuna import Trial

from .pytorchjob import PyTorchJob

logger = logging.getLogger("zenith-tune")


def _deep_merge(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge patch into base dictionary.

    Args:
        base: Base dictionary to merge into
        patch: Patch dictionary to apply

    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in patch.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def annotation_job_converter(trial: Trial, job: PyTorchJob) -> PyTorchJob:
    """
    Convert job based on annotation configuration.

    This function reads the zenith-tune/optimization-config annotation
    and applies the hyperparameter values suggested by the trial.

    Args:
        trial: Optuna trial object
        job: Original PyTorchJob

    Returns:
        Modified PyTorchJob with trial parameters applied

    Raises:
        ValueError: If tuning config is invalid or missing required fields
    """
    tuning_config = job.get_tuning_config()
    if tuning_config is None:
        raise ValueError("No tuning config found")

    variables = tuning_config.get("variables", [])
    if not variables:
        raise ValueError("Invalid tuning config: no variables found")

    # Collect parameter labels for ZENITH_TUNE_PARAMS_LABEL
    param_labels = []

    for i, variable in enumerate(variables):
        try:
            # Validate required fields
            if "name" not in variable:
                raise ValueError("Invalid tuning config: variable missing 'name' field")
            if "type" not in variable:
                raise ValueError("Invalid tuning config: variable missing 'type' field")

            name = variable["name"]
            var_type = variable["type"]
            target_env = variable.get("target_env", name.upper())

            if var_type == "float":
                if "range" not in variable:
                    raise ValueError(
                        "Invalid tuning config: float variable missing 'range' field"
                    )
                try:
                    low, high = variable["range"]
                    if len(variable["range"]) != 2:
                        raise ValueError(
                            "Invalid tuning config: range must have exactly 2 values"
                        )
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        "Invalid tuning config: invalid range format"
                    ) from e

                log = variable.get("log", False)
                try:
                    value = trial.suggest_float(name, low, high, log=log)
                except ValueError as e:
                    raise ValueError(
                        f"Invalid tuning config: invalid float range for {name}"
                    ) from e

            elif var_type == "int":
                if "range" not in variable:
                    raise ValueError(
                        "Invalid tuning config: int variable missing 'range' field"
                    )
                try:
                    low, high = variable["range"]
                    if len(variable["range"]) != 2:
                        raise ValueError(
                            "Invalid tuning config: range must have exactly 2 values"
                        )
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        "Invalid tuning config: invalid range format"
                    ) from e

                step = variable.get("step", 1)
                try:
                    value = trial.suggest_int(name, low, high, step=step)
                except ValueError as e:
                    raise ValueError(
                        f"Invalid tuning config: invalid int range for {name}"
                    ) from e

            elif var_type == "categorical":
                if "choices" not in variable:
                    raise ValueError(
                        "Invalid tuning config: categorical variable missing 'choices' field"
                    )
                choices = variable["choices"]
                if not choices or not isinstance(choices, list):
                    raise ValueError(
                        "Invalid tuning config: choices must be a non-empty list"
                    )
                try:
                    value = trial.suggest_categorical(name, choices)
                except ValueError as e:
                    raise ValueError(
                        f"Invalid tuning config: invalid choices for {name}"
                    ) from e

            else:
                raise ValueError(
                    f"Invalid tuning config: unsupported variable type: {var_type}"
                )

            # Set environment variable
            job.set_env(target_env, str(value))

            # Collect parameter label
            param_labels.append(f"{name}={value}")

        except (KeyError, TypeError) as e:
            raise ValueError(
                f"Invalid tuning config: error processing variable {i}"
            ) from e

    # Set tuning metadata environment variables
    job.set_env("ZENITH_TUNE_ENABLED", "1")
    job.set_env("ZENITH_TUNE_TRIAL_ID", str(trial.number))
    if param_labels:
        job.set_env("ZENITH_TUNE_PARAMS_LABEL", ",".join(param_labels))

    # Apply custom patches to job manifest
    custom_patches = tuning_config.get("custom_patches")
    if custom_patches is not None:
        if not isinstance(custom_patches, dict):
            raise ValueError(
                "Invalid tuning config: custom_patches must be a dictionary"
            )

        # Deep merge custom_patches into job manifest
        merged = _deep_merge(job._job_dict, custom_patches)
        job._job_dict = merged
        logger.debug(
            f"Applied custom patches to job manifest: {list(custom_patches.keys())}"
        )

    return job


def annotation_value_extractor(log_path: str, job: PyTorchJob) -> float:
    """
    Extract objective value from logs based on annotation configuration.

    This function reads the zenith-tune/optimization-config annotation
    and extracts the objective value using the specified regex pattern.

    Args:
        log_path: Path to the log file
        job: PyTorchJob object

    Returns:
        Extracted objective value

    Raises:
        ValueError: If no objective configuration found or value cannot be extracted
    """
    tuning_config = job.get_tuning_config()
    if tuning_config is None:
        raise ValueError("No tuning config found")

    objective_config = tuning_config.get("objective")
    if objective_config is None:
        raise ValueError("No objective configuration found in annotation")

    # Validate objective config structure
    if not isinstance(objective_config, dict):
        raise ValueError("Invalid objective config: must be a dictionary")

    if "regex" not in objective_config:
        raise ValueError("Invalid objective config: missing 'regex' field")

    regex_pattern = objective_config["regex"]
    if not regex_pattern or not isinstance(regex_pattern, str):
        raise ValueError("Invalid objective config: 'regex' must be a non-empty string")

    try:
        with open(log_path) as f:
            log_content = f.read()
    except FileNotFoundError:
        raise ValueError(f"Log file not found: {log_path}") from None
    except OSError as e:
        raise ValueError(f"Error reading log file {log_path}: {e}") from e

    # Validate regex pattern
    try:
        compiled_pattern = re.compile(regex_pattern)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern '{regex_pattern}': {e}") from e

    # Find all matches
    try:
        matches = compiled_pattern.findall(log_content)
    except Exception as e:
        raise ValueError(f"Error applying regex pattern: {e}") from e

    if not matches:
        raise ValueError(f"No matches found for pattern: {regex_pattern}")

    # Convert all matches to float
    try:
        values = [float(m) for m in matches]
    except (ValueError, TypeError) as e:
        raise ValueError(f"Failed to convert extracted values to float: {e}") from None

    # Get selector method (default: first for backward compatibility)
    selector = objective_config.get("selector", "last")

    # Apply selector
    if selector == "first":
        value = values[0]
    elif selector == "last":
        value = values[-1]
    elif selector == "min":
        value = min(values)
    elif selector == "max":
        value = max(values)
    elif selector == "mean":
        value = statistics.mean(values)
    elif selector == "median":
        value = statistics.median(values)
    else:
        raise ValueError(
            f"Invalid selector: {selector}. "
            "Must be one of: first, last, min, max, mean, median"
        )

    logger.info(
        f"Extracted objective value: {value} (selector: {selector}, matches: {len(values)})"
    )
    return value

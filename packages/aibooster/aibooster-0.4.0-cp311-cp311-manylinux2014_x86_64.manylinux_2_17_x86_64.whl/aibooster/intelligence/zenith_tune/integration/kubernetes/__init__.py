"""Kubernetes job tuning implementation using 1-job-1-trial approach."""

# Check kubernetes dependency at import time
try:
    import kubernetes  # noqa: F401
except ImportError as e:
    raise ImportError(
        "Kubernetes client is required for job tuning functionality. "
        "Install it with: pip install kubernetes>=30.0.0"
    ) from e

from .pytorchjob import PyTorchJob
from .pytorchjob_tuner import PyTorchJobTuner
from .pytorchjob_tuning_scheduler import (
    JobFilter,
    PyTorchJobTuningScheduler,
    TuningConfig,
    TuningRule,
)

__all__ = [
    "PyTorchJobTuner",
    "PyTorchJob",
    "PyTorchJobTuningScheduler",
    "TuningConfig",
    "JobFilter",
    "TuningRule",
]

from typing import Callable, Optional

from .cpu_affinity import set_cpu_affinity


def worker_affinity_init_fn(
    worker_id: int, available_cpus: int = 0, init_fn: Optional[Callable] = None
):
    """
    Initializes CPU affinity for a worker process.

    Args:
        worker_id: The ID of the worker process.
        available_cpus: The number of available CPUs.
        init_fn: An optional initialization function.
    """
    if available_cpus > 0:
        set_cpu_affinity(0, available_cpus, verbose=worker_id == 0)

    if callable(init_fn):
        init_fn(worker_id)


try:
    from ..integration.mmengine.registry import FUNCTIONS

    FUNCTIONS.register_module(module=worker_affinity_init_fn)
except Exception:
    pass

import logging
import os
from typing import List, Optional, Tuple

import psutil
import pynvml

from ..distributed import get_local_rank

logger = logging.getLogger("zenith-tune")


def is_hyper_threading() -> bool:
    """
    Checks if the system supports hyper-threading.

    Returns:
        True if hyper-threading is enabled, False otherwise.
    """
    return psutil.cpu_count(logical=True) != psutil.cpu_count(logical=False)


def get_current_cpu_affinity() -> List[int]:
    """
    Gets the current CPU affinity of the current process.

    Returns:
        A list of CPU core IDs that the process is currently bound to.
    """
    return sorted(os.sched_getaffinity(os.getpid()))


def get_cpu_affinity_tied_with_device(device_id: int) -> List[int]:
    """
    Gets the CPU affinity tied to a specific GPU device.

    Args:
        device_id: The ID of the GPU device.

    Returns:
        A list of CPU core IDs that are tied to the specified GPU device.
    """
    handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)

    os_bit = 64
    cpu_set_size = (os.cpu_count() + os_bit - 1) // os_bit
    cpu_bitmask_array = pynvml.nvmlDeviceGetCpuAffinity(handle, cpu_set_size)
    cpu_bitmask = "".join(f"{v:064b}" for v in cpu_bitmask_array[::-1])
    cpu_list = [i for i, x in enumerate(cpu_bitmask[::-1]) if x == "1"]
    return cpu_list


def get_cpu_affinity_tied_with_devices() -> List[List[int]]:
    """
    Gets the CPU affinity tied to all available GPU devices.

    Returns:
        A list of lists, where each inner list contains the CPU core IDs
        tied to a specific GPU device.
    """
    pynvml.nvmlInit()

    num_devices = pynvml.nvmlDeviceGetCount()
    cpu_affinity = [get_cpu_affinity_tied_with_device(i) for i in range(num_devices)]

    pynvml.nvmlShutdown()

    return cpu_affinity


def set_cpu_affinity(
    idx_from: int = 0, idx_to: Optional[int] = None, verbose: bool = False
) -> None:
    """
    Sets the CPU affinity for the current process.

    Args:
        idx_from: The starting index of the CPU cores to bind to.
        idx_to: The ending index of the CPU cores to bind to.
        verbose: Whether to print verbose logging information.
    """
    local_rank = get_local_rank()
    cpu_affinity_tied_with_devices = get_cpu_affinity_tied_with_devices()
    local_cpu_affinity = cpu_affinity_tied_with_devices[local_rank]
    num_cpus = len(local_cpu_affinity)
    if num_cpus < 2:
        logging.warning(
            "The number of local cpus must be at least 2. Cpu affinity setting has been disabled."
        )
        return

    def convert_cpu_couples(cpu_list: List[int]) -> List[Tuple[int,]]:
        """Converts a list of CPUs into pairs if hyperthreading is enabled."""
        num_cpus = len(cpu_list)
        cpu_list = sorted(cpu_list)
        if is_hyper_threading() and num_cpus % 2 == 0:
            cpu_couples = [
                (cpu_list[i], cpu_list[i + num_cpus // 2]) for i in range(num_cpus // 2)
            ]
        else:
            cpu_couples = [(cpu,) for cpu in cpu_list]
        return cpu_couples

    def flatten_cpu_couples(cpu_couples: List[Tuple[int,]]) -> List[int]:
        """Flattens a list of CPU couples into a single list of CPUs."""
        return sorted([cpu for cpu_couple in cpu_couples for cpu in cpu_couple])

    num_shared_node_rank = cpu_affinity_tied_with_devices.count(local_cpu_affinity)
    idx_shared_node_rank = cpu_affinity_tied_with_devices[:local_rank].count(
        local_cpu_affinity
    )
    local_cpu_couples = convert_cpu_couples(local_cpu_affinity)
    num_cpu_couples_per_rank = len(local_cpu_couples) // num_shared_node_rank

    # Split a numa node across shared node ranks
    local_cpu_couples = local_cpu_couples[
        num_cpu_couples_per_rank * idx_shared_node_rank :
        num_cpu_couples_per_rank * (idx_shared_node_rank + 1)
    ]  # fmt:skip

    # Limit avaiable cpus by given args
    set_cpu_couples = local_cpu_couples[idx_from:idx_to]

    set_cpu_affinity = flatten_cpu_couples(set_cpu_couples)
    if len(set_cpu_affinity) == 0:
        logging.warning(
            f"Invalid cpu affinity settings: {set_cpu_affinity=}, {idx_from=}, {idx_to=}"
        )
        return

    current_cpu_affinity = get_current_cpu_affinity()
    os.sched_setaffinity(os.getpid(), set_cpu_affinity)
    new_cpu_affinity = get_current_cpu_affinity()
    if verbose:
        logging.info(f"cpu affinity: {current_cpu_affinity}->{new_cpu_affinity}")


if __name__ == "__main__":
    set_cpu_affinity(verbose=True)
    set_cpu_affinity(0, 8, verbose=True)
    set_cpu_affinity(-4, verbose=True)
    set_cpu_affinity(-4, verbose=True)

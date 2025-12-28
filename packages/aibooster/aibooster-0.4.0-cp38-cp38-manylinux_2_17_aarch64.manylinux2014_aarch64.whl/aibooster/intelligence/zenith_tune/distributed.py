import os
from typing import Dict, Optional, Union


def get_dist_info() -> Dict[str, Union[int, str]]:
    """
    Get distributed training information.

    Returns:
        A dictionary containing rank, local_rank, world_size, and launcher.
    """
    return {
        "rank": get_rank(),
        "local_rank": get_local_rank(),
        "world_size": get_world_size(),
        "launcher": get_launcher(),
    }


def get_rank() -> int:
    """
    Get the rank of current process.

    Returns:
        The rank of current process.
    """
    if "RANK" in os.environ:
        return int(os.environ["RANK"])
    if "OMPI_COMM_WORLD_RANK" in os.environ:
        return int(os.environ["OMPI_COMM_WORLD_RANK"])
    return 0


def get_local_rank() -> int:
    """
    Get the local rank of current process.

    Returns:
        The local rank of current process.
    """
    if "LOCAL_RANK" in os.environ:
        return int(os.environ["LOCAL_RANK"])
    if "OMPI_COMM_WORLD_LOCAL_RANK" in os.environ:
        return int(os.environ["OMPI_COMM_WORLD_LOCAL_RANK"])
    return 0


def get_world_size() -> int:
    """
    Get the world size.

    Returns:
        The number of processes.
    """
    if "WORLD_SIZE" in os.environ:
        return int(os.environ["WORLD_SIZE"])
    if "OMPI_COMM_WORLD_SIZE" in os.environ:
        return int(os.environ["OMPI_COMM_WORLD_SIZE"])
    return 1


def get_launcher() -> Optional[str]:
    """
    Get the launcher type.

    Returns:
        The launcher type: 'torch', 'mpi', or None.
    """
    if "RANK" in os.environ:
        return "torch"
    if "OMPI_COMM_WORLD_RANK" in os.environ:
        return "mpi"
    return None

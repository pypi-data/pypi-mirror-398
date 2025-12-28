import argparse
import csv
import os
import time
from importlib import metadata, util
from typing import List, Tuple

import mpi4py.MPI as MPI
import torch
import torch.distributed
from packaging import version

try:
    import pynvml
except ImportError:
    raise ImportError(
        "'pynvml' import package (NVIDIA pyNVML) is required. Install the distribution package 'nvidia-ml-py==12.570.86'. \
         Do not install the distribution package 'pynvml' since \
         the distribution package name of the import package 'pynvml' is 'nvidia-ml-py'."
    )

nvidia_ml_py_ver = metadata.version("nvidia-ml-py")
if version.parse(nvidia_ml_py_ver) < version.parse("12.570.86"):
    raise ImportError(
        "Incorrect version of 'nvidia-py-ml' distribution package is installed. \
         The program requires the distribution package 'nvidia-ml-py>=12.570.86' since \
         pynvml.NVML_NVLINK_VERSION_?_? are not defined in 'nvidia-ml-py<=12.560.30'."
    )
if util.find_spec("pynvml_utils") is not None:
    pynvml_ver = metadata.version(
        "pynvml"
    )  # This finds 'pynvml_utils' distribution package's version. Do not confuse with the distribution package 'nvidia-ml-py' whose import package name is 'pynvml'.
    if version.parse(pynvml_ver) < version.parse("12.0.0"):
        raise ImportError(
            "Incorrect version of 'pynvml' distribution package is installed. \
             If you have installed the distribution package 'pynvml' \
             (not confused with 'ndivia-ml-py' (NVIDIA pyNVML)), \
             the version must be 12.0.0 or higher since older versions conflict with 'nvidia-ml-py'."
        )

nRanks = MPI.COMM_WORLD.Get_size()
rank = MPI.COMM_WORLD.Get_rank()
pynvml.nvmlInit()
GPUS_PER_NODE = pynvml.nvmlDeviceGetCount()
pynvml.nvmlShutdown()

warmup_iters = 5
iters = 20
op = torch.distributed.ReduceOp.SUM


# This order must correspond to ncclDataType_t enum definition at https://github.com/NVIDIA/nccl/blob/145e67e70745c5f78f18334f82de29dbe59bde63/src/nccl.h.in#L238-L252
NCCL_DATATYPE_T = {
    k: getattr(torch, k)
    for k in [
        "int8",
        "uint8",
        "int32",
        "uint32",
        "int64",
        "uint64",
        "float16",
        "float32",
        "float64",
        "bfloat16",
        "float8_e4m3fn",
        "float8_e5m2",
    ]
}

UNSUPPORTED_DATATYPES = {
    # Collective communications with the following types are inexecutable on PyTorch while supported by NCCL.
    "uint32",
    "uint64",
    "float8_e4m3fn",
    "float8_e5m2",
}


def byte_value(byte: str) -> int:
    """
    converts data to bytes if in MB, or GB format
    """
    suffix = {"K": 1, "M": 2, "G": 3}
    if byte[-1].upper() in suffix:
        return int(byte[:-1]) * 1024 ** suffix[byte[-1]]
    return int(byte)


def factor_range(minbytes: str, maxbytes: str, stepfactor: float) -> List[int]:
    """
    creates the range for the values for which nccl bw needs to be tested
    """
    assert 1 < stepfactor, stepfactor
    assert 1 <= minbytes <= maxbytes, (minbytes, maxbytes)
    ret = []
    while minbytes <= maxbytes:
        ret.append(int(minbytes))
        minbytes *= stepfactor
    return ret


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--patternfile",
        type=str,
        help="path to CSV file which contains NCCL patterns to reproduce",
    )
    parser.add_argument(
        "--routine",
        type=str,
        choices=["allgather", "allreduce", "reducescatter", "broadcast"],
        help="select which routine to run test for. ignored if patternfile is provided",
    )
    parser.add_argument(
        "-b",
        "--minbytes",
        type=byte_value,
        default="32M",
        help=". ignored if patternfile is provided",
    )
    parser.add_argument(
        "-e",
        "--maxbytes",
        type=byte_value,
        default="32M",
        help=". ignored if patternfile is provided",
    )
    parser.add_argument(
        "-d", "--dtype", type=str, default="float32", choices=NCCL_DATATYPE_T.keys()
    )
    parser_step = parser.add_mutually_exclusive_group()
    parser_step.add_argument(
        "-i",
        "--stepbytes",
        type=byte_value,
        default="1M",
        help=". ignored if patternfile is provided",
    )
    parser_step.add_argument(
        "-f", "--stepfactor", type=float, help=". ignored if patternfile is provided"
    )
    parser.add_argument(
        "-w", "--warmup", type=int, default=5, help="num of iterations for warmup"
    )
    parser.add_argument(
        "-n", "--iters", type=int, default=20, help="num of iterations used for testing"
    )

    return parser.parse_args()


def run_broadcast(
    group: torch.distributed.ProcessGroup,
    bytes: int,
    buffers: torch.Tensor,
    world_size: int,
    dtype: torch.dtype,
) -> Tuple[float, float, float | None]:
    temp = buffers[: bytes // dtype.itemsize]

    target = torch.ones(
        temp.shape[0], device=f"cuda:{rank % GPUS_PER_NODE}", dtype=dtype
    )

    # set value of all tensor in each rank equal to the rank
    target = target * rank

    # broadcast the 0th ranks tensor to all ranks
    for i in range(warmup_iters):
        torch.distributed.broadcast(target, 0, group=group)
        torch.cuda.synchronize()

    torch.distributed.barrier(
        device_ids=[rank % GPUS_PER_NODE]
    )  # ensure all processes start together

    # benchmark
    elapsed_time = 0
    start = time.time()
    for _ in range(iters):
        torch.distributed.broadcast(target, 0, group=group)
        torch.cuda.synchronize()
    end = time.time()
    elapsed_time += (end - start) * 1000 * 1000
    elapsed_time = elapsed_time / iters

    algbw, bw, ideal_bw = calculate_bw(elapsed_time, bytes, world_size, "broadcast")
    return (elapsed_time, algbw, bw, ideal_bw)


def run_reducescatter(
    group: torch.distributed.ProcessGroup,
    bytes: int,
    buffers: torch.Tensor,
    world_size: int,
    dtype: torch.dtype,
) -> Tuple[float, float, float | None]:
    temp = buffers[: bytes // dtype.itemsize // world_size]
    target = torch.zeros_like(temp, device=f"cuda:{rank % GPUS_PER_NODE}", dtype=dtype)
    scattered = torch.ones(
        target.shape[0] * world_size, device=f"cuda:{rank % GPUS_PER_NODE}", dtype=dtype
    )
    for i in range(warmup_iters):
        torch.distributed.reduce_scatter_tensor(target, scattered, group=group)
        torch.cuda.synchronize()

    torch.distributed.barrier(
        device_ids=[rank % GPUS_PER_NODE]
    )  # ensure all processes start together

    # benchmark
    elapsed_time = 0
    start = time.time()
    for _ in range(iters):
        torch.distributed.reduce_scatter_tensor(target, scattered, group=group)
        torch.cuda.synchronize()

    end = time.time()
    elapsed_time += (end - start) * 1000 * 1000
    elapsed_time = elapsed_time / iters

    algbw, bw, ideal_bw = calculate_bw(elapsed_time, bytes, world_size, "reducescatter")
    return (elapsed_time, algbw, bw, ideal_bw)


def run_allgather(
    group: torch.distributed.ProcessGroup,
    bytes: int,
    buffers: torch.Tensor,
    world_size: int,
    dtype: torch.dtype,
) -> Tuple[float, float, float | None]:
    """
    group: distributed group
    bytes: total data that needs to be transferred
    buffers: torch tensor that can fit the maximum num of elements specified in -e argument

    returns:
    (inplace_time, inplace_algbw, inplace_busbw)
    """
    # select the num of elements based on byte size provided
    temp = buffers[: bytes // dtype.itemsize // world_size]
    target = (
        torch.ones_like(temp, device=f"cuda:{rank % GPUS_PER_NODE}", dtype=dtype) * rank
    )

    gathered = torch.zeros(
        (target.shape[0] * world_size),
        device=f"cuda:{rank % GPUS_PER_NODE}",
        dtype=dtype,
    )
    # warmup
    for _ in range(warmup_iters):
        torch.distributed.all_gather_into_tensor(gathered, target, group=group)
        torch.cuda.synchronize()

    torch.distributed.barrier(
        device_ids=[rank % GPUS_PER_NODE]
    )  # ensure all processes start together

    # benchmark
    elapsed_time = 0
    start = time.time()
    for _ in range(iters):
        torch.distributed.all_gather_into_tensor(gathered, target, group=group)
        torch.cuda.synchronize()
    end = time.time()
    elapsed_time += (end - start) * 1000 * 1000
    elapsed_time = elapsed_time / iters

    algbw, bw, ideal_bw = calculate_bw(elapsed_time, bytes, world_size, "allgather")
    return (elapsed_time, algbw, bw, ideal_bw)


def run_allredeuce(
    group: torch.distributed.ProcessGroup,
    bytes: int,
    buffers: torch.Tensor,
    world_size: int,
    dtype: torch.dtype,
) -> Tuple[float, float, float | None]:
    """
    group: distributed group
    bytes: total data that needs to be transferred
    buffers: torch tensor that can fit the maximum num of elements specified in -e argument

    returns:
    (inplace_time, inplace_algbw, inplace_busbw)
    """
    # select the num of elements based on byte size provided
    target = buffers[: bytes // dtype.itemsize]

    # warmup
    for _ in range(warmup_iters):
        torch.distributed.all_reduce(target, op=op, group=group)
        torch.cuda.synchronize()

    # benchmark
    elapsed_time = 0

    torch.distributed.barrier(
        device_ids=[rank % GPUS_PER_NODE]
    )  # ensure all processes start together
    start = time.time()
    for _ in range(iters):
        torch.distributed.all_reduce(target, op=op, group=group)
        torch.cuda.synchronize()
    end = time.time()
    elapsed_time += (end - start) * 1000 * 1000

    elapsed_time = elapsed_time / iters
    algbw, bw, ideal_bw = calculate_bw(elapsed_time, bytes, world_size, "allreduce")
    return elapsed_time, algbw, bw, ideal_bw


def get_internode_unidirectional_bw() -> float:
    # Return the unidirectional bandwidth for internode communication in GB/s.
    # If no known interfaces are found, just returns 0.0.
    internode_interface_name_candidates = {
        # https://manual.sakura.ad.jp/ds/phy/specs/os/ubuntu22rkv1.html
        # Sakura's dedicated server PHY has high bandwidth NICs with the following names:
        "p1p0",
        "p2p0",
        "p3p0",
        "p4p0",
        "p5p0",
        "p6p0",
        "p7p0",
        "p8p0",
    }
    ifspeed_path_format = "/sys/class/net/{ifname}/speed"
    total_link_speed = 0.0  # in GB/s
    for ifname in internode_interface_name_candidates:
        ifspeed_path = ifspeed_path_format.format(ifname=ifname)
        if os.path.isfile(ifspeed_path):
            with open(ifspeed_path) as fp:
                speed_in_mbps = int(fp.read().strip())
            # Chechk if the interface is active.
            #   speed_in_mbps > 0: Active.
            #   speed_in_mbps == -1: Inactive.
            #   otherwise: Unknown.
            if speed_in_mbps > 0:
                total_link_speed += speed_in_mbps / (8 * 1000)
            elif speed_in_mbps != -1:
                raise ValueError(
                    f"Unknown interface speed (interface: {ifname}, speed: {speed_in_mbps})"
                )
    return total_link_speed


def get_nvlink_unidirectional_bw(deviceId: int) -> float:
    # Return the unidirectional bandwidth of a GPU whose device ID = deviceId in GB/s.
    # An NVIDIA GPU has multiple NVLinks and the NVLink speed depends on their generations.
    # https://github.com/open-mpi/hwloc/blob/c88afaf23b2caa41b6b4fdaa73dadc5f8b01bf88/hwloc/topology-nvml.c#L373
    pynvml.nvmlInit()
    total_bw = 0.0
    handle = pynvml.nvmlDeviceGetHandleByIndex(deviceId)
    for i in range(pynvml.NVML_NVLINK_MAX_LINKS):
        # Exception handling is used for checking if the i-th NVLink is active
        # since 'nvidia-ml-py' does not have an interface to get the set of
        # active NVLinks. pynvml.nvmlDeviceGetNvLinkVersion(handle, i) raises
        # an exception when the i-th NVLink is inactive.
        try:
            nvlink_version = pynvml.nvmlDeviceGetNvLinkVersion(handle, i)
            device_arch = pynvml.nvmlDeviceGetArchitecture(handle)

            if nvlink_version in {pynvml.NVML_NVLINK_VERSION_1_0}:
                link_bw = 20
            elif nvlink_version in {
                pynvml.NVML_NVLINK_VERSION_2_0,
                pynvml.NVML_NVLINK_VERSION_2_2,
                pynvml.NVML_NVLINK_VERSION_3_0,
                pynvml.NVML_NVLINK_VERSION_3_1,
                pynvml.NVML_NVLINK_VERSION_4_0,
            }:
                link_bw = 25
            elif nvlink_version in {pynvml.NVML_NVLINK_VERSION_5_0}:
                link_bw = 50
                if device_arch == pynvml.NVML_DEVICE_ARCH_HOPPER:
                    # Workaround for the problem that pynvml.nvmlDeviceGetNvLinkVersion
                    # returns pynvml.NVML_NVLINK_VERSION_5_0 for H100 GPUs unexpectedly.
                    link_bw = 25
            total_bw += link_bw
        except pynvml.NVMLError:
            # i-th NVLink not found.
            continue
    pynvml.nvmlShutdown()
    return total_bw


def calculate_bw(
    time: float, bytes: int, world_size: int, routine: str
) -> Tuple[float, float, float | None]:
    """
    takes the execution time and calculates algo bw, busbw, and ideal bw
    returns (algbw, busbw, idealbw)
    """
    assert routine in ["allreduce", "allgather", "reducescatter", "broadcast"]
    alg_bw = bytes / time / 1e3  # calculate algobw in GBs
    bw = None

    # https://github.com/NVIDIA/nccl-tests/blob/master/doc/PERFORMANCE.md
    if routine == "allreduce":
        bw = alg_bw * 2 * (world_size - 1) / world_size
    elif routine == "allgather" or routine == "reducescatter":
        bw = alg_bw * (world_size - 1) / world_size
    elif routine == "broadcast":
        bw = alg_bw
    else:
        raise ValueError("sanity check: should never get here")

    # Check if the device is supported for calculating ideal_bw.
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(rank % GPUS_PER_NODE)
    device_arch = pynvml.nvmlDeviceGetArchitecture(handle)
    nvlink_version = pynvml.nvmlDeviceGetNvLinkVersion(handle, 0)
    has_ideal_bw_calc_supported_device = (
        nvlink_version
        in {pynvml.NVML_NVLINK_VERSION_4_0, pynvml.NVML_NVLINK_VERSION_5_0}
        and device_arch == pynvml.NVML_DEVICE_ARCH_HOPPER
    )
    pynvml.nvmlShutdown()

    if has_ideal_bw_calc_supported_device:
        # Each of allreduce/allgather/reducescatter/broadcast has same ideal_bw.
        nvbw = get_nvlink_unidirectional_bw(rank % GPUS_PER_NODE)
        has_multiple_nodes = world_size > GPUS_PER_NODE
        if has_multiple_nodes:
            ibw = get_internode_unidirectional_bw()
            has_ideal_bw_calc_supported_interface = ibw > 0.0
            if has_ideal_bw_calc_supported_interface:
                num_nodes = world_size / GPUS_PER_NODE
                ideal_bw = min(
                    (ibw * (world_size - 1) * num_nodes)
                    / (world_size * (num_nodes - 1)),
                    (nvbw * (world_size - 1)) / (world_size - num_nodes),
                )
            else:
                ideal_bw = None
        else:
            ideal_bw = nvbw
    else:
        ideal_bw = None

    return alg_bw, bw, ideal_bw


def get_routine(routine: str) -> callable:
    """
    all routines will have same interface for calling
    returns which routine to use for the test
    """
    assert routine in ["allreduce", "allgather", "reducescatter", "broadcast"]
    algo = None
    if routine == "allreduce":
        algo = run_allredeuce
    elif routine == "allgather":
        algo = run_allgather
    elif routine == "reducescatter":
        algo = run_reducescatter
    else:
        algo = run_broadcast
    return algo


def main():
    # setup for multi gpu
    world_size = MPI.COMM_WORLD.Get_size()
    rank = MPI.COMM_WORLD.Get_rank()
    print(
        f"initializing rank#{rank}/{world_size} local_rank: {rank % GPUS_PER_NODE} / {GPUS_PER_NODE}"
    )

    # Warn about NCCL_ALGO and NCCL_PROTO
    nccAlgo = os.environ.get("NCCL_ALGO")
    nccProto = os.environ.get("NCCL_PROTO")
    if rank == 0:
        if nccAlgo is None:
            print("Warning: NCCL_ALGO is not set, Using default algorithm")
        if nccProto is None:
            print("Warning: NCCL_PROTO is not set, Using default protocol")

    args = parse_args()
    if args.dtype in UNSUPPORTED_DATATYPES:
        raise ValueError(
            f"Collective communications with data type {args.dtype} are unsupported with PyTorch"
        )
    if args.patternfile:
        with open(args.patternfile, "r") as file:
            reader = csv.DictReader(file)
            header = reader.fieldnames
            patterns = [
                {
                    **pattern,
                    # overwrite NCCL_ALGO and NCCL_PROTO with environment variables
                    "ALGO": "Default" if nccAlgo is None else nccAlgo,
                    "PROTOCOL": "Default" if nccProto is None else nccProto,
                }
                for pattern in reader
            ]

    else:
        dtype = NCCL_DATATYPE_T[args.dtype]

        # build range of different data bytes that need to be tested
        if args.stepfactor is not None:
            test_range = factor_range(args.minbytes, args.maxbytes, args.stepfactor)
        else:
            test_range = list(range(args.minbytes, args.maxbytes + 1, args.stepbytes))

        header = [
            "size(B)",
            "count(elements)",
            "type",
            "redop",
        ]

        patterns = [
            {
                header[0]: bytes,
                # gather uses different num of elements per gpu
                header[1]: bytes
                // dtype.itemsize
                // (1 if args.routine != "allgather" else world_size),
                header[2]: args.dtype,
                # same format as nccl-tests
                header[3]: op.name.lower(),
            }
            for bytes in test_range
        ]

    header_output = [
        "in-place time(us)",
        "in-place algbw(GB/s)",
        "in-place busbw(GB/s)",
        "in-place ideal busbw(GB/s)",
        "in-place busbw efficiency(%)",
    ]
    header.extend(header_output)

    # build group for distributed communication of the current world size
    torch.distributed.init_process_group("nccl", rank=rank, world_size=world_size)
    group = torch.distributed.new_group(list(range(world_size)))

    global warmup_iters
    warmup_iters = args.warmup
    global iters
    iters = args.iters

    if rank == 0:
        print(", ".join(header))

    for pattern in patterns:
        routine = pattern.get("routine", args.routine)
        dtype = NCCL_DATATYPE_T[pattern.get("datatype", pattern.get("type"))]
        bytes = int(pattern.get("TOTALBYTES", pattern.get("size(B)")))

        # create buffer
        buffers = torch.ones(
            bytes // dtype.itemsize,
            dtype=dtype,
            device=f"cuda:{rank % GPUS_PER_NODE}",
        )

        header_output = [
            "in-place time(us)",
            "in-place algbw(GB/s)",
            "in-place busbw(GB/s)",
            "in-place ideal busbw(GB/s)",
            "in-place busbw efficiency(%)",
        ]
        (
            pattern[header_output[0]],
            pattern[header_output[1]],
            pattern[header_output[2]],
            pattern[header_output[3]],
        ) = get_routine(routine)(group, bytes, buffers, world_size, dtype)
        # Computing busbw efficiency in percentage.
        if pattern[header_output[3]] is None:
            pattern[header_output[3]] = "N/A"
            pattern[header_output[4]] = "N/A"
        else:
            pattern[header_output[4]] = (
                100 * pattern[header_output[2]] / pattern[header_output[3]]
            )

        if rank == 0:
            print(", ".join([str(pattern[k]) for k in header]), flush=True)

    torch.distributed.barrier(device_ids=[rank % GPUS_PER_NODE])

    torch.distributed.destroy_process_group(group)
    torch.distributed.destroy_process_group()


if __name__ == "__main__":
    main()

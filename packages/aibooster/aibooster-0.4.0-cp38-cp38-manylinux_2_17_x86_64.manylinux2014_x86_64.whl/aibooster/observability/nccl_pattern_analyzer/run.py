import sys

# parameters to extract info in

UNIQUE_PATTERNS = set()

# https://github.com/NVIDIA/nccl/blob/80f6bda4378b99d99e82b4d76a633791cc45fef0/src/nccl.h.in#L237-L250
NCCL_DATATYPE_T = [
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
    "Float8e4m3",
    "Float8e5m2",
]

# https://github.com/NVIDIA/nccl/blob/80f6bda4378b99d99e82b4d76a633791cc45fef0/src/include/nccl_common.h#L55-L62
NCCL_ALGO = ["Tree", "Ring", "CollnetDiret", "CollnetChain", "Nvls", "NvlsTree", "Pat"]

# https://github.com/NVIDIA/nccl/blob/80f6bda4378b99d99e82b4d76a633791cc45fef0/src/include/nccl_common.h#L66-L68
NCCL_PROTO = ["LL", "LL128", "Simple"]


def update_comm_unique_patterns(routine: str, curr_status: dict, content: str):
    """
    This is to update the tracked patterns when a specific pattern is completed
    Decides if the finished pattern is unique and saves the pattern if extracted pattern is unique
    routine:
        is the name of the nccl collective routine currently being tracked
    curr_satus:
        is a dictionary that keeps track of the current nccl routines being tracked
    line:
        is the log from the tracer split in list containing 2 elements [0: process info, 1: comm info]
    returns:
        dict maintaing current comm patterns being tracked
    """
    volume_bytes = int(content.split("Bytes")[0].split()[-1])

    # will not be same depending on different nccl versions
    try:
        algorithm_id = int(content.split("Algo ")[1].split()[0])
        algorithm = NCCL_ALGO[algorithm_id]
    except ValueError as e:  # noqa:F841
        algorithm = content.split("Algo ")[1].split()[0]
    # could also be int or text depending on nccl version
    try:
        protocol_id = int(content.split("proto")[1].split()[0])
        protocol = NCCL_PROTO[protocol_id]
    except ValueError as e:  # noqa:F841
        protocol = content.split("proto")[1].split()[0]

    # older nccl-version does not log time so in case program is run with older version it uses ? place holder for time
    try:
        time_taken = float(content.split("time")[1])
    except Exception as e:
        print(
            "nccl-logger WARN: could not extract the time taken for algo to complete", e
        )
        time_taken = "?"

    if routine in curr_status:
        status = curr_status[routine]
        status = f"{routine},{curr_status[routine]},{algorithm},{protocol},{volume_bytes},{time_taken}"
        UNIQUE_PATTERNS.add(status)
        # reset the current status because the call has been completed
        del curr_status[routine]
    return curr_status


def track_comm_patterns(routine: str, curr_status: dict, content: str):
    """
    if new comm pattern is discovered in the log starts tracking it in curr_status dict.
    if a comm pattern ends, removes it from the tracked status and updates unique patterns
    """

    if "opCount" not in content and "Bytes" not in content:
        return curr_status, routine

    routine = content.split(":")[0].lower()
    routine = routine[1:]  # remove a leading space

    if "opCount" in content:
        # tracking the pattern
        num_elements = int(content.split("count")[-1].split()[0])
        data_type_id = int(content.split("datatype")[-1].split()[0])
        data_type = NCCL_DATATYPE_T[data_type_id]
        nranks = int(content.split("nranks=")[-1].split("]")[0])
        curr_status[routine] = f"{num_elements},{data_type},{nranks}"
    elif "Bytes" in content and "Algo" in content:
        # finishing the tracking of pattern
        curr_status = update_comm_unique_patterns(routine, curr_status, content)
    return curr_status, routine


def main():
    filename = sys.argv[1]

    curr_status = {}
    routine = ""
    with open(filename, "r") as file:
        for line in file:
            if "NCCL INFO" in line:
                content = line.split("NCCL INFO")[1]
                if ":" in content:
                    curr_status, routine = track_comm_patterns(
                        routine, curr_status, content
                    )
                elif "Bytes" in content and "Algo" in content:
                    # update patteren is called here again because logging pattern for ending comm is different in different cuda versions
                    curr_status = update_comm_unique_patterns(
                        routine, curr_status, content
                    )

    print(
        "routine,num_samples,datatype,nranks,ALGO,PROTOCOL,TOTALBYTES,TIME_FOR_EACH_NCCL_COMM_CALL_MICROSEC"
    )

    # sort unique patterns by routine + time if time is available else sort by routine
    global UNIQUE_PATTERNS
    if any("?" in item for item in UNIQUE_PATTERNS):
        # sort by routine
        UNIQUE_PATTERNS = sorted(
            UNIQUE_PATTERNS,
            key=lambda x: [
                x.split(",")[0],
            ],
        )
    else:
        UNIQUE_PATTERNS = sorted(
            UNIQUE_PATTERNS, key=lambda x: [x.split(",")[0], float(x.split(",")[-1])]
        )  # sort by routine + time

    for x in UNIQUE_PATTERNS:
        print(x)


if __name__ == "__main__":
    main()

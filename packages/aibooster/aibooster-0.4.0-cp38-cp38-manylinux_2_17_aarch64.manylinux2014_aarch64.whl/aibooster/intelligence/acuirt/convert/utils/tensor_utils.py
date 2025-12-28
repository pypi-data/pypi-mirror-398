from collections.abc import Mapping, Sequence
from typing import Union, Optional, Any, Tuple, List, Dict

import torch

type_cannot_recursived = (str,)


def move_tensors(data: Union[Sequence, Mapping, torch.Tensor], device):
    # move dict, list nested tensors to cuda
    if isinstance(data, type_cannot_recursived):
        return data
    elif isinstance(data, Mapping):
        return {key: move_tensors(value, device) for key, value in data.items()}
    elif isinstance(data, Sequence):
        return type(data)([move_tensors(item, device) for item in data])
    elif isinstance(data, torch.Tensor):
        return data.to(device)
    else:
        return data


def get_shape_from_tensor(data):
    if isinstance(data, type_cannot_recursived):
        return data
    elif isinstance(data, Mapping):
        return {key: get_shape_from_tensor(value) for key, value in data.items()}
    elif isinstance(data, Sequence):
        return type(data)([get_shape_from_tensor(item) for item in data])
    elif torch.is_tensor(data):
        return tuple(data.shape)
    else:
        return data


def make_tensor(input, device):
    if isinstance(input, (list, tuple)) and all(type(x) is int for x in input):
        return torch.randn(input, device=device)
    if isinstance(input, dict):
        return {key: make_tensor(value, device) for key, value in input.items()}
    if isinstance(input, (list, tuple)):
        return type(input)([make_tensor(x, device) for x in input])
    return input


def flatten_arguments(input):
    result = []
    if isinstance(input, Mapping):
        for el in input.values():
            result.extend(flatten_arguments(el))
    elif isinstance(input, Sequence):
        for el in input:
            result.extend(flatten_arguments(el))
    else:
        result.append(input)
    return result


def is_same_shape(shape_a, shape_b):
    if type(shape_a) is not type(shape_b):
        return False
    if isinstance(shape_a, type_cannot_recursived):
        return True
    if (
        isinstance(shape_a, torch.Size)
        or isinstance(shape_a, tuple)
        and all([isinstance(el, int) for el in shape_a])
    ):
        return shape_a == shape_b
    if isinstance(shape_a, Mapping):
        if shape_a.keys() != shape_b.keys():
            return False
        for key in shape_a.keys():
            if not is_same_shape(shape_a[key], shape_b[key]):
                return False
        return True
    elif isinstance(shape_a, Sequence):
        if len(shape_a) != len(shape_b):
            return False
        for a, b in zip(shape_a, shape_b):
            if not is_same_shape(a, b):
                return False
        return True
    else:
        return True


def parse_arg_names(
    arg_names: Tuple[List[str], Optional[str], Optional[str]],
    sample_data: Tuple[List[Any], Dict[str, Any]],
) -> List[str]:
    """
    Parse argument names from sample data based on torch.onnx.export
    """
    ret: List[str] = []
    arg_name, vararg_name, kwargs_name = arg_names
    len_args = len(arg_name)

    args, kwargs = sample_data

    def decompose_args(data: Any, base_name: str) -> List[str]:
        names: List[str] = []
        if isinstance(data, str) or data is None:
            # string and None are ignored in ONNX export.
            return names
        if isinstance(data, dict):
            for key, value in data.items():
                names.extend(decompose_args(value, f"{base_name}.{key}"))
        elif isinstance(data, (list, tuple)):
            for idx, item in enumerate(data):
                names.extend(decompose_args(item, f"{base_name}.{idx}"))
        else:
            names.append(base_name)
        return names

    # process regular arguments
    for i in range(len_args):
        ret.extend(decompose_args(args[i], arg_name[i]))

    # process *args and **kwargs
    if vararg_name is not None:
        for i in range(len_args, len(args)):
            ret.extend(decompose_args(args[i], f"{vararg_name}.{i - len_args}"))

    if kwargs_name is not None:
        ret.extend(decompose_args(kwargs, f"{kwargs_name}"))

    return ret

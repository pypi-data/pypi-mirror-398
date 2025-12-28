import torch
from torch import nn

from ..utils.logger import AcuiRTDefaultLogger
from ..convert.utils.tensor_utils import move_tensors
from .inference import load_runtime_module


def validate_trt_modules(
    model: nn.Module,
    rt_mode: str,
    engine_path: str,
    argument_infos: dict,
    logger: AcuiRTDefaultLogger,
):
    rt_model = load_runtime_module(model, rt_mode, engine_path, logger)
    arguments = argument_infos["arguments"][id(model)]

    error = []
    for idx in range(len(arguments)):
        args = arguments[idx]
        ret = _validate_batch(model, rt_model, args)
        if ret is None:
            return None
        error.append(ret)
    del rt_model
    return torch.tensor(error)


def _calc_snr(orig_out: torch.Tensor, trt_out: torch.Tensor):
    p_sig = orig_out.square().mean()
    err = orig_out - trt_out

    p_err = err.square().mean()
    if p_err == 0:
        return torch.inf
    else:
        return 10.0 * torch.log10(p_sig / p_err).item()


def _validate_batch(
    model: nn.Module,
    rt_model,
    argument,
):
    model.cuda()
    if len(list(model.parameters())) == 0:
        device = torch.device("cuda")
    else:
        device = next(model.parameters()).device
    args, kwargs = move_tensors(argument, device)

    with torch.no_grad():
        returns = model(*args, **kwargs)
    ret = rt_model(*args, **kwargs)

    if not isinstance(ret, (tuple, list)):
        ret = (ret,)

    error = [
        _calc_snr(a.detach().cpu(), b.detach().cpu()) for a, b in zip(returns, ret)
    ]
    return error

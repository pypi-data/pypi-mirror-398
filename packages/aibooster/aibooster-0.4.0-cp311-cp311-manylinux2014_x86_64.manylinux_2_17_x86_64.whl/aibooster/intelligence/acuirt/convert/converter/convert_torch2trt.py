import tensorrt as trt
import torch
from torch import nn
from torch2trt import torch2trt
from ...utils.logger import AcuiRTDefaultLogger
from ..registration import register_conversion
from ..utils.tensor_utils import get_shape_from_tensor
from ...dataclasses import AcuiRTTorch2TRTConversionReport


@register_conversion("torch2trt")
def convert_with_torch2trt(
    model: nn.Module,
    input_args,
    export_path: str,
    logger: AcuiRTDefaultLogger,
    int8: bool = False,
    fp16: bool = False,
    use_dla: bool = False,
    **kwargs,
):
    """Convert PyTorch model to TensorRT engine using torch2trt.

    Args:
        model (nn.Module): The PyTorch model to be converted.
        input_args: Input arguments used for conversion.
        export_path (str): Path to save the TensorRT engine.
        int8 (bool, optional): Whether to use int8 precision. Defaults to False.
        fp16 (bool, optional): Whether to use fp16 precision. Defaults to False.
        use_dla (bool, optional): Whether to use DLA. Defaults to False.
        **kwargs: Additional arguments for torch2trt conversion.

    Returns:
        None: The function saves the TensorRT engine to the specified path.
    """

    if use_dla:
        default_device_type = trt.DeviceType.DLA
    else:
        default_device_type = trt.DeviceType.GPU
    # convert nn.Module to TensorRT engine with torch2trt
    input_args = input_args[0]
    args, kwargs = input_args

    model_trt = torch2trt(
        model,
        (*args,),
        int8_mode=int8,
        fp16_mode=fp16,
        default_device_type=default_device_type,
    )
    torch.save(model_trt.state_dict(), export_path)
    ret = AcuiRTTorch2TRTConversionReport(
        rt_mode="torch2trt",
        children=None,
        input_shapes=get_shape_from_tensor(args),
        input_args=None,
        class_name=model.__class__,
        module_name=model.__module__,
        status="success",
        error=None,
        traceback=None,
        int8=int8,
        fp16=fp16,
        use_dla=use_dla,
    )
    return ret

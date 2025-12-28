import os
from typing import List, Tuple, Union, Optional

import tensorrt as trt
import torch
from torch import nn
from torch2trt import TRTModule

from ..utils.logger import AcuiRTDefaultLogger
from ..dataclasses import AcuiRTBaseConversionReport


def torch_dtype_from_trt(dtype) -> torch.dtype:
    """Convert TensorRT data types to PyTorch data types.

    Args:
        dtype (trt.DataType): TensorRT data type to convert

    Returns:
        torch.dtype: Corresponding PyTorch data type

    Raises:
        TypeError: If dtype is not supported by PyTorch
    """
    if dtype == trt.int8:
        return torch.int8
    elif dtype == trt.bool:
        return torch.bool
    elif dtype == trt.int32:
        return torch.int32
    elif dtype == trt.float16:
        return torch.float16
    elif dtype == trt.float32:
        return torch.float32
    else:
        raise TypeError("%s is not supported by torch" % dtype)


def torch_device_from_trt(device) -> torch.device:
    """Convert TensorRT device locations to PyTorch device objects.

    Args:
        device (trt.TensorLocation): TensorRT device location to convert

    Returns:
        torch.device: Corresponding PyTorch device (cuda or cpu)

    Raises:
        TypeError: If device location is not supported
    """
    if device == trt.TensorLocation.DEVICE:
        return torch.device("cuda")
    elif device == trt.TensorLocation.HOST:
        return torch.device("cpu")
    else:
        raise TypeError("%s is not supported by torch" % device)


def _parse_trt_version(version_str: str):
    return [int(part) if part.isdigit() else part for part in version_str.split(".")]


class TRTInferenceEngine(nn.Module):
    """TensorRT inference engine wrapper for PyTorch modules.

    Handles dynamic input/output bindings and device-specific execution
    for TensorRT-optimized models.

    Attributes:
        context: TensorRT execution context
        input_names: List of input tensor names
        output_names: List of output tensor names
        output_bindings: Tensor bindings for outputs
        variadic_output_binding_idx: Dictionary of variadic output bindings
        variadic_input_binding_idx: List of variadic input binding indices
        class_name: Optional custom class name for identification
        tensorrt_version_tuple: TensorRT version as a tuple
    """

    def __init__(
        self,
        engine_path: str,
        class_name: Union[str, None] = None,
        *,
        logger: AcuiRTDefaultLogger,
    ):
        """Initialize TensorRT inference engine.

        Args:
            engine_path (str): Path to TensorRT engine file
            class_name (Union[str, None], optional): Custom class name for identification
            logger (AcuiRTDefaultLogger): Logger object for tracking conversion progress
        """
        super().__init__()
        self.context, self.input_names, self.output_names = self.load_engine(
            engine_path,
            logger,
        )
        self.logger = logger

        self.output_bindings = []
        self.variadic_output_binding_idx = {}
        self.variadic_input_binding_idx = []
        self.tensorrt_version_tuple = tuple(_parse_trt_version(trt.__version__))
        self.tensorrt_version_num = "_".join(map(str, self.tensorrt_version_tuple))

        for i, (idx, output_name) in enumerate(self.output_names):
            if self.tensorrt_version_tuple >= (10, 0):
                dtype = torch_dtype_from_trt(
                    self.context.engine.get_tensor_dtype(output_name)
                )
                shape = tuple(self.context.engine.get_tensor_shape(output_name))
                device = torch_device_from_trt(
                    self.context.engine.get_tensor_location(output_name)
                )
            else:
                dtype = torch_dtype_from_trt(self.context.engine.get_binding_dtype(idx))
                shape = tuple(self.context.engine.get_binding_shape(idx))
                device = torch_device_from_trt(self.context.engine.get_location(idx))
            if -1 in shape:
                self.variadic_output_binding_idx[i] = (idx, dtype, device)
                self.output_bindings.append(None)
            else:
                output = torch.empty(size=shape, dtype=dtype, device=device)
                if self.tensorrt_version_tuple >= (10, 0):
                    self.context.set_tensor_address(output_name, output.data_ptr())
                self.output_bindings.append(output)

        for i, (idx, input_name) in enumerate(self.input_names):
            if self.tensorrt_version_tuple >= (10, 0):
                shape = tuple(self.context.engine.get_tensor_shape(input_name))
            else:
                shape = tuple(self.context.engine.get_binding_shape(idx))
            if -1 in shape:
                self.variadic_input_binding_idx.append(i)

        self.class_name = class_name

    @classmethod
    def _flatten(cls, ll):
        result = []
        for item in ll:
            if isinstance(item, (list, tuple)):
                result.extend(cls._flatten(item))
                continue
            result.append(item)
        return result

    @staticmethod
    def load_engine(engine_path: str, logger: AcuiRTDefaultLogger):
        """Load TensorRT engine from file and extract binding information.

        Args:
            engine_path (str): Path to TensorRT engine file
            logger (AcuiRTDefaultLogger): Logger object for tracking conversion progress

        Returns:
            tuple: (execution context, input names list, output names list)

        Raises:
            AssertionError: If engine file fails to deserialize
        """
        with open(engine_path, "rb") as f:
            runtime = trt.Runtime(logger)
            engine = runtime.deserialize_cuda_engine(f.read())
            assert engine is not None, (
                f"Failed to deserialize the engine from file {engine_path}"
            )
            context = engine.create_execution_context()

        input_names: List[Tuple[int, str]] = []
        output_names: List[Tuple[int, str]] = []
        # get version of tensorrt
        tensorrt_version_tuple = tuple(_parse_trt_version(trt.__version__))

        # TensorRT 10.0 or higher
        if tensorrt_version_tuple >= (10, 0):
            for i in range(engine.num_io_tensors):
                name: str = engine.get_tensor_name(i)
                if engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT:
                    input_names.append((i, name))
                elif engine.get_tensor_mode(name) == trt.TensorIOMode.OUTPUT:
                    output_names.append((i, name))
        # TensorRT 8.5 to 9.x
        elif tensorrt_version_tuple >= (8, 5):
            for i in range(engine.num_bindings):
                name: str = engine.get_tensor_name(i)
                tensor_mode = engine.get_tensor_mode(name).name
                if tensor_mode == "INPUT":
                    input_names.append((i, name))
                elif tensor_mode == "OUTPUT":
                    output_names.append((i, name))
        # TensorRT before 8.5
        else:
            for i in range(engine.num_bindings):
                name = engine.get_binding_name(i)
                if engine.binding_is_input(name):
                    input_names.append((i, name))
                elif not engine.binding_is_input(name):
                    output_names.append((i, name))

        return context, input_names, output_names

    def forward_deprecate(self, *args):
        """Execute inference with TensorRT engine using execute_async_v2.

        This method is for compatibility with TensorRT versions before 10.0.
        """
        # deal with variadic input
        bindings = []

        filt_args: List[torch.Tensor] = [
            x for x in self._flatten(args) if hasattr(x, "data_ptr")
        ]
        input_errors: List[str] = []
        if len(filt_args) != len(self.input_names):
            input_errors.append(
                f"input binding count mismatch: expected {len(self.input_names)}, got {len(filt_args)}"
            )

        for idx, x in enumerate(filt_args):
            if idx >= len(self.input_names):
                input_errors.append(
                    f"too many inputs: expected {len(self.input_names)}, got {len(filt_args)}. shape: {x.shape}"
                )

            if idx in self.variadic_input_binding_idx:
                assert self.context.set_binding_shape(idx, x.shape)

            tensor_shape = self.context.get_binding_shape(idx)
            tensor_dtype = torch_dtype_from_trt(
                self.context.engine.get_binding_dtype(idx)
            )
            tensor_device = torch_device_from_trt(
                self.context.engine.get_location(idx)
            ).type

            self.logger.debug(
                f"Input binding {idx} info: expected shape: {tensor_shape}, got {x.shape}. expected dtype: {tensor_dtype}, got {x.dtype}. expected device: {tensor_device}, got {x.device.type}"
            )
            if tensor_shape != x.shape:
                input_errors.append(
                    f"input binding {idx} has shape mismatch: expected {tensor_shape}, got {x.shape}"
                )
            if tensor_dtype != x.dtype:
                input_errors.append(
                    f"input binding {idx} has dtype mismatch: expected {tensor_dtype}, got {x.dtype}"
                )
            if tensor_device != x.device.type:
                input_errors.append(
                    f"input binding {idx} has device mismatch: expected {tensor_device}, got {x.device.type}"
                )

            bindings.append(x.data_ptr())

        if len(self.input_names) > len(filt_args):
            for idx in range(len(filt_args), len(self.input_names)):
                input_errors.append(
                    f"input binding {idx} is not provided, expected shape: {self.context.get_binding_shape(idx)}"
                )

        if len(input_errors) > 0:
            raise RuntimeError("Input validation failed:\n" + "\n".join(input_errors))

        for i, x in enumerate(self.output_bindings):
            if i in self.variadic_output_binding_idx:
                idx, dtype, device = self.variadic_output_binding_idx[i]
                shape = tuple(self.context.get_binding_shape(idx))
                x = torch.empty(size=shape, device=device, dtype=dtype)
            self.output_bindings[i] = x
            bindings.append(x.data_ptr())

        assert len(bindings) == self.context.engine.num_bindings, (
            f"num bindings is different between engine ({self.context.engine.num_bindings}) and present ({len(bindings)})."
        )

        self.context.execute_async_v2(bindings, 0)
        torch.cuda.synchronize()

    def forward(self, *args, **kwargs):
        """Execute inference with TensorRT engine.

        Handles variadic input/output bindings and executes the engine
        asynchronously. Uses `execute_v3` for TensorRT 10.0+ and falls
        back to `execute_async_v2` for older versions.

        Returns:
            torch.Tensor or list: Inference output(s) as PyTorch tensor(s)
        """
        non_tensor = [x for x in self._flatten(args) if not hasattr(x, "data_ptr")]
        if len(non_tensor) > 0:
            self.logger.warning(
                f"{len(non_tensor)} of Non-tensor inputs detected, they will be ignored."
            )
            for el in non_tensor:
                self.logger.debug(f"Non-tensor input: {el}")

        args = list(args) + list(kwargs.values())

        # Use execute_v3 for TensorRT 10.0+
        if self.tensorrt_version_tuple >= (10, 0):
            # Map input tensors to names
            # deal with variadic input
            filt_args: List[torch.Tensor] = [
                x for x in self._flatten(args) if hasattr(x, "data_ptr")
            ]
            input_errors: List[str] = []
            if len(filt_args) != len(self.input_names):
                input_errors.append(
                    f"input binding count mismatch: expected {len(self.input_names)}, got {len(filt_args)}"
                )

            for idx, x in enumerate(filt_args):
                if idx >= len(self.input_names):
                    input_errors.append(
                        f"too many inputs: expected {len(self.input_names)}, got {len(filt_args)}. shape: {x.shape}"
                    )
                    continue

                if idx in self.variadic_input_binding_idx:
                    assert self.context.set_tensor_shape(
                        self.input_names[idx], x.shape
                    ), f"Failed to set shape for input {idx}"
                self.context.set_tensor_address(self.input_names[idx][1], x.data_ptr())
                tensor_shape = self.context.get_tensor_shape(self.input_names[idx][1])
                tensor_dtype = torch_dtype_from_trt(
                    self.context.engine.get_tensor_dtype(self.input_names[idx][1])
                )
                tensor_device = torch_device_from_trt(
                    self.context.engine.get_tensor_location(self.input_names[idx][1])
                ).type

                self.logger.debug(
                    f"Input binding {idx} info: expected shape: {tensor_shape}, got {x.shape}. expected dtype: {tensor_dtype}, got {x.dtype}. expected device: {tensor_device}, got {x.device.type}"
                )
                if tensor_shape != x.shape:
                    input_errors.append(
                        f"input binding {idx} has shape mismatch: expected {tensor_shape}, got {x.shape}"
                    )
                if tensor_dtype != x.dtype:
                    input_errors.append(
                        f"input binding {idx} has dtype mismatch: expected {tensor_dtype}, got {x.dtype}"
                    )
                if tensor_device != x.device.type:
                    input_errors.append(
                        f"input binding {idx} has device mismatch: expected {tensor_device}, got {x.device.type}"
                    )

            if len(self.input_names) > len(filt_args):
                for idx in range(len(filt_args), len(self.input_names)):
                    input_errors.append(
                        f"input binding {idx} is not provided, expected shape: {self.context.get_tensor_shape(self.input_names[idx][1])}"
                    )

            if len(input_errors) > 0:
                raise RuntimeError(
                    "Input validation failed:\n" + "\n".join(input_errors)
                )

            for i, x in enumerate(self.output_bindings):
                if i in self.variadic_output_binding_idx:
                    idx, dtype, device = self.variadic_output_binding_idx[i]
                    tensor_name = next(s for j, s in self.output_names if j == idx)
                    shape = tuple(self.context.get_tensor_shape(tensor_name))
                    x = torch.empty(size=shape, device=device, dtype=dtype)

                    self.context.set_tensor_address(tensor_name, x.data_ptr())
                    self.output_bindings[i] = x
            stream = torch.cuda.Stream()
            self.context.execute_async_v3(stream.cuda_stream)
            torch.cuda.synchronize()

        else:
            self.forward_deprecate(*args)
        output_tensors = self.output_bindings

        if len(output_tensors) == 1:
            return output_tensors[0]
        return output_tensors


def load_runtime_modules(
    model: nn.Module,
    rt_config: AcuiRTBaseConversionReport,
    engine_path: str,
    *,
    logger: Optional[AcuiRTDefaultLogger] = None,
):
    """Recursively load RunTime modules into PyTorch model.

    Supports hierarchical model structures by recursively applying
    RunTime module loading to submodules.

    Args:
        model (nn.Module): Base PyTorch model to modify
        rt_config (dict): RunTime configuration
        engine_path (str): Base path for engine files
        logger (Optional[AcuiRTDefaultLogger]): Logger object for tracking conversion progress. Defaults to None.

    Returns:
        nn.Module: Modified model with RunTime modules loaded
    """
    engine_path = os.path.join(engine_path, "model")

    if logger is None:
        logger = AcuiRTDefaultLogger("AcuiRT")

    return _load_runtime_module_helper(
        model,
        rt_config,
        engine_path,
        logger,
    )


def _load_runtime_module_helper(
    model: nn.Module,
    rt_config: AcuiRTBaseConversionReport,
    engine_path: str,
    logger: AcuiRTDefaultLogger,
):
    if rt_config.rt_mode is not None:
        # overwrite modules with Runtime Engine
        load_path = f"{engine_path}.trt"
        return load_runtime_module(model, rt_config.rt_mode, load_path, logger)

    elif rt_config.children is None:
        pass
    else:
        for key, value in rt_config.children.items():
            # recursively load modules
            setattr(
                model,
                key,
                _load_runtime_module_helper(
                    getattr(model, key),
                    value,
                    engine_path + f"_{key}",
                    logger,
                ),
            )
    return model


def load_runtime_module(
    model: nn.Module, rt_mode: str, engine_path: str, logger: AcuiRTDefaultLogger
):
    """Load RunTime engine into PyTorch module.

    Args:
        model (nn.Module): Target PyTorch module
        rt_mode (str): RunTime mode ("onnx" or "torch2trt")
        engine_path (str): Path to engine file
        logger (AcuiRTDefaultLogger): Logger object for tracking conversion progress

    Returns:
        nn.Module: Modified module with RunTime engine loaded
    """
    class_name = model.__class__.__name__ + "_RT"
    logger.info(f"load engine from: {engine_path}")
    assert os.path.exists(engine_path), f"file not found: {engine_path}"
    if rt_mode == "onnx":
        model = TRTInferenceEngine(engine_path, class_name, logger=logger)
    elif rt_mode == "torch2trt":
        model = TRTModule()
        model.load_state_dict(torch.load(engine_path))
    logger.info("engine loaded")
    return model

import os
from collections.abc import Callable
from typing import Any, Dict, Iterable, Tuple, Union, Optional
from dataclasses import asdict

import torch
from torch import nn
from ..utils.logger import AcuiRTDefaultLogger
from ..convert.converter import auto_preprocess
from ..convert.registration import CONVERSION_REGISTRY
from ..convert.utils.tensor_utils import make_tensor
from ..convert.utils.config import flatten_converted_models, unflatten_config
from ..dataclasses import (
    AcuiRTBaseConversionReport,
    AcuiRTBaseConversionConfig,
    from_dict,
)


def convert_model_kernel(
    model: nn.Module,
    config: Union[
        Dict[str, Any], AcuiRTBaseConversionConfig, AcuiRTBaseConversionReport
    ],
    export_path: str,
    argument_infos: Any,
    logger: AcuiRTDefaultLogger,
) -> AcuiRTBaseConversionReport:
    """Convert model based on configuration settings.

    Args:
        model (nn.Module): PyTorch model to convert
        config (dict): Conversion configuration dictionary
        export_path (str): Base path for exporting converted model
        argument_infos (Any): Input argument information for conversion
        logger (AcuiRTDefaultLogger): Logger object for tracking conversion progress

    Returns:
        dict: Conversion summary with updated configuration
    """
    if isinstance(config, (AcuiRTBaseConversionConfig, AcuiRTBaseConversionReport)):
        config = asdict(config)

    if config.get("rt_mode") is not None:
        # get basic settings from config
        export_path += ".trt"
        logger.info(f"convert {export_path}")

        if config.get("auto", False):
            rt_mode = "auto"
            config["conversion_mode"] = config.pop("rt_mode")
        else:
            rt_mode = config.pop("rt_mode")
        input_args = config.pop("input_args", None)
        input_shapes = config.pop("input_shapes", None)

        assert input_args is None or input_shapes is None, (
            "input_args and input_shapes cannot be both specified"
        )

        if len(list(model.parameters())) == 0:
            device = torch.device("cuda")
        else:
            device = next(model.parameters()).device

        if input_shapes is not None:
            input_args = make_tensor(input_shapes, device)
            assert isinstance(input_args, tuple)
        inputs = [(input_args, {})]

        conversion_fn = CONVERSION_REGISTRY[rt_mode]
        summary: AcuiRTBaseConversionReport = conversion_fn(
            model,
            inputs,
            export_path,
            argument_infos=argument_infos,
            logger=logger,
            **config,
        )
        logger.info(f"converted {export_path}")

        return summary
    else:
        ret_cfg = AcuiRTBaseConversionReport(
            rt_mode=None,
            children=None,
            input_shapes=None,
            input_args=None,
            status="ignored",
            class_name=model.__class__,
            module_name=model.__module__,
            error=None,
            traceback=None,
        )
        report_children = {}
        children = config.get("children", {})
        for key, value in children.items():
            summary = convert_model_kernel(
                getattr(model, key),
                value,
                export_path + f"_{key}",
                argument_infos=argument_infos,
                logger=logger,
            )
            report_children[key] = summary
        ret_cfg.children = report_children
        return ret_cfg


def convert_model(
    model: nn.Module,
    config: Union[dict, AcuiRTBaseConversionReport, AcuiRTBaseConversionConfig],
    export_path: str,
    data_loader: Optional[Iterable[Union[Tuple[Tuple, Dict], Dict]]] = None,
    data_loader_post_process: Optional[Callable] = None,
    *,
    logger: Optional[AcuiRTDefaultLogger] = None,
):
    """Convert model with preprocessing and postprocessing.

    Args:
        model (nn.Module): PyTorch model to convert
        config (dict): Conversion configuration dictionary
        export_path (str): Base path for exporting converted model
        data_loader (Optional[Iterable[Dict]]): Data loader for preprocessing. Defaults to None.
        data_loader_post_process (Optional[Callable]): Postprocessing function for data loader. Defaults to None.
        logger (Optional[AcuiRTDefaultLogger]): Logger object for tracking conversion progress. Defaults to None.

    Returns:
        dict: Conversion configuration dictionary
    """

    if logger is None:
        logger = AcuiRTDefaultLogger("AcuiRT")

    if isinstance(config, dict):
        logger.warning(
            "DeprecationWarning: config is dict, converting to AcuiRTBaseConversionConfig"
        )
        try:
            config = from_dict(config)
        except Exception as e:
            logger.warning(
                f"Could not convert config to AcuiRTBaseConversionConfig, trying unflatten: error: {e}"
            )
            config = unflatten_config(config)
            config = from_dict(config)

    if not os.path.exists(export_path):
        os.makedirs(export_path)
    export_path = os.path.join(export_path, "model")

    ret = auto_preprocess(model, data_loader, data_loader_post_process, logger)
    ret_cfg = convert_model_kernel(model, config, export_path, ret, logger)

    def trim_none_dict(input: dict):
        for key in list(input.keys()):
            if input[key] is None:
                input.pop(key)
            elif isinstance(input[key], dict):
                input[key] = trim_none_dict(input[key])
            if key in input and input[key] == {}:
                input.pop(key)
        return input

    conversion_rate = _report_conversion_rate(ret_cfg, model)

    return (ret_cfg, conversion_rate)


def _report_conversion_rate(config: AcuiRTBaseConversionReport, model: nn.Module):
    flatten_config = flatten_converted_models(config)
    module_names = set(el for el, _ in model.named_modules())

    all_modules = len(module_names)
    if flatten_config is None:
        return (0, 0), 0

    if all_modules == 0:
        return (0, 0), len(flatten_config)

    converted_params = 0
    num_modules = 0
    for query, value in flatten_config.items():
        if len(module_names) == 0:
            break
        if value.status != "success":
            continue
        num_modules += 1
        if query == "":
            result = module_names
        else:
            result = set(
                param_name
                for param_name in module_names
                if param_name == query or param_name.startswith(query + ".")
            )
        converted_params += len(result)
        module_names = module_names.difference(result)

    return (converted_params, all_modules), num_modules

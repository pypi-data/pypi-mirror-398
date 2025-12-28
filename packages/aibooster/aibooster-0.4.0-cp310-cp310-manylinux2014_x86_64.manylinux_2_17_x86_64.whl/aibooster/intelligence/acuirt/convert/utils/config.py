from typing import Dict
from ...dataclasses import AcuiRTBaseConversionReport
import copy


def flatten_converted_models(config: AcuiRTBaseConversionReport):
    ret: Dict[str, AcuiRTBaseConversionReport] = {}
    cfg = copy.deepcopy(config)
    cfg.children = None
    ret[""] = cfg

    if config.children is not None:
        for key, value in config.children.items():
            models = flatten_converted_models(value)
            for el, conf in models.items():
                if el == "":
                    ret[f"{key}"] = conf
                else:
                    ret[f"{key}.{el}"] = conf
    return ret


def unflatten_config(flatten_config: Dict[str, dict]):
    sorted_keys = sorted(flatten_config.keys())
    if "" in flatten_config and len(flatten_config) > 1:
        raise ValueError(
            "Ambiguous structure: Root key ('') cannot coexist with specific child keys."
        )

    for i, raw_key in enumerate(sorted_keys):
        key = str(raw_key)
        if key == "":
            continue
        if not key.isascii():
            raise ValueError(
                f"Invalid key format: '{key}' contains non-ASCII characters."
            )

        parts = key.split(".")
        if not all(
            (part.isidentifier() and part.isascii()) or part.isdigit() for part in parts
        ):
            raise ValueError(
                f"Invalid key format: '{key}' contains invalid characters or empty segments."
            )

        if i + 1 < len(sorted_keys):
            next_key = sorted_keys[i + 1]
            if key != "" and next_key.startswith(key + "."):
                raise ValueError(
                    f"Ambiguous structure: '{key}' is defined as a leaf, but also acts as a parent for '{next_key}'."
                )

    def create_default_node():
        return {
            "rt_mode": None,
            "auto": False,
        }

    root = create_default_node()

    for path, attributes in flatten_config.items():
        if path == "":
            root.update(attributes)
            continue

        parts = path.split(".")
        current_node = root

        for i, part in enumerate(parts):
            if "children" not in current_node:
                current_node["children"] = {}

            if part not in current_node["children"]:
                current_node["children"][part] = create_default_node()

            current_node = current_node["children"][part]

        current_node.update(attributes)

    return root

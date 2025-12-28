import copy
import importlib
import json
import os
import sys
import traceback
from typing import Any, List, Optional

import torch
import yaml


def truncate_long_strings(obj, max_length=50):
    if isinstance(obj, str):
        return obj if len(obj) <= max_length else obj[:max_length] + "..."
    elif isinstance(obj, dict):
        return {k: truncate_long_strings(v, max_length) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [truncate_long_strings(v, max_length) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(truncate_long_strings(v, max_length) for v in obj)
    elif isinstance(obj, torch.Tensor):
        return obj.shape, obj.dtype, obj.device
    else:
        return obj


def deepcopy_except_tensor(obj, exclude_types=[torch.Tensor]):
    return deepcopy_except_types(obj=obj, exclude_types=exclude_types)


def deepcopy_except_types(obj, exclude_types):
    """
    Recursively copy an object, excluding specified data types.

    :param obj: The object to be copied
    :param exclude_types: A list of data types to be excluded from deep copying
    :return: The copied object
    """
    if any(isinstance(obj, t) for t in exclude_types):
        return obj  # Return the object directly without deep copying
    elif isinstance(obj, (list, tuple)):
        return type(obj)(deepcopy_except_types(item, exclude_types) for item in obj)
    elif isinstance(obj, dict):
        return {
            deepcopy_except_types(key, exclude_types): deepcopy_except_types(
                value, exclude_types
            )
            for key, value in obj.items()
        }
    else:
        return copy.deepcopy(obj)


def recursive_extract_models(data: Any, prefix_path: str = "") -> List[str]:
    def merge_paths(base_path: str, new_path: Any) -> str:
        if not isinstance(new_path, str):
            return base_path
        return f"{base_path}/{new_path}" if base_path else new_path

    results: List[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = merge_paths(prefix_path, key)
            results.extend(recursive_extract_models(value, new_prefix))
    elif isinstance(data, list):
        for item in data:
            new_prefix = merge_paths(prefix_path, item)
            results.extend(recursive_extract_models(item, new_prefix))
    elif isinstance(data, str) and prefix_path.endswith(data):
        return [prefix_path]

    return results


def _load_yaml_config(file_path):
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
    return config


def _load_json_config(file_path: str) -> dict:
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


def load_config_file(file_path: str) -> dict:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    if file_path.endswith(".json"):
        return _load_json_config(file_path)
    elif file_path.endswith(".yaml"):
        return _load_yaml_config(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_path}")


def safe_star_import(module: str, package: Optional[str] = None) -> None:
    """
    在模块级执行  from module import * （支持相对导入）
    失败时打印异常，不终止程序
    :param module: 模块名，可带前导点，如 '.nodes_advanced_refluxcontrol'
    :param package: 当前包名，如 'ui.nodes'；若 module 为相对导入则必须传
    """
    try:
        # 1. 导入模块（相对导入必须传 package）
        mod = importlib.import_module(module, package=package)
        # 2. 取 __all__ 或全部非下划线名字
        names = getattr(mod, "__all__", None)
        if names is None:
            names = [k for k in mod.__dict__ if not k.startswith("_")]
        # 3. 注入到调用者 globals
        caller_globals = sys._getframe(1).f_globals
        for name in names:
            caller_globals[name] = getattr(mod, name)
    except Exception as e:
        print(
            f"\033[92m[BizyAir]\033[0m safe_star_import {module} failed: {e}",
            file=sys.stderr,
        )
        traceback.print_exc()

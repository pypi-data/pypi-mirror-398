#!/usr/bin/env python
# coding: utf-8

import os
from typing import Dict, Any, List, Tuple  # noqa: F401
import json
import importlib.util
import inspect

from athenah_ai.logger import logger


def get_tools_in_dir(dir_path: str) -> Tuple[List[str], Dict[str, Any]]:
    functions_list = []
    functions_dict = {}

    # Get all .py files in the directory
    python_files = [f for f in os.listdir(dir_path) if f.endswith(".py")]

    for filename in python_files:
        module_name = filename[:-3]  # Remove '.py' from the end
        module_path = os.path.join(dir_path, filename)

        # Load the module from the file
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get all function members from the module
        module_functions = inspect.getmembers(module, inspect.isfunction)

        # Append functions to the list or dictionary
        for func_name, func_obj in module_functions:
            functions_list.append(func_name)
            functions_dict[func_name] = func_obj  # If using a dictionary

    # Now functions_list contains all functions from all modules
    # functions_dict maps function names to function objects
    return functions_list, functions_dict

def build_agent_tools(tool_names: List[str], dir: str) -> List[Any]:
    try:
        name_list, tool_dict = get_tools_in_dir(dir)
        if tool_names is None:
            raise Exception("Tool names is None")

        logger.info(f"Tools Found #: {len(name_list)}")
        if len(name_list) == 0:
            raise Exception("No Tools found in the directory")
        tools: List[Any] = []
        for name in tool_names:
            logger.info(f"Query for LocalTool: {name}")
            if name in name_list:
                tools.append(tool_dict[name])
        return tools
    except Exception as e:
        logger.error(f"Error building tool list: {e}")
        return []
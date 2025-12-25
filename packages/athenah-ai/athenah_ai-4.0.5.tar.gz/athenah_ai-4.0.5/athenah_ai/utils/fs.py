#!/usr/bin/env python
# coding: utf-8

import os
from typing import Dict, Any, List  # noqa: F401
import json


def read_file(path: str) -> str:
    """Read File

     # noqa: E501

    :param path: Path to file
    :type path: str

    :rtype: str
    """
    with open(path, "r") as f:
        return f.read()


def write_file(path: str, data: Any) -> str:
    """Write File

     # noqa: E501

    :param path: Path to file
    :type path: str

    :rtype: str
    """
    with open(path, "w") as f:
        return f.write(data)


def read_json(path: str) -> Dict[str, object]:
    """Read Json

     # noqa: E501

    :param path: Path to json
    :type path: str

    :rtype: Dict[str, object]
    """
    with open(path) as json_file:
        return json.load(json_file)
    
def write_json(path: str, data: Any):
    """Write Json

     # noqa: E501

    :param path: Path to json
    :type path: str

    :rtype: Dict[str, object]
    """
    # Write the JSON data to the file
    if not path.endswith('.json'):
        raise ValueError("Path must end with .json extension.")
    if not isinstance(data, (dict, list)):
        raise ValueError("Data must be a dictionary or a list.")
    if isinstance(data, dict):
        # If data is a dictionary, convert it to a list of dictionaries
        data = data
    elif isinstance(data, list):
        # If data is a list, ensure each item is a dictionary
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Each item in the list must be a dictionary.")
    # Write the JSON data to the file
    # if not os.path.exists(os.path.dirname(path)):
    #     os.makedirs(os.path.dirname(path))
    with open(path, "w") as json_file:
        return json.dump(data, json_file, indent=4)


def get_files_in_dir(root_path: str, rel_path: str, ext: str = None, number_lines: bool = False) -> List[Dict[str, Any]]:
    """Get Files in Directory with Numbered Lines

     # noqa: E501

    :param path: Path to directory
    :type path: str
    :param ext: File extension to filter by, defaults to None
    :type ext: str, optional

    :rtype: List[Dict[str, Any]]
    """
    files_with_lines = []
    abs_path = os.path.join(root_path, rel_path)
    for inner_root, _, filenames in os.walk(abs_path):
        for filename in filenames:
            if ext is None or filename.endswith(ext):
                file_path = os.path.join(inner_root, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                if number_lines:
                    numbered_content = ""
                    for i, line in enumerate(lines, 1):
                        numbered_content += f"{i:4d}: {line}"
                    files_with_lines.append({
                        "path": file_path,
                        "content": numbered_content
                    })
                else:
                    files_with_lines.append({
                        "path": file_path,
                        "content": "".join(lines)
                    })
    return files_with_lines
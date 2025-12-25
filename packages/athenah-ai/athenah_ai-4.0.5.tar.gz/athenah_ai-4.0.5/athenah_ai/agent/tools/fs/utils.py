import os
import json
from typing import List, Any, Optional, Dict, Union

from langchain_core.tools import tool

# --- Error Classes ---


class FileReadError(Exception):
    pass


class FileWriteError(Exception):
    pass


# --- Constants ---

IGNORE_FOLDERS = {
    "xahau",
    "node_modules",
    "dist",
    "build",
    ".github",
    ".git",
    ".venv",
    ".vscode",
    "__pycache__",
    "poetry.lock",
    "tmp",
    "env",
    "logs",
    "coverage",
    "docs",
    "Builds",
    "bin",
    "cfg",
    "examples",
    "external",
}

CODE_EXTENSIONS = {
    ".py",
    ".cpp",
    ".h",
    ".hpp",
    ".c",
    ".cc",
    ".cxx",
    ".java",
    ".js",
    ".ts",
}

# --- File Tree Utilities ---


@tool
def get_file_tree(root_path: str, ignore: bool = True) -> List[str]:
    """
    Generates a list of file paths representing the file tree under the specified root directory.

    Args:
        root_path (str): The root directory path from which to generate the file tree.
        ignore (bool, optional): If True, directories listed in IGNORE_FOLDERS will be skipped. Defaults to True.

    Returns:
        List[str]: A list of relative file paths found under the root directory.
    """
    file_tree = []
    for dirpath, dirs, filenames in os.walk(root_path):
        if ignore:
            dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(dirpath, filename), root_path)
            file_tree.append(rel_path)
    return file_tree


# --- File I/O Utilities ---


@tool
def read_file(root_path: str, rel_path: str, with_line_numbers: bool = True) -> str:
    """
    Opens and reads the contents of a file specified by a root directory and a relative path.

    Args:
        root_path (str): The root directory path.
        rel_path (str): The relative path to the file from the root directory.

    Returns:
        str: The contents of the file as a string.

    Raises:
        FileReadError: If the file cannot be read for any reason.
    """
    abs_path = os.path.join(root_path, rel_path)
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if with_line_numbers:
            numbered_content = ""
            for i, line in enumerate(lines, 1):
                numbered_content += f"{i:4d}: {line}"
            return numbered_content

        return "".join(lines)
    except Exception as e:
        raise FileReadError(f"Could not read file {rel_path}: {e}")


@tool
def write_file(root_path: str, rel_path: str, content: str) -> None:
    """
    Writes the given content to a file located at the specified relative path within the root directory.

    Args:
        root_path (str): The root directory path where the file will be written.
        rel_path (str): The relative path to the file from the root directory.
        content (str): The content to write to the file.

    Raises:
        FileWriteError: If the file cannot be written due to an exception.
    """
    abs_path = os.path.join(root_path, rel_path)
    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        raise FileWriteError(f"Could not write file {rel_path}: {e}")


# --- Code Manipulation Utilities ---


@tool
def replace_lines(
    root: str,
    rel_path: str,
    start_line: int,
    start_char: int,
    end_line: Optional[int] = None,
    end_char: Optional[int] = None,
    replacement: str = "",
) -> None:
    """
    Replaces a portion of code in a file specified by line and character positions.

    Args:
        root (str): The root directory path.
        rel_path (str): The relative path to the target file from the root.
        start_line (int): The 1-based starting line number for the replacement.
        start_char (int): The 1-based starting character position in the start line.
        end_line (Optional[int], optional): The 1-based ending line number for the replacement. Defaults to None (same as start_line).
        end_char (Optional[int], optional): The 1-based ending character position in the end line. Defaults to None (one character after start_char).
        replacement (str, optional): The string to replace the specified code segment with. Defaults to "".

    Raises:
        FileWriteError: If the line or character positions are out of range, or if any file operation fails.
    """
    abs_path = os.path.join(root, rel_path)
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Convert to 0-based indexing
        sl, sc = start_line - 1, start_char - 1
        el = (end_line - 1) if end_line else sl
        # Since end_char is now inclusive, we need to add 1 to make it exclusive for slicing
        ec = end_char if end_char else sc + 1

        if sl < 0 or sl >= len(lines) or el < 0 or el >= len(lines):
            raise FileWriteError("Line numbers out of range.")

        if sl == el:
            # Single line replace
            line = lines[sl]
            if sc < 0 or ec > len(line):
                raise FileWriteError("Character positions out of range.")
            lines[sl] = line[:sc] + replacement + line[ec:]
        else:
            # Multi-line replace
            # Check bounds
            if sc < 0 or sc > len(lines[sl]):
                raise FileWriteError("Start character position out of range.")
            if ec < 0 or ec > len(lines[el]):
                raise FileWriteError("End character position out of range.")

            first = lines[sl][:sc]
            last = lines[el][ec:]
            lines = lines[:sl] + [first + replacement + last] + lines[el + 1 :]

        with open(abs_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        # After replacing code format the file
        # TODO: create an agnostic formatter
        # os.system(f"clang-format -i {abs_path}")
    except Exception as e:
        raise FileWriteError(f"Failed to replace code in {rel_path}: {e}")


# --- Source Code Search ---


@tool
def search_folder(word: str, folder: str, window: int = 10) -> List[Dict[str, Any]]:
    """
    Searches for occurrences of a specified word in folder within a given folder,
    returning context around each match.

    Args:
        word (str): The word to search for in the source code files.
        folder (str): The root directory to begin the search.
        window (int, optional): The number of lines before and after the match to include as context. Defaults to 10.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each containing:
            - 'symbol': The searched word.
            - 'file_path': The path to the file containing the match.
            - 'lineno': The line number where the match was found (1-based).
            - 'line': The line containing the match, stripped of leading/trailing whitespace.
            - 'context': A string with the surrounding lines (window before and after the match).
    """
    results = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]
        for file in files:
            _, ext = os.path.splitext(file)
            if ext not in CODE_EXTENSIONS:
                continue
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                continue
            for i, line in enumerate(lines):
                if word in line:
                    start = max(i - window, 0)
                    end = min(i + window + 1, len(lines))
                    context = "".join(lines[start:end])
                    results.append(
                        {
                            "symbol": word,
                            "file_path": file_path,
                            "lineno": i + 1,
                            "line": line.strip(),
                            "context": context,
                        }
                    )
    return results


# --- JSON Utilities ---


@tool
def write_json(path: str, data: Union[Dict, List[Dict]]) -> None:
    """
    Writes the given data to a JSON file at the specified path.

    Args:
        path (str): The file path where the JSON data will be written. Must end with '.json'.
        data (Union[Dict, List[Dict]]): The data to write. Must be a dictionary or a list of dictionaries.

    Raises:
        ValueError: If the path does not end with '.json', if data is not a dictionary or a list,
            or if any item in the list is not a dictionary.
        FileWriteError: If there is an error writing the file.
    """
    if not path.endswith(".json"):
        raise ValueError("Path must end with .json extension.")
    if not isinstance(data, (dict, list)):
        raise ValueError("Data must be a dictionary or a list.")
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Each item in the list must be a dictionary.")
    try:
        with open(path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)
    except Exception as e:
        raise FileWriteError(f"Could not write JSON file {path}: {e}")

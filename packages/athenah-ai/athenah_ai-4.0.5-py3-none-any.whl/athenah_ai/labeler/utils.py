def code_matches_line(filename: str, code: str, line_number: int):
    """
    Checks if the provided code matches the content at the specified line number in the given file.

    Parameters:
    - filename (str): The path to the file.
    - code (str): The code to compare.
    - line_number (int): The line number to check (1-based index).

    Returns:
    - bool: True if the code matches the line content, False otherwise.
    """
    try:
        with open(filename, "r") as file:
            for current_line_number, line_content in enumerate(file, start=1):
                if current_line_number == line_number:
                    line_content = line_content.rstrip("\n")
                    return code[:10].lower() == line_content[:10].lower()

            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def update_file_with_code(
    file_path: str,
    code: str,
    line_number: int,
    replace: bool = False,
    num_lines_to_replace: int = 0,
):
    """
    Inserts or replaces code at the specified line number in the file,
    while preserving the original file format and line endings.

    Parameters:
    - file_path (str): The path to the file to be updated.
    - code (str): The new code to insert or replace at the specified line.
    - line_number (int): The line number to start the insertion/replacement (1-based index).
    - replace (bool): If True, replaces existing lines with the new code. Default is False (insert).
    - num_lines_to_replace (int): The number of lines to replace (used if replace=True).

    Raises:
    - ValueError: If the line_number is out of range.
    - IOError: If there's an issue reading or writing to the file.
    """
    try:
        # Read the file's contents and capture the original line endings
        with open(file_path, "r", newline="") as file:
            lines = file.readlines()

        # Adjust line_number to zero-based index
        index = line_number - 1

        if index < 0 or index > len(lines):
            raise ValueError(
                f"Line number {line_number} is out of range. File has {len(lines)} lines."
            )

        # Determine the line ending used in the file (assuming consistent line endings)
        line_ending = "\n"  # Default line ending
        if lines:
            if lines[0].endswith("\r\n"):
                line_ending = "\r\n"
            elif lines[0].endswith("\n"):
                line_ending = "\n"
            elif lines[0].endswith("\r"):
                line_ending = "\r"

        # Split the code into lines and add the appropriate line endings
        code_lines = [line + line_ending for line in code.splitlines()]

        if replace:
            # Replace existing lines with the new code
            end_index = index + num_lines_to_replace
            if end_index > len(lines):
                raise ValueError(
                    f"Cannot replace {num_lines_to_replace} lines starting from line {line_number} as it exceeds the file length."
                )
            lines[index:end_index] = code_lines
        else:
            # Insert the new code without replacing existing lines
            lines[index:index] = code_lines

        # Write the updated lines back to the file
        with open(file_path, "w", newline="") as file:
            file.writelines(lines)

    except Exception as e:
        print(f"An error occurred while updating the file: {e}")
        raise


# ========== JSON Parsing Utilities ==========

import json
import logging

logger = logging.getLogger("app")


def safe_json_loads(s: str):
    """
    Attempts to extract and load valid JSON from a string.
    If not possible, returns None.

    Args:
        s: String that may contain JSON

    Returns:
        Parsed JSON object or None if parsing fails
    """
    try:
        # Remove code block markers and language hints
        s = s.strip()
        if s.startswith("```"):
            s = s.lstrip("`")
            # Remove language hint if present
            if s.startswith("json"):
                s = s[4:]
            s = s.strip()
        # Remove trailing code block if present
        if s.endswith("```"):
            s = s[:-3].strip()
        return json.loads(s)
    except Exception as e:
        logger.error(f"safe_json_loads error: {e} | input: {s}")
        return None

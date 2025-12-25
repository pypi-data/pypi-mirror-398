import os
import re
import ast
import logging
from typing import Set, List

from athenah_ai.config import config

logger = logging.getLogger("app")


# Placeholder for FileType Enum
class FileType:
    UNKNOWN = 0
    JSON = 1
    # Define other file types as needed


# Placeholder for detect_filetype function
def detect_filetype(file_path: str) -> FileType:
    """
    Detects the file type of the given file.
    This implementation uses the file extension.
    """
    _, ext = os.path.splitext(file_path)
    if ext.lower() == ".json":
        return FileType.JSON
    else:
        return FileType.UNKNOWN


class AthenahCleaner:
    storage_type: str = "local"
    id: str = ""
    dir: str = ""
    name: str = ""
    version: str = ""

    def postclean_directory(self, root: str, recursive: bool = False) -> None:
        """
        Post-process the directory after cleaning.
        If recursive is True, it will process subdirectories as well.
        """
        logger.debug(f"POST-CLEAN DIR: {root}")

        # First, remove any .png and .pdf files
        self.remove_binary_files(root, recursive=recursive)

        all_files = []
        ignore_folders = {".git"}
        logger.debug("Finding all files in the root folder...")

        if recursive:
            # Walk through all subdirectories
            for path, subdirs, files in os.walk(root):
                # Ignore directories in ignore_folders
                subdirs[:] = [d for d in subdirs if d not in ignore_folders]
                for name in files:
                    folder_path = os.path.join(path, name)
                    all_files.append(folder_path)
        else:
            # Only list files in the top-level directory
            for name in os.listdir(root):
                folder_path = os.path.join(root, name)
                if os.path.isfile(folder_path):
                    all_files.append(folder_path)

        logger.debug("Finding unknown file types...")
        unknown_files = []
        for file in all_files:
            if detect_filetype(file) == FileType.UNKNOWN:
                unknown_files.append(file)

        logger.debug("Renaming unknown file types to .txt...")
        for file in unknown_files:
            new_name = file + ".txt"
            os.rename(file, new_name)
            logger.debug(f"Renamed {file} to {new_name}")

        logger.debug("Finding all json files...")
        json_files = []
        for file in all_files:
            if detect_filetype(file) == FileType.JSON:
                json_files.append(file)

        logger.debug("Renaming json files to .txt...")
        for file in json_files:
            new_name = file + ".txt"
            os.rename(file, new_name)
            logger.debug(f"Renamed {file} to {new_name}")

        logger.debug("Post-cleaning complete for directory.")

    def postclean_files(self, file_paths: List[str]) -> None:
        """
        Post-process the directory after cleaning.
        If recursive is True, it will process subdirectories as well.
        """
        for file_path in file_paths:
            self.postclean_file(file_path)

    def remove_binary_files(self, root: str, recursive: bool = False) -> None:
        """
        Removes any .png, .pdf, and other binary files in the given directory.
        If recursive is True, it will process subdirectories as well.
        """
        logger.debug("Removing .png and .pdf files...")

        binary_extensions = (".png", ".pdf", ".jpg", ".jpeg", ".ico")
        if recursive:
            # Walk through all subdirectories
            for path, subdirs, files in os.walk(root):
                for name in files:
                    if name.lower().endswith(binary_extensions):
                        file_path = os.path.join(path, name)
                        try:
                            os.remove(file_path)
                            logger.debug(f"Removed file: {file_path}")
                        except Exception as e:
                            logger.error(f"Error removing file {file_path}: {e}")
        else:
            # Only list files in the top-level directory
            for name in os.listdir(root):
                file_path = os.path.join(root, name)
                if os.path.isfile(file_path) and name.lower().endswith(
                    binary_extensions
                ):
                    try:
                        os.remove(file_path)
                        logger.debug(f"Removed file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error removing file {file_path}: {e}")

    def postclean_file(self, file: str) -> None:
        """
        Post-process a single file after cleaning.
        """
        logger.debug(f"POST-CLEAN FILE: {file}")
        filetype = detect_filetype(file)
        if filetype == FileType.UNKNOWN or filetype == FileType.JSON:
            new_name = file + ".txt"
            os.rename(file, new_name)
            logger.debug(f"Renamed {file} to {new_name}")
        else:
            logger.debug(f"No post-cleaning needed for {file}")

    def clean_file(self, filepath: str) -> None:
        """
        Cleans a single file by removing comments that are not docstrings.
        """
        # Use the original filepath
        _, ext = os.path.splitext(filepath)
        language = config.file_processing.language_extensions.get(ext.lower(), None)
        if not language:
            logger.debug(f"Unsupported file: {filepath} type: {ext}")
            return
        try:
            if self.is_binary_file(filepath):
                logger.debug(f"Skipping binary file: {filepath}")
                return
            with open(filepath, "r", encoding="utf-8") as file:
                code = file.read()
        except UnicodeDecodeError:
            logger.error(f"Could not read file due to UnicodeDecodeError: {filepath}")
            return
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return

        try:
            if language == "python":
                cleaned_code = self.clean_python_code(code)
            elif language in ("cpp", "c", "c header"):
                cleaned_code = self.clean_c_cpp_code(code)
            elif language in ("javascript", "typescript"):
                cleaned_code = self.clean_js_ts_code(code)
            else:
                logger.warning(f"No cleaning function for language: {language}")
                return

            with open(filepath, "w", encoding="utf-8") as file:
                file.write(cleaned_code)
            logger.debug(f"Cleaned file: {filepath}")

        except Exception as e:
            logger.error(f"Error cleaning file {filepath}: {e}")

    def is_binary_file(self, filepath: str) -> bool:
        """
        Checks if the file is binary.
        """
        try:
            with open(filepath, "rb") as file:
                chunk = file.read(config.file_processing.binary_detection_sample_size)
                if b"\0" in chunk:
                    return True  # It's a binary file
            return False
        except Exception as e:
            logger.error(f"Error checking if file is binary: {filepath}, {e}")
            return True  # Assume binary if error occurs

    def clean_python_code(self, code: str) -> str:
        """
        Removes comments from Python code while preserving docstrings.
        """
        try:
            # Parse the code into an AST
            parsed_ast = ast.parse(code)

            # Get the set of line numbers that are part of docstrings
            docstring_lines = self.get_docstring_lines(parsed_ast)

            # Split the code into lines for processing
            code_lines = code.splitlines()
            cleaned_lines = []

            # Loop through each line and remove comments unless it's part of a docstring
            for lineno, line in enumerate(code_lines, start=1):
                if lineno in docstring_lines:
                    # Keep the line as it is if it's part of a docstring
                    cleaned_lines.append(line)
                else:
                    # Remove comments from the line
                    cleaned_line = self.remove_python_comment(line)
                    cleaned_lines.append(cleaned_line)

            # Join the cleaned lines back into a single string
            return "\n".join(cleaned_lines)

        except SyntaxError as e:
            logger.error(f"Syntax error when parsing code: {e}")
            return code  # Return the original code if parsing fails
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error when parsing code: {e}")
            return code  # Return the original code if decoding fails

    def get_docstring_lines(self, node: ast.AST) -> Set[int]:
        """
        Recursively collects the line numbers of all docstrings in the AST.
        """
        docstring_lines = set()

        def visit_node(node):
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)
            ):
                docstring = ast.get_docstring(node)
                if docstring:
                    # Get the source code of the docstring node
                    docstring_node = node.body[0]
                    if isinstance(docstring_node, (ast.Expr, ast.Constant)):
                        # Collect line numbers of the docstring
                        start_lineno = docstring_node.lineno
                        end_lineno = getattr(docstring_node, "end_lineno", start_lineno)
                        docstring_lines.update(range(start_lineno, end_lineno + 1))
            for child in ast.iter_child_nodes(node):
                visit_node(child)

        visit_node(node)
        return docstring_lines

    def remove_python_comment(self, line: str) -> str:
        """
        Removes comments from a single line of Python code.
        """
        # Check if there is a comment in the line
        if "#" in line:
            try:
                index = line.index("#")
                in_string = False
                escape = False
                for i, char in enumerate(line):
                    if i >= index:
                        break
                    if char == "\\" and not escape:
                        escape = True
                        continue
                    if char in ('"', "'") and not escape:
                        if not in_string:
                            in_string = char
                        elif in_string == char:
                            in_string = False
                    escape = False
                if not in_string:
                    # Remove the comment
                    line = line[:index].rstrip()
            except ValueError:
                pass
        return line

    def clean_c_cpp_code(self, code: str) -> str:
        """
        Removes comments from C/C++ code while preserving string literals.
        """
        pattern = r"""
            (?P<comment>
                //.*?$         |   # Single-line comments
                /\*.*?\*/          # Multi-line comments
            )
            |
            (?P<string>
                "([^"\\]|\\.)*"   |  # Double-quoted strings
                '([^'\\]|\\.)*'      # Single-quoted strings
            )
        """
        regex = re.compile(pattern, re.VERBOSE | re.MULTILINE | re.DOTALL)

        def replacer(match):
            if match.group("comment"):
                return ""  # Remove comments
            else:
                return match.group("string")  # Keep strings

        return regex.sub(replacer, code)

    def clean_js_ts_code(self, code: str) -> str:
        """
        Removes comments from JavaScript/TypeScript code while preserving string literals.
        """
        # Similar to C/C++ cleaner
        return self.clean_c_cpp_code(code)

    def clean_dir(self, directory: str, recursive: bool = False) -> None:
        """
        Cleans all files in the given directory.
        If recursive is True, it will clean files in subdirectories as well.
        """
        # Now proceed to clean the files
        if recursive:
            # Walk through all subdirectories
            for root, _, files in os.walk(directory):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    logger.debug(f"Cleaning file `{filepath}`")
                    self.clean_file(filepath)
        else:
            # Only list files in the top-level directory
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    logger.debug(f"Cleaning file `{filepath}`")
                    self.clean_file(filepath)

        # Post-clean the directory
        self.postclean_directory(directory, recursive=recursive)

    def clean_files(self, file_paths: List[str]) -> None:
        for file_path in file_paths:
            self.clean_file(file_path)

        # Post-clean the file_paths
        self.postclean_files(file_paths)

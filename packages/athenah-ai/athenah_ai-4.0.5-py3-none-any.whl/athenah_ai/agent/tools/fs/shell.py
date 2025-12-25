import logging
import os
import subprocess
from typing import List, Optional, Any

logger = logging.getLogger(__name__)


class ShellClient:
    """
    ShellClient provides methods to execute shell commands safely and capture their output.
    """

    def __init__(self) -> None:
        pass

    def run_with_args(
        self,
        path: Optional[str],
        command: List[str],
        args: List[str] = [],
        **kwargs: Any,
    ) -> subprocess.CompletedProcess:
        """
        Executes a command with additional arguments in a specified directory.

        Parameters:
            path (Optional[str]): The directory in which to execute the command.
            command (List[str]): The base command to execute.
            args (List[str], optional): Additional arguments to append to the command.
            **kwargs: Additional keyword arguments for subprocess.run.

        Returns:
            subprocess.CompletedProcess: The result of the executed command.

        Raises:
            subprocess.CalledProcessError: If the command exits with a non-zero status.
            Exception: For any other unexpected errors.
        """
        command.extend(args)
        return self.do_run(path, command, **kwargs)

    def do_run(
        self, path: Optional[str], command: List[str], **kwargs: Any
    ) -> subprocess.CompletedProcess:
        """
        Executes a command in a specified directory, capturing output and errors.

        Parameters:
            path (Optional[str]): The directory in which to execute the command.
            command (List[str]): The command to execute.
            **kwargs: Additional keyword arguments for subprocess.run.

        Returns:
            subprocess.CompletedProcess: The result of the executed command.

        Raises:
            subprocess.TimeoutExpired: If the command times out.
            subprocess.CalledProcessError: If the command exits with a non-zero status.
            Exception: For any other unexpected errors.
        """
        try:
            logger.debug(f"Executing command: {' '.join(command)}")

            # Prepare the working directory
            if path:
                os.makedirs(path, exist_ok=True)
                cwd = path
            else:
                cwd = None  # Use the current directory

            # Run the command
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                check=False,
                **kwargs,
            )

            logger.debug(f"Command exited with return code {result.returncode}")
            if result.stdout:
                logger.debug(f"Command output:\n{result.stdout}")
            if result.stderr:
                logger.error(f"Command error output:\n{result.stderr}")

            # Raise an exception if the command failed
            result.check_returncode()

            return result

        except subprocess.TimeoutExpired as e:
            logger.error(
                f"Command '{' '.join(command)}' timed out after {e.timeout} seconds"
            )
            raise
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Command '{' '.join(e.cmd)}' returned non-zero exit status {e.returncode}"
            )
            raise
        except Exception as e:
            logger.exception(
                f"An unexpected error occurred during command execution: {e}"
            )
            raise

    def do_subprocess(
        self, command: List[str], path: Optional[str] = None, **kwargs: Any
    ) -> subprocess.Popen:
        """
        Executes a command using Popen, capturing output and errors.

        Parameters:
            command (List[str]): The command to execute.
            path (Optional[str], optional): The directory in which to execute the command.
            **kwargs: Additional keyword arguments for subprocess.Popen.

        Returns:
            subprocess.Popen: The Popen object representing the executed process.

        Raises:
            subprocess.TimeoutExpired: If the command times out.
            subprocess.CalledProcessError: If the command exits with a non-zero status.
            Exception: For any other unexpected errors.
        """
        try:
            debug_command = f"Executing command: {' '.join(command)}"
            logger.debug(debug_command)

            # Prepare the working directory
            if path:
                os.makedirs(path, exist_ok=True)
                cwd = path
            else:
                cwd = None

            # Start the process
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                **kwargs,
            )

            # Wait for the process to complete and capture output
            stdout, stderr = process.communicate()

            logger.debug(f"Process exited with return code {process.returncode}")
            if stdout:
                logger.debug(f"Process output:\n{stdout}")
            if stderr:
                logger.error(f"Process error output:\n{stderr}")

            # Raise an exception if the process failed
            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    returncode=process.returncode,
                    cmd=command,
                    output=stdout,
                    stderr=stderr,
                )

            return process

        except subprocess.TimeoutExpired as e:
            logger.error(
                f"Command '{' '.join(command)}' timed out after {e.timeout} seconds"
            )
            raise
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Command '{' '.join(e.cmd)}' returned non-zero exit status {e.returncode}"
            )
            raise
        except Exception as e:
            logger.exception(
                f"An unexpected error occurred during subprocess execution: {e}"
            )
            raise

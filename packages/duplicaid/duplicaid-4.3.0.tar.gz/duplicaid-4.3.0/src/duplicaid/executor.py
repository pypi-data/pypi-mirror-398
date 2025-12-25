from abc import ABC, abstractmethod
from typing import Optional, Tuple

from .config import Config


class ExecutorError(Exception):
    """Base exception for all executor errors."""

    pass


# In executor.py

# In executor.py


class BaseExecutor(ABC):
    """
    Abstract Base Class for command execution.

    Defines a common interface for executing commands either locally or remotely
    and provides shared logic for building Docker commands.
    """

    def __init__(self, config: Config):
        self.config = config

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def execute(
        self,
        command: str,
        show_command: bool = True,
        stdin: Optional[str] = None,
        check: bool = True,  # Add this parameter
    ) -> Tuple[str, str, int]:
        """
        Abstract method to execute a command.

        Concrete implementations will run this on a local or remote machine.

        Args:
            command: The command string to execute.
            show_command: Whether to display the command being executed.
            stdin: Optional string data to be passed to the command's standard input.
            check: If True, raise an exception on non-zero exit code.

        Returns:
            A tuple of (stdout, stderr, exit_code).
        """
        raise NotImplementedError

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """
        Abstract method to check if a file exists.

        Args:
            path: The file path to check.

        Returns:
            True if the file exists, False otherwise.
        """
        raise NotImplementedError

    def docker_exec(
        self,
        container: str,
        command: str,
        stdin: Optional[str] = None,
        check: bool = True,
        show_command: bool = True,
    ) -> Tuple[str, str, int]:
        """
        Execute command inside a Docker container.

        Args:
            container: Container name
            command: Command to execute
            stdin: Optional input to pass to command
            check: Whether to raise exception on non-zero exit code
            show_command: Whether to print the command being executed

        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        docker_cmd = f"docker exec {container} {command}"
        return self.execute(
            docker_cmd, stdin=stdin, check=check, show_command=show_command
        )

    def check_container_running(self, container: str) -> bool:
        """
        Check if a Docker container is running.

        Args:
            container: The exact name or ID of the container.

        Returns:
            True if the container is running, False otherwise.
        """
        # The command returns the container name if it's running.
        # If the output is empty, it's not running or doesn't exist.
        command = f"docker ps --filter name=^{container}$ --filter status=running --format '{{{{.Names}}}}'"
        stdout, _, exit_code = self.execute(command, show_command=False, check=False)

        # Check if the exact container name is in the output.
        return exit_code == 0 and container in stdout.strip().split("\n")

    def get_container_status(self, container: str) -> Optional[str]:
        """
        Get the status of a Docker container.

        Args:
            container: The exact name or ID of the container.

        Returns:
            The container status string (e.g., "Up 2 hours", "Exited (0) 5 minutes ago")
            or None if the container is not found.
        """
        command = f"docker ps -a --filter name=^{container}$ --format '{{{{.Status}}}}'"
        stdout, _, exit_code = self.execute(command, show_command=False, check=False)

        if exit_code == 0 and stdout:
            return stdout.strip()
        return None

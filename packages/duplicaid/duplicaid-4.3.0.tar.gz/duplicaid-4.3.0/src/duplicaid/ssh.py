from typing import Optional, Tuple

import paramiko
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from .config import Config
from .executor import BaseExecutor, ExecutorError

console = Console()


class SSHError(ExecutorError):
    pass


class RemoteExecutor(BaseExecutor):
    """SSH client wrapper for executing commands on a remote server."""

    def __init__(self, config: Config):
        super().__init__(config)
        self.client: Optional[paramiko.SSHClient] = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def connect(self) -> None:
        """Establish SSH connection to remote server."""
        if not self.config.validate():
            raise SSHError("Invalid configuration")

        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            with Live(
                Spinner("dots", text=f"Connecting to {self.config.remote_host}..."),
                console=console,
                transient=True,
            ):
                self.client.connect(
                    hostname=self.config.remote_host,
                    port=self.config.remote_port,
                    username=self.config.remote_user,
                    key_filename=self.config.ssh_key_path,
                    timeout=10,
                )

            console.print(f"[green]✓ Connected to {self.config.remote_host}[/green]")

        except Exception as e:
            raise SSHError(f"Failed to connect to {self.config.remote_host}: {e}")

    def disconnect(self) -> None:
        """Close SSH connection."""
        if self.client:
            self.client.close()
            self.client = None

    def execute(
        self,
        command: str,
        show_command: bool = False,
        stdin: Optional[str] = None,
        check: bool = True,
    ) -> Tuple[str, str, int]:
        """Execute command on remote host via SSH."""
        if show_command:
            console.print(f"[dim]$ {command}[/dim]")

        try:
            stdin_channel, stdout, stderr = self.client.exec_command(command)

            stdout_str = stdout.read().decode("utf-8").strip()
            stderr_str = stderr.read().decode("utf-8").strip()
            exit_code = stdout.channel.recv_exit_status()

            if exit_code != 0:
                error_msg = f"Command failed with exit code {exit_code}"
                if stderr_str:
                    error_msg += f"\nStderr: {stderr_str}"
                if stdout_str:
                    error_msg += f"\nStdout: {stdout_str}"

                # Only raise if check=True
                if check:
                    console.print(f"[red]{error_msg}[/red]")
                    raise SSHError(error_msg)

            return stdout_str, stderr_str, exit_code

        except Exception as e:
            if isinstance(e, SSHError):
                raise
            raise SSHError(f"Failed to execute command: {e}")

    def file_exists(self, path: str) -> bool:
        """Check if a file exists on the remote host."""
        _, _, exit_code = self.execute(
            f"test -f {path}",
            show_command=False,
            check=False,  # Don't raise exception on non-zero exit code
        )
        return exit_code == 0

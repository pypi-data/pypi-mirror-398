import subprocess
from typing import Optional, Tuple

from rich.console import Console

from .executor import BaseExecutor, ExecutorError

console = Console()


class LocalError(ExecutorError):
    pass


class LocalExecutor(BaseExecutor):
    """Executor for running commands on the local machine."""

    def execute(
        self,
        command: str,
        show_command: bool = False,
        stdin: Optional[str] = None,
        check: bool = True,
    ) -> Tuple[str, str, int]:
        """Execute command on the local machine."""
        if show_command:
            console.print(f"[dim]$ {command}[/dim]")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
                executable="/bin/bash",
                input=stdin,
            )

            if result.returncode != 0:
                error_msg = f"Command failed with exit code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nStderr: {result.stderr.strip()}"

                console.print(f"[red]{error_msg}[/red]")

                if check:
                    raise LocalError(error_msg)

            return result.stdout.strip(), result.stderr.strip(), result.returncode

        except subprocess.TimeoutExpired:
            raise LocalError("Command timed out")
        except Exception as e:
            if isinstance(e, LocalError):
                raise
            raise LocalError(f"Failed to execute command: {e}")

    def file_exists(self, path: str) -> bool:
        """Check if a file exists locally."""
        _, _, exit_code = self.execute(
            f"test -f {path}",
            show_command=False,
            check=False,  # Don't raise exception on non-zero exit code
        )
        return exit_code == 0

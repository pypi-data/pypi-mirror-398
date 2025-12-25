"""Configuration management for DuplicAid."""

import os
from pathlib import Path
from typing import List, Optional

import yaml
from rich.console import Console
from rich.prompt import Prompt

console = Console()


class Config:
    """Configuration manager for DuplicAid."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.cwd() / ".duplicaid.yml"
        self._data = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    self._data = yaml.safe_load(f) or {}
            except Exception as e:
                console.print(f"[red]Error loading config: {e}[/red]")
                self._data = {}
        else:
            self._data = {}

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_path, "w") as f:
                yaml.dump(self._data, f, default_flow_style=False, indent=2)
            console.print(f"[green]Configuration saved to {self.config_path}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving config: {e}[/red]")

    @property
    def execution_mode(self) -> str:
        """Get execution mode (remote or local)."""
        return self._data.get("execution_mode", "remote")

    @property
    def remote_host(self) -> Optional[str]:
        """Get remote host address."""
        return self._data.get("remote", {}).get("host")

    @property
    def remote_user(self) -> Optional[str]:
        """Get remote SSH user."""
        return self._data.get("remote", {}).get("user", "root")

    @property
    def ssh_key_path(self) -> Optional[str]:
        """Get SSH private key path."""
        path = self._data.get("remote", {}).get("ssh_key_path")
        if path:
            return os.path.expanduser(path)
        return path

    @property
    def remote_port(self) -> int:
        """Get remote SSH port."""
        return self._data.get("remote", {}).get("port", 22)

    @property
    def postgres_container(self) -> str:
        """Get PostgreSQL container name."""
        return self._data.get("containers", {}).get("postgres", "postgres")

    @property
    def backup_container(self) -> str:
        """Get backup container name."""
        return self._data.get("containers", {}).get("backup", "db-backup")

    @property
    def docker_compose_path(self) -> str:
        """Get Docker Compose file path on remote server."""
        return self._data.get("paths", {}).get(
            "docker_compose", "/home/correlaid/postgres/docker-compose.yml"
        )

    @property
    def databases(self) -> List[str]:
        """Get list of configured databases."""
        return self._data.get("databases", [])

    @property
    def postgres_user(self) -> str:
        """Get PostgreSQL user."""
        return self._data.get("postgres", {}).get("user", "postgres")

    @property
    def postgres_password(self) -> Optional[str]:
        """Get PostgreSQL password."""
        return self._data.get("postgres", {}).get("password")

    @property
    def postgres_host(self) -> Optional[str]:

        return self._data.get("postgres", {}).get("host")

    @property
    def postgres_port(self) -> Optional[str]:

        return self._data.get("postgres", {}).get("port")

    @property
    def s3_endpoint(self) -> Optional[str]:
        """Get S3 endpoint URL."""
        return self._data.get("s3", {}).get("endpoint")

    @property
    def s3_bucket(self) -> Optional[str]:
        """Get S3 bucket name."""
        return self._data.get("s3", {}).get("bucket")

    @property
    def s3_access_key(self) -> Optional[str]:
        """Get S3 access key from config or environment variable."""
        return (
            self._data.get("s3", {}).get("access_key")
            or os.environ.get("AWS_ACCESS_KEY_ID")
            or os.environ.get("S3_ACCESS_KEY")
        )

    @property
    def s3_secret_key(self) -> Optional[str]:
        """Get S3 secret key from config or environment variable."""
        return (
            self._data.get("s3", {}).get("secret_key")
            or os.environ.get("AWS_SECRET_ACCESS_KEY")
            or os.environ.get("S3_SECRET_KEY")
        )

    @property
    def s3_path(self) -> str:
        """Get S3 path for logical backups."""
        return self._data.get("s3", {}).get("path", "backups/logical")

    def init_config(self) -> None:
        """Initialize configuration interactively."""
        console.print("[bold blue]DuplicAid Configuration Setup[/bold blue]")
        console.print("Please provide the following information:\n")

        # Execution mode
        mode = Prompt.ask(
            "Execution mode", choices=["remote", "local"], default="remote"
        )

        # Remote server configuration (only if remote mode)
        if mode == "remote":
            host = Prompt.ask("Remote server hostname/IP")
            user = Prompt.ask("SSH username", default="root")
            port = Prompt.ask("SSH port", default="22")

            ssh_key_default = str(Path.home() / ".ssh" / "id_rsa")
            ssh_key = Prompt.ask("SSH private key path", default=ssh_key_default)
        else:
            host = user = port = ssh_key = None

        # Container configuration
        postgres_container = Prompt.ask("PostgreSQL container name", default="postgres")
        backup_container = Prompt.ask("Backup container name", default="db-backup")

        # PostgreSQL credentials
        postgres_user = Prompt.ask("PostgreSQL user", default="postgres")
        postgres_password = Prompt.ask("PostgreSQL password", password=True)

        # Paths
        if mode == "remote":
            compose_path = Prompt.ask(
                "Docker Compose file path on remote",
                default="/home/correlaid/postgres/docker-compose.yml",
            )
        else:
            compose_path = Prompt.ask(
                "Docker Compose file path",
                default="./docker-compose.test.yml",
            )

        # Databases
        console.print("\n[yellow]Database configuration:[/yellow]")
        databases = []
        while True:
            db = Prompt.ask(
                "Database name (dont input anything and press Enter to finish)",
                default="",
            )
            if not db:
                break
            if db in databases:
                console.print(f"[yellow]'{db}' already added, skipping[/yellow]")
                continue
            databases.append(db)
            console.print(f"[green]✓ Added '{db}'[/green]")

        if not databases:
            console.print(
                "[yellow]No databases configured. You can add them later with "
                "'duplicaid config add-db'[/yellow]"
            )

        # Save configuration
        self._data = {
            "execution_mode": mode,
            "containers": {"postgres": postgres_container, "backup": backup_container},
            "paths": {"docker_compose": compose_path},
            "databases": databases,
            "postgres": {"user": postgres_user, "password": postgres_password},
        }

        if mode == "remote":
            self._data["remote"] = {
                "host": host,
                "user": user,
                "port": int(port),
                "ssh_key_path": ssh_key,
            }

        self.save()
        console.print("\n[green]✓ Configuration completed![/green]")

    def add_database(self, database: str) -> None:
        """Add a database to the configuration."""
        if "databases" not in self._data:
            self._data["databases"] = []

        if database not in self._data["databases"]:
            self._data["databases"].append(database)
            self.save()
            console.print(f"[green]✓ Added database: {database}[/green]")
        else:
            console.print(f"[yellow]Database {database} already configured[/yellow]")

    def remove_database(self, database: str) -> None:
        """Remove a database from the configuration."""
        if "databases" in self._data and database in self._data["databases"]:
            self._data["databases"].remove(database)
            self.save()
            console.print(f"[green]✓ Removed database: {database}[/green]")
        else:
            console.print(
                f"[yellow]Database {database} not found in configuration[/yellow]"
            )

    def is_configured(self) -> bool:
        """Check if configuration is complete."""
        if self.execution_mode == "local":
            return bool(self.postgres_container and self.docker_compose_path)
        else:
            if not self.remote_host or not self.ssh_key_path:
                return False
            if not os.path.exists(self.ssh_key_path):
                console.print(f"[red]SSH key not found ): : {self.ssh_key_path}[/red]")
                return False
            return True

    def validate(self) -> bool:
        """Validate configuration."""
        if self.execution_mode == "local":
            if not self.docker_compose_path:
                console.print("[red]Missing Docker Compose path configuration[/red]")
                return False
            return True
        else:
            if not self.remote_host:
                console.print("[red]Missing remote host configuration[/red]")
                return False

            if not self.ssh_key_path:
                console.print("[red]Missing SSH key path configuration[/red]")
                return False

            if not os.path.exists(self.ssh_key_path):
                console.print(f"[red]SSH key not found: {self.ssh_key_path}[/red]")
                return False

            return True

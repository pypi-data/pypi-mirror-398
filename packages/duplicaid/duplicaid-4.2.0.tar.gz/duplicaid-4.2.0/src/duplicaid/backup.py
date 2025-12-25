"""Backup operations for PostgreSQL logical dumps."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from minio import Minio
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import Config
from .executor import BaseExecutor
from .ssh import RemoteExecutor, SSHError

console = Console()


@dataclass
class BackupInfo:
    """Information about a backup."""

    name: str
    timestamp: datetime
    size: Optional[str] = None
    type: str = "unknown"
    database: Optional[str] = None


class LogicalBackupManager:
    """Manager for logical backup operations."""

    def __init__(self, config: Config):
        self.config = config

    def create_backup(self, executor: RemoteExecutor) -> bool:
        """
        Create a logical backup.

        Args:
            executor: SSH executor instance
            database: Specific database to backup (None for all)

        Returns:
            True if backup was successful, False otherwise
        """
        console.print("[blue]Creating logical backup for all databases[/blue]")
        return self._create_all_databases_backup(executor)

    def _create_all_databases_backup(self, executor: RemoteExecutor) -> bool:
        """Create backup for all databases using db-backup container."""
        if not executor.check_container_running(self.config.backup_container):
            console.print(
                f"[red]Backup container '{self.config.backup_container}' is not running[/red]"
            )
            return False

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task("Creating logical backup...", total=None)

                stdout, stderr, exit_code = executor.docker_exec(
                    self.config.backup_container, "backup-now"
                )

                if exit_code == 0:
                    console.print(
                        "[green]✓ Logical backup created successfully[/green]"
                    )
                    return True
                else:
                    console.print("[red]✗ Logical backup failed[/red]")
                    if stderr:
                        console.print(f"[red]Error: {stderr}[/red]")
                    return False

        except SSHError as e:
            console.print(f"[red]✗ Logical backup failed: {e}[/red]")
            return False

    def list_backups(self, executor: RemoteExecutor) -> List[BackupInfo]:
        """
        List available logical backups from S3.

        Args:
            executor: SSH executor instance

        Returns:
            List of BackupInfo objects
        """
        if not self.config.s3_endpoint or not self.config.s3_bucket:
            console.print(
                "[yellow]S3 not configured, listing local backups...[/yellow]"
            )
            return self._list_local_backups(executor)

        try:
            endpoint = self.config.s3_endpoint.replace("http://", "").replace(
                "https://", ""
            )
            secure = self.config.s3_endpoint.startswith("https://")

            client = Minio(
                endpoint,
                access_key=self.config.s3_access_key,
                secret_key=self.config.s3_secret_key,
                secure=secure,
            )

            backups = []
            objects = client.list_objects(
                self.config.s3_bucket, prefix=self.config.s3_path, recursive=True
            )

            for obj in objects:
                if any(ext in obj.object_name for ext in [".sql", ".bz2", ".gz"]):
                    filename = obj.object_name.split("/")[-1]
                    match = re.search(
                        r"(?:pgsql|mysql|mongo)_\w+_(\w+)_(\d{8}[_-]\d{6})", filename
                    )
                    if match:
                        database = match.group(1)
                        timestamp_str = match.group(2).replace("-", "_")
                        try:
                            timestamp = datetime.strptime(
                                timestamp_str, "%Y%m%d_%H%M%S"
                            )
                            backups.append(
                                BackupInfo(
                                    name=filename,
                                    timestamp=timestamp,
                                    type="logical",
                                    database=database,
                                    size=obj.size,
                                )
                            )
                        except ValueError:
                            continue

            return sorted(backups, key=lambda x: x.timestamp, reverse=True)

        except Exception as e:
            console.print(f"[red]Failed to list S3 backups: {e}[/red]")
            return []

    def _list_local_backups(self, executor: RemoteExecutor) -> List[BackupInfo]:
        """List backups from local /backup directory."""
        if not executor.check_container_running(self.config.backup_container):
            console.print(
                f"[red]Backup container '{self.config.backup_container}' is not running[/red]"
            )
            return []

        try:
            stdout, stderr, exit_code = executor.docker_exec(
                self.config.backup_container, "ls -1 /backup"
            )

            if exit_code != 0:
                console.print("[red]Failed to list local backups[/red]")
                if stderr:
                    console.print(f"[red]Error: {stderr}[/red]")
                return []

            return self._parse_logical_backup_list(stdout)

        except SSHError as e:
            console.print(f"[red]Failed to list local backups: {e}[/red]")
            return []

    def _parse_logical_backup_list(self, output: str) -> List[BackupInfo]:
        """Parse logical backup list output."""
        backups = []
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Parse db-backup filename format: pgsql_host_database_timestamp.sql.bz2
            if ".sql" in line or ".bz2" in line:
                try:
                    match = re.search(
                        r"(?:pgsql|mysql|mongo)_\w+_(\w+)_(\d{8}[_-]\d{6})", line
                    )
                    if match:
                        database = match.group(1)
                        timestamp_str = match.group(2).replace("-", "_")
                        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                        backups.append(
                            BackupInfo(
                                name=line,
                                timestamp=timestamp,
                                type="logical",
                                database=database,
                            )
                        )
                except ValueError:
                    continue

        return sorted(backups, key=lambda x: x.timestamp, reverse=True)

    def restore_backup(
        self, executor: BaseExecutor, database: str, backup_name: str
    ) -> bool:
        """
        Restore a logical backup for a specific database.

        Args:
            executor: The executor to use for running commands
            database: The database to restore to
            backup_name: The name of the backup file to restore

        Returns:
            True if restore was successful, False otherwise
        """
        console = Console()

        with console.status(f"[bold blue]Restoring {database}...") as status:
            backup_path = f"/backup/{backup_name}"

            # Check if backup exists locally
            try:
                _, _, exit_code = executor.docker_exec(
                    "db-backup",
                    f"test -f {backup_path}",
                    check=False,  # Don't raise on failure
                )

                file_exists_locally = exit_code == 0
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not check local file: {e}[/yellow]"
                )
                file_exists_locally = False

            # Download from S3 if not available locally
            if not file_exists_locally:
                if self.config.s3_endpoint and self.config.s3_bucket:
                    status.update(f"[bold blue]Downloading {backup_name} from S3...")

                    try:
                        s3_path = f"{self.config.s3_path}/{backup_name}"
                        s3_uri = f"s3://{self.config.s3_bucket}/{s3_path}"

                        container_endpoint = re.sub(
                            r"localhost(:\d+)?", r"minio\1", self.config.s3_endpoint
                        )

                        download_cmd = (
                            f"sh -c 'AWS_ACCESS_KEY_ID={self.config.s3_access_key} "
                            f"AWS_SECRET_ACCESS_KEY={self.config.s3_secret_key} "
                            f"aws --endpoint-url {container_endpoint} "
                            f"s3 cp {s3_uri} {backup_path}'"
                        )

                        stdout, stderr, exit_code = executor.docker_exec(
                            self.config.backup_container, download_cmd, check=False
                        )

                        if exit_code != 0:
                            console.print(
                                "[red]✗ Failed to download backup from S3[/red]"
                            )
                            console.print(f"[red]Error: {stderr}[/red]")
                            return False

                        console.print(
                            f"[green]✓ Downloaded {backup_name} from S3[/green]"
                        )

                    except Exception as e:
                        console.print(f"[red]✗ Failed to download from S3: {e}[/red]")
                        return False
                else:
                    console.print(
                        f"[red]✗ Backup file {backup_name} not found and S3 not configured[/red]"
                    )
                    return False

            # Now restore the backup
            status.update(f"[bold blue]Restoring {database} from {backup_name}...")

            try:
                restore_cmd = (
                    f"restore {backup_path} pgsql "
                    f"{self.config.postgres_host} {database} "
                    f"{self.config.postgres_user} {self.config.postgres_password} "
                    f"{self.config.postgres_port}"
                )

                executor.docker_exec("db-backup", restore_cmd, check=True)
                console.print(
                    f"[green]✓ Logical restore completed for {database}[/green]"
                )
                return True

            except Exception as e:
                console.print(f"[red]✗ Logical restore failed for {database}[/red]")
                console.print(f"[red]Error: {e}[/red]")
                return False

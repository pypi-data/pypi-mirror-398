"""Database discovery functionality for DuplicAid."""

from typing import Any, Dict, List

from rich.console import Console

from .config import Config
from .ssh import RemoteExecutor, SSHError

console = Console()


class DatabaseDiscovery:
    """Database discovery and information gathering."""

    def __init__(self, config: Config):
        self.config = config

    def get_databases(self, executor: RemoteExecutor) -> List[Dict[str, Any]]:
        """
        Discover databases on the remote PostgreSQL server.

        Args:
            executor: SSH executor instance

        Returns:
            List of database information dictionaries
        """
        if not executor.check_container_running(self.config.postgres_container):
            console.print(
                f"[red]PostgreSQL container '{self.config.postgres_container}' is not running[/red]"
            )
            return []

        try:
            # Query for database names and sizes
            query = """
            SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
            FROM pg_database
            WHERE datistemplate = false
            AND datname != 'postgres'
            ORDER BY datname;
            """

            command = f'psql -U {self.config.postgres_user} -t -c "{query}"'

            stdout, stderr, exit_code = executor.docker_exec(
                self.config.postgres_container, command
            )

            if exit_code != 0:
                console.print("[red]Failed to query database information[/red]")
                if stderr:
                    console.print(f"[red]Error: {stderr}[/red]")
                return []

            return self._parse_database_list(stdout)

        except SSHError as e:
            console.print(f"[red]Failed to discover databases: {e}[/red]")
            return []

    def _parse_database_list(self, output: str) -> List[Dict[str, Any]]:
        """Parse database list output from PostgreSQL."""
        databases = []
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("datname"):
                continue

            # Split by pipe character (PostgreSQL default separator)
            parts = [part.strip() for part in line.split("|")]
            if len(parts) >= 2:
                name = parts[0]
                size = parts[1]

                # Skip template and system databases
                if name not in ["template0", "template1", "postgres"]:
                    databases.append({"name": name, "size": size})

        return databases

    def get_database_info(
        self, executor: RemoteExecutor, database: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific database.

        Args:
            executor: SSH executor instance
            database: Database name

        Returns:
            Dictionary with database information
        """
        if not executor.check_container_running(self.config.postgres_container):
            console.print(
                f"[red]PostgreSQL container '{self.config.postgres_container}' is not running[/red]"
            )
            return {}

        try:
            # Query for detailed database information
            query = f"""
            SELECT
                datname,
                pg_size_pretty(pg_database_size(datname)) as size,
                datcollate,
                datctype,
                datistemplate,
                datallowconn,
                datconnlimit
            FROM pg_database
            WHERE datname = '{database}';
            """

            command = f'psql -U {self.config.postgres_user} -t -c "{query}"'

            stdout, stderr, exit_code = executor.docker_exec(
                self.config.postgres_container, command
            )

            if exit_code != 0:
                console.print(
                    f"[red]Failed to query information for database '{database}'[/red]"
                )
                return {}

            return self._parse_database_info(stdout, database)

        except SSHError as e:
            console.print(f"[red]Failed to get database info: {e}[/red]")
            return {}

    def _parse_database_info(self, output: str, database: str) -> Dict[str, Any]:
        """Parse detailed database information."""
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = [part.strip() for part in line.split("|")]
            if len(parts) >= 7 and parts[0] == database:
                return {
                    "name": parts[0],
                    "size": parts[1],
                    "collate": parts[2],
                    "ctype": parts[3],
                    "is_template": parts[4] == "t",
                    "allow_conn": parts[5] == "t",
                    "conn_limit": parts[6],
                }

        return {}

    def check_database_exists(self, executor: RemoteExecutor, database: str) -> bool:
        """
        Check if a database exists.

        Args:
            executor: SSH executor instance
            database: Database name to check

        Returns:
            True if database exists, False otherwise
        """
        databases = self.get_databases(executor)
        return any(db["name"] == database for db in databases)

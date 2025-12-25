"""CLI interface for DuplicAid."""

from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from .backup import LogicalBackupManager
from .config import Config
from .discovery import DatabaseDiscovery
from .executor import ExecutorError
from .local import LocalExecutor
from .ssh import RemoteExecutor

console = Console()
app = typer.Typer(
    name="duplicaid",
    help="PostgreSQL backup management CLI tool",
    rich_markup_mode="rich",
)

# Subcommands
config_app = typer.Typer(name="config", help="Configuration management")
list_app = typer.Typer(name="list", help="List available backups and databases")

app.add_typer(config_app)
app.add_typer(list_app)

# Global configuration instance
config: Optional[Config] = None


@app.callback()
def main_callback(
    ctx: typer.Context,
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file (default: .duplicaid.yml in cwd)",
    ),
):
    """DuplicAid - PostgreSQL backup management CLI."""
    global config
    config = Config(config_path)


def get_executor():
    """Get the appropriate executor based on configuration."""
    if config.execution_mode == "local":
        return LocalExecutor(config)
    else:
        return RemoteExecutor(config)


def check_config() -> bool:
    """Check if configuration is valid."""
    if not config.is_configured():
        console.print("[red]Configuration not found or incomplete.[/red]")
        console.print("Run [bold]duplicaid config init[/bold] to set up configuration.")
        raise typer.Exit(1)

    if not config.validate():
        console.print("[red]Configuration validation failed.[/red]")
        raise typer.Exit(1)

    return True


# Configuration commands
@config_app.command("init")
def config_init():
    """Initialize DuplicAid configuration."""
    config.init_config()


@config_app.command("show")
def config_show():
    """Show current configuration."""
    if not config.is_configured():
        console.print(
            "[yellow]No configuration found. Run 'duplicaid config init' to set up.[/yellow]"
        )
        return

    table = Table(title="DuplicAid Configuration", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Config File", str(config.config_path))
    table.add_row("Execution Mode", config.execution_mode)

    if config.execution_mode == "remote":
        table.add_row("Remote Host", config.remote_host or "Not set")
        table.add_row("Remote User", config.remote_user or "Not set")
        table.add_row("Remote Port", str(config.remote_port))
        table.add_row("SSH Key Path", config.ssh_key_path or "Not set")

    table.add_row("PostgreSQL Container", config.postgres_container)
    table.add_row("Backup Container", config.backup_container)
    table.add_row("Docker Compose Path", config.docker_compose_path)
    table.add_row(
        "Databases", ", ".join(config.databases) if config.databases else "None"
    )

    console.print(table)


@config_app.command("add-db")
def config_add_db(database: str = typer.Argument(..., help="Database name to add")):
    """Add a database to the configuration."""
    config.add_database(database)


@config_app.command("remove-db")
def config_remove_db(
    database: str = typer.Argument(..., help="Database name to remove")
):
    """Remove a database from the configuration."""
    config.remove_database(database)


# Backup command
@app.command("backup")
def backup():
    """Create a database backup."""
    check_config()

    try:
        with get_executor() as executor:
            logical_manager = LogicalBackupManager(config)
            success = logical_manager.create_backup(executor)

            if not success:
                raise typer.Exit(1)

    except ExecutorError as e:
        console.print(f"[red]Executor Error: {e}[/red]")
        raise typer.Exit(1)


# Restore command
@app.command("restore")
def restore(
    database: str = typer.Argument(..., help="Database name to restore"),
    backup_file: str = typer.Argument(..., help="Backup filename"),
):
    """Restore from backup."""
    check_config()

    if database not in config.databases:
        console.print(f"[red]Database '{database}' not found in configuration.[/red]")
        console.print("Available databases:", ", ".join(config.databases))
        raise typer.Exit(1)

    # Confirm destructive operation
    if not typer.confirm(f"This will overwrite database '{database}'. Are you sure?"):
        console.print("[yellow]Operation cancelled.[/yellow]")
        raise typer.Exit()

    try:
        with get_executor() as executor:
            logical_manager = LogicalBackupManager(config)
            success = logical_manager.restore_backup(executor, database, backup_file)

            if not success:
                raise typer.Exit(1)

    except ExecutorError as e:
        console.print(f"[red]Executor Error: {e}[/red]")
        raise typer.Exit(1)


# List commands
@list_app.command("backups")
def list_backups():
    """List available backups."""
    check_config()

    try:
        with get_executor() as executor:
            logical_manager = LogicalBackupManager(config)
            backup_list = logical_manager.list_backups(executor)

            if not backup_list:
                console.print("[yellow]No backups found.[/yellow]")
                return

            table = Table(title="Available Backups", box=box.ROUNDED)
            table.add_column("Name", style="cyan")
            table.add_column("Database", style="blue")
            table.add_column("Timestamp", style="green")

            for backup in backup_list:
                table.add_row(
                    backup.name,
                    backup.database or "Unknown",
                    backup.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                )

            console.print(table)

    except ExecutorError as e:
        console.print(f"[red]Executor Error: {e}[/red]")
        raise typer.Exit(1)


@list_app.command("databases")
def list_databases():
    """List available databases in PostgreSQL."""
    check_config()

    try:
        with get_executor() as executor:
            postgres_running = executor.check_container_running(
                config.postgres_container
            )

            if not postgres_running:
                console.print("[red]PostgreSQL container is not running.[/red]")
                raise typer.Exit(1)

            discovery = DatabaseDiscovery(config)
            databases = discovery.get_databases(executor)

            if not databases:
                console.print("[yellow]No databases found.[/yellow]")
                return

            table = Table(title="Available Databases", box=box.ROUNDED)
            table.add_column("Database", style="cyan")
            table.add_column("Size", style="green")
            table.add_column("Owner", style="blue")

            for db_info in databases:
                table.add_row(
                    db_info["name"],
                    db_info.get("size", "Unknown"),
                    db_info.get("owner", "Unknown"),
                )

            console.print(table)

    except ExecutorError as e:
        console.print(f"[red]Executor Error: {e}[/red]")
        raise typer.Exit(1)


# Status command
@app.command("status")
def status():
    """Show system status."""
    check_config()

    try:
        with get_executor() as executor:
            console.print("[bold blue]DuplicAid Status[/bold blue]\n")

            # Check container status
            postgres_running = executor.check_container_running(
                config.postgres_container
            )
            backup_running = executor.check_container_running(config.backup_container)

            table = Table(title="Container Status", box=box.ROUNDED)
            table.add_column("Container", style="cyan")
            table.add_column("Status", style="green")

            postgres_status = (
                "[green]Running[/green]" if postgres_running else "[red]Stopped[/red]"
            )
            backup_status = (
                "[green]Running[/green]" if backup_running else "[red]Stopped[/red]"
            )

            table.add_row(config.postgres_container, postgres_status)
            table.add_row(config.backup_container, backup_status)

            console.print(table)

            # Show database status if postgres is running
            if postgres_running:
                discovery = DatabaseDiscovery(config)
                databases = discovery.get_databases(executor)

                if databases:
                    console.print("\n")
                    db_table = Table(title="Database Status", box=box.ROUNDED)
                    db_table.add_column("Database", style="cyan")
                    db_table.add_column("Size", style="green")

                    for db_info in databases:
                        db_table.add_row(
                            db_info["name"], db_info.get("size", "Unknown")
                        )

                    console.print(db_table)

    except ExecutorError as e:
        console.print(f"[red]Executor Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

from typer.testing import CliRunner

from duplicaid.cli import app

runner = CliRunner()


def test_cli_help():
    """Test main CLI help message."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "PostgreSQL backup management CLI tool" in result.stdout


def test_config_commands():
    """Test config subcommand help."""
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "Configuration management" in result.stdout


def test_backup_command_help():
    """Test backup command help (now a top-level command)."""
    result = runner.invoke(app, ["backup", "--help"])
    assert result.exit_code == 0
    assert "Create a database backup" in result.stdout


def test_restore_command_help():
    """Test restore command help (now a top-level command)."""
    result = runner.invoke(app, ["restore", "--help"])
    assert result.exit_code == 0
    assert "Restore from backup" in result.stdout


def test_status_command_help():
    """Test status command help."""
    result = runner.invoke(app, ["status", "--help"])
    assert result.exit_code == 0
    assert "Show system status" in result.stdout


def test_list_commands():
    """Test list subcommand help."""
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0
    assert "List available backups" in result.stdout or "databases" in result.stdout


def test_list_backups_help():
    """Test list backups subcommand help."""
    result = runner.invoke(app, ["list", "backups", "--help"])
    assert result.exit_code == 0
    assert "List available backups" in result.stdout


def test_list_databases_help():
    """Test list databases subcommand help."""
    result = runner.invoke(app, ["list", "databases", "--help"])
    assert result.exit_code == 0
    assert "List available databases in PostgreSQL" in result.stdout


def test_status_without_config():
    """Test status command fails without configuration."""
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "Configuration not found" in result.stdout


def test_backup_without_config():
    """Test backup command fails without configuration."""
    result = runner.invoke(app, ["backup"])
    assert result.exit_code == 1
    assert "Configuration not found" in result.stdout


def test_config_show_empty():
    """Test config show with no configuration."""
    result = runner.invoke(app, ["config", "show"])
    assert (
        "No configuration found" in result.stdout
        or "DuplicAid Configuration" in result.stdout
    )


def test_config_init_help():
    """Test config init command help."""
    result = runner.invoke(app, ["config", "init", "--help"])
    assert result.exit_code == 0
    assert "Initialize DuplicAid configuration" in result.stdout


def test_config_add_db_help():
    """Test config add-db command help."""
    result = runner.invoke(app, ["config", "add-db", "--help"])
    assert result.exit_code == 0
    assert "Add a database to the configuration" in result.stdout


def test_config_remove_db_help():
    """Test config remove-db command help."""
    result = runner.invoke(app, ["config", "remove-db", "--help"])
    assert result.exit_code == 0
    assert "Remove a database from the configuration" in result.stdout


def test_restore_missing_arguments():
    """Test restore command fails with missing arguments."""
    result = runner.invoke(app, ["restore"])
    # Exit code 2 indicates a usage error (missing arguments)
    assert result.exit_code == 2


def test_global_config_option():
    """Test global --config option."""
    result = runner.invoke(app, ["--config", "/tmp/test.yml", "--help"])
    assert result.exit_code == 0

import pytest
from minio import Minio
from typer.testing import CliRunner

from duplicaid.backup import LogicalBackupManager
from duplicaid.cli import app
from duplicaid.discovery import DatabaseDiscovery


@pytest.mark.integration
def test_database_discovery(test_services, local_executor):
    discovery = DatabaseDiscovery(local_executor.config)
    databases = discovery.get_databases(local_executor)

    db_names = [db["name"] for db in databases]
    assert "test" in db_names


@pytest.mark.integration
def test_container_status_check(test_services, local_executor):
    assert local_executor.check_container_running("postgres")
    assert not local_executor.check_container_running("nonexistent")

    status = local_executor.get_container_status("postgres")
    assert status is not None
    assert "Up" in status


@pytest.mark.integration
def test_logical_backup_manager_init(test_services, local_executor):
    logical_manager = LogicalBackupManager(local_executor.config)
    assert logical_manager.config == local_executor.config


## Listing


@pytest.mark.integration
def test_logical_backup_list(test_services, local_executor):
    logical_manager = LogicalBackupManager(local_executor.config)
    backups = logical_manager.list_backups(local_executor)
    assert isinstance(backups, list)
    print(backups)


@pytest.mark.integration
def test_s3_backup_listing(test_services, local_executor):
    client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False,
    )

    test_content = b"test backup content"
    test_filename = "pgsql_testhost_testdb_20241107-120000.sql.bz2"
    test_path = f"test/logical/{test_filename}"

    from io import BytesIO

    client.put_object(
        "test-bucket",
        test_path,
        BytesIO(test_content),
        len(test_content),
    )

    logical_manager = LogicalBackupManager(local_executor.config)
    backups = logical_manager.list_backups(local_executor)

    assert isinstance(backups, list)
    assert len(backups) >= 1

    backup_names = [b.name for b in backups]
    assert test_filename in backup_names

    client.remove_object("test-bucket", test_path)


## Backup


@pytest.mark.integration
def test_db_backup_container_integration(test_services, local_executor):
    logical_manager = LogicalBackupManager(local_executor.config)

    # create the logical backup via the manager
    success = logical_manager.create_backup(local_executor)
    assert success is True, "Logical backup should be created successfully"

    # verify the backup shows up in the listing
    backups = logical_manager.list_backups(local_executor)
    assert isinstance(backups, list)
    assert len(backups) >= 1

    latest_backup = backups[0]
    print(latest_backup)
    print(backups)
    assert latest_backup.type == "logical"
    assert latest_backup.database == "postgres"


## Restore


@pytest.mark.integration
def test_logical_restore(test_services, local_executor):
    logical_manager = LogicalBackupManager(local_executor.config)
    database = "test"

    # 1. Create table
    local_executor.docker_exec(
        "postgres",
        f"psql -U {local_executor.config.postgres_user} -d {database} "
        '-c "CREATE TABLE restore_check(id int); INSERT INTO restore_check VALUES (42);"',
    )

    # 2. Backup
    logical_manager.create_backup(local_executor)

    # 3. Drop table
    local_executor.docker_exec(
        "postgres",
        f"psql -U {local_executor.config.postgres_user} -d {database} "
        '-c "DROP TABLE restore_check;"',
    )

    # 4. Restore
    backups = logical_manager.list_backups(local_executor)
    latest_backup = next(b for b in backups if database in b.name)

    # 5. Verify file doesn't exist locally (use check=False for expected failure)
    _, _, exit_code = local_executor.docker_exec(
        "db-backup",
        f"test -f /backup/{latest_backup.name}",
        check=False,  # Don't raise on this expected failure
    )
    assert exit_code != 0, "Backup file should not exist locally"

    # 6. Restore should now succeed (will raise if it fails)
    assert logical_manager.restore_backup(local_executor, database, latest_backup.name)

    # 7. Verify restoration (will raise if command fails)
    stdout, _, code = local_executor.docker_exec(
        "postgres",
        f'psql -U {local_executor.config.postgres_user} -d {database} -t -c "SELECT id FROM restore_check;"',
    )
    assert "42" in stdout.strip()


@pytest.mark.integration
def test_status_with_custom_config(test_services, test_config, tmp_path):
    runner = CliRunner()

    config_file = tmp_path / "custom_config.yml"
    test_config.config_path = config_file
    test_config.save()

    result = runner.invoke(app, ["--config", str(config_file), "status"])
    assert result.exit_code == 0
    assert "Container Status" in result.stdout


@pytest.mark.integration
def test_list_backups_with_custom_config(test_services, test_config, tmp_path):
    runner = CliRunner()

    config_file = tmp_path / "custom_config.yml"
    test_config.config_path = config_file
    test_config.save()

    result = runner.invoke(app, ["--config", str(config_file), "list", "backups"])
    assert result.exit_code == 0


@pytest.mark.integration
def test_list_databases_with_custom_config(test_services, test_config, tmp_path):
    runner = CliRunner()

    config_file = tmp_path / "custom_config.yml"
    test_config.config_path = config_file
    test_config.save()

    result = runner.invoke(app, ["--config", str(config_file), "list", "databases"])
    assert result.exit_code == 0
    assert "Available Databases" in result.stdout


@pytest.mark.integration
def test_config_show_with_custom_config(test_config, tmp_path):
    runner = CliRunner()

    config_file = tmp_path / "custom_config.yml"
    test_config.config_path = config_file
    test_config.save()

    result = runner.invoke(app, ["--config", str(config_file), "config", "show"])
    assert result.exit_code == 0
    assert "DuplicAid Configuration" in result.stdout


@pytest.mark.integration
def test_nonexistent_config_file():
    runner = CliRunner()

    result = runner.invoke(app, ["--config", "/nonexistent/config.yml", "status"])
    assert result.exit_code == 1
    assert "Configuration not found" in result.stdout

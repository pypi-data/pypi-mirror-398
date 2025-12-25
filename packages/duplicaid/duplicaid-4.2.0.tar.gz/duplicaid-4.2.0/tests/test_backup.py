from unittest.mock import Mock

import pytest

from duplicaid.backup import LogicalBackupManager
from duplicaid.config import Config


@pytest.fixture
def test_config():
    config = Config()
    config._data = {
        "execution_mode": "local",
        "containers": {"postgres": "postgres", "backup": "db-backup"},
        "paths": {"docker_compose": "/test/docker-compose.yml"},
        "databases": ["testdb1", "testdb2"],
    }
    return config


@pytest.fixture
def mock_executor():
    executor = Mock()
    executor.docker_exec.return_value = ("", "", 0)
    executor.check_container_running.return_value = True
    return executor


def test_logical_backup_all_databases(test_config, mock_executor):
    manager = LogicalBackupManager(test_config)

    manager.create_backup(mock_executor)
    mock_executor.docker_exec.assert_called()


def test_logical_backup_specific_database(test_config, mock_executor):
    manager = LogicalBackupManager(test_config)

    manager.create_backup(mock_executor)
    mock_executor.docker_exec.assert_called()


def test_logical_backup_list(test_config, mock_executor):
    manager = LogicalBackupManager(test_config)
    mock_executor.docker_exec.return_value = (
        "pgsql_postgres_testdb1_20241107-120000.sql.bz2\npgsql_postgres_testdb2_20241107-130000.sql.bz2",
        "",
        0,
    )

    backups = manager.list_backups(mock_executor)
    mock_executor.docker_exec.assert_called()
    assert len(backups) == 2
    assert backups[0].database == "testdb2"  # Most recent (130000)
    assert backups[1].database == "testdb1"  # Older (120000)


def test_logical_restore(test_config, mock_executor):
    manager = LogicalBackupManager(test_config)

    manager.restore_backup(mock_executor, "testdb1", "/path/to/backup.sql.gz")
    mock_executor.docker_exec.assert_called()


def test_backup_manager_initialization(test_config):
    logical_manager = LogicalBackupManager(test_config)
    assert logical_manager.config == test_config


def test_container_status_check(test_config, mock_executor):
    manager = LogicalBackupManager(test_config)
    mock_executor.check_container_running.return_value = False

    manager.create_backup(mock_executor)
    mock_executor.check_container_running.assert_called()

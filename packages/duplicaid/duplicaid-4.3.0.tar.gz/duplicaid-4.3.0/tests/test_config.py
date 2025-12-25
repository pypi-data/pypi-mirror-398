from duplicaid.config import Config


def test_config_default_values():
    config = Config()
    assert config.execution_mode == "remote"
    assert config.postgres_container == "postgres"
    assert config.backup_container == "db-backup"
    assert config.postgres_user == "postgres"
    assert config.postgres_password is None


def test_config_local_mode():
    config = Config()
    config._data = {
        "execution_mode": "local",
        "containers": {"postgres": "test-postgres", "backup": "test-backup"},
        "paths": {"docker_compose": "./test.yml"},
        "databases": ["testdb"],
        "postgres": {"user": "testuser", "password": "testpass"},
    }

    assert config.execution_mode == "local"
    assert config.postgres_container == "test-postgres"
    assert config.backup_container == "test-backup"
    assert config.docker_compose_path == "./test.yml"
    assert config.databases == ["testdb"]
    assert config.postgres_user == "testuser"
    assert config.postgres_password == "testpass"


def test_config_remote_mode():
    config = Config()
    config._data = {
        "execution_mode": "remote",
        "remote": {
            "host": "test.example.com",
            "user": "testuser",
            "port": 2222,
            "ssh_key_path": "/test/key",
        },
        "containers": {"postgres": "postgres", "backup": "db-backup"},
        "paths": {"docker_compose": "/remote/compose.yml"},
        "databases": ["db1", "db2"],
        "postgres": {"user": "pguser", "password": "pgpass"},
    }

    assert config.execution_mode == "remote"
    assert config.remote_host == "test.example.com"
    assert config.remote_user == "testuser"
    assert config.remote_port == 2222
    assert config.ssh_key_path == "/test/key"
    assert config.postgres_user == "pguser"
    assert config.postgres_password == "pgpass"


def test_config_validation_local():
    config = Config()
    config._data = {
        "execution_mode": "local",
        "containers": {"postgres": "postgres", "backup": "db-backup"},
        "paths": {"docker_compose": "./test.yml"},
    }

    assert config.validate()


def test_config_validation_remote_missing_host():
    config = Config()
    config._data = {
        "execution_mode": "remote",
        "containers": {"postgres": "postgres", "backup": "db-backup"},
    }

    assert not config.validate()


def test_add_remove_database():
    config = Config()
    config._data = {"databases": ["existing_db"]}

    config.add_database("new_db")
    assert "new_db" in config.databases

    config.remove_database("new_db")
    assert "new_db" not in config.databases


def test_ssh_key_path_tilde_expansion():
    import os

    config = Config()
    config._data = {
        "execution_mode": "remote",
        "remote": {
            "host": "test.example.com",
            "user": "testuser",
            "ssh_key_path": "~/.ssh/id_rsa",
        },
    }

    expanded_path = config.ssh_key_path
    assert expanded_path is not None
    assert "~" not in expanded_path
    assert expanded_path.startswith(os.path.expanduser("~"))

import subprocess
import time
from pathlib import Path

import pytest

from duplicaid.config import Config
from duplicaid.local import LocalExecutor


@pytest.fixture(scope="session")
def docker_compose_file():
    return Path(__file__).parent.parent / "docker-compose.test.yml"


@pytest.fixture(scope="session")
def test_services(docker_compose_file):
    subprocess.run(
        ["docker", "compose", "-f", str(docker_compose_file), "down", "-v"],
        capture_output=True,
    )

    result = subprocess.run(
        ["docker", "compose", "-f", str(docker_compose_file), "up", "-d"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        pytest.fail(f"Failed to start test services: {result.stderr}")

    time.sleep(20)

    yield

    # subprocess.run(
    #     ["docker", "compose", "-f", str(docker_compose_file), "down", "-v"],
    #     capture_output=True,
    # )


@pytest.fixture
def test_config(docker_compose_file):
    config = Config()
    config._data = {
        "execution_mode": "local",
        "containers": {"postgres": "postgres", "backup": "db-backup"},
        "paths": {"docker_compose": str(docker_compose_file)},
        "databases": ["test"],
        "postgres": {
            "user": "postgres",
            "password": "testpassword",
            "host": "postgres",
            "port": 5432,
        },
        "s3": {
            "endpoint": "http://localhost:9000",
            "bucket": "test-bucket",
            "access_key": "minioadmin",
            "secret_key": "minioadmin",
            "path": "test/logical",
        },
    }
    return config


@pytest.fixture
def local_executor(test_config):
    return LocalExecutor(test_config)

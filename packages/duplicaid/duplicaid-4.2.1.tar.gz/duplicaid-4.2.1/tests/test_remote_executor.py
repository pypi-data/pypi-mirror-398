from unittest.mock import MagicMock, Mock, patch

import pytest

from duplicaid.config import Config
from duplicaid.ssh import RemoteExecutor, SSHError


@pytest.fixture
def remote_config():
    config = Config()
    config._data = {
        "execution_mode": "remote",
        "remote": {
            "host": "test.example.com",
            "user": "testuser",
            "port": 22,
            "ssh_key_path": "/path/to/key",
        },
        "containers": {"postgres": "postgres", "backup": "db-backup"},
        "paths": {"docker_compose": "/test/docker-compose.yml"},
        "databases": ["testdb"],
    }
    return config


@pytest.fixture
def mock_ssh_client():
    """Mock SSH client for all tests."""
    with patch("duplicaid.ssh.paramiko.SSHClient") as mock:
        # Setup default behavior
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@patch("os.path.exists", return_value=True)
def test_remote_executor_connect(mock_exists, mock_ssh_client, remote_config):
    """Test that RemoteExecutor connects with correct parameters."""
    executor = RemoteExecutor(remote_config)
    with executor:
        mock_ssh_client.connect.assert_called_once_with(
            hostname="test.example.com",
            port=22,
            username="testuser",
            key_filename="/path/to/key",
            timeout=10,
        )


@patch("os.path.exists", return_value=True)
def test_remote_executor_command_execution(mock_exists, mock_ssh_client, remote_config):
    """Test command execution returns stdout correctly."""
    # Setup mock channel with exit status
    mock_channel = MagicMock()
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = Mock()
    mock_stdout.read.return_value = b"test output"
    mock_stdout.channel = mock_channel

    mock_stderr = Mock()
    mock_stderr.read.return_value = b""

    mock_ssh_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

    executor = RemoteExecutor(remote_config)
    with executor:
        stdout, stderr, exit_code = executor.execute("test command", show_command=False)
        assert stdout == "test output"
        assert stderr == ""
        assert exit_code == 0
        mock_ssh_client.exec_command.assert_called_with("test command")


@patch("os.path.exists", return_value=True)
def test_remote_executor_command_failure(mock_exists, mock_ssh_client, remote_config):
    """Test command execution with non-zero exit code."""
    # Setup mock channel with non-zero exit status
    mock_channel = MagicMock()
    mock_channel.recv_exit_status.return_value = 1

    mock_stdout = Mock()
    mock_stdout.read.return_value = b""
    mock_stdout.channel = mock_channel

    mock_stderr = Mock()
    mock_stderr.read.return_value = b"error message"

    mock_ssh_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

    executor = RemoteExecutor(remote_config)
    with executor:
        # With check=False, should return exit code
        stdout, stderr, exit_code = executor.execute(
            "failing command", show_command=False, check=False
        )
        assert exit_code == 1
        assert stderr == "error message"

        # With check=True, should raise
        with pytest.raises(SSHError, match="Command failed with exit code"):
            executor.execute("failing command", show_command=False, check=True)


def test_remote_executor_connection_error(mock_ssh_client, remote_config):
    """Test that connection errors are properly raised."""
    # Mock os.path.exists to return True so we get past the key check
    with patch("os.path.exists", return_value=True):
        mock_ssh_client.connect.side_effect = Exception("Connection failed")

        executor = RemoteExecutor(remote_config)
        with pytest.raises(SSHError, match="Failed to connect"):
            executor.connect()


@patch("os.path.exists", return_value=False)
def test_remote_executor_missing_ssh_key(mock_exists, mock_ssh_client, remote_config):
    """Test that missing SSH key file raises an error."""
    executor = RemoteExecutor(remote_config)
    with pytest.raises(SSHError, match="Invalid configuration"):
        executor.connect()


@patch("os.path.exists", return_value=True)
def test_remote_executor_file_exists(mock_exists, mock_ssh_client, remote_config):
    """Test file existence check when file exists."""
    # Mock successful test command (exit code 0)
    mock_channel = MagicMock()
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = Mock()
    mock_stdout.read.return_value = b""
    mock_stdout.channel = mock_channel

    mock_stderr = Mock()
    mock_stderr.read.return_value = b""

    mock_ssh_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

    executor = RemoteExecutor(remote_config)
    with executor:
        assert executor.file_exists("/test/path") is True
        # Verify the correct test command was used
        mock_ssh_client.exec_command.assert_called_with("test -f /test/path")


@patch("os.path.exists", return_value=True)
def test_remote_executor_file_not_exists(mock_exists, mock_ssh_client, remote_config):
    """Test file existence check when file doesn't exist."""
    # Mock failed test command (exit code 1)
    mock_channel = MagicMock()
    mock_channel.recv_exit_status.return_value = 1

    mock_stdout = Mock()
    mock_stdout.read.return_value = b""
    mock_stdout.channel = mock_channel

    mock_stderr = Mock()
    mock_stderr.read.return_value = b""

    mock_ssh_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

    executor = RemoteExecutor(remote_config)
    with executor:
        assert executor.file_exists("/nonexistent/path") is False


@patch("os.path.exists", return_value=True)
def test_remote_executor_docker_exec(mock_exists, mock_ssh_client, remote_config):
    """Test docker exec command construction."""
    mock_channel = MagicMock()
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = Mock()
    mock_stdout.read.return_value = b"docker output"
    mock_stdout.channel = mock_channel

    mock_stderr = Mock()
    mock_stderr.read.return_value = b""

    mock_ssh_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

    executor = RemoteExecutor(remote_config)
    with executor:
        stdout, stderr, exit_code = executor.docker_exec(
            "postgres", "psql -U postgres -l", show_command=False
        )
        assert stdout == "docker output"
        # Verify correct docker exec command
        expected_cmd = "docker exec postgres psql -U postgres -l"
        mock_ssh_client.exec_command.assert_called_with(expected_cmd)

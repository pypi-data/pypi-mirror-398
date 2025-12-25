# DuplicAid

[![PyPI version](https://badge.fury.io/py/duplicaid.svg)](https://badge.fury.io/py/duplicaid)
[![Tests](https://github.com/jstet/duplicaid/workflows/Release/badge.svg)](https://github.com/jstet/duplicaid/actions)
[![Python versions](https://img.shields.io/pypi/pyversions/duplicaid.svg)](https://pypi.org/project/duplicaid/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

DuplicAid is a CLI tool for managing PostgreSQL backups using SQL dumps. It provides a unified interface for creating, listing, and restoring backups from PostgreSQL instances running in Docker containers.

The tool supports both local and remote execution modes.

⚠️ The package depends on `tiredofit/docker-db-backup:4.1.21` for backup operations.


## Features

- **SQL Dumps**: Create and restore database backups using pg_dump/pg_restore
- **S3 Integration**: Store and retrieve backups from S3-compatible storage
- **Dual Execution Modes**: Manage backups locally or on remote servers via SSH

## Installation

Install duplicaid using uv:

```bash
# Install from PyPI
uv add duplicaid

# Or install from source
git clone <repository-url>
cd duplicaid
uv sync --extra dev
```

## Configuration

Duplicaid stores configuration in `.duplicaid.yml` in your current working directory by default. You can specify a different location using the `--config` flag.

### Execution Modes

**Remote Mode** (default):
- Manages PostgreSQL containers on a remote server via SSH
- Requires SSH key authentication
- All Docker commands executed on remote server

**Local Mode**:
- Manages PostgreSQL containers on the local machine
- No SSH connection required
- Docker commands executed locally

### Setup

Initialize configuration interactively:

```bash
duplicaid config init
```

### Configuration Options

- **Execution Mode**: `remote` or `local`
- **Remote Server** (remote mode only): SSH connection details (host, user, port, key path)
- **Container Names**: PostgreSQL and backup container names
- **PostgreSQL Credentials**: Database user and password
- **Paths**: Docker Compose file location

### Example Configurations

**Remote Mode:**
```yaml
execution_mode: remote
remote:
  host: your-server.example.com
  user: root
  port: 22
  ssh_key_path: /home/user/.ssh/id_rsa
containers:
  postgres: postgres
  backup: db-backup
postgres:
  user: postgres
  password: your_secure_password
  host: postgres
s3:
  endpoint: https://s3.amazonaws.com
  bucket: my-backups
  path: postgres/backups
  # access_key and secret_key can be set here or via env vars:
  # AWS_ACCESS_KEY_ID / S3_ACCESS_KEY
  # AWS_SECRET_ACCESS_KEY / S3_SECRET_KEY
paths:
  docker_compose: /home/user/postgres/docker-compose.yml
databases:
  - myapp
  - analytics
```

**Local Mode:**
```yaml
execution_mode: local
containers:
  postgres: postgres
  backup: db-backup
postgres:
  user: postgres
  password: your_secure_password
  host: postgres
s3:
  endpoint: http://localhost:9000
  bucket: my-backups
  path: postgres/backups
paths:
  docker_compose: /home/user/postgres/docker-compose.yml
```

**S3 Credentials:**

S3 credentials can be configured in two ways:

1. **In config file** (less secure):
   ```yaml
   s3:
     access_key: YOUR_ACCESS_KEY
     secret_key: YOUR_SECRET_KEY
   ```

2. **Via environment variables** (recommended):
   ```bash
   export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
   export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
   # or
   export S3_ACCESS_KEY=YOUR_ACCESS_KEY
   export S3_SECRET_KEY=YOUR_SECRET_KEY
   ```

## Quick Start

1. **Initialize Configuration**:
   ```bash
   duplicaid config init
   ```

2. **Check Status**:
   ```bash
   duplicaid status
   ```

3. **Create a Backup**:
   ```bash
   duplicaid backup create
   ```

4. **List Backups**:
   ```bash
   duplicaid list backups
   ```

5. **Restore a Backup**:
   ```bash
   duplicaid restore mydb backup_file.sql.bz2
   ```

## Backup Operations

### Creating Backups
- **Storage**: S3-compatible storage (compressed with bzip2)
- **Scope**: All configured databases backed up automatically
- **Format**: `pgsql_hostname_database_YYYYMMDD-HHMMSS.sql.bz2`

### Listing Backups
Backups can be listed from:
- S3-compatible storage (if configured)
- Local backup directory (fallback)

### Restoring Backups
- **Source**: Automatically downloads from S3 if not found locally
- **Scope**: Database-specific restoration
- **Compatibility**: Works across PostgreSQL versions

## Requirements

### Common Requirements
- Python 3.12+
- Docker and Docker Compose
- PostgreSQL container
- tiredofit/db-backup container for backup operations

### Remote Mode Additional Requirements
- SSH access to remote server
- SSH key authentication configured

### Local Mode Additional Requirements
- Docker daemon running locally
- Access to local Docker socket

## Development

### Setup

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd duplicaid
   uv sync --extra dev
   ```

2. **Install pre-commit hooks**:
   ```bash
   uv run pre-commit install
   ```

3. **Run tests**:
   ```bash
   uv run pytest
   ```

### Project Structure

```
duplicaid/
├── pyproject.toml          # Project configuration and dependencies
├── README.md               # This file
├── src/
│   └── duplicaid/          # Main package
│       ├── __init__.py
│       ├── cli.py          # CLI interface
│       ├── config.py       # Configuration management
│       ├── backup.py       # Backup operations
│       ├── ssh.py          # SSH connectivity
│       ├── executor.py     # Command execution
│       ├── discovery.py    # Database discovery
│       └── local.py        # Local operations
└── tests/                  # Test suite
    ├── conftest.py
    ├── test_cli.py
    ├── test_config.py
    ├── test_integration.py
    └── test_local_executor.py
```

### Testing

The test suite includes:
- **Unit tests**: Test individual components
- **Integration tests**: Test component interactions
- **CLI tests**: Test command-line interface

Run specific test types:
```bash
# All tests
uv run pytest

# Unit tests only
uv run pytest -k "not integration"

# Integration tests only
uv run pytest -m integration

# With coverage
uv run pytest --cov=duplicaid
```


### Development Workflow

This project uses automated releases with semantic commits.

#### Quick Start
```bash
# 1. Create feature branch
git checkout -b feat/new-feature

# 2. Push and create PR
git push origin feat/new-feature

# 3. Merge PR → Auto-release to PyPI
```

#### Semantic Commits
```bash
git commit -m "fix: resolve timeout"      # → patch release
git commit -m "feat: add encryption"      # → minor release
git commit -m "feat!: redesign API"       # → major release
```


#### Automation
- **PRs**: Auto-test, lint, format
- **Main branch**: Auto-version, auto-publish to PyPI
- **Pre-commit**: Enforce quality and commit format

### Building and Publishing

```bash
# Manual build (for testing)
uv build

# Automated publishing (via GitHub Actions)
# → Happens automatically on main branch pushes
# → No manual PyPI uploads needed

# Emergency manual publish (not recommended)
uv publish
```

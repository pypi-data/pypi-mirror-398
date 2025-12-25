## v4.3.0 (2025-12-23)

### Feat

- drop before recreate (#13)

## v4.2.3 (2025-12-23)

### Fix

- validate postgres credentials and default host/port for restore (#10)

## v4.2.2 (2025-12-23)

### Fix

- use configured backup container name in restore operations

## v4.2.1 (2025-12-23)

### Fix

- backup filename regex

## v4.2.0 (2025-12-23)

### Feat

- improve error message when ssh key is missing 2 (#5)

## v4.1.0 (2025-12-23)

### Feat

- improve error message when ssh key is missing (#4)

## v4.0.1 (2025-11-08)

### Fix

- hide commands and environment variables from output

## v4.0.0 (2025-11-08)

### Feat

- simplify cli

## v3.0.0 (2025-11-08)

### Feat

- simplify cli

## v2.0.0 (2025-11-08)

### Feat

- update log messages
- yeet walg, rework executors and improve integration tests

## v1.2.0 (2025-11-07)

### Feat

- add S3 support for listing logical backups using minio

## v1.1.1 (2025-11-07)

### Fix

- use configured postgres user instead of hardcoded 'postgres'

## v1.1.0 (2025-11-07)

### Feat

- add postgres user and password to config

## v1.0.0 (2025-11-07)

### Feat

- change config location to project directory

## v0.5.0 (2025-09-28)

### Feat

- add list databases command to show available PostgreSQL databases

## v0.4.0 (2025-09-28)

### Feat

- update Docker image dependency from lafayettegabe/wald to jstet/wald

### Fix

- simplify release workflow condition

## v0.2.0 (2025-09-27)

### Feat

- initial release of duplicaid CLI tool

### Fix

- resolve black/ruff formatting conflict
- **workflow**: handle existing tags in release process
- **executor**: resolve container name mapping in LocalExecutor methods
- **executor**: resolve container name mapping in LocalExecutor methods (#2)
- update uv version in workflow
- resolve all test failures for CI pipeline
- resolve test failures in CI workflow
- configure Git identity for automated releases
- add --yes flag to commitizen commands for CI
- add OIDC permissions and fix build step logic
- workflow dependency issue preventing releases

### Refactor

- remove redundant container name mapping method (#3)

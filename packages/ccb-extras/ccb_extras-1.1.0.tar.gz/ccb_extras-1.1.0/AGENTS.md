# AI Coding Instructions

## Project Overview

`ccb-extras` is a production Python 3.10+ utility library with two independent modules:
- **`crypto.py`**: File encryption/decryption via OpenSSL wrapper, plus MD5 hashing
- **`yaml.py`**: Config file handling with YAML persistence, comment preservation, and hierarchical key access

## Architecture & Key Patterns

### Type Safety & Quality Standards
- **Strict mypy enforcement** (see [mypy.ini](mypy.ini)): `disallow_untyped_defs=True`, `disallow_any_unimported=True`, `disallow_incomplete_defs=True`
- All functions must have complete type annotations; return types are mandatory
- The project is `py.typed` — any new code impacts downstream consumers

### Module Design
- **`crypto.py`**: Wraps OpenSSL CLI via `subprocess_command()` from `ccb_essentials`. Has a hardcoded `OPENSSL` path (`/opt/local/bin/openssl`); designed for macOS/MacPorts. Symmetric AES-256-CBC with PBKDF2 (100K iterations). File paths use `Path` objects; MD5 chunked reads (8KB) for memory efficiency.
- **`yaml.py`**: `YamlFile` class maps a YAML file to a Python `Dict` (actually `ruamel.yaml.CommentedMap`). Lazy file creation on first write. Supports nested dot/custom-delimited keys via `get_delimited_value()` / `set_delimited_value()`. Uses `ruamel.yaml` (typ='rt') for round-trip comment/formatting preservation.

### Dependencies
- **External**: `ruamel-yaml>=0.18.5`, `ccb-essentials>=1.0.1` (contains `subprocess_command`, `shell_escape`, `UTF8` constant)
- **Dev**: pytest, mypy, ruff (max line length: 120)

## Developer Workflow

### Setup
The project uses `hatchling` as the build backend, and `uv` to manage the virtual environment (see the `uv.lock` file).

### Testing & Linting
```bash
uv run pytest              # Run all tests
uv run bin/lint.sh         # Run mypy + ruff
```

### Publishing (semver versioning)
This project uses `hatchling` for building and publishing. See the `pyproject.toml` for configuration.

## Code Patterns & Conventions

### Logging
Use module-level logger: `log = logging.getLogger(__name__)`. Example: `log.debug('encrypt %s -> %s', source, dest)`.

### Path Handling
Always use `pathlib.Path`, not strings. Assertions validate file existence: `assert source.is_file()` and `assert not dest.exists()`.

### Error Handling
`crypto.py` uses assertions for preconditions; returns `bool` from subprocess calls. `yaml.py` catches `FileNotFoundError` during load, initializes with defaults, asserts the result is a `CommentedMap`.

### Comments & Examples
Significant utilities include detailed docstrings and are documented in [docs/](docs/) (e.g., [docs/crypto.md](docs/crypto.md), [docs/yaml.md](docs/yaml.md)). Add similar when creating new modules.

### Testing Patterns
Tests use `pytest` and `temporary_path()` from `ccb_essentials` for fixtures. See [tests/test_yaml.py](tests/test_yaml.py) for multi-file YAML format examples and hierarchical key tests.

## When Adding Features

1. **Type everything**: No `Any` or untyped imports without `noqa` exceptions
2. **Test coverage**: Add pytest tests in [tests/](tests/) with clear setup/tear-down
3. **Update docs**: Add examples to [docs/](docs/) for public APIs
4. **Lint before committing**: Run full `lint.sh` to catch violations
5. **Consider ccb-essentials reuse**: Check if utilities (paths, subprocess, constants) already exist there first

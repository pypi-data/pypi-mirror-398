# bitranox_template_cli_app_config_log

<!-- Badges -->
[![CI](https://github.com/bitranox/bitranox_template_cli_app_config_log/actions/workflows/ci.yml/badge.svg)](https://github.com/bitranox/bitranox_template_cli_app_config_log/actions/workflows/ci.yml)
[![CodeQL](https://github.com/bitranox/bitranox_template_cli_app_config_log/actions/workflows/codeql.yml/badge.svg)](https://github.com/bitranox/bitranox_template_cli_app_config_log/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Open in Codespaces](https://img.shields.io/badge/Codespaces-Open-blue?logo=github&logoColor=white&style=flat-square)](https://codespaces.new/bitranox/bitranox_template_cli_app_config_log?quickstart=1)
[![PyPI](https://img.shields.io/pypi/v/bitranox_template_cli_app_config_log.svg)](https://pypi.org/project/bitranox_template_cli_app_config_log/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/bitranox_template_cli_app_config_log.svg)](https://pypi.org/project/bitranox_template_cli_app_config_log/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-46A3FF?logo=ruff&labelColor=000)](https://docs.astral.sh/ruff/)
[![codecov](https://codecov.io/gh/bitranox/bitranox_template_cli_app_config_log/graph/badge.svg?token=UFBaUDIgRk)](https://codecov.io/gh/bitranox/bitranox_template_cli_app_config_log)
[![Maintainability](https://qlty.sh/badges/041ba2c1-37d6-40bb-85a0-ec5a8a0aca0c/maintainability.svg)](https://qlty.sh/gh/bitranox/projects/bitranox_template_cli_app_config_log)
[![Known Vulnerabilities](https://snyk.io/test/github/bitranox/bitranox_template_cli_app_config_log/badge.svg)](https://snyk.io/test/github/bitranox/bitranox_template_cli_app_config_log)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

`bitranox_template_cli_app_config_log` is a template CLI application demonstrating configuration management and structured logging. It showcases rich-click for ergonomics and lib_cli_exit_tools for exits, providing a solid foundation for building CLI applications.
- CLI entry point styled with rich-click (rich output + click ergonomics).
- Layered configuration system with lib_layered_config (defaults → app → host → user → .env → env).
- Rich structured logging with lib_log_rich (console, journald, eventlog, Graylog/GELF).
- Exit-code and messaging helpers powered by lib_cli_exit_tools.
- Metadata helpers ready for packaging, testing, and release automation.

## Install - recommended via UV
UV - the ultrafast installer - written in Rust (10–20× faster than pip/poetry)

```bash
# recommended Install via uv 
pip install --upgrade uv
# Create and activate a virtual environment (optional but recommended)
uv venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# install via uv from PyPI
uv pip install bitranox_template_cli_app_config_log
```

For alternative install paths (pip, pipx, uv, uvx source builds, etc.), see
[INSTALL.md](INSTALL.md). All supported methods register both the
`bitranox_template_cli_app_config_log` and `bitranox-template-cli-app-config-log` commands on your PATH.

### Python 3.13+ Baseline

- The project targets **Python 3.13 and newer only**. 
- Runtime dependencies stay on the current stable releases (`rich-click>=1.9.3`
  and `lib_cli_exit_tools>=2.0.0`) and keeps pytest, ruff, pyright, bandit,
  build, twine, codecov-cli, pip-audit, textual, and import-linter pinned to
  their newest majors.
- CI workflows exercise GitHub's rolling runner images (`ubuntu-latest`,
  `macos-latest`, `windows-latest`) and cover CPython 3.13 alongside the latest
  available 3.x release provided by Actions.


## Usage

The CLI leverages [rich-click](https://github.com/ewels/rich-click) so help output, validation errors, and prompts render with Rich styling while keeping the familiar click ergonomics.

### Available Commands

```bash
# Display package information
bitranox-template-cli-app-config-log info

# Test commands for development
bitranox-template-cli-app-config-log hello
bitranox-template-cli-app-config-log fail
bitranox-template-cli-app-config-log --traceback fail

# Configuration management
bitranox-template-cli-app-config-log config                    # Show current configuration
bitranox-template-cli-app-config-log config --format json      # Show as JSON
bitranox-template-cli-app-config-log config --section lib_log_rich  # Show specific section
bitranox-template-cli-app-config-log config --profile production    # Show config from a profile
bitranox-template-cli-app-config-log config-deploy --target user    # Deploy config to user directory
bitranox-template-cli-app-config-log config-deploy --target user --target host  # Deploy to multiple locations
bitranox-template-cli-app-config-log config-deploy --target user --profile staging  # Deploy to profile directory

# All commands work with any entry point
python -m bitranox_template_cli_app_config_log info
uvx bitranox_template_cli_app_config_log info
```

### Configuration Management

The application uses [lib_layered_config](https://github.com/bitranox/lib_layered_config) for hierarchical configuration with the following precedence (lowest to highest):

**defaults → app → host → user → .env → environment variables**

#### Configuration Locations

Platform-specific paths:
- **Linux (user)**: `~/.config/bitranox-template-cli-app-config-log/config.toml`
- **Linux (app)**: `/etc/xdg/bitranox-template-cli-app-config-log/config.toml`
- **Linux (host)**: `/etc/bitranox-template-cli-app-config-log/hosts/{hostname}.toml`
- **macOS (user)**: `~/Library/Application Support/bitranox/Bitranox Template CLI App Config Log/config.toml`
- **Windows (user)**: `%APPDATA%\bitranox\Bitranox Template CLI App Config Log\config.toml`

#### Profile-specific Paths

Profiles enable environment isolation by creating dedicated subdirectories for each profile name. Use `--profile <name>` with `config` or `config-deploy` commands.

- **Linux (user, profile=production)**: `~/.config/bitranox-template-cli-app-config-log/profile/production/config.toml`
- **Linux (user, profile=staging)**: `~/.config/bitranox-template-cli-app-config-log/profile/staging/config.toml`

Valid profile names: alphanumeric characters, hyphens, and underscores (e.g., `test`, `production`, `staging-v2`).

#### View Configuration

```bash
# Show merged configuration from all sources
bitranox-template-cli-app-config-log config

# Show as JSON for scripting
bitranox-template-cli-app-config-log config --format json

# Show specific section only
bitranox-template-cli-app-config-log config --section lib_log_rich

# Show configuration from a specific profile
bitranox-template-cli-app-config-log config --profile production
bitranox-template-cli-app-config-log config --profile staging --format json
```

#### Deploy Configuration Files

```bash
# Create user configuration file
bitranox-template-cli-app-config-log config-deploy --target user

# Deploy to system-wide location (requires privileges)
sudo bitranox-template-cli-app-config-log config-deploy --target app

# Deploy to multiple locations at once
bitranox-template-cli-app-config-log config-deploy --target user --target host

# Overwrite existing configuration
bitranox-template-cli-app-config-log config-deploy --target user --force

# Deploy to a profile-specific directory
bitranox-template-cli-app-config-log config-deploy --target user --profile production
bitranox-template-cli-app-config-log config-deploy --target user --profile staging --force
```

#### Environment Variable Overrides

Configuration can be overridden via environment variables using two methods:

**Method 1: Native lib_log_rich variables (highest precedence)**
```bash
LOG_CONSOLE_LEVEL=DEBUG bitranox-template-cli-app-config-log hello
LOG_ENABLE_GRAYLOG=true LOG_GRAYLOG_ENDPOINT="logs.example.com:12201" bitranox-template-cli-app-config-log hello
```

**Method 2: Application-prefixed variables**
```bash
# Format: <SLUG>___<SECTION>__<KEY>=<VALUE>
BITRANOX_TEMPLATE_CLI_APP_CONFIG_LOG___LIB_LOG_RICH__CONSOLE_LEVEL=DEBUG bitranox-template-cli-app-config-log hello
```

#### .env File Support

Create a `.env` file in your project directory for local development:

```bash
# .env
LOG_CONSOLE_LEVEL=DEBUG
LOG_CONSOLE_FORMAT_PRESET=short
LOG_ENABLE_GRAYLOG=false
```

The application automatically discovers and loads `.env` files from the current directory or parent directories.

### Library Use

You can import the documented helpers directly:

```python
import bitranox_template_cli_app_config_log as btcacl

btcacl.emit_greeting()
try:
    btcacl.raise_intentional_failure()
except RuntimeError as exc:
    print(f"caught expected failure: {exc}")

btcacl.print_info()
```


## Further Documentation

- [Install Guide](INSTALL.md)
- [Development Handbook](DEVELOPMENT.md)
- [Contributor Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Module Reference](docs/systemdesign/module_reference.md)
- [License](LICENSE)

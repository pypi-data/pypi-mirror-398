# Changelog

All notable changes to this project will be documented in this file following
the [Keep a Changelog](https://keepachangelog.com/) format.


## [0.1.5] - 2025-12-27

### Fixed
- Intermittent test failures on Windows (Python 3.10/3.11) when parsing JSON output from `config --format json`
- Tests now use `result.stdout` instead of `result.output` to avoid async log messages from `lib_log_rich` contaminating JSON output
- Error message assertions now correctly use `result.stderr` for messages written with `err=True`

## [0.1.4] - 2025-12-15

### Changed
- Lowered minimum Python version from 3.13 to 3.10
- CI test matrix now includes Python 3.10, 3.11, 3.12, and 3.13
- CI workflows and tests now use `rtoml` for TOML parsing (cross-version compatible)
- Ruff target version set to `py310`

## [0.1.3] - 2025-12-15

### Added
- Global `--profile` option on root CLI command for profile-specific configuration
- Profile inheritance from root command to subcommands (`config`, `config-deploy`)
- `LoggingConfig` Pydantic model for validated logging configuration

### Changed
- **BREAKING**: Refactored configuration loading - config is now loaded once in root CLI command
  and stored in Click context (`ctx.obj.config`) for all subcommands to access
- `init_logging()`, `_build_runtime_config()`, `_load_logging_config()` now accept `Config` object
  instead of profile string
- `display_config()` now accepts `Config` object as first parameter instead of profile
- Subcommand `--profile` options act as overrides that reload config when specified
- Conditional `lib_log_rich.runtime.shutdown()` - only when runtime was initialized

### Fixed
- All subcommands (`config`, `config-deploy`) now correctly use profile-specific
  configuration when `--profile` is specified on the root command

## [0.1.2] - 2025-12-15

### Fixed
- `deploy_configuration` now correctly returns `list[Path]` by extracting destination paths from `DeployResult` objects
- `--profile` option now correctly applies profile-specific settings to the logger

## [0.1.1] - 2025-12-08

### Fixed
- `config --format json` now outputs valid JSON by suppressing info log messages that were polluting stdout

## [0.1.0] - 2025-12-07

### Added
- `--profile` option to `config` command for loading configuration from named profiles
- `--profile` option to `config-deploy` command for deploying configuration to profile-specific directories
- Profile support enables environment isolation (e.g., `production`, `staging`, `test`)
- Profile-specific paths: `~/.config/<slug>/profile/<name>/config.toml`
- Comprehensive test coverage for profile functionality (154 tests, 93% coverage)
- Default configuration values in `defaultconfig.toml` for `[lib_log_rich]` section

### Fixed
- Windows Unicode encoding issues in CI tests (subprocess handling of emoji characters)
- Set `PYTHONIOENCODING=utf-8` in CI workflow for cross-platform compatibility

## [0.0.1] - 2025-11-11
- Bootstrap 

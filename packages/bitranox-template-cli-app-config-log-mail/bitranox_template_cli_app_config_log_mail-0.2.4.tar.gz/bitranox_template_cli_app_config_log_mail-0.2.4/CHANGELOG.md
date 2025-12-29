# Changelog

All notable changes to this project will be documented in this file following
the [Keep a Changelog](https://keepachangelog.com/) format.


## [0.2.4] - 2025-12-27

### Fixed
- Intermittent test failures on Windows (Python 3.10/3.11) when parsing JSON output from `config --format json`
- Tests now use `result.stdout` instead of `result.output` to avoid async log messages from `lib_log_rich` contaminating JSON output
- Error message assertions now correctly use `result.stderr` for messages written with `err=True`

## [0.2.3] - 2025-12-15

### Changed
- Lowered minimum Python version from 3.13 to 3.10
- Updated ruff target-version from py313 to py310
- Added Python 3.10, 3.11, 3.12, 3.13 classifiers to pyproject.toml
- Expanded CI test matrix to cover Python 3.10, 3.11, 3.12, 3.13
- Replaced `tomllib` with `rtoml` in CI workflows and tests for Python 3.10 compatibility

## [0.2.2] - 2025-12-15

### Added
- Global `--profile` option on root CLI command for profile-specific configuration
- Profile inheritance from root command to subcommands (`config`, `config-deploy`)

### Changed
- **BREAKING**: Refactored configuration loading - config is now loaded once in root CLI command
  and stored in Click context (`ctx.obj["config"]`) for all subcommands to access
- `init_logging()`, `_build_runtime_config()`, `_load_logging_config()` now accept `Config` object
  instead of profile string
- `display_config()` now accepts `Config` object as first parameter instead of profile
- `_load_and_validate_email_config()` now accepts `Config` object instead of profile
- Subcommand `--profile` options act as overrides that reload config when specified
- Conditional `lib_log_rich.runtime.shutdown()` - only when runtime was initialized
- Updated `actions/cache` from v4 to v5 in CI workflow
- Updated `actions/upload-artifact` from v5 to v6 in release workflow

### Fixed
- Type compatibility with `lib_layered_config.deploy_config()` returning `list[DeployResult]`
- All subcommands (`config`, `send-email`, `send-notification`) now correctly use profile-specific
  configuration when `--profile` is specified on the root command

## [0.2.1] - 2025-12-08

### Changed
- Updated `lib_cli_exit_tools` from >=2.1.0 to >=2.1.1
- Updated `lib_log_rich` from >=5.5.0 to >=5.5.1
- Updated `lib_layered_config` from >=4.0.0 to >=4.0.1
- Updated `import-linter` dev dependency from >=2.7 to >=2.8

## [0.2.0] - 2025-12-07

### Added
- `--profile` option for `config` command to load profile-specific configuration
- `--profile` option for `config-deploy` command to deploy to profile directories
- Profile parameter support in `get_config()`, `display_config()`, and `deploy_configuration()`
- Profile-specific configuration paths (e.g., `~/.config/slug/profile/<name>/config.toml`)
- `OutputFormat` and `DeployTarget` enums for type-safe CLI options
- `LoggingConfig` Pydantic model for validated logging configuration
- 4 new behavioral tests for profile functionality
- PYTHONIOENCODING=utf-8 for all subprocess calls in scripts

### Changed
- Centralized test fixtures in `conftest.py` (`MockConfig`, `mock_config_factory`, `clear_config_cache`)
- Flattened `test_mail.py` from class-based to function-based tests
- Added `@pytest.mark.os_agnostic` markers to all mail tests
- Increased lru_cache maxsize from 1 to 4 in `get_config()` for profile variations
- Added lru_cache to `get_default_config_path()` since the path never changes at runtime
- Updated `config_deploy.py` to use `DeployTarget` enum instead of strings
- Updated README with profile configuration documentation and examples

### Fixed
- UTF-8 encoding issues in subprocess calls across different locales

## [0.1.0] - 2025-12-07

### Added
- Email sending functionality via `btx-lib-mail>=1.0.1` integration
- Two new CLI commands: `send-email` and `send-notification`
- Email configuration support via lib_layered_config with sensible defaults
- Comprehensive email wrapper with `EmailConfig` dataclass in `mail.py`
- Email configuration validation in `__post_init__` (timeout, from_address, SMTP host:port format)
- Real SMTP integration tests using .env configuration (TEST_SMTP_SERVER, TEST_EMAIL_ADDRESS)
- 48 new tests covering email functionality:
  - 18 EmailConfig validation tests
  - 4 configuration loading tests
  - 6 email sending tests (unit)
  - 2 notification tests (unit)
  - 5 error scenario tests
  - 5 edge case tests
  - 3 real SMTP integration tests
  - 10 CLI integration tests
- `.env.example` documentation for TEST_SMTP_SERVER and TEST_EMAIL_ADDRESS
- DotEnv loading in test suite for integration test configuration

### Changed
- Extracted `_load_and_validate_email_config()` helper function to eliminate code duplication between CLI email commands
- Updated test suite from 56 to 104 passing tests
- Increased code coverage from 79% to 87.50%
- Enhanced `conftest.py` with automatic .env loading for integration tests

### Dependencies
- Added `btx-lib-mail>=1.0.1` for SMTP email sending capabilities

## [0.0.1] - 2025-11-11
- Bootstrap 

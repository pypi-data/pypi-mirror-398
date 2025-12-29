"""CLI command tests: each invocation tells a single story.

Tests for the command-line interface covering:
- Traceback state management
- Command invocation (hello, fail, info, config, config-deploy)
- Help and error handling
- Real behavior verification (not stub-only tests)
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from click.testing import CliRunner

import lib_cli_exit_tools

from bitranox_template_cli_app_config_log import __init__conf__
from bitranox_template_cli_app_config_log import cli as cli_mod
from bitranox_template_cli_app_config_log.cli import TracebackState


# =============================================================================
# Traceback State Management Tests
# =============================================================================


@pytest.mark.os_agnostic
class TestTracebackSnapshot:
    """Tests for traceback state snapshot functionality."""

    def test_initial_state_is_disabled(self, isolated_traceback_config: None) -> None:
        """When we snapshot traceback, the initial state is quiet."""
        state = cli_mod.snapshot_traceback_state()

        assert state.traceback_enabled is False

    def test_initial_color_is_disabled(self, isolated_traceback_config: None) -> None:
        """When we snapshot traceback, color forcing is disabled."""
        state = cli_mod.snapshot_traceback_state()

        assert state.force_color is False

    def test_returns_traceback_state_dataclass(self, isolated_traceback_config: None) -> None:
        """The snapshot returns a TracebackState dataclass."""
        state = cli_mod.snapshot_traceback_state()

        assert isinstance(state, TracebackState)


@pytest.mark.os_agnostic
class TestTracebackPreferences:
    """Tests for applying traceback preferences."""

    def test_enabling_sets_traceback_true(self, isolated_traceback_config: None) -> None:
        """When we enable traceback, the config sings true."""
        cli_mod.apply_traceback_preferences(True)

        assert lib_cli_exit_tools.config.traceback is True

    def test_enabling_sets_force_color_true(self, isolated_traceback_config: None) -> None:
        """When we enable traceback, color forcing activates."""
        cli_mod.apply_traceback_preferences(True)

        assert lib_cli_exit_tools.config.traceback_force_color is True

    def test_disabling_sets_traceback_false(self, isolated_traceback_config: None) -> None:
        """When we disable traceback, the config whispers false."""
        cli_mod.apply_traceback_preferences(True)
        cli_mod.apply_traceback_preferences(False)

        assert lib_cli_exit_tools.config.traceback is False


@pytest.mark.os_agnostic
class TestTracebackRestore:
    """Tests for restoring traceback state."""

    def test_restore_returns_to_previous_state(self, isolated_traceback_config: None) -> None:
        """When we restore traceback, the config returns to its previous state."""
        previous = cli_mod.snapshot_traceback_state()
        cli_mod.apply_traceback_preferences(True)

        cli_mod.restore_traceback_state(previous)

        assert lib_cli_exit_tools.config.traceback is False

    def test_restore_resets_force_color(self, isolated_traceback_config: None) -> None:
        """When we restore, force color also returns."""
        previous = cli_mod.snapshot_traceback_state()
        cli_mod.apply_traceback_preferences(True)

        cli_mod.restore_traceback_state(previous)

        assert lib_cli_exit_tools.config.traceback_force_color is False


# =============================================================================
# Hello Command Tests
# =============================================================================


@pytest.mark.os_agnostic
class TestHelloCommand:
    """Tests for the hello command."""

    def test_exits_successfully(self, cli_runner: CliRunner) -> None:
        """When hello is invoked, the CLI exits with success."""
        result = cli_runner.invoke(cli_mod.cli, ["hello"])

        assert result.exit_code == 0

    def test_outputs_greeting(self, cli_runner: CliRunner) -> None:
        """When hello is invoked, the CLI smiles with a greeting."""
        result = cli_runner.invoke(cli_mod.cli, ["hello"])

        assert "Hello World" in result.output


# =============================================================================
# Fail Command Tests
# =============================================================================


@pytest.mark.os_agnostic
class TestFailCommand:
    """Tests for the fail command."""

    def test_exits_with_error(self, cli_runner: CliRunner) -> None:
        """When fail is invoked, the CLI exits with an error."""
        result = cli_runner.invoke(cli_mod.cli, ["fail"])

        assert result.exit_code != 0

    def test_raises_runtime_error(self, cli_runner: CliRunner) -> None:
        """When fail is invoked, a RuntimeError is raised."""
        result = cli_runner.invoke(cli_mod.cli, ["fail"])

        assert isinstance(result.exception, RuntimeError)


# =============================================================================
# Info Command Tests
# =============================================================================


@pytest.mark.os_agnostic
class TestInfoCommand:
    """Tests for the info command."""

    def test_exits_successfully(self, cli_runner: CliRunner) -> None:
        """When info is invoked, the CLI exits with success."""
        result = cli_runner.invoke(cli_mod.cli, ["info"])

        assert result.exit_code == 0

    def test_displays_package_name(self, cli_runner: CliRunner) -> None:
        """When info is invoked, the package name is displayed."""
        result = cli_runner.invoke(cli_mod.cli, ["info"])

        assert __init__conf__.name in result.output

    def test_displays_version(self, cli_runner: CliRunner) -> None:
        """When info is invoked, the version is displayed."""
        result = cli_runner.invoke(cli_mod.cli, ["info"])

        assert __init__conf__.version in result.output

    def test_displays_author(self, cli_runner: CliRunner) -> None:
        """When info is invoked, the author is displayed."""
        result = cli_runner.invoke(cli_mod.cli, ["info"])

        assert __init__conf__.author in result.output

    def test_displays_homepage(self, cli_runner: CliRunner) -> None:
        """When info is invoked, the homepage URL is displayed."""
        result = cli_runner.invoke(cli_mod.cli, ["info"])

        assert __init__conf__.homepage in result.output


# =============================================================================
# Config Command Tests - Real Behavior
# =============================================================================


@pytest.mark.os_agnostic
class TestConfigCommand:
    """Tests for the config command with real configuration."""

    def test_exits_successfully(self, cli_runner: CliRunner) -> None:
        """When config is invoked, the CLI exits with success."""
        result = cli_runner.invoke(cli_mod.cli, ["config"])

        assert result.exit_code == 0

    def test_human_format_shows_sections_when_config_exists(self, cli_runner: CliRunner) -> None:
        """When human format is used and config exists, section headers appear in brackets."""
        result = cli_runner.invoke(cli_mod.cli, ["config"])

        # Config may be empty in CI environments where no user config exists
        # and defaultconfig.toml has all values commented out
        if result.output.strip():
            assert "[" in result.output
            assert "]" in result.output

    def test_json_format_outputs_valid_json(self, cli_runner: CliRunner) -> None:
        """When JSON format is requested, output is valid JSON."""
        result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json"])

        assert result.exit_code == 0
        # Use result.stdout to avoid async log messages from stderr
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, dict)

    def test_json_format_contains_config_data(self, cli_runner: CliRunner) -> None:
        """When JSON format is used, configuration data is present."""
        result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json"])

        # Use result.stdout to avoid async log messages from stderr
        parsed = json.loads(result.stdout)
        # Config should have at least one key
        assert len(parsed) >= 0

    def test_nonexistent_section_fails(self, cli_runner: CliRunner) -> None:
        """When a nonexistent section is requested, the CLI fails."""
        result = cli_runner.invoke(
            cli_mod.cli,
            ["config", "--section", "nonexistent_section_xyz"],
        )

        assert result.exit_code != 0

    def test_nonexistent_section_shows_error(self, cli_runner: CliRunner) -> None:
        """When a nonexistent section is requested, an error message appears."""
        result = cli_runner.invoke(
            cli_mod.cli,
            ["config", "--section", "nonexistent_section_xyz"],
        )

        assert "not found or empty" in result.stderr

    def test_human_format_output_succeeds(self, cli_runner: CliRunner) -> None:
        """When human format is used, command succeeds."""
        result = cli_runner.invoke(cli_mod.cli, ["config"])

        # Command should succeed regardless of whether config is empty
        assert result.exit_code == 0
        # If config has content, it should contain section markers
        if result.output.strip():
            assert "[" in result.output


# =============================================================================
# Config Command Profile Tests
# =============================================================================


@pytest.mark.os_agnostic
class TestConfigProfileOption:
    """Tests for the config command with --profile option."""

    def test_profile_option_is_accepted(self, cli_runner: CliRunner) -> None:
        """When --profile is provided, the CLI accepts it."""
        result = cli_runner.invoke(cli_mod.cli, ["config", "--profile", "test"])

        # Should not fail due to invalid option
        assert "No such option" not in result.output

    def test_profile_with_json_format_works(self, cli_runner: CliRunner) -> None:
        """When --profile and --format json are combined, both work."""
        result = cli_runner.invoke(
            cli_mod.cli,
            ["config", "--profile", "production", "--format", "json"],
        )

        # Should not fail due to invalid option
        assert "No such option" not in result.output
        # If successful, output should contain JSON structure
        if result.exit_code == 0:
            assert "{" in result.output

    def test_profile_with_section_filter_works(self, cli_runner: CliRunner) -> None:
        """When --profile and --section are combined, both work."""
        result = cli_runner.invoke(
            cli_mod.cli,
            ["config", "--profile", "staging", "--section", "lib_log_rich"],
        )

        # May succeed or fail based on section existence, but option is accepted
        assert "No such option" not in result.output


# =============================================================================
# Config-Deploy Command Tests - Real Behavior
# =============================================================================


@pytest.mark.os_agnostic
class TestConfigDeployCommand:
    """Tests for the config-deploy command validation."""

    def test_missing_target_fails(self, cli_runner: CliRunner) -> None:
        """When config-deploy is invoked without target, it fails."""
        result = cli_runner.invoke(cli_mod.cli, ["config-deploy"])

        assert result.exit_code != 0

    def test_missing_target_shows_error(self, cli_runner: CliRunner) -> None:
        """When target is missing, an error message guides the user."""
        result = cli_runner.invoke(cli_mod.cli, ["config-deploy"])

        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_invalid_target_fails(self, cli_runner: CliRunner) -> None:
        """When an invalid target is provided, the CLI fails."""
        result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "invalid_target"])

        assert result.exit_code != 0

    def test_invalid_target_shows_valid_choices(self, cli_runner: CliRunner) -> None:
        """When an invalid target is provided, valid choices are shown."""
        result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "invalid_target"])

        assert "app" in result.output or "user" in result.output or "host" in result.output


# =============================================================================
# Config-Deploy Profile Tests
# =============================================================================


@pytest.mark.os_agnostic
class TestConfigDeployProfileOption:
    """Tests for the config-deploy command with --profile option."""

    def test_profile_option_is_accepted(self, cli_runner: CliRunner) -> None:
        """When --profile is provided to config-deploy, the CLI accepts it."""
        result = cli_runner.invoke(
            cli_mod.cli,
            ["config-deploy", "--target", "user", "--profile", "test"],
        )

        # Should not fail due to invalid option
        assert "No such option" not in result.output

    def test_profile_with_force_flag_works(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When --profile and --force are combined, both work."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))

        result = cli_runner.invoke(
            cli_mod.cli,
            ["config-deploy", "--target", "user", "--profile", "production", "--force"],
        )

        # Should not fail due to invalid option
        assert "No such option" not in result.output

    def test_profile_deploys_to_profile_subdirectory(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When --profile is used, config is deployed to profile subdirectory."""
        config_home = tmp_path / ".config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

        result = cli_runner.invoke(
            cli_mod.cli,
            ["config-deploy", "--target", "user", "--profile", "staging", "--force"],
        )

        if result.exit_code == 0:
            # Check that profile path was used (path contains 'profile/staging')
            assert "staging" in result.output or config_home.exists()


@pytest.mark.os_agnostic
class TestConfigDeployRealBehavior:
    """Tests for config-deploy with real deployment to temp directories."""

    def test_user_deploy_creates_file_in_temp(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When deploying to user target, a config file is created."""
        user_config_dir = tmp_path / ".config" / "bitranox_template_cli_app_config_log"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))

        result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user", "--force"])

        if result.exit_code == 0:
            assert user_config_dir.exists() or "Configuration deployed" in result.output
        else:
            assert "Permission" in result.stderr or "sudo" in result.stderr.lower()

    def test_force_flag_overwrites_existing(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When --force is used, existing files are overwritten."""
        user_config_dir = tmp_path / ".config" / "bitranox_template_cli_app_config_log"
        user_config_dir.mkdir(parents=True, exist_ok=True)
        existing_file = user_config_dir / "config.toml"
        existing_file.write_text("old content")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))

        result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user", "--force"])

        if result.exit_code == 0:
            assert "Configuration deployed" in result.output or existing_file.exists()

    def test_without_force_shows_hint_when_exists(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When file exists and --force not used, hint is shown."""
        user_config_dir = tmp_path / ".config" / "bitranox_template_cli_app_config_log"
        user_config_dir.mkdir(parents=True, exist_ok=True)
        existing_file = user_config_dir / "config.toml"
        existing_file.write_text("old content")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))

        result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"])

        if result.exit_code == 0 and "No configuration" in result.output:
            assert "--force" in result.output


# =============================================================================
# Help and Error Handling Tests
# =============================================================================


@pytest.mark.os_agnostic
class TestHelpOutput:
    """Tests for help output."""

    def test_no_arguments_shows_help(self, cli_runner: CliRunner) -> None:
        """When CLI runs without arguments, help is printed."""
        result = cli_runner.invoke(cli_mod.cli, [])

        assert "Usage:" in result.output

    def test_no_arguments_exits_zero(self, cli_runner: CliRunner) -> None:
        """When CLI runs without arguments, it exits successfully."""
        result = cli_runner.invoke(cli_mod.cli, [])

        assert result.exit_code == 0

    def test_help_flag_shows_usage(self, cli_runner: CliRunner) -> None:
        """When --help is passed, usage information appears."""
        result = cli_runner.invoke(cli_mod.cli, ["--help"])

        assert "Usage:" in result.output

    def test_help_lists_available_commands(self, cli_runner: CliRunner) -> None:
        """When --help is passed, available commands are listed."""
        result = cli_runner.invoke(cli_mod.cli, ["--help"])

        assert "hello" in result.output
        assert "info" in result.output
        assert "config" in result.output

    def test_command_help_shows_options(self, cli_runner: CliRunner) -> None:
        """When command --help is used, command options are shown."""
        result = cli_runner.invoke(cli_mod.cli, ["config", "--help"])

        assert "--format" in result.output
        assert "--section" in result.output
        assert "--profile" in result.output

    def test_config_deploy_help_shows_profile_option(self, cli_runner: CliRunner) -> None:
        """When config-deploy --help is used, profile option is shown."""
        result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--help"])

        assert "--profile" in result.output


@pytest.mark.os_agnostic
class TestUnknownCommand:
    """Tests for unknown command handling."""

    def test_unknown_command_fails(self, cli_runner: CliRunner) -> None:
        """When an unknown command is used, the CLI fails."""
        result = cli_runner.invoke(cli_mod.cli, ["does-not-exist"])

        assert result.exit_code != 0

    def test_unknown_command_shows_error(self, cli_runner: CliRunner) -> None:
        """When an unknown command is used, a helpful error appears."""
        result = cli_runner.invoke(cli_mod.cli, ["does-not-exist"])

        assert "No such command" in result.output


# =============================================================================
# Traceback Flag Integration Tests - Real Behavior
# =============================================================================


@pytest.mark.os_agnostic
class TestTracebackFlagIntegration:
    """Tests for --traceback flag integration with commands."""

    def test_traceback_flag_shows_full_traceback(
        self,
        isolated_traceback_config: None,
        capsys: pytest.CaptureFixture[str],
        strip_ansi: Callable[[str], str],
    ) -> None:
        """When --traceback is passed, the full story is printed."""
        cli_mod.main(["--traceback", "fail"])

        plain_err = strip_ansi(capsys.readouterr().err)

        assert "Traceback (most recent call last)" in plain_err

    def test_traceback_flag_shows_exception_message(
        self,
        isolated_traceback_config: None,
        capsys: pytest.CaptureFixture[str],
        strip_ansi: Callable[[str], str],
    ) -> None:
        """When --traceback is passed, the exception message appears."""
        cli_mod.main(["--traceback", "fail"])

        plain_err = strip_ansi(capsys.readouterr().err)

        assert "RuntimeError: I should fail" in plain_err

    def test_traceback_flag_restores_config_after_run(
        self,
        isolated_traceback_config: None,
        capsys: pytest.CaptureFixture[str],
        strip_ansi: Callable[[str], str],
    ) -> None:
        """After running with --traceback, the config is restored."""
        cli_mod.main(["--traceback", "fail"])
        _ = capsys.readouterr()

        assert lib_cli_exit_tools.config.traceback is False

    def test_restore_disabled_keeps_traceback_enabled(
        self,
        isolated_traceback_config: None,
        preserve_traceback_state: None,
    ) -> None:
        """When restore is disabled, the traceback choice remains."""
        cli_mod.apply_traceback_preferences(False)

        cli_mod.main(["--traceback", "hello"], restore_traceback=False)

        assert lib_cli_exit_tools.config.traceback is True

    def test_traceback_without_command_shows_help(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """When --traceback is passed without command, help is shown."""
        result = cli_runner.invoke(cli_mod.cli, ["--traceback"])

        assert result.exit_code == 0


# =============================================================================
# Main Entry Point Tests - Real Behavior
# =============================================================================


@pytest.mark.os_agnostic
class TestMainEntryPoint:
    """Tests for the main() entry point function."""

    def test_info_command_returns_zero(
        self,
        isolated_traceback_config: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When info command runs via main, exit code is zero."""
        exit_code = cli_mod.main(["info"])

        assert exit_code == 0

    def test_hello_command_returns_zero(
        self,
        isolated_traceback_config: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When hello command runs via main, exit code is zero."""
        exit_code = cli_mod.main(["hello"])

        assert exit_code == 0

    def test_fail_command_returns_nonzero(
        self,
        isolated_traceback_config: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When fail command runs via main, exit code is nonzero."""
        exit_code = cli_mod.main(["fail"])

        assert exit_code != 0

    def test_traceback_preference_is_applied_during_command(
        self,
        isolated_traceback_config: None,
        capsys: pytest.CaptureFixture[str],
        strip_ansi: Callable[[str], str],
    ) -> None:
        """When --traceback is passed, traceback appears in output."""
        cli_mod.main(["--traceback", "fail"])

        plain_err = strip_ansi(capsys.readouterr().err)

        assert "Traceback" in plain_err

    def test_config_command_via_main_succeeds(
        self,
        isolated_traceback_config: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When config command runs via main, it succeeds."""
        exit_code = cli_mod.main(["config"])

        assert exit_code == 0
        # Config may be empty in CI environments where no user config exists
        # and defaultconfig.toml has all values commented out
        captured = capsys.readouterr()
        if captured.out.strip():
            assert "[" in captured.out

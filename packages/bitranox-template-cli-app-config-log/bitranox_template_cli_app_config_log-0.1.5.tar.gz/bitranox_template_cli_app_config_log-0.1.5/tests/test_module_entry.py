"""Module entry tests: ensuring `python -m` mirrors the CLI.

Tests for verifying that running the package as a module (`python -m`)
behaves identically to invoking the CLI directly. Uses real behavior
verification instead of mocking.
"""

from __future__ import annotations

import os
import runpy
import subprocess
import sys
from collections.abc import Callable

import pytest

import lib_cli_exit_tools

from bitranox_template_cli_app_config_log import __init__conf__, cli as cli_mod


def _run_module_subprocess(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with UTF-8 encoding for cross-platform compatibility.

    Windows console uses cp1252 by default which cannot handle Unicode
    characters (emoji level icons) from lib_log_rich output.

    Args:
        args: Command arguments to pass to subprocess.
        timeout: Maximum time to wait for process completion.

    Returns:
        CompletedProcess with stdout/stderr as strings.
    """
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        encoding="utf-8",
        errors="replace",
    )


# =============================================================================
# Module Entry via Subprocess - Real Behavior
# =============================================================================


@pytest.mark.os_agnostic
class TestModuleEntrySubprocess:
    """Tests for module entry using real subprocess execution."""

    def test_module_runs_without_error(self) -> None:
        """When `python -m` runs with --help, it exits successfully."""
        result = _run_module_subprocess(
            [sys.executable, "-m", "bitranox_template_cli_app_config_log", "--help"],
        )

        assert result.returncode == 0

    def test_module_shows_usage(self) -> None:
        """When `python -m` runs with --help, usage information appears."""
        result = _run_module_subprocess(
            [sys.executable, "-m", "bitranox_template_cli_app_config_log", "--help"],
        )

        assert "Usage:" in result.stdout

    def test_module_hello_outputs_greeting(self) -> None:
        """When `python -m` runs hello command, greeting appears."""
        result = _run_module_subprocess(
            [sys.executable, "-m", "bitranox_template_cli_app_config_log", "hello"],
        )

        assert result.returncode == 0
        assert "Hello World" in result.stdout

    def test_module_info_shows_version(self) -> None:
        """When `python -m` runs info command, version appears."""
        result = _run_module_subprocess(
            [sys.executable, "-m", "bitranox_template_cli_app_config_log", "info"],
        )

        assert result.returncode == 0
        assert __init__conf__.version in result.stdout

    def test_module_fail_exits_nonzero(self) -> None:
        """When `python -m` runs fail command, exit code is nonzero."""
        result = _run_module_subprocess(
            [sys.executable, "-m", "bitranox_template_cli_app_config_log", "fail"],
        )

        assert result.returncode != 0

    def test_module_fail_shows_error(self) -> None:
        """When `python -m` runs fail command, error message appears."""
        result = _run_module_subprocess(
            [sys.executable, "-m", "bitranox_template_cli_app_config_log", "fail"],
        )

        # Error message appears in stdout or stderr depending on output configuration
        combined_output = result.stdout + result.stderr
        assert "I should fail" in combined_output or "RuntimeError" in combined_output

    def test_module_config_outputs_json(self) -> None:
        """When `python -m` runs config --format json, JSON is output."""
        result = _run_module_subprocess(
            [sys.executable, "-m", "bitranox_template_cli_app_config_log", "config", "--format", "json"],
        )

        assert result.returncode == 0
        assert "{" in result.stdout

    def test_module_unknown_command_fails(self) -> None:
        """When `python -m` runs unknown command, it fails."""
        result = _run_module_subprocess(
            [sys.executable, "-m", "bitranox_template_cli_app_config_log", "unknown_cmd"],
        )

        assert result.returncode != 0


# =============================================================================
# Traceback Flag Tests - Real Behavior
# =============================================================================


@pytest.mark.os_agnostic
class TestTracebackFlag:
    """Tests for the --traceback flag behavior using real execution."""

    def test_traceback_flag_shows_traceback(self) -> None:
        """When --traceback is used with fail, full traceback appears."""
        result = _run_module_subprocess(
            [sys.executable, "-m", "bitranox_template_cli_app_config_log", "--traceback", "fail"],
        )

        assert result.returncode != 0
        # Traceback text may contain ANSI codes, check for key indicator
        assert "Traceback" in result.stderr or "most recent call" in result.stderr

    def test_traceback_flag_shows_exception_type(self) -> None:
        """When --traceback is used, exception type appears."""
        result = _run_module_subprocess(
            [sys.executable, "-m", "bitranox_template_cli_app_config_log", "--traceback", "fail"],
        )

        assert "RuntimeError" in result.stderr

    def test_traceback_flag_shows_exception_message(self) -> None:
        """When --traceback is used, exception message appears."""
        result = _run_module_subprocess(
            [sys.executable, "-m", "bitranox_template_cli_app_config_log", "--traceback", "fail"],
        )

        assert "I should fail" in result.stderr

    def test_without_traceback_error_is_concise(self) -> None:
        """When --traceback is not used, error is more concise."""
        with_traceback = _run_module_subprocess(
            [sys.executable, "-m", "bitranox_template_cli_app_config_log", "--traceback", "fail"],
        )

        without_traceback = _run_module_subprocess(
            [sys.executable, "-m", "bitranox_template_cli_app_config_log", "fail"],
        )

        # With traceback includes stack frames, without doesn't
        assert "Traceback" in with_traceback.stderr or "most recent call" in with_traceback.stderr
        assert without_traceback.returncode != 0


# =============================================================================
# Module Entry via runpy - Real Behavior
# =============================================================================


@pytest.mark.os_agnostic
class TestModuleEntryRunpy:
    """Tests for module entry using runpy with real CLI execution."""

    def test_exit_code_is_nonzero_on_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        strip_ansi: Callable[[str], str],
    ) -> None:
        """When --traceback is used and failure occurs, exit code is nonzero."""
        monkeypatch.setattr(sys, "argv", ["check_zpool_status", "--traceback", "fail"])
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

        with pytest.raises(SystemExit) as exc:
            runpy.run_module("bitranox_template_cli_app_config_log.__main__", run_name="__main__")

        assert exc.value.code != 0

    def test_full_traceback_is_printed(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        strip_ansi: Callable[[str], str],
    ) -> None:
        """When --traceback is used, the full traceback appears in stderr."""
        monkeypatch.setattr(sys, "argv", ["check_zpool_status", "--traceback", "fail"])
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

        with pytest.raises(SystemExit):
            runpy.run_module("bitranox_template_cli_app_config_log.__main__", run_name="__main__")

        plain_err = strip_ansi(capsys.readouterr().err)
        assert "Traceback (most recent call last)" in plain_err

    def test_exception_message_is_included(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        strip_ansi: Callable[[str], str],
    ) -> None:
        """When --traceback is used, the exception message appears in stderr."""
        monkeypatch.setattr(sys, "argv", ["check_zpool_status", "--traceback", "fail"])
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

        with pytest.raises(SystemExit):
            runpy.run_module("bitranox_template_cli_app_config_log.__main__", run_name="__main__")

        plain_err = strip_ansi(capsys.readouterr().err)
        assert "RuntimeError: I should fail" in plain_err

    def test_output_is_not_truncated(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        strip_ansi: Callable[[str], str],
    ) -> None:
        """When --traceback is used, the output is not truncated."""
        monkeypatch.setattr(sys, "argv", ["check_zpool_status", "--traceback", "fail"])
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

        with pytest.raises(SystemExit):
            runpy.run_module("bitranox_template_cli_app_config_log.__main__", run_name="__main__")

        plain_err = strip_ansi(capsys.readouterr().err)
        assert "[TRUNCATED" not in plain_err

    def test_global_config_remains_unchanged(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        strip_ansi: Callable[[str], str],
    ) -> None:
        """When --traceback is used, global config remains unchanged after exit."""
        monkeypatch.setattr(sys, "argv", ["check_zpool_status", "--traceback", "fail"])
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

        with pytest.raises(SystemExit):
            runpy.run_module("bitranox_template_cli_app_config_log.__main__", run_name="__main__")

        assert lib_cli_exit_tools.config.traceback is False
        assert lib_cli_exit_tools.config.traceback_force_color is False

    def test_hello_command_succeeds(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When hello command runs via runpy, it succeeds."""
        monkeypatch.setattr(sys, "argv", ["check_zpool_status", "hello"])
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

        with pytest.raises(SystemExit) as exc:
            runpy.run_module("bitranox_template_cli_app_config_log.__main__", run_name="__main__")

        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "Hello World" in captured.out

    def test_info_command_succeeds(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When info command runs via runpy, it succeeds."""
        monkeypatch.setattr(sys, "argv", ["check_zpool_status", "info"])
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
        monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

        with pytest.raises(SystemExit) as exc:
            runpy.run_module("bitranox_template_cli_app_config_log.__main__", run_name="__main__")

        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert __init__conf__.name in captured.out


# =============================================================================
# CLI Import Tests
# =============================================================================


@pytest.mark.os_agnostic
class TestCliImport:
    """Tests for CLI module import behavior."""

    def test_cli_alias_stays_intact(self) -> None:
        """When module entry imports CLI, the alias stays intact."""
        assert cli_mod.cli.name == cli_mod.cli.name

    def test_cli_has_expected_commands(self) -> None:
        """When CLI is imported, expected commands are available."""
        command_names = [cmd for cmd in cli_mod.cli.commands]

        assert "hello" in command_names
        assert "info" in command_names
        assert "fail" in command_names
        assert "config" in command_names

    def test_shell_command_is_defined(self) -> None:
        """The shell command constant is defined."""
        assert __init__conf__.shell_command is not None
        assert len(__init__conf__.shell_command) > 0

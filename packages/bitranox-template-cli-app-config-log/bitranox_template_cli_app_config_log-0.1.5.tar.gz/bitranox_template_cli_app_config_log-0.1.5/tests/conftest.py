"""Shared pytest fixtures and markers for the test suite.

Provides centralized test infrastructure including:
- OS-specific markers (os_agnostic, posix_only, windows_only, macos_only)
- CLI test fixtures (cli_runner, strip_ansi)
- Configuration isolation fixtures (isolated_traceback_config, preserve_traceback_state)

Note:
    Coverage uses JSON output to avoid SQLite locking issues during parallel execution.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable, Iterator
from dataclasses import fields

import pytest
from click.testing import CliRunner

import lib_cli_exit_tools


# =============================================================================
# Constants
# =============================================================================

ANSI_ESCAPE_PATTERN = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
CONFIG_FIELDS: tuple[str, ...] = tuple(field.name for field in fields(type(lib_cli_exit_tools.config)))


# =============================================================================
# OS-Specific Markers Registration
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers for OS-specific test categorization."""
    config.addinivalue_line("markers", "os_agnostic: test runs on all platforms")
    config.addinivalue_line("markers", "posix_only: test runs only on POSIX systems (Linux, macOS)")
    config.addinivalue_line("markers", "windows_only: test runs only on Windows")
    config.addinivalue_line("markers", "macos_only: test runs only on macOS")
    config.addinivalue_line("markers", "linux_only: test runs only on Linux")


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Skip tests based on OS markers when running on incompatible platforms."""
    if item.get_closest_marker("windows_only") and sys.platform != "win32":
        pytest.skip("test requires Windows")
    if item.get_closest_marker("posix_only") and sys.platform == "win32":
        pytest.skip("test requires POSIX system")
    if item.get_closest_marker("macos_only") and sys.platform != "darwin":
        pytest.skip("test requires macOS")
    if item.get_closest_marker("linux_only") and sys.platform != "linux":
        pytest.skip("test requires Linux")


# =============================================================================
# ANSI Escape Handling
# =============================================================================


def _remove_ansi_codes(text: str) -> str:
    """Strip ANSI escape sequences from text for stable assertions."""
    return ANSI_ESCAPE_PATTERN.sub("", text)


# =============================================================================
# CLI Configuration Snapshot/Restore
# =============================================================================


def _snapshot_cli_config() -> dict[str, object]:
    """Capture all attributes from lib_cli_exit_tools.config."""
    return {name: getattr(lib_cli_exit_tools.config, name) for name in CONFIG_FIELDS}


def _restore_cli_config(snapshot: dict[str, object]) -> None:
    """Restore lib_cli_exit_tools.config from a snapshot."""
    for name, value in snapshot.items():
        setattr(lib_cli_exit_tools.config, name, value)


# =============================================================================
# CLI Test Fixtures
# =============================================================================


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a fresh CliRunner for invoking Click commands.

    Click 8.x provides separate result.stdout and result.stderr attributes.
    Use result.stdout for clean output (e.g., JSON parsing) to avoid
    async log messages from stderr contaminating the output.
    """
    return CliRunner()


@pytest.fixture
def strip_ansi() -> Callable[[str], str]:
    """Provide a helper to strip ANSI escape sequences from strings."""
    return _remove_ansi_codes


# =============================================================================
# Traceback Configuration Fixtures
# =============================================================================


@pytest.fixture
def preserve_traceback_state() -> Iterator[None]:
    """Snapshot and restore the entire lib_cli_exit_tools configuration."""
    snapshot = _snapshot_cli_config()
    try:
        yield
    finally:
        _restore_cli_config(snapshot)


@pytest.fixture
def isolated_traceback_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset traceback flags to a known baseline before each test."""
    lib_cli_exit_tools.reset_config()
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback", False, raising=False)
    monkeypatch.setattr(lib_cli_exit_tools.config, "traceback_force_color", False, raising=False)

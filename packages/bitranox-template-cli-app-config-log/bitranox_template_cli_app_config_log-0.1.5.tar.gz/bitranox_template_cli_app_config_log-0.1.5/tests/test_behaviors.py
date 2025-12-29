"""Behavior layer tests: each function tells a single story.

Tests for the domain behaviors module covering:
- Greeting emission to various streams
- Intentional failure for error handling tests
- No-op placeholder behavior
"""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO

import pytest

from bitranox_template_cli_app_config_log import behaviors
from bitranox_template_cli_app_config_log.behaviors import CANONICAL_GREETING


# =============================================================================
# Greeting Emission Tests
# =============================================================================


@pytest.mark.os_agnostic
class TestGreetingEmission:
    """Tests for the emit_greeting function."""

    def test_greeting_reaches_provided_buffer(self) -> None:
        """When a buffer is provided, the greeting flows into it."""
        buffer = StringIO()

        behaviors.emit_greeting(stream=buffer)

        assert buffer.getvalue() == f"{CANONICAL_GREETING}\n"

    def test_greeting_reaches_stdout_when_no_stream_named(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When no stream is named, stdout hears the song."""
        behaviors.emit_greeting()

        captured = capsys.readouterr()

        assert captured.out == f"{CANONICAL_GREETING}\n"

    def test_stderr_remains_silent(self, capsys: pytest.CaptureFixture[str]) -> None:
        """When greeting emits, stderr stays silent."""
        behaviors.emit_greeting()

        captured = capsys.readouterr()

        assert captured.err == ""

    def test_stream_is_flushed_when_flushable(self) -> None:
        """When the stream supports flush, it is polished clean."""

        @dataclass
        class FlushableStream:
            content: list[str]
            flushed: bool = False

            def write(self, text: str) -> None:
                self.content.append(text)

            def flush(self) -> None:
                self.flushed = True

        stream = FlushableStream(content=[])

        behaviors.emit_greeting(stream=stream)  # type: ignore[arg-type]

        assert stream.flushed is True

    def test_greeting_content_matches_canonical_constant(self) -> None:
        """The greeting text matches the canonical constant."""
        buffer = StringIO()

        behaviors.emit_greeting(stream=buffer)

        assert CANONICAL_GREETING in buffer.getvalue()


# =============================================================================
# Intentional Failure Tests
# =============================================================================


@pytest.mark.os_agnostic
class TestIntentionalFailure:
    """Tests for the raise_intentional_failure function."""

    def test_runtime_error_rises(self) -> None:
        """When failure is invoked, a RuntimeError rises."""
        with pytest.raises(RuntimeError):
            behaviors.raise_intentional_failure()

    def test_error_message_is_clear(self) -> None:
        """The error message speaks its intent clearly."""
        with pytest.raises(RuntimeError, match="I should fail"):
            behaviors.raise_intentional_failure()


# =============================================================================
# No-Op Placeholder Tests
# =============================================================================


@pytest.mark.os_agnostic
class TestNoopPlaceholder:
    """Tests for the noop_main placeholder function."""

    def test_returns_none(self) -> None:
        """When no work is requested, nothing is returned."""
        result = behaviors.noop_main()

        assert result is None

    def test_has_no_side_effects(self, capsys: pytest.CaptureFixture[str]) -> None:
        """The placeholder sits still without output."""
        behaviors.noop_main()

        captured = capsys.readouterr()

        assert captured.out == ""
        assert captured.err == ""

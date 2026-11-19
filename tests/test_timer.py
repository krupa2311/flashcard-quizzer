"""Tests for the timer module."""

import io
import sys

import pytest

from utils.timer import InputTimeout, timed_input, timed_input_supported


class TestTimedInput:
    """Tests for the timed_input function."""

    def test_timed_input_returns_input_when_ready(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """timed_input returns input when stdin is ready."""
        monkeypatch.setattr(
            "select.select",
            lambda *args, **kwargs: ([sys.stdin], [], []),
        )
        fake_stdin = io.StringIO("test answer\n")
        monkeypatch.setattr("sys.stdin", fake_stdin)

        result = timed_input("Your answer: ", 10)

        assert result == "test answer"

    def test_timed_input_strips_trailing_newline(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """timed_input returns input without trailing newline."""
        monkeypatch.setattr(
            "select.select",
            lambda *args, **kwargs: ([sys.stdin], [], []),
        )
        fake_stdin = io.StringIO("answer\n")
        monkeypatch.setattr("sys.stdin", fake_stdin)

        result = timed_input("Your answer: ", 10)

        assert result == "answer"
        assert "\n" not in result

    def test_timed_input_raises_eof_on_empty_read(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """timed_input raises EOFError when stdin is empty."""
        monkeypatch.setattr(
            "select.select",
            lambda *args, **kwargs: ([sys.stdin], [], []),
        )
        fake_stdin = io.StringIO("")
        monkeypatch.setattr("sys.stdin", fake_stdin)

        with pytest.raises(EOFError):
            timed_input("Your answer: ", 10)

    def test_timed_input_raises_timeout_when_not_ready(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """timed_input raises InputTimeout when stdin is not ready."""
        monkeypatch.setattr(
            "select.select",
            lambda *args, **kwargs: ([], [], []),
        )
        fake_stdin = io.StringIO("unused")
        monkeypatch.setattr("sys.stdin", fake_stdin)

        with pytest.raises(InputTimeout):
            timed_input("Your answer: ", 1)

    def test_timed_input_flushes_tcflush_on_timeout_when_tty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """timed_input calls tcflush on timeout when stdin is a tty."""
        monkeypatch.setattr(
            "select.select",
            lambda *args, **kwargs: ([], [], []),
        )
        fake_stdin = io.StringIO("unused")
        monkeypatch.setattr("sys.stdin", fake_stdin)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)

        tcflush_called = []

        def mock_tcflush(fd, how):
            tcflush_called.append((fd, how))

        import termios  # noqa: F401

        monkeypatch.setattr("termios.tcflush", mock_tcflush)

        with pytest.raises(InputTimeout):
            timed_input("Your answer: ", 1)

        assert len(tcflush_called) > 0

    def test_timed_input_no_tcflush_when_not_tty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """timed_input does not call tcflush when stdin is not a tty."""
        monkeypatch.setattr(
            "select.select",
            lambda *args, **kwargs: ([], [], []),
        )
        fake_stdin = io.StringIO("unused")
        monkeypatch.setattr("sys.stdin", fake_stdin)
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        tcflush_called = []

        def mock_tcflush(fd, how):
            tcflush_called.append((fd, how))

        import termios  # noqa: F401

        monkeypatch.setattr("termios.tcflush", mock_tcflush)

        with pytest.raises(InputTimeout):
            timed_input("Your answer: ", 1)

        assert len(tcflush_called) == 0

    def test_timed_input_handles_tcflush_exception(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """timed_input still raises InputTimeout if tcflush fails."""
        monkeypatch.setattr(
            "select.select",
            lambda *args, **kwargs: ([], [], []),
        )
        fake_stdin = io.StringIO("unused")
        monkeypatch.setattr("sys.stdin", fake_stdin)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)

        def mock_tcflush_fail(fd, how):
            raise OSError("tcflush failed")

        import termios  # noqa: F401

        monkeypatch.setattr("termios.tcflush", mock_tcflush_fail)

        with pytest.raises(InputTimeout):
            timed_input("Your answer: ", 1)

    def test_timed_input_handles_termios_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """timed_input handles termios.error gracefully."""
        monkeypatch.setattr(
            "select.select",
            lambda *args, **kwargs: ([], [], []),
        )
        fake_stdin = io.StringIO("unused")
        monkeypatch.setattr("sys.stdin", fake_stdin)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)

        import termios

        def mock_tcflush_fail(fd, how):
            raise termios.error("Device or resource busy")

        monkeypatch.setattr("termios.tcflush", mock_tcflush_fail)

        with pytest.raises(InputTimeout):
            timed_input("Your answer: ", 1)

    def test_timed_input_writes_prompt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """timed_input writes the prompt to stdout."""
        monkeypatch.setattr(
            "select.select",
            lambda *args, **kwargs: ([sys.stdin], [], []),
        )
        fake_stdin = io.StringIO("answer\n")
        monkeypatch.setattr("sys.stdin", fake_stdin)

        fake_stdout = io.StringIO()
        monkeypatch.setattr("sys.stdout", fake_stdout)

        timed_input("Your answer: ", 10)

        assert "Your answer: " in fake_stdout.getvalue()


class TestTimedInputSupported:
    """Tests for the timed_input_supported function."""

    def test_timed_input_supported_returns_false_on_windows(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """timed_input_supported returns False on Windows."""
        monkeypatch.setattr("os.name", "nt")

        result = timed_input_supported()

        assert result is False

    def test_timed_input_supported_returns_true_on_unix(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """timed_input_supported returns True on Unix-like systems."""
        monkeypatch.setattr("os.name", "posix")

        result = timed_input_supported()

        assert result is True


class TestInputTimeoutException:
    """Tests for the InputTimeout exception."""

    def test_input_timeout_is_exception(self) -> None:
        """InputTimeout is an Exception subclass."""
        assert issubclass(InputTimeout, Exception)

    def test_input_timeout_can_be_raised_and_caught(self) -> None:
        """InputTimeout can be raised and caught."""
        with pytest.raises(InputTimeout):
            raise InputTimeout()

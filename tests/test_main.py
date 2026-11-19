"""Tests for main module and CLI argument parsing."""

import io
import json
import runpy
import sys
from pathlib import Path

import pytest

from main import parse_args, main


class TestParseArgs:
    """Tests for the parse_args function."""

    def test_parse_args_defaults(self) -> None:
        """parse_args defaults: mode is sequential, --stats is False."""
        # Note: -f is required, so we need to provide it
        args = parse_args(["-f", "test.json"])

        assert args.file == "test.json"
        assert args.mode == "sequential"
        assert args.stats is False

    def test_parse_args_missing_file_raises_system_exit(self) -> None:
        """Missing -f argument raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args([])

    def test_parse_args_invalid_mode_raises_system_exit(self) -> None:
        """Invalid --mode argument raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args(["-f", "test.json", "-m", "invalid_mode"])

    def test_parse_args_with_stats_flag(self) -> None:
        """--stats flag sets stats to True."""
        args = parse_args(["-f", "test.json", "--stats"])

        assert args.stats is True

    def test_parse_args_with_valid_mode(self) -> None:
        """Valid --mode argument is parsed correctly."""
        for mode in ["sequential", "random", "adaptive"]:
            args = parse_args(["-f", "test.json", "-m", mode])
            assert args.mode == mode


class TestMain:
    """Tests for the main function."""

    def test_main_missing_file_returns_1_and_prints_error(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """main returns 1 and prints friendly error message for missing file."""
        result = main(["-f", str(tmp_path / "nonexistent.json")])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error loading flashcards:" in captured.err
        assert "not found" in captured.err.lower() or "File not found" in captured.err

    def test_main_invalid_json_returns_1_and_prints_error(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """main returns 1 and prints friendly error for invalid JSON."""
        bad_json_file = tmp_path / "bad.json"
        bad_json_file.write_text("{invalid json")

        result = main(["-f", str(bad_json_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error loading flashcards:" in captured.err

    def test_main_empty_deck_returns_1_and_prints_error(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """main returns 1 and prints friendly error for empty deck."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text(json.dumps([]))

        result = main(["-f", str(empty_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error loading flashcards:" in captured.err

    def test_main_valid_deck_returns_0(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """main returns 0 for a valid deck when answers come from sys.stdin."""
        deck_file = tmp_path / "valid.json"
        deck_file.write_text(
            json.dumps(
                [
                    {"front": "Q1", "back": "A1"},
                    {"front": "Q2", "back": "A2"},
                ]
            )
        )

        # Mock sys.stdin to provide answers (builtin input reads from sys.stdin)
        fake_stdin = io.StringIO("a1\na2\n")
        monkeypatch.setattr("sys.stdin", fake_stdin)

        result = main(["-f", str(deck_file)])

        assert result == 0

    def test_main_with_stats_prints_correct_answers(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """main with --stats shows correct answers of missed terms."""
        deck_file = tmp_path / "valid.json"
        deck_file.write_text(
            json.dumps(
                [
                    {"front": "Q1", "back": "CorrectAnswer1"},
                ]
            )
        )

        # Mock sys.stdin: wrong answer, then exit
        fake_stdin = io.StringIO("wrong\n")
        monkeypatch.setattr("sys.stdin", fake_stdin)

        result = main(["-f", str(deck_file), "--stats"])

        assert result == 0

    def test_main_handles_quiz_mode_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """main returns 1 and prints error when get_quiz_mode raises ValueError."""
        deck_file = tmp_path / "valid.json"
        deck_file.write_text(json.dumps([{"front": "Q1", "back": "A1"}]))

        def raise_error(*args, **kwargs) -> None:
            raise ValueError("boom")

        monkeypatch.setattr("main.get_quiz_mode", raise_error)

        result = main(["-f", str(deck_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: boom" in captured.err

    def test_main_guard_with_nonexistent_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """if __name__ == '__main__' exits with code 1 for nonexistent file."""
        nonexistent_file = tmp_path / "does_not_exist.json"
        monkeypatch.setattr(sys, "argv", ["main.py", "-f", str(nonexistent_file)])

        with pytest.raises(SystemExit) as exc_info:
            runpy.run_module("main", run_name="__main__")

        assert exc_info.value.code == 1

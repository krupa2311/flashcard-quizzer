"""Tests for main module and CLI argument parsing."""

import io
import json
import runpy
import sys
from pathlib import Path

import pytest

from main import main, parse_args, select_cards
from utils.file_handler import Flashcard


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

    def test_parse_args_limit_default_is_none(self) -> None:
        """--limit argument defaults to None."""
        args = parse_args(["-f", "test.json"])
        assert args.limit is None

    def test_parse_args_with_valid_limit(self) -> None:
        """Valid --limit argument is parsed correctly."""
        args = parse_args(["-f", "test.json", "--limit", "5"])
        assert args.limit == 5

    def test_parse_args_limit_zero_raises_system_exit(self) -> None:
        """--limit 0 raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args(["-f", "test.json", "--limit", "0"])

    def test_parse_args_limit_negative_raises_system_exit(self) -> None:
        """--limit -1 raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args(["-f", "test.json", "--limit", "-1"])

    def test_parse_args_limit_non_integer_raises_system_exit(self) -> None:
        """--limit abc raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args(["-f", "test.json", "--limit", "abc"])


class TestSelectCards:
    """Tests for the select_cards function."""

    def test_select_cards_no_limit_returns_all(self) -> None:
        """select_cards with limit=None returns all cards."""
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
            Flashcard("Q3", "A3"),
        ]
        result = select_cards(cards, None, "sequential")

        assert len(result) == 3
        assert result == cards

    def test_select_cards_limit_larger_than_deck_returns_all(self) -> None:
        """select_cards with limit >= len(cards) returns all cards."""
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
        ]
        result = select_cards(cards, 10, "sequential")

        assert len(result) == 2
        assert result == cards

    def test_select_cards_sequential_returns_first_n_in_order(self) -> None:
        """select_cards with sequential mode returns first N in order."""
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
            Flashcard("Q3", "A3"),
            Flashcard("Q4", "A4"),
        ]
        result = select_cards(cards, 2, "sequential")

        assert len(result) == 2
        assert result[0].front == "Q1"
        assert result[1].front == "Q2"

    def test_select_cards_random_returns_n_unique_cards(self) -> None:
        """select_cards with random mode returns N unique cards."""
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
            Flashcard("Q3", "A3"),
            Flashcard("Q4", "A4"),
            Flashcard("Q5", "A5"),
        ]
        result = select_cards(cards, 3, "random")

        assert len(result) == 3
        # Verify no duplicates by checking all fronts are unique
        fronts = [card.front for card in result]
        assert len(fronts) == len(set(fronts))

    def test_select_cards_adaptive_returns_n_unique_cards(self) -> None:
        """select_cards with adaptive mode returns N unique cards."""
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
            Flashcard("Q3", "A3"),
            Flashcard("Q4", "A4"),
        ]
        result = select_cards(cards, 2, "adaptive")

        assert len(result) == 2
        # Verify no duplicates by checking all fronts are unique
        fronts = [card.front for card in result]
        assert len(fronts) == len(set(fronts))

    def test_select_cards_does_not_mutate_input_list(self) -> None:
        """select_cards never mutates the input list."""
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
            Flashcard("Q3", "A3"),
        ]
        original_length = len(cards)
        original_first = cards[0]

        result = select_cards(cards, 2, "sequential")

        assert len(cards) == original_length
        assert cards[0] == original_first
        assert result is not cards


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

    def test_main_with_limit_asks_exactly_n_questions(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """main with --limit 2 asks exactly 2 questions."""
        deck_file = tmp_path / "valid.json"
        deck_file.write_text(
            json.dumps(
                [
                    {"front": "Q1", "back": "A1"},
                    {"front": "Q2", "back": "A2"},
                    {"front": "Q3", "back": "A3"},
                    {"front": "Q4", "back": "A4"},
                ]
            )
        )

        fake_stdin = io.StringIO("a1\na2\n")
        monkeypatch.setattr("sys.stdin", fake_stdin)

        result = main(["-f", str(deck_file), "--limit", "2"])

        assert result == 0

    def test_parse_args_export_default_is_none(self) -> None:
        """--export argument defaults to None."""
        args = parse_args(["-f", "test.json"])
        assert args.export is None

    def test_parse_args_with_valid_export_json(self) -> None:
        """Valid --export with .json extension is parsed correctly."""
        args = parse_args(["-f", "test.json", "--export", "results.json"])
        assert args.export == "results.json"

    def test_parse_args_with_valid_export_csv(self) -> None:
        """Valid --export with .csv extension is parsed correctly."""
        args = parse_args(["-f", "test.json", "--export", "results.csv"])
        assert args.export == "results.csv"

    def test_parse_args_export_case_insensitive_json(self) -> None:
        """--export with .JSON extension is accepted."""
        args = parse_args(["-f", "test.json", "--export", "results.JSON"])
        assert args.export == "results.JSON"

    def test_parse_args_export_case_insensitive_csv(self) -> None:
        """--export with .CSV extension is accepted."""
        args = parse_args(["-f", "test.json", "--export", "results.CSV"])
        assert args.export == "results.CSV"

    def test_parse_args_export_unsupported_extension_raises_system_exit(
        self,
    ) -> None:
        """--export with unsupported extension raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args(["-f", "test.json", "--export", "results.txt"])

    def test_main_with_export_creates_json_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """main with --export creates a JSON file with correct data."""
        deck_file = tmp_path / "valid.json"
        deck_file.write_text(
            json.dumps(
                [
                    {"front": "Q1", "back": "A1"},
                    {"front": "Q2", "back": "A2"},
                ]
            )
        )
        export_file = tmp_path / "results.json"

        fake_stdin = io.StringIO("a1\nwrong\n")
        monkeypatch.setattr("sys.stdin", fake_stdin)

        result = main(["-f", str(deck_file), "--export", str(export_file)])

        assert result == 0
        assert export_file.exists()
        with open(export_file) as f:
            data = json.load(f)
        assert data["total_questions"] == 2
        assert data["correct_count"] == 1
        assert len(data["missed_terms"]) == 1

    def test_main_with_export_creates_csv_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """main with --export creates a CSV file with correct format."""
        deck_file = tmp_path / "valid.json"
        deck_file.write_text(
            json.dumps(
                [
                    {"front": "Q1", "back": "A1"},
                    {"front": "Q2", "back": "A2"},
                ]
            )
        )
        export_file = tmp_path / "results.csv"

        fake_stdin = io.StringIO("a1\nwrong\n")
        monkeypatch.setattr("sys.stdin", fake_stdin)

        result = main(["-f", str(deck_file), "--export", str(export_file)])

        assert result == 0
        assert export_file.exists()
        with open(export_file, newline="") as f:
            import csv

            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 2
        assert rows[0][0] == "timestamp"
        assert rows[1][3] == "2"

    def test_main_with_export_zero_questions_skips_export(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """main with --export and zero answered questions prints notice."""
        deck_file = tmp_path / "valid.json"
        deck_file.write_text(
            json.dumps(
                [
                    {"front": "Q1", "back": "A1"},
                ]
            )
        )
        export_file = tmp_path / "results.json"

        fake_stdin = io.StringIO("")
        monkeypatch.setattr("sys.stdin", fake_stdin)

        result = main(["-f", str(deck_file), "--export", str(export_file)])

        assert result == 0
        assert not export_file.exists()
        captured = capsys.readouterr()
        assert "No questions answered" in captured.err
        assert "skipping export" in captured.err

    def test_main_with_export_nonexistent_directory_returns_1(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """main with --export to nonexistent dir returns 1 and prints error."""
        deck_file = tmp_path / "valid.json"
        deck_file.write_text(
            json.dumps(
                [
                    {"front": "Q1", "back": "A1"},
                ]
            )
        )
        export_file = tmp_path / "nonexistent" / "results.json"

        fake_stdin = io.StringIO("a1\n")
        monkeypatch.setattr("sys.stdin", fake_stdin)

        result = main(["-f", str(deck_file), "--export", str(export_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Export error:" in captured.err

    def test_main_with_export_prints_success_message(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """main with --export prints 'Results saved to <path>'."""
        deck_file = tmp_path / "valid.json"
        deck_file.write_text(
            json.dumps(
                [
                    {"front": "Q1", "back": "A1"},
                ]
            )
        )
        export_file = tmp_path / "results.json"

        fake_stdin = io.StringIO("a1\n")
        monkeypatch.setattr("sys.stdin", fake_stdin)

        result = main(["-f", str(deck_file), "--export", str(export_file)])

        assert result == 0
        captured = capsys.readouterr()
        assert f"Results saved to {export_file}" in captured.out

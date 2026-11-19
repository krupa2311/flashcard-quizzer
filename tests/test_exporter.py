"""Tests for the exporter module."""

import csv
import json
from datetime import datetime
from pathlib import Path

import pytest

from quiz_engine import QuizSession, SequentialMode
from utils.exporter import ExportError, export_session
from utils.file_handler import Flashcard


class TestExportError:
    """Tests for ExportError exception."""

    def test_export_error_is_exception(self) -> None:
        """ExportError is a subclass of Exception."""
        assert issubclass(ExportError, Exception)


class TestExportSession:
    """Tests for the export_session function."""

    def test_export_json_creates_file_with_correct_structure(
        self, tmp_path: Path
    ) -> None:
        """JSON export creates a file with correct structure and data."""
        output_file = tmp_path / "results.json"
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
        ]
        mode = SequentialMode(cards)
        session = QuizSession(mode)
        session.check_answer(cards[0], "A1")
        session.check_answer(cards[1], "wrong")

        fixed_timestamp = datetime(2026, 11, 19, 14, 30, 45)
        export_session(
            session,
            str(output_file),
            "sequential",
            "test.json",
            timestamp=fixed_timestamp,
        )

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)

        assert data["timestamp"] == "2026-11-19T14:30:45"
        assert data["deck_file"] == "test.json"
        assert data["mode"] == "sequential"
        assert data["total_questions"] == 2
        assert data["correct_count"] == 1
        assert data["accuracy"] == 50.0
        assert len(data["missed_terms"]) == 1
        assert data["missed_terms"][0]["front"] == "Q2"
        assert data["missed_terms"][0]["back"] == "A2"

    def test_export_json_has_right_fields_and_values(self, tmp_path: Path) -> None:
        """JSON export has all required fields with correct values."""
        output_file = tmp_path / "results.json"
        cards = [
            Flashcard("French", "Bonjour"),
            Flashcard("Spanish", "Hola"),
            Flashcard("German", "Hallo"),
        ]
        mode = SequentialMode(cards)
        session = QuizSession(mode)
        session.check_answer(cards[0], "bonjour")
        session.check_answer(cards[1], "wrong")
        session.check_answer(cards[2], "hallo")

        fixed_timestamp = datetime(2026, 1, 1, 0, 0, 0)
        export_session(
            session,
            str(output_file),
            "random",
            "languages.json",
            timestamp=fixed_timestamp,
        )

        with open(output_file) as f:
            data = json.load(f)

        assert data["timestamp"] == "2026-01-01T00:00:00"
        assert data["deck_file"] == "languages.json"
        assert data["mode"] == "random"
        assert data["total_questions"] == 3
        assert data["correct_count"] == 2
        assert data["accuracy"] == 66.7
        assert len(data["missed_terms"]) == 1

    def test_export_csv_creates_file_with_header_and_row(self, tmp_path: Path) -> None:
        """CSV export creates a file with header row and one data row."""
        output_file = tmp_path / "results.csv"
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
        ]
        mode = SequentialMode(cards)
        session = QuizSession(mode)
        session.check_answer(cards[0], "A1")
        session.check_answer(cards[1], "wrong")

        fixed_timestamp = datetime(2026, 11, 19, 14, 30, 45)
        export_session(
            session,
            str(output_file),
            "sequential",
            "test.json",
            timestamp=fixed_timestamp,
        )

        assert output_file.exists()
        with open(output_file, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) == 2
        header = rows[0]
        assert header == [
            "timestamp",
            "deck_file",
            "mode",
            "total_questions",
            "correct_count",
            "accuracy",
            "missed_terms",
        ]

        data_row = rows[1]
        assert data_row[0] == "2026-11-19T14:30:45"
        assert data_row[1] == "test.json"
        assert data_row[2] == "sequential"
        assert data_row[3] == "2"
        assert data_row[4] == "1"
        assert data_row[5] == "50.0"
        assert "Q2: A2" in data_row[6]

    def test_export_csv_joins_multiple_missed_terms_with_pipe(
        self, tmp_path: Path
    ) -> None:
        """CSV export joins multiple missed terms by ' | '."""
        output_file = tmp_path / "results.csv"
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
            Flashcard("Q3", "A3"),
        ]
        mode = SequentialMode(cards)
        session = QuizSession(mode)
        session.check_answer(cards[0], "wrong1")
        session.check_answer(cards[1], "wrong2")
        session.check_answer(cards[2], "A3")

        export_session(
            session,
            str(output_file),
            "sequential",
            "test.json",
        )

        with open(output_file, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        data_row = rows[1]
        missed_terms = data_row[6]
        assert "Q1: A1" in missed_terms
        assert "Q2: A2" in missed_terms
        assert " | " in missed_terms

    def test_export_extension_matching_is_case_insensitive_json(
        self, tmp_path: Path
    ) -> None:
        """Extension matching is case-insensitive for .JSON."""
        output_file = tmp_path / "results.JSON"
        cards = [Flashcard("Q", "A")]
        mode = SequentialMode(cards)
        session = QuizSession(mode)

        export_session(
            session,
            str(output_file),
            "sequential",
            "test.json",
        )

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert "timestamp" in data

    def test_export_extension_matching_is_case_insensitive_csv(
        self, tmp_path: Path
    ) -> None:
        """Extension matching is case-insensitive for .CSV."""
        output_file = tmp_path / "results.CSV"
        cards = [Flashcard("Q", "A")]
        mode = SequentialMode(cards)
        session = QuizSession(mode)

        export_session(
            session,
            str(output_file),
            "sequential",
            "test.json",
        )

        assert output_file.exists()
        with open(output_file, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 2

    def test_export_unsupported_extension_raises_export_error(
        self, tmp_path: Path
    ) -> None:
        """Unsupported file extension raises ExportError."""
        output_file = tmp_path / "results.txt"
        cards = [Flashcard("Q", "A")]
        mode = SequentialMode(cards)
        session = QuizSession(mode)

        with pytest.raises(ExportError) as exc_info:
            export_session(
                session,
                str(output_file),
                "sequential",
                "test.json",
            )

        assert "Unsupported file extension" in str(exc_info.value)

    def test_export_nonexistent_directory_raises_export_error(
        self, tmp_path: Path
    ) -> None:
        """Writing to a nonexistent directory raises ExportError."""
        output_file = tmp_path / "nonexistent" / "results.json"
        cards = [Flashcard("Q", "A")]
        mode = SequentialMode(cards)
        session = QuizSession(mode)

        with pytest.raises(ExportError) as exc_info:
            export_session(
                session,
                str(output_file),
                "sequential",
                "test.json",
            )

        assert "Directory does not exist" in str(exc_info.value)

    def test_export_error_has_proper_error_chaining(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ExportError wraps OSError with 'raise ... from e'."""
        output_file = tmp_path / "results.json"
        cards = [Flashcard("Q", "A")]
        mode = SequentialMode(cards)
        session = QuizSession(mode)

        def mock_open(*args, **kwargs):
            raise OSError("Mock write error")

        monkeypatch.setattr("builtins.open", mock_open)

        with pytest.raises(ExportError) as exc_info:
            export_session(
                session,
                str(output_file),
                "sequential",
                "test.json",
            )

        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, OSError)

    def test_export_session_with_no_missed_terms(self, tmp_path: Path) -> None:
        """Export works when there are no missed terms."""
        output_file = tmp_path / "results.json"
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
        ]
        mode = SequentialMode(cards)
        session = QuizSession(mode)
        session.check_answer(cards[0], "A1")
        session.check_answer(cards[1], "A2")

        export_session(
            session,
            str(output_file),
            "sequential",
            "test.json",
        )

        with open(output_file) as f:
            data = json.load(f)

        assert data["missed_terms"] == []
        assert data["accuracy"] == 100.0

    def test_export_timestamp_defaults_to_now(self, tmp_path: Path) -> None:
        """timestamp parameter defaults to datetime.now()."""
        output_file = tmp_path / "results.json"
        cards = [Flashcard("Q", "A")]
        mode = SequentialMode(cards)
        session = QuizSession(mode)

        before = datetime.now().isoformat(timespec="seconds")
        export_session(
            session,
            str(output_file),
            "sequential",
            "test.json",
        )
        after = datetime.now().isoformat(timespec="seconds")

        with open(output_file) as f:
            data = json.load(f)

        timestamp = data["timestamp"]
        assert before <= timestamp <= after

    def test_export_accuracy_rounded_to_one_decimal(self, tmp_path: Path) -> None:
        """Accuracy is rounded to 1 decimal place."""
        output_file = tmp_path / "results.json"
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
            Flashcard("Q3", "A3"),
        ]
        mode = SequentialMode(cards)
        session = QuizSession(mode)
        session.check_answer(cards[0], "A1")
        session.check_answer(cards[1], "wrong")
        session.check_answer(cards[2], "A3")

        export_session(
            session,
            str(output_file),
            "sequential",
            "test.json",
        )

        with open(output_file) as f:
            data = json.load(f)

        assert data["accuracy"] == 66.7

"""Export quiz session results to CSV or JSON formats.

This module handles saving quiz session data to files in multiple formats,
with proper error handling and data formatting for both JSON and CSV output.
"""

import csv
import json
from datetime import datetime
from pathlib import Path

from quiz_engine import QuizSession


class ExportError(Exception):
    """Custom exception for export operation errors."""

    pass


def export_session(
    session: QuizSession,
    path: str,
    mode: str,
    deck_file: str,
    timestamp: datetime | None = None,
) -> None:
    """Export a quiz session to a file in JSON or CSV format.

    The format is determined by the file extension (.csv or .json,
    case-insensitive). The timestamp is formatted using isoformat with
    timespec="seconds" and defaults to the current time.

    For JSON: writes a single object with fields: timestamp, deck_file,
    mode, total_questions, correct_count, accuracy (rounded to 1 decimal),
    and missed_terms (list of {"front", "back"} objects).

    For CSV: writes a header row and one data row. Missed terms are joined
    by " | " in a single column.

    Args:
        session: The QuizSession to export.
        path: The file path where the results will be saved.
        mode: The quiz mode name (e.g., "sequential", "random", "adaptive").
        deck_file: The original deck file path.
        timestamp: Optional datetime to use; defaults to datetime.now().

    Raises:
        ExportError: If the file extension is unsupported, if the target
            directory does not exist, or if an OSError occurs during write.
    """
    if timestamp is None:
        timestamp = datetime.now()

    path_obj = Path(path)
    extension = path_obj.suffix.lower()

    if extension not in {".csv", ".json"}:
        raise ExportError(
            f"Unsupported file extension: {extension}. " f"Use .csv or .json"
        )

    if not path_obj.parent.exists():
        raise ExportError(f"Directory does not exist: {path_obj.parent}")

    timestamp_str = timestamp.isoformat(timespec="seconds")
    accuracy = round(session.accuracy, 1)

    front_to_back = {card.front: card.back for card in session.mode.cards}
    missed_terms = [
        {"front": term, "back": front_to_back.get(term, "")}
        for term in session.missed_terms
    ]

    try:
        if extension == ".json":
            _export_json(
                path_obj,
                timestamp_str,
                deck_file,
                mode,
                session.total_questions,
                session.correct_count,
                accuracy,
                missed_terms,
            )
        else:
            _export_csv(
                path_obj,
                timestamp_str,
                deck_file,
                mode,
                session.total_questions,
                session.correct_count,
                accuracy,
                missed_terms,
            )
    except OSError as e:
        raise ExportError(f"Failed to write to {path}: {e}") from e


def _export_json(
    path: Path,
    timestamp: str,
    deck_file: str,
    mode: str,
    total_questions: int,
    correct_count: int,
    accuracy: float,
    missed_terms: list[dict[str, str]],
) -> None:
    """Write session data to a JSON file.

    Args:
        path: The file path to write to.
        timestamp: ISO format timestamp string.
        deck_file: The deck file path.
        mode: The quiz mode name.
        total_questions: Total questions asked.
        correct_count: Number of correct answers.
        accuracy: Accuracy percentage (rounded to 1 decimal).
        missed_terms: List of missed term objects with front and back.
    """
    data = {
        "timestamp": timestamp,
        "deck_file": deck_file,
        "mode": mode,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "accuracy": accuracy,
        "missed_terms": missed_terms,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _export_csv(
    path: Path,
    timestamp: str,
    deck_file: str,
    mode: str,
    total_questions: int,
    correct_count: int,
    accuracy: float,
    missed_terms: list[dict[str, str]],
) -> None:
    """Write session data to a CSV file.

    Args:
        path: The file path to write to.
        timestamp: ISO format timestamp string.
        deck_file: The deck file path.
        mode: The quiz mode name.
        total_questions: Total questions asked.
        correct_count: Number of correct answers.
        accuracy: Accuracy percentage (rounded to 1 decimal).
        missed_terms: List of missed term objects with front and back.
    """
    missed_str = " | ".join(
        [f"{term['front']}: {term['back']}" for term in missed_terms]
    )

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "timestamp",
                "deck_file",
                "mode",
                "total_questions",
                "correct_count",
                "accuracy",
                "missed_terms",
            ]
        )
        writer.writerow(
            [
                timestamp,
                deck_file,
                mode,
                total_questions,
                correct_count,
                accuracy,
                missed_str,
            ]
        )

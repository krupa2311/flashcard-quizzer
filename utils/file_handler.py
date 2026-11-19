"""Data loading and flashcard management for the Flashcard Quizzer.

This module handles loading flashcards from JSON files and validates the data
to ensure it meets the application's requirements.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class FlashcardLoadError(Exception):
    """Custom exception for flashcard loading errors."""

    pass


@dataclass
class Flashcard:
    """A single flashcard with a front (question) and back (answer).

    Attributes:
        front: The question or prompt side of the card (non-empty string).
        back: The answer or response side of the card (non-empty string).
    """

    front: str
    back: str


def load_flashcards(path: str) -> list[Flashcard]:
    """Load flashcards from a JSON file.

    Supports two JSON formats:
    1. Top-level list: [{"front": "...", "back": "..."}, ...]
    2. Wrapped format: {"cards": [{"front": "...", "back": "..."}, ...]}

    Args:
        path: Path to the JSON file containing flashcards.

    Returns:
        A list of Flashcard objects loaded from the file.

    Raises:
        FlashcardLoadError: If the file cannot be found, contains invalid JSON,
            has an unexpected structure, or any card is missing required fields.
    """
    file_path = Path(path)

    # Check if file exists
    if not file_path.exists():
        raise FlashcardLoadError(f"File not found: {path}")

    # Try to read and parse JSON
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise FlashcardLoadError(
            f"Invalid JSON syntax in {path}: {e.msg} at line {e.lineno}, "
            f"column {e.colno}"
        )
    except (IOError, OSError) as e:
        raise FlashcardLoadError(f"Error reading file {path}: {e}")

    # Determine which format and extract cards list
    cards_data: list[Any]
    if isinstance(data, list):
        cards_data = data
    elif isinstance(data, dict) and "cards" in data:
        cards_data = data["cards"]
    else:
        raise FlashcardLoadError(
            f"Invalid structure in {path}: expected either a list of cards or "
            '{"cards": [...]} format'
        )

    # Validate and create Flashcard objects
    flashcards: list[Flashcard] = []
    for index, card in enumerate(cards_data, start=1):
        if not isinstance(card, dict):
            raise FlashcardLoadError(
                f"Card at position {index} is not a dictionary: {type(card).__name__}"
            )

        if "front" not in card:
            raise FlashcardLoadError(
                f"Card at position {index} is missing required field: 'front'"
            )

        if "back" not in card:
            raise FlashcardLoadError(
                f"Card at position {index} is missing required field: 'back'"
            )

        front = card["front"]
        back = card["back"]

        # Validate that front and back are non-empty strings
        if not isinstance(front, str) or not front.strip():
            raise FlashcardLoadError(
                f"Card at position {index}: 'front' must be a non-empty string, "
                f"got {type(front).__name__}"
            )

        if not isinstance(back, str) or not back.strip():
            raise FlashcardLoadError(
                f"Card at position {index}: 'back' must be a non-empty string, "
                f"got {type(back).__name__}"
            )

        flashcards.append(Flashcard(front=front.strip(), back=back.strip()))

    return flashcards

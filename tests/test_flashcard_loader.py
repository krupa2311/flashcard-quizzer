"""Tests for flashcard data loading and validation."""

import json
from pathlib import Path

import pytest

from utils.file_handler import Flashcard, FlashcardLoadError, load_flashcards


class TestLoadValidFlashcardsArray:
    """Tests for loading valid flashcard arrays."""

    def test_load_valid_flashcards_array(self, tmp_path: Path) -> None:
        """Load a valid array of flashcards from JSON."""
        deck_file = tmp_path / "test_deck.json"
        cards = [
            {"front": "Q1", "back": "A1"},
            {"front": "Q2", "back": "A2"},
        ]
        deck_file.write_text(json.dumps(cards))

        result = load_flashcards(str(deck_file))
        assert len(result) == 2
        assert result[0].front == "Q1"
        assert result[0].back == "A1"
        assert result[1].front == "Q2"
        assert result[1].back == "A2"

    def test_load_wrapped_format(self, tmp_path: Path) -> None:
        """Load flashcards from wrapped {"cards": [...]} format."""
        deck_file = tmp_path / "wrapped_deck.json"
        cards = {
            "cards": [
                {"front": "Q1", "back": "A1"},
                {"front": "Q2", "back": "A2"},
            ]
        }
        deck_file.write_text(json.dumps(cards))

        result = load_flashcards(str(deck_file))
        assert len(result) == 2
        assert result[0].front == "Q1"
        assert result[1].front == "Q2"


class TestInvalidJSON:
    """Tests for invalid JSON handling."""

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """Reject malformed JSON with helpful error message."""
        deck_file = tmp_path / "invalid.json"
        deck_file.write_text("{invalid json]")

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "Invalid JSON syntax" in str(exc_info.value)


class TestMissingFields:
    """Tests for missing required fields."""

    def test_load_missing_required_field(self, tmp_path: Path) -> None:
        """Reject cards missing required fields."""
        deck_file = tmp_path / "missing_field.json"
        cards = [
            {"front": "Q1"},  # Missing 'back'
        ]
        deck_file.write_text(json.dumps(cards))

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "missing required field: 'back'" in str(exc_info.value)

    def test_missing_front_field(self, tmp_path: Path) -> None:
        """Reject cards missing 'front' field."""
        deck_file = tmp_path / "no_front.json"
        cards = [
            {"back": "A1"},  # Missing 'front'
        ]
        deck_file.write_text(json.dumps(cards))

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "missing required field: 'front'" in str(exc_info.value)


class TestFileHandling:
    """Tests for file reading and existence."""

    def test_file_not_found(self) -> None:
        """Raise error when file does not exist."""
        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards("/nonexistent/path/deck.json")
        assert "File not found" in str(exc_info.value)

    def test_non_utf8_file(self, tmp_path: Path) -> None:
        """Reject files with non-UTF-8 encoding."""
        deck_file = tmp_path / "non_utf8.json"
        deck_file.write_bytes(b"\x80\x81\x82")

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "not valid UTF-8" in str(exc_info.value)

    def test_load_directory_raises_error(self, tmp_path: Path) -> None:
        """Raise error when path is a directory instead of a file."""
        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(tmp_path))
        assert "Error reading file" in str(exc_info.value)


class TestStructureValidation:
    """Tests for JSON structure validation."""

    def test_cards_not_list(self, tmp_path: Path) -> None:
        """Reject when 'cards' is not a list."""
        deck_file = tmp_path / "cards_not_list.json"
        data = {"cards": "not a list"}
        deck_file.write_text(json.dumps(data))

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "'cards' must be a list" in str(exc_info.value)

    def test_top_level_neither_list_nor_dict(self, tmp_path: Path) -> None:
        """Reject top-level values that are neither list nor dict."""
        deck_file = tmp_path / "invalid_top_level.json"
        deck_file.write_text(json.dumps("just a string"))

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "Invalid structure" in str(exc_info.value)

    def test_card_not_dictionary(self, tmp_path: Path) -> None:
        """Reject cards that are not dictionaries."""
        deck_file = tmp_path / "card_not_dict.json"
        cards = ["string", "not", "dicts"]
        deck_file.write_text(json.dumps(cards))

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "not a dictionary" in str(exc_info.value)


class TestFieldValidation:
    """Tests for field value validation."""

    def test_empty_front(self, tmp_path: Path) -> None:
        """Reject cards with empty front field."""
        deck_file = tmp_path / "empty_front.json"
        cards = [
            {"front": "", "back": "A1"},
        ]
        deck_file.write_text(json.dumps(cards))

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "non-empty string" in str(exc_info.value)

    def test_whitespace_only_front(self, tmp_path: Path) -> None:
        """Reject cards with whitespace-only front field."""
        deck_file = tmp_path / "ws_front.json"
        cards = [
            {"front": "   ", "back": "A1"},
        ]
        deck_file.write_text(json.dumps(cards))

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "non-empty string" in str(exc_info.value)

    def test_empty_back(self, tmp_path: Path) -> None:
        """Reject cards with empty back field."""
        deck_file = tmp_path / "empty_back.json"
        cards = [
            {"front": "Q1", "back": ""},
        ]
        deck_file.write_text(json.dumps(cards))

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "non-empty string" in str(exc_info.value)

    def test_whitespace_only_back(self, tmp_path: Path) -> None:
        """Reject cards with whitespace-only back field."""
        deck_file = tmp_path / "ws_back.json"
        cards = [
            {"front": "Q1", "back": "\t\n  "},
        ]
        deck_file.write_text(json.dumps(cards))

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "non-empty string" in str(exc_info.value)

    def test_non_string_front(self, tmp_path: Path) -> None:
        """Reject cards with non-string front field."""
        deck_file = tmp_path / "int_front.json"
        cards = [
            {"front": 123, "back": "A1"},
        ]
        deck_file.write_text(json.dumps(cards))

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "non-empty string" in str(exc_info.value)

    def test_non_string_back(self, tmp_path: Path) -> None:
        """Reject cards with non-string back field."""
        deck_file = tmp_path / "list_back.json"
        cards = [
            {"front": "Q1", "back": ["A1", "A2"]},
        ]
        deck_file.write_text(json.dumps(cards))

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "non-empty string" in str(exc_info.value)


class TestEmptyDeck:
    """Tests for empty deck handling."""

    def test_empty_array_deck(self, tmp_path: Path) -> None:
        """Reject empty array deck."""
        deck_file = tmp_path / "empty_array.json"
        deck_file.write_text(json.dumps([]))

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "contains no flashcards" in str(exc_info.value)

    def test_empty_wrapped_deck(self, tmp_path: Path) -> None:
        """Reject empty wrapped deck."""
        deck_file = tmp_path / "empty_wrapped.json"
        data: dict[str, list[dict[str, str]]] = {"cards": []}
        deck_file.write_text(json.dumps(data))

        with pytest.raises(FlashcardLoadError) as exc_info:
            load_flashcards(str(deck_file))
        assert "contains no flashcards" in str(exc_info.value)


class TestWhitespaceStripping:
    """Tests for whitespace handling."""

    def test_whitespace_stripping(self, tmp_path: Path) -> None:
        """Whitespace is stripped from front and back."""
        deck_file = tmp_path / "ws_strip.json"
        cards = [
            {"front": "  Q1  ", "back": "\tA1\n"},
        ]
        deck_file.write_text(json.dumps(cards))

        result = load_flashcards(str(deck_file))
        assert result[0].front == "Q1"
        assert result[0].back == "A1"


class TestRealDataFiles:
    """Tests loading real deck files."""

    def test_load_glossary(self) -> None:
        """Load the glossary.json deck and verify it's non-empty."""
        result = load_flashcards("data/glossary.json")
        assert len(result) > 0
        assert all(isinstance(card, Flashcard) for card in result)
        assert all(card.front and card.back for card in result)

    def test_load_python_basics(self) -> None:
        """Load the python_basics.json deck and verify it's non-empty."""
        result = load_flashcards("data/python_basics.json")
        assert len(result) > 0
        assert all(isinstance(card, Flashcard) for card in result)
        assert all(card.front and card.back for card in result)

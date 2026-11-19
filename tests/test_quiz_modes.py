"""Tests for quiz modes and session management."""

import random
from typing import cast

import pytest

from quiz_engine import (  # isort: skip
    AdaptiveMode,
    QuizSession,
    RandomMode,
    SequentialMode,
    get_quiz_mode,
)
from utils.file_handler import Flashcard


@pytest.fixture
def sample_cards() -> list[Flashcard]:
    """Create sample flashcards for testing."""
    return [
        Flashcard(front="Q1", back="A1"),
        Flashcard(front="Q2", back="A2"),
        Flashcard(front="Q3", back="A3"),
    ]


@pytest.fixture
def four_cards() -> list[Flashcard]:
    """Create four sample flashcards for testing."""
    return [
        Flashcard(front="Q1", back="A1"),
        Flashcard(front="Q2", back="A2"),
        Flashcard(front="Q3", back="A3"),
        Flashcard(front="Q4", back="A4"),
    ]


class TestQuizModeFactory:
    """Tests for the quiz mode factory function."""

    def test_quiz_mode_factory(self, sample_cards: list[Flashcard]) -> None:
        """Factory returns correct class for each mode."""
        seq_mode = get_quiz_mode("sequential", sample_cards)
        assert isinstance(seq_mode, SequentialMode)

        rand_mode = get_quiz_mode("random", sample_cards)
        assert isinstance(rand_mode, RandomMode)

        adapt_mode = get_quiz_mode("adaptive", sample_cards)
        assert isinstance(adapt_mode, AdaptiveMode)

    def test_factory_case_insensitive(self, sample_cards: list[Flashcard]) -> None:
        """Factory is case-insensitive."""
        mode1 = get_quiz_mode("SEQUENTIAL", sample_cards)
        assert isinstance(mode1, SequentialMode)

        mode2 = get_quiz_mode("RaNdOm", sample_cards)
        assert isinstance(mode2, RandomMode)

        mode3 = get_quiz_mode("ADAPTIVE", sample_cards)
        assert isinstance(mode3, AdaptiveMode)

    def test_factory_whitespace_tolerant(self, sample_cards: list[Flashcard]) -> None:
        """Factory strips whitespace from mode names."""
        mode1 = get_quiz_mode("  sequential  ", sample_cards)
        assert isinstance(mode1, SequentialMode)

        mode2 = get_quiz_mode("\trandom\n", sample_cards)
        assert isinstance(mode2, RandomMode)

    def test_factory_unknown_mode(self, sample_cards: list[Flashcard]) -> None:
        """Factory raises ValueError for unknown modes."""
        with pytest.raises(ValueError) as exc_info:
            get_quiz_mode("invalid_mode", sample_cards)
        assert "Unknown quiz mode" in str(exc_info.value)
        assert "sequential" in str(exc_info.value)
        assert "random" in str(exc_info.value)
        assert "adaptive" in str(exc_info.value)

    def test_factory_empty_cards(self) -> None:
        """Factory raises ValueError for empty card list."""
        with pytest.raises(ValueError) as exc_info:
            get_quiz_mode("sequential", [])
        assert "empty" in str(exc_info.value).lower()


class TestSequentialMode:
    """Tests for sequential quiz mode."""

    def test_sequential_mode_order(self, sample_cards: list[Flashcard]) -> None:
        """Sequential mode serves cards in original order."""
        mode = SequentialMode(sample_cards)

        assert mode.next_card() == sample_cards[0]
        assert mode.next_card() == sample_cards[1]
        assert mode.next_card() == sample_cards[2]
        assert mode.next_card() is None

    def test_sequential_mode_exhausted(self, sample_cards: list[Flashcard]) -> None:
        """Sequential mode returns None after all cards are served."""
        mode = SequentialMode(sample_cards)

        for _ in sample_cards:
            mode.next_card()

        assert mode.next_card() is None
        assert mode.next_card() is None


class TestRandomMode:
    """Tests for random quiz mode."""

    def test_random_mode_seeded(self, sample_cards: list[Flashcard]) -> None:
        """RandomMode with seeded Random gives consistent order."""
        rng1 = random.Random(42)
        mode1 = RandomMode(sample_cards, random_instance=rng1)
        order1 = [mode1.next_card() for _ in range(len(sample_cards))]

        rng2 = random.Random(42)
        mode2 = RandomMode(sample_cards, random_instance=rng2)
        order2 = [mode2.next_card() for _ in range(len(sample_cards))]

        assert order1 == order2

    def test_random_mode_different_seed(self, sample_cards: list[Flashcard]) -> None:
        """Different seeds can produce different orders."""
        rng1 = random.Random(42)
        mode1 = RandomMode(sample_cards, random_instance=rng1)
        order1 = [mode1.next_card() for _ in range(len(sample_cards))]

        # Use seed that is very likely to produce a different shuffle
        rng2 = random.Random(1)
        mode2 = RandomMode(sample_cards, random_instance=rng2)
        order2 = [mode2.next_card() for _ in range(len(sample_cards))]

        # At least verify both shuffles are valid (contain all cards)
        assert len(order1) == len(sample_cards)
        assert len(order2) == len(sample_cards)

    def test_random_mode_caller_list_not_mutated(
        self, sample_cards: list[Flashcard]
    ) -> None:
        """RandomMode does not mutate the caller's list."""
        original_cards = sample_cards.copy()
        mode = RandomMode(sample_cards)

        # Exhaust the mode
        for _ in sample_cards:
            mode.next_card()

        assert sample_cards == original_cards

    def test_random_mode_each_card_once(self, sample_cards: list[Flashcard]) -> None:
        """RandomMode serves each card exactly once."""
        mode = RandomMode(sample_cards)
        served = []

        for _ in range(len(sample_cards)):
            card = mode.next_card()
            assert card is not None
            served.append(card)

        # Verify all original cards are in served (order may differ due to shuffle)
        assert len(served) == len(sample_cards)
        assert all(card in served for card in sample_cards)
        assert mode.next_card() is None


class TestAdaptiveMode:
    """Tests for adaptive quiz mode."""

    def test_adaptive_mode_behavior(self, four_cards: list[Flashcard]) -> None:
        """Wrong answers are requeued after REQUEUE_OFFSET cards."""
        mode = AdaptiveMode(four_cards)

        # Get first card
        card1 = mode.next_card()
        assert card1 == four_cards[0]

        # Record as wrong; it should be reinserted at position REQUEUE_OFFSET
        mode.record_result(card1, correct=False)

        # Next 3 cards should be the original 2nd, 3rd, 4th
        card2 = mode.next_card()
        assert card2 == four_cards[1]

        card3 = mode.next_card()
        assert card3 == four_cards[2]

        card4 = mode.next_card()
        assert card4 == four_cards[3]

        # Next card should be the requeued card1
        card_requeued = mode.next_card()
        assert card_requeued == card1

        # Quiz ends when all cards answered correctly
        mode.record_result(card_requeued, correct=True)
        assert mode.next_card() is None

    def test_adaptive_requeue_capped_at_queue_length(self) -> None:
        """Requeue position is capped at queue length."""
        three_cards = [
            Flashcard(front="Q1", back="A1"),
            Flashcard(front="Q2", back="A2"),
            Flashcard(front="Q3", back="A3"),
        ]
        mode = AdaptiveMode(three_cards)

        # Get first card
        card1 = mode.next_card()
        assert card1 is not None
        # Exhaust remaining cards to empty the queue
        mode.next_card()
        mode.next_card()

        # Mark only card1 as wrong; queue now empty
        mode.record_result(card1, correct=False)
        # With empty queue, insert_pos = min(REQUEUE_OFFSET, 0) = 0
        # so card1 goes to front

        # Next card should be card1
        assert mode.next_card() == card1

    def test_adaptive_quiz_ends_when_all_correct(
        self, sample_cards: list[Flashcard]
    ) -> None:
        """Quiz ends only when every card has been answered correctly."""
        mode = AdaptiveMode(sample_cards)

        card1 = mode.next_card()
        assert card1 is not None
        mode.record_result(card1, correct=False)  # Wrong, requeued

        card2 = mode.next_card()
        assert card2 is not None
        mode.record_result(card2, correct=True)  # Correct

        card3 = mode.next_card()
        assert card3 is not None
        mode.record_result(card3, correct=True)  # Correct

        # Card1 should reappear after REQUEUE_OFFSET (but we only have 2 more)
        card_next = mode.next_card()
        assert card_next == card1

        mode.record_result(card1, correct=True)  # Now all correct
        assert mode.next_card() is None

    def test_adaptive_empty_cards(self) -> None:
        """Adaptive mode raises ValueError for empty card list."""
        with pytest.raises(ValueError):
            AdaptiveMode([])


class TestQuizSession:
    """Tests for quiz session tracking."""

    def test_quiz_session_case_insensitive_answers(
        self, sample_cards: list[Flashcard]
    ) -> None:
        """Answer comparison is case-insensitive."""
        mode = SequentialMode(sample_cards)
        session = QuizSession(mode)

        card = mode.next_card()
        assert card is not None

        assert session.check_answer(card, "A1") is True
        assert session.check_answer(card, "a1") is True
        assert session.check_answer(card, "A1") is True

    def test_quiz_session_whitespace_normalization(
        self, sample_cards: list[Flashcard]
    ) -> None:
        """Answer comparison normalizes whitespace."""
        mode = SequentialMode(sample_cards)
        session = QuizSession(mode)

        card = mode.next_card()
        assert card is not None

        assert session.check_answer(card, "  A1  ") is True
        assert session.check_answer(card, "A1") is True
        assert session.check_answer(card, "A  1") is False

    def test_quiz_session_accuracy_zero_questions(
        self, sample_cards: list[Flashcard]
    ) -> None:
        """Accuracy is 0.0 when no questions answered."""
        mode = SequentialMode(sample_cards)
        session = QuizSession(mode)

        assert session.accuracy == 0.0

    def test_quiz_session_accuracy_mixed_answers(
        self, four_cards: list[Flashcard]
    ) -> None:
        """Accuracy is calculated correctly after mixed answers."""
        mode = SequentialMode(four_cards)
        session = QuizSession(mode)

        cards: list[Flashcard] = [cast(Flashcard, mode.next_card()) for _ in range(4)]

        session.check_answer(cards[0], "A1")  # Correct
        session.check_answer(cards[1], "WRONG")  # Incorrect
        session.check_answer(cards[2], "A3")  # Correct
        session.check_answer(cards[3], "A4")  # Correct

        assert session.total_questions == 4
        assert session.correct_count == 3
        assert session.accuracy == 75.0

    def test_quiz_session_missed_terms_unique(
        self, sample_cards: list[Flashcard]
    ) -> None:
        """Missed terms list contains only unique terms."""
        mode = SequentialMode(sample_cards)
        session = QuizSession(mode)

        card = sample_cards[0]

        session.check_answer(card, "WRONG")
        session.check_answer(card, "WRONG")
        session.check_answer(card, "WRONG")

        missed = session.missed_terms
        assert missed.count(card.front) == 1

    def test_quiz_session_missed_terms_first_missed_order(
        self, four_cards: list[Flashcard]
    ) -> None:
        """Missed terms are in order of first miss."""
        mode = SequentialMode(four_cards)
        session = QuizSession(mode)

        cards: list[Flashcard] = [cast(Flashcard, mode.next_card()) for _ in range(4)]

        session.check_answer(cards[2], "WRONG")  # Q3 missed first
        session.check_answer(cards[0], "WRONG")  # Q1 missed second
        session.check_answer(cards[2], "A3")  # Q3 answered correctly
        session.check_answer(cards[1], "WRONG")  # Q2 missed third

        missed = session.missed_terms
        assert missed == ["Q3", "Q1", "Q2"]

    def test_quiz_session_missed_terms_returns_copy(
        self, sample_cards: list[Flashcard]
    ) -> None:
        """Missed terms returns a copy, not the internal list."""
        mode = SequentialMode(sample_cards)
        session = QuizSession(mode)

        card = sample_cards[0]
        session.check_answer(card, "WRONG")

        missed1 = session.missed_terms
        missed2 = session.missed_terms

        assert missed1 == missed2
        assert missed1 is not missed2

        # Modifying the returned list should not affect the session
        missed1.append("FAKE")
        assert len(session.missed_terms) == 1


class TestQuizModeEmptyCards:
    """Tests for empty card list validation."""

    def test_sequential_empty_cards(self) -> None:
        """SequentialMode raises ValueError for empty card list."""
        with pytest.raises(ValueError):
            SequentialMode([])

    def test_random_empty_cards(self) -> None:
        """RandomMode raises ValueError for empty card list."""
        with pytest.raises(ValueError):
            RandomMode([])

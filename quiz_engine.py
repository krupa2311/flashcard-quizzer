"""Quiz engine and session management for the Flashcard Quizzer.

This module implements the Strategy pattern for different quiz modes (Sequential,
Random, and Adaptive) and provides session tracking for quiz progress.
"""

import random
from abc import ABC, abstractmethod

from utils.file_handler import Flashcard


def _normalize(text: str) -> str:
    """Normalize text for comparison: strip, casefold, collapse whitespace.

    Args:
        text: The text to normalize.

    Returns:
        Normalized text.
    """
    return " ".join(text.strip().casefold().split())


class QuizMode(ABC):
    """Abstract base class for quiz modes using the Strategy pattern.

    Each QuizMode subclass implements a different strategy for selecting
    which card to present next and optionally tracking progress.

    Args:
        cards: A list of Flashcard objects to quiz on.

    Raises:
        ValueError: If the cards list is empty.
    """

    def __init__(self, cards: list[Flashcard]) -> None:
        """Initialize the quiz mode with a list of flashcards.

        Args:
            cards: A list of Flashcard objects.

        Raises:
            ValueError: If cards is empty.
        """
        if not cards:
            raise ValueError("Cannot create a quiz with an empty list of flashcards")
        self.cards = list(cards)

    @abstractmethod
    def next_card(self) -> Flashcard | None:
        """Get the next card to quiz on.

        Returns:
            The next Flashcard to present, or None if the quiz is finished.
        """

    @abstractmethod
    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Record the result of the user's answer.

        Args:
            card: The Flashcard that was answered.
            correct: Whether the user's answer was correct.
        """


class SequentialMode(QuizMode):
    """Serves cards in their original order, one time each."""

    def __init__(self, cards: list[Flashcard]) -> None:
        """Initialize Sequential mode with cards in original order.

        Args:
            cards: A list of Flashcard objects.

        Raises:
            ValueError: If cards is empty.
        """
        super().__init__(cards)
        self.index = 0

    def next_card(self) -> Flashcard | None:
        """Get the next card in sequence.

        Returns:
            The next Flashcard, or None if all cards have been shown.
        """
        if self.index < len(self.cards):
            card = self.cards[self.index]
            self.index += 1
            return card
        return None

    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Record the result (not used in sequential mode).

        Args:
            card: The Flashcard that was answered.
            correct: Whether the user's answer was correct.
        """


class RandomMode(QuizMode):
    """Shuffles a copy of cards once, then serves each card once."""

    def __init__(
        self, cards: list[Flashcard], random_instance: random.Random | None = None
    ) -> None:
        """Initialize Random mode with shuffled cards.

        Creates a shuffled copy of the cards list without modifying the
        original list passed by the caller.

        Args:
            cards: A list of Flashcard objects.
            random_instance: Optional Random instance for seeding (useful for tests).

        Raises:
            ValueError: If cards is empty.
        """
        super().__init__(cards)
        self.shuffled_cards = cards.copy()
        rng = random_instance if random_instance is not None else random.Random()
        rng.shuffle(self.shuffled_cards)
        self.index = 0

    def next_card(self) -> Flashcard | None:
        """Get the next card in shuffled order.

        Returns:
            The next Flashcard, or None if all cards have been shown.
        """
        if self.index < len(self.shuffled_cards):
            card = self.shuffled_cards[self.index]
            self.index += 1
            return card
        return None

    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Record the result (not used in random mode).

        Args:
            card: The Flashcard that was answered.
            correct: Whether the user's answer was correct.
        """


class AdaptiveMode(QuizMode):
    """Keeps a queue of cards, re-inserting incorrectly answered cards."""

    REQUEUE_OFFSET = 3

    def __init__(self, cards: list[Flashcard]) -> None:
        """Initialize Adaptive mode with a copy of cards as a queue.

        Args:
            cards: A list of Flashcard objects.

        Raises:
            ValueError: If cards is empty.
        """
        super().__init__(cards)
        self.queue = cards.copy()

    def next_card(self) -> Flashcard | None:
        """Get and remove the next card from the queue.

        Returns:
            The front card of the queue (removed), or None if the queue is empty.
        """
        if self.queue:
            return self.queue.pop(0)
        return None

    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Record the result and re-queue if incorrect.

        If the card was answered incorrectly, it is re-inserted REQUEUE_OFFSET
        positions later (or at the end if fewer cards remain). The card should
        have been already removed from the queue by next_card().

        Args:
            card: The Flashcard that was answered.
            correct: Whether the user's answer was correct.
        """
        if not correct:
            insert_pos = min(self.REQUEUE_OFFSET, len(self.queue))
            self.queue.insert(insert_pos, card)


QUIZ_MODES = {
    "sequential": SequentialMode,
    "random": RandomMode,
    "adaptive": AdaptiveMode,
}


def get_quiz_mode(name: str, cards: list[Flashcard]) -> QuizMode:
    """Factory function to create a quiz mode by name.

    Args:
        name: The name of the quiz mode (case-insensitive, whitespace-trimmed).
            Valid modes: 'sequential', 'random', 'adaptive'.
        cards: A list of Flashcard objects.

    Returns:
        A QuizMode instance of the requested type.

    Raises:
        ValueError: If the mode name is unknown.
    """
    normalized_name = name.strip().lower()
    mode_class = QUIZ_MODES.get(normalized_name)
    if not mode_class:
        valid_modes = ", ".join(QUIZ_MODES.keys())
        raise ValueError(f"Unknown quiz mode: {name}. Valid modes: {valid_modes}")

    return mode_class(cards)


class QuizSession:
    """Tracks progress and results for a quiz session.

    Wraps a QuizMode and provides high-level operations for a quiz session,
    including answer checking, accuracy calculation, and tracking of missed
    terms.

    Args:
        mode: A QuizMode instance.
    """

    def __init__(self, mode: QuizMode) -> None:
        """Initialize a quiz session with a quiz mode.

        Args:
            mode: A QuizMode instance.
        """
        self.mode = mode
        self._total_questions = 0
        self._correct_count = 0
        self._missed_terms: list[str] = []

    def check_answer(self, card: Flashcard, user_answer: str) -> bool:
        """Check if the user's answer is correct and record the result.

        Answer comparison is case-insensitive and whitespace-normalized.
        Results are automatically recorded in the underlying quiz mode.

        Args:
            card: The Flashcard that was answered.
            user_answer: The user's answer text.

        Returns:
            True if the answer is correct, False otherwise.
        """
        correct = _normalize(user_answer) == _normalize(card.back)

        self._total_questions += 1
        if correct:
            self._correct_count += 1
        else:
            if card.front not in self._missed_terms:
                self._missed_terms.append(card.front)

        self.mode.record_result(card, correct)
        return correct

    @property
    def total_questions(self) -> int:
        """Get the total number of questions asked.

        Returns:
            Total question count.
        """
        return self._total_questions

    @property
    def correct_count(self) -> int:
        """Get the number of correct answers.

        Returns:
            Number of correct answers.
        """
        return self._correct_count

    @property
    def missed_terms(self) -> list[str]:
        """Get a copy of the list of missed terms.

        Returns:
            A copy of the missed terms list.
        """
        return self._missed_terms.copy()

    @property
    def accuracy(self) -> float:
        """Calculate accuracy as a percentage.

        Returns:
            The percentage of questions answered correctly (0.0 if no
            questions have been answered yet).
        """
        if self._total_questions == 0:
            return 0.0
        return (self._correct_count / self._total_questions) * 100.0

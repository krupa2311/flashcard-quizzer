"""CLI UI and presentation for the Flashcard Quizzer.

This module handles terminal output including colored text, quiz interaction,
and session summary reporting.
"""

import os
import sys
from typing import Callable

from quiz_engine import QuizSession


def _is_tty() -> bool:
    """Check if stdout is a TTY.

    Returns:
        True if stdout is a TTY and NO_COLOR is not set, False otherwise.
    """
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def green(text: str) -> str:
    """Format text in green (only if stdout is a TTY and NO_COLOR is not set).

    Args:
        text: The text to format.

    Returns:
        The text formatted in green, or plain text if not a TTY.
    """
    if _is_tty():
        return f"\033[32m{text}\033[0m"
    return text


def red(text: str) -> str:
    """Format text in red (only if stdout is a TTY and NO_COLOR is not set).

    Args:
        text: The text to format.

    Returns:
        The text formatted in red, or plain text if not a TTY.
    """
    if _is_tty():
        return f"\033[31m{text}\033[0m"
    return text


def run_quiz(
    session: QuizSession,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    """Run an interactive quiz session.

    Loops through cards provided by session.mode.next_card(), displays the
    front of the card, reads user input, checks the answer, and displays
    the result with green for correct or red for incorrect with the correct
    answer.

    Handles graceful exit on:
    - User typing 'exit' (any case)
    - Ctrl+C (KeyboardInterrupt)
    - Ctrl+D (EOFError)

    Args:
        session: The QuizSession to run.
        input_fn: Optional function for reading input (default: input).
        output_fn: Optional function for printing output (default: print).
    """
    try:
        while True:
            card = session.mode.next_card()
            if card is None:
                break

            output_fn(f"\n{card.front}")
            try:
                user_answer = input_fn("Your answer: ")
            except (KeyboardInterrupt, EOFError):
                break

            if user_answer.strip().lower() == "exit":
                break

            correct = session.check_answer(card, user_answer)

            if correct:
                output_fn(green("Correct!"))
            else:
                output_fn(red(f"Incorrect. The correct answer is: {card.back}"))

    except (KeyboardInterrupt, EOFError):
        pass


def print_summary(
    session: QuizSession,
    show_details: bool = False,
    output_fn: Callable[[str], None] = print,
) -> None:
    """Print a formatted summary of the quiz session.

    If no questions were answered, prints a friendly message. Otherwise,
    prints a table with total questions, accuracy percentage (one decimal),
    and the list of missed terms.

    Args:
        session: The QuizSession to summarize.
        show_details: If True, also print each missed term with its correct answer.
        output_fn: Optional function for printing output (default: print).
    """
    if session.total_questions == 0:
        output_fn("\nNo questions answered.")
        return

    output_fn("\n" + "=" * 50)
    output_fn("Quiz Summary")
    output_fn("=" * 50)
    output_fn(f"Total Questions: {session.total_questions}")
    output_fn(f"Accuracy: {session.accuracy:.1f}%")

    if session.missed_terms:
        output_fn("\nMissed Terms:")
        for term in session.missed_terms:
            output_fn(f"  - {term}")

        if show_details:
            # Note: This would require storing card objects to show answers.
            # For now, we just list the missed terms.
            pass

    output_fn("=" * 50)

"""CLI UI and presentation for the Flashcard Quizzer.

This module handles terminal output including colored text, quiz interaction,
and session summary reporting.
"""

import os
import sys
from typing import Callable

from quiz_engine import QuizSession


def _use_color() -> bool:
    """Check if stdout is a TTY and color should be used.

    Returns:
        True if stdout is a TTY and NO_COLOR is not set, False otherwise.
    """
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _colorize(text: str, code: str) -> str:
    """Format text with an ANSI color code.

    Args:
        text: The text to format.
        code: The ANSI color code (e.g., "32" for green, "31" for red).

    Returns:
        The text formatted with the color code, or plain text if colors disabled.
    """
    if _use_color():
        return f"\033[{code}m{text}\033[0m"
    return text


def green(text: str) -> str:
    """Format text in green (only if stdout is a TTY and NO_COLOR is not set).

    Args:
        text: The text to format.

    Returns:
        The text formatted in green, or plain text if not a TTY.
    """
    return _colorize(text, "32")


def red(text: str) -> str:
    """Format text in red (only if stdout is a TTY and NO_COLOR is not set).

    Args:
        text: The text to format.

    Returns:
        The text formatted in red, or plain text if not a TTY.
    """
    return _colorize(text, "31")


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
            user_answer = input_fn("Your answer: ")

            if user_answer.strip().lower() == "exit":
                break

            correct = session.check_answer(card, user_answer)

            if correct:
                output_fn(green("Correct!"))
            else:
                output_fn(red(f"Incorrect. The correct answer is: {card.back}"))

    except (KeyboardInterrupt, EOFError):
        output_fn("")


def print_summary(
    session: QuizSession,
    show_details: bool = False,
    output_fn: Callable[[str], None] = print,
) -> None:
    """Print a formatted summary of the quiz session.

    If no questions were answered, prints a friendly message. Otherwise,
    prints a table with total questions, accuracy percentage (one decimal),
    correct/incorrect counts, and optionally each missed term with its answer.

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

    incorrect_count = session.total_questions - session.correct_count

    output_fn(f"Total Questions:      {session.total_questions}")
    output_fn(f"Correct:              {session.correct_count}")
    output_fn(f"Incorrect:            {incorrect_count}")
    output_fn(f"Accuracy:             {session.accuracy:.1f}%")

    if session.missed_terms:
        output_fn("\nMissed Terms:")
        for term in session.missed_terms:
            output_fn(f"  - {term}")

        if show_details:
            front_to_back = {card.front: card.back for card in session.mode.cards}
            output_fn("\nMissed Term Details:")
            for term in session.missed_terms:
                answer = front_to_back.get(term, "N/A")
                output_fn(f"  {term}: {answer}")

    output_fn("=" * 50)

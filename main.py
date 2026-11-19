"""Entry point for the Flashcard Quizzer CLI.

This module provides command-line argument parsing and the main application
flow for the Flashcard Quizzer.
"""

import argparse
import random
import sys

from quiz_engine import QUIZ_MODES, QuizSession, get_quiz_mode
from ui import print_summary, run_quiz
from utils.exporter import ExportError, export_session
from utils.file_handler import Flashcard, FlashcardLoadError, load_flashcards


def _validate_limit(value: str) -> int:
    """Validate that --limit argument is a positive integer.

    Args:
        value: The string value from argparse.

    Returns:
        The validated integer value.

    Raises:
        argparse.ArgumentTypeError: If the value is not a positive integer.
    """
    try:
        num = int(value)
        if num < 1:
            raise argparse.ArgumentTypeError(
                f"--limit must be a positive integer (>= 1), got {num}"
            )
        return num
    except ValueError:
        raise argparse.ArgumentTypeError(f"--limit must be an integer, got '{value}'")


def _validate_export_path(value: str) -> str:
    """Validate that --export path has a supported extension.

    Args:
        value: The file path from argparse.

    Returns:
        The validated file path.

    Raises:
        argparse.ArgumentTypeError: If the extension is not .csv or .json.
    """
    path_lower = value.lower()
    if not (path_lower.endswith(".csv") or path_lower.endswith(".json")):
        raise argparse.ArgumentTypeError(
            f"Export path must end with .csv or .json (got {value})"
        )
    return value


def select_cards(
    cards: list[Flashcard], limit: int | None, mode: str
) -> list[Flashcard]:
    """Select a subset of cards based on limit and quiz mode.

    If limit is None or greater than or equal to the number of cards,
    all cards are returned. For sequential mode, the first limit cards
    are returned in order. For other modes, limit cards are randomly
    selected using random.sample.

    Args:
        cards: The list of Flashcard objects to select from.
        limit: Maximum number of cards to return, or None for all cards.
        mode: The quiz mode ('sequential', 'random', 'adaptive').

    Returns:
        A list of selected Flashcard objects (never mutates the input list).
    """
    if limit is None or limit >= len(cards):
        return cards.copy()

    if mode == "sequential":
        return cards[:limit]

    return random.sample(cards, limit)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional list of arguments (default: sys.argv[1:]).

    Returns:
        Parsed arguments as an argparse.Namespace.
    """
    mode_choices = list(QUIZ_MODES.keys())
    mode_help = f"Quiz mode: {', '.join(mode_choices)} (default: sequential)"

    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Quiz yourself with flashcards from a JSON file.",
    )

    parser.add_argument(
        "-f",
        "--file",
        required=True,
        help="Path to the JSON file containing flashcards",
    )

    parser.add_argument(
        "-m",
        "--mode",
        default="sequential",
        choices=mode_choices,
        help=mode_help,
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show detailed statistics after the quiz",
    )

    parser.add_argument(
        "--limit",
        type=_validate_limit,
        default=None,
        help="Limit the number of cards to quiz on",
    )

    parser.add_argument(
        "--export",
        type=_validate_export_path,
        default=None,
        help="Export session results to a JSON or CSV file",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the Flashcard Quizzer application.

    Loads flashcards from a file, creates a quiz session, runs the quiz,
    prints a summary, and optionally exports results.

    Args:
        argv: Optional list of arguments (default: sys.argv[1:]).

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    args = parse_args(argv)

    try:
        cards = load_flashcards(args.file)
        selected_cards = select_cards(cards, args.limit, args.mode)
        mode = get_quiz_mode(args.mode, selected_cards)
        session = QuizSession(mode)
    except FlashcardLoadError as e:
        print(f"Error loading flashcards: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    run_quiz(session)
    print_summary(session, show_details=args.stats)

    if args.export:
        if session.total_questions == 0:
            print(
                "No questions answered; skipping export.",
                file=sys.stderr,
            )
        else:
            try:
                export_session(
                    session,
                    args.export,
                    args.mode,
                    args.file,
                )
                print(f"Results saved to {args.export}")
            except ExportError as e:
                print(f"Export error: {e}", file=sys.stderr)
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

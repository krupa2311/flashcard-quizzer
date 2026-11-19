"""Entry point for the Flashcard Quizzer CLI.

This module provides command-line argument parsing and the main application
flow for the Flashcard Quizzer.
"""

import argparse
import sys

from quiz_engine import QUIZ_MODES, QuizSession, get_quiz_mode
from ui import print_summary, run_quiz
from utils.file_handler import FlashcardLoadError, load_flashcards


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

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the Flashcard Quizzer application.

    Loads flashcards from a file, creates a quiz session, runs the quiz,
    and prints a summary.

    Args:
        argv: Optional list of arguments (default: sys.argv[1:]).

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    args = parse_args(argv)

    try:
        cards = load_flashcards(args.file)
        mode = get_quiz_mode(args.mode, cards)
        session = QuizSession(mode)
    except FlashcardLoadError as e:
        print(f"Error loading flashcards: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    run_quiz(session)
    print_summary(session, show_details=args.stats)

    return 0


if __name__ == "__main__":
    sys.exit(main())

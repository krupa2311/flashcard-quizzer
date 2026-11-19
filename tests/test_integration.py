"""Integration tests for full quiz sessions."""

from quiz_engine import QuizSession, get_quiz_mode
from ui import run_quiz
from utils.file_handler import Flashcard


def test_full_session() -> None:
    """Quiz session with 3 cards, 2 correct and 1 wrong (mixed capitalization)."""
    cards = [
        Flashcard("What is 2+2?", "Four"),
        Flashcard("What is the capital of France?", "Paris"),
        Flashcard("What is H2O?", "Water"),
    ]
    session = QuizSession(get_quiz_mode("sequential", cards))

    # Simulate user input: correct, correct, wrong with different capitalization
    input_responses = ["four", "PARIS", "hydrogen", "exit"]
    input_index = [0]

    def mock_input_fn(prompt: str) -> str:
        response = input_responses[input_index[0]]
        input_index[0] += 1
        return response

    output_lines = []

    def mock_output_fn(line: str) -> None:
        output_lines.append(line)

    # Run the quiz
    run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

    # Check totals
    assert session.total_questions == 3
    assert session.correct_count == 2
    assert abs(session.accuracy - 66.7) < 0.1  # ~66.7%
    assert session.missed_terms == ["What is H2O?"]

    # Verify correct/incorrect feedback was printed
    output_text = "\n".join(output_lines)
    assert "Correct!" in output_text
    assert "Incorrect" in output_text


def test_full_session_adaptive_mode() -> None:
    """Adaptive mode: missed card returns and final totals are correct."""
    cards = [
        Flashcard("Q1", "A1"),
        Flashcard("Q2", "A2"),
        Flashcard("Q3", "A3"),
    ]
    session = QuizSession(get_quiz_mode("adaptive", cards))

    # Simulate: wrong on Q1, right on Q2, right on Q3, right on Q1 (requeued)
    input_responses = ["wrong", "a2", "a3", "a1"]
    input_index = [0]

    def mock_input_fn(prompt: str) -> str:
        response = input_responses[input_index[0]]
        input_index[0] += 1
        return response

    output_lines = []

    def mock_output_fn(line: str) -> None:
        output_lines.append(line)

    # Run the quiz
    run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

    # Check totals (3 cards + 1 requeue = 4 total questions)
    assert session.total_questions == 4
    assert session.correct_count == 3
    assert abs(session.accuracy - 75.0) < 0.1  # 75%
    assert session.missed_terms == ["Q1"]

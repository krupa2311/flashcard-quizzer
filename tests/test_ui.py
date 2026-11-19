"""Tests for UI functions and presentation."""

import sys

import pytest

from quiz_engine import QuizSession, get_quiz_mode
from ui import green, print_summary, red, run_quiz
from utils.file_handler import Flashcard
from utils.timer import InputTimeout


class TestColorHelpers:
    """Tests for color formatting functions."""

    def test_green_with_tty_and_color_enabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """green() returns ANSI-wrapped text when stdout is TTY and NO_COLOR not set."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        monkeypatch.delenv("NO_COLOR", raising=False)

        result = green("test")
        assert "\033[32m" in result
        assert "test" in result
        assert "\033[0m" in result

    def test_green_with_no_color_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """green() returns plain text when NO_COLOR environment variable is set."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        monkeypatch.setenv("NO_COLOR", "1")

        result = green("test")
        assert result == "test"
        assert "\033[" not in result

    def test_green_with_non_tty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """green() returns plain text when stdout is not a TTY."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
        monkeypatch.delenv("NO_COLOR", raising=False)

        result = green("test")
        assert result == "test"
        assert "\033[" not in result

    def test_red_with_tty_and_color_enabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """red() returns ANSI-wrapped text when stdout is TTY and NO_COLOR not set."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        monkeypatch.delenv("NO_COLOR", raising=False)

        result = red("test")
        assert "\033[31m" in result
        assert "test" in result
        assert "\033[0m" in result

    def test_red_with_no_color_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """red() returns plain text when NO_COLOR environment variable is set."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        monkeypatch.setenv("NO_COLOR", "1")

        result = red("test")
        assert result == "test"
        assert "\033[" not in result


class TestRunQuiz:
    """Tests for the run_quiz function."""

    def test_run_quiz_prints_correct_feedback(self) -> None:
        """run_quiz prints Correct feedback when answer is right."""
        cards = [Flashcard("Q1", "A1")]
        session = QuizSession(get_quiz_mode("sequential", cards))

        def mock_input_fn(prompt: str) -> str:
            return "a1"

        output_lines = []

        def mock_output_fn(line: str) -> None:
            output_lines.append(line)

        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

        output_text = "\n".join(output_lines)
        assert "Correct!" in output_text

    def test_run_quiz_prints_incorrect_feedback(self) -> None:
        """run_quiz prints Incorrect feedback with correct answer when wrong."""
        cards = [Flashcard("Q1", "A1")]
        session = QuizSession(get_quiz_mode("sequential", cards))

        def mock_input_fn(prompt: str) -> str:
            return "wrong"

        output_lines = []

        def mock_output_fn(line: str) -> None:
            output_lines.append(line)

        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

        output_text = "\n".join(output_lines)
        assert "Incorrect" in output_text
        assert "A1" in output_text

    def test_run_quiz_exit_command_ends_quiz(self) -> None:
        """exit command ends the quiz and is not counted as a question."""
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
        ]
        session = QuizSession(get_quiz_mode("sequential", cards))

        input_responses = ["exit"]
        input_index = [0]

        def mock_input_fn(prompt: str) -> str:
            response = input_responses[input_index[0]]
            input_index[0] += 1
            return response

        output_lines = []

        def mock_output_fn(line: str) -> None:
            output_lines.append(line)

        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

        assert session.total_questions == 0

    def test_run_quiz_keyboard_interrupt_ends_gracefully(self) -> None:
        """KeyboardInterrupt (Ctrl+C) ends the quiz cleanly."""
        cards = [Flashcard("Q1", "A1")]
        session = QuizSession(get_quiz_mode("sequential", cards))

        def mock_input_fn(prompt: str) -> str:
            raise KeyboardInterrupt()

        output_lines = []

        def mock_output_fn(line: str) -> None:
            output_lines.append(line)

        # Should not raise, should catch and exit gracefully
        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)
        assert True  # Reached here without exception

    def test_run_quiz_eof_error_ends_gracefully(self) -> None:
        """EOFError (Ctrl+D) ends the quiz cleanly."""
        cards = [Flashcard("Q1", "A1")]
        session = QuizSession(get_quiz_mode("sequential", cards))

        def mock_input_fn(prompt: str) -> str:
            raise EOFError()

        output_lines = []

        def mock_output_fn(line: str) -> None:
            output_lines.append(line)

        # Should not raise, should catch and exit gracefully
        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)
        assert True  # Reached here without exception

    def test_run_quiz_stops_when_deck_finished(self) -> None:
        """Quiz stops when all cards from deck are presented."""
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
        ]
        session = QuizSession(get_quiz_mode("sequential", cards))

        input_responses = ["a1", "a2"]
        input_index = [0]

        def mock_input_fn(prompt: str) -> str:
            response = input_responses[input_index[0]]
            input_index[0] += 1
            return response

        output_lines = []

        def mock_output_fn(line: str) -> None:
            output_lines.append(line)

        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

        # Quiz should have asked all 2 questions and stopped
        assert session.total_questions == 2

    def test_run_quiz_timeout_counts_as_incorrect(self) -> None:
        """InputTimeout causes the question to be counted as incorrect."""
        cards = [Flashcard("Q1", "A1")]
        session = QuizSession(get_quiz_mode("sequential", cards))

        def mock_input_fn(prompt: str) -> str:
            raise InputTimeout()

        output_lines = []

        def mock_output_fn(line: str) -> None:
            output_lines.append(line)

        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

        assert session.total_questions == 1
        assert session.correct_count == 0

    def test_run_quiz_timeout_prints_correct_answer(self) -> None:
        """InputTimeout prints the correct answer in red."""
        cards = [Flashcard("Q1", "CorrectAnswer")]
        session = QuizSession(get_quiz_mode("sequential", cards))

        def mock_input_fn(prompt: str) -> str:
            raise InputTimeout()

        output_lines = []

        def mock_output_fn(line: str) -> None:
            output_lines.append(line)

        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

        output_text = "\n".join(output_lines)
        assert "Time's up!" in output_text
        assert "CorrectAnswer" in output_text

    def test_run_quiz_timeout_adds_to_missed_terms(self) -> None:
        """InputTimeout adds the card to missed_terms."""
        cards = [Flashcard("MissedTerm", "CorrectAnswer")]
        session = QuizSession(get_quiz_mode("sequential", cards))

        def mock_input_fn(prompt: str) -> str:
            raise InputTimeout()

        output_lines = []

        def mock_output_fn(line: str) -> None:
            output_lines.append(line)

        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

        assert "MissedTerm" in session.missed_terms

    def test_run_quiz_timeout_continues_to_next_card(self) -> None:
        """Quiz continues to next card after timeout."""
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
        ]
        session = QuizSession(get_quiz_mode("sequential", cards))

        call_count = [0]

        def mock_input_fn(prompt: str) -> str:
            call_count[0] += 1
            if call_count[0] == 1:
                raise InputTimeout()
            return "a2"

        output_lines = []

        def mock_output_fn(line: str) -> None:
            output_lines.append(line)

        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

        assert session.total_questions == 2
        assert session.correct_count == 1

    def test_run_quiz_timeout_in_adaptive_mode_requeues_card(self) -> None:
        """In adaptive mode, timeout causes card to be re-queued."""
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
        ]
        session = QuizSession(get_quiz_mode("adaptive", cards))

        input_calls = []

        def mock_input_fn(prompt: str) -> str:
            input_calls.append(prompt)
            if len(input_calls) == 1:
                raise InputTimeout()
            elif len(input_calls) == 2:
                return "a2"
            else:
                return "exit"

        output_lines = []

        def mock_output_fn(line: str) -> None:
            output_lines.append(line)

        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

        # First question timed out (Q1), second was answered (Q2)
        assert session.total_questions == 2


class TestPrintSummary:
    """Tests for the print_summary function."""

    def test_print_summary_no_questions_answered(self) -> None:
        """Print friendly message when no questions were answered."""
        cards = [Flashcard("Q1", "A1")]
        session = QuizSession(get_quiz_mode("sequential", cards))

        output_lines = []

        def mock_output_fn(line: str) -> None:
            output_lines.append(line)

        print_summary(session, show_details=False, output_fn=mock_output_fn)

        output_text = "\n".join(output_lines)
        assert "No questions answered" in output_text

    def test_print_summary_shows_total_and_accuracy(self) -> None:
        """Print total questions and accuracy with one decimal place."""
        cards = [
            Flashcard("Q1", "A1"),
            Flashcard("Q2", "A2"),
        ]
        session = QuizSession(get_quiz_mode("sequential", cards))

        input_responses = ["a1", "exit"]
        input_index = [0]

        def mock_input_fn(prompt: str) -> str:
            response = input_responses[input_index[0]]
            input_index[0] += 1
            return response

        def mock_output_fn(line: str) -> None:
            pass

        # Answer first question correctly, then exit
        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

        output_lines = []

        def summary_output_fn(line: str) -> None:
            output_lines.append(line)

        print_summary(session, show_details=False, output_fn=summary_output_fn)

        output_text = "\n".join(output_lines)
        assert "Total Questions:" in output_text
        assert "Accuracy:" in output_text
        # Accuracy should be formatted with one decimal
        assert "100.0%" in output_text

    def test_print_summary_lists_missed_terms(self) -> None:
        """List all missed terms in the summary."""
        cards = [
            Flashcard("Term1", "Answer1"),
            Flashcard("Term2", "Answer2"),
        ]
        session = QuizSession(get_quiz_mode("sequential", cards))

        def mock_input_fn(prompt: str) -> str:
            return "wrong"

        def mock_output_fn(line: str) -> None:
            pass

        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

        output_lines = []

        def summary_output_fn(line: str) -> None:
            output_lines.append(line)

        print_summary(session, show_details=False, output_fn=summary_output_fn)

        output_text = "\n".join(output_lines)
        assert "Missed Terms:" in output_text
        assert "Term1" in output_text

    def test_print_summary_show_details_false_no_answers(self) -> None:
        """With show_details=False, do not print correct answers for missed terms."""
        cards = [Flashcard("Q1", "CorrectAnswer")]
        session = QuizSession(get_quiz_mode("sequential", cards))

        def mock_input_fn(prompt: str) -> str:
            return "wrong"

        def mock_output_fn(line: str) -> None:
            pass

        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

        output_lines = []

        def summary_output_fn(line: str) -> None:
            output_lines.append(line)

        print_summary(session, show_details=False, output_fn=summary_output_fn)

        output_text = "\n".join(output_lines)
        assert "Missed Term Details:" not in output_text

    def test_print_summary_show_details_true_prints_answers(self) -> None:
        """With show_details=True, print each missed term with its correct answer."""
        cards = [Flashcard("Q1", "CorrectAnswer")]
        session = QuizSession(get_quiz_mode("sequential", cards))

        def mock_input_fn(prompt: str) -> str:
            return "wrong"

        def mock_output_fn(line: str) -> None:
            pass

        run_quiz(session, input_fn=mock_input_fn, output_fn=mock_output_fn)

        output_lines = []

        def summary_output_fn(line: str) -> None:
            output_lines.append(line)

        print_summary(session, show_details=True, output_fn=summary_output_fn)

        output_text = "\n".join(output_lines)
        assert "Missed Term Details:" in output_text
        assert "CorrectAnswer" in output_text

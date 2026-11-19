"""Timed input functionality for the Flashcard Quizzer.

This module provides a timed input function that reads user input with a timeout,
using select.select on Unix-like systems. The function is not available on Windows.
"""

import os
import select
import sys


class InputTimeout(Exception):
    """Exception raised when timed input exceeds the timeout."""

    pass


def timed_input(prompt: str, timeout: int) -> str:
    """Read user input with a timeout.

    Writes the prompt to stdout and reads one line of input from stdin.
    If stdin is ready within the timeout, returns the line without trailing newline.
    If the timeout expires, discards unread terminal input and raises InputTimeout.

    Args:
        prompt: The prompt to display.
        timeout: Timeout in seconds.

    Returns:
        The user's input line without trailing newline.

    Raises:
        InputTimeout: If the timeout expires before input is received.
        EOFError: If stdin reaches EOF (end of input).
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()

    ready, _, _ = select.select([sys.stdin], [], [], timeout)

    if ready:
        line = sys.stdin.readline()
        if not line:
            raise EOFError()
        return line.rstrip("\n")

    if sys.stdin.isatty():
        try:
            import termios

            termios.tcflush(sys.stdin, termios.TCIFLUSH)
        except Exception:
            pass

    raise InputTimeout()


def timed_input_supported() -> bool:
    """Check if timed input is supported on this platform.

    Returns False on Windows (os.name == "nt"), True otherwise.

    Returns:
        True if timed input is supported, False otherwise.
    """
    return os.name != "nt"

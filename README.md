# Flashcard Quizzer

A command-line flashcard quiz app. It loads flashcards from a JSON file and
quizzes you in sequential, random, or adaptive mode, then shows a session
summary. Built with AI-assisted development as part of a Udacity course project.

## Features

- Load decks from JSON (two supported formats) with friendly error messages
- Three quiz modes: sequential, random, adaptive (repeats cards you missed)
- Case-insensitive answer checking with green/red feedback
- Session summary: total questions, correct/incorrect, accuracy %, missed terms
- Type `exit` or press Ctrl+C / Ctrl+D to quit at any time, with no traceback
- Extra features: `--limit` (quiz on a subset), `--export` (save results to
  CSV or JSON), `--timed` (per-question timer)

## Requirements

- Python 3.10 or higher
- Dependencies are listed in `requirements.txt` (pytest, pytest-cov, black,
  flake8, isort, mypy, and others). The app itself uses only the standard
  library.

## Installation

In the provided Udacity workspace, install directly:

```bash
cd project/starter
python -m pip install -r requirements.txt
```

On your own computer, use a virtual environment first:

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Usage

```bash
python main.py --help
python main.py -m sequential -f data/glossary.json
python main.py -m adaptive -f data/python_basics.json --stats
```

| Flag | Description |
|------|-------------|
| `-f FILE`, `--file FILE` | Path to the JSON deck (required) |
| `-m MODE`, `--mode MODE` | `sequential` (default), `random`, or `adaptive` |
| `--stats` | Adds a "Missed Term Details" section showing the correct answer for each missed term |
| `--limit N` | Quiz on only N cards (N must be 1 or more) |
| `--export PATH` | Save session results to a `.csv` or `.json` file |
| `--timed` | Enable a per-question timer |
| `--time-limit SECONDS` | Seconds per question in timed mode (default 20, used only with `--timed`) |

### Examples

```bash
# Ten random cards
python main.py -m random -f data/glossary.json --limit 10

# Adaptive quiz, 15-second timer, results saved to a file
python main.py -m adaptive -f data/python_basics.json --timed --time-limit 15 --export results.json
```

### Exit codes

`0` success, `1` load or runtime error (printed as a friendly message),
`2` invalid command-line arguments.

## Deck format

Two JSON formats are supported. Each card needs a non-empty `front` and `back`.

```json
[{"front": "Which keyword defines a function?", "back": "def"}]
```

```json
{"cards": [{"front": "Which keyword defines a function?", "back": "def"}]}
```

Missing files, invalid JSON, wrong structure, non-UTF-8 files, empty decks, and
cards with missing or empty fields all produce a one-line error message that
names the problem (and the card position where relevant).

## Quiz modes

- **Sequential**: cards in file order, once each.
- **Random**: shuffled order, once each.
- **Adaptive**: a missed card is re-queued three cards later, and the quiz ends
  only when every card has been answered correctly. Total questions can
  therefore exceed the deck size.

With `--limit N`, sequential mode uses the first N cards; random and adaptive
modes pick N cards at random.

## Timed mode

With `--timed`, you must submit your complete answer (press Enter) within the
time limit. If time runs out, the question counts as incorrect, the correct
answer is shown, and any partly typed text is discarded so it cannot affect
the next question. Timed mode needs Linux or macOS and is not available on
Windows (the app prints a message and exits).

## Exporting results

`--export results.json` or `--export results.csv` saves the session after the
summary. The format follows the file extension, and an unsupported extension is
rejected before the quiz starts. Exported fields: timestamp, deck file, mode,
total questions, correct count, accuracy, and missed terms with their correct
answers. Nothing is written if no questions were answered.

## Project structure

```
main.py              CLI entry point (argparse, error handling, exit codes)
quiz_engine.py       Strategy pattern quiz modes, factory, QuizSession
ui.py                Colors, quiz loop, summary output
utils/file_handler.py  JSON loading and validation
utils/exporter.py    CSV/JSON export
utils/timer.py       Timed input
data/                Sample decks
tests/               pytest suite
docs/                AI edit log, design notes, report
```

## Design patterns

- **Strategy**: `QuizMode` is an abstract base class, and `SequentialMode`,
  `RandomMode`, and `AdaptiveMode` each implement how the next card is chosen.
- **Factory**: `get_quiz_mode(name, cards)` looks the mode up in the
  `QUIZ_MODES` registry (case-insensitive).

To add a mode (for example spaced repetition), subclass `QuizMode` and add it
to `QUIZ_MODES`. The `--mode` choices update automatically.

## Testing and code quality

```bash
python -m pytest tests/
python -m pytest --cov=. --cov-report=term-missing
python -m pytest --cov=. --cov-report=html
python -m black --check .
python -m flake8 .
python -m mypy .
```

The suite has 142 tests with 100% line coverage of the source modules.

## Known limitations

- The word `exit` always quits the quiz, so a card whose answer is `exit`
  cannot be answered.
- If two cards share the same front text, `--stats` shows only one of the
  answers.
- Timed mode is not supported on Windows. With scripted (piped) multi-line
  input, the timer can report a spurious timeout; interactive terminals are
  unaffected.

## AI-assisted development

The code was generated with Claude Code and then reviewed, tested, and
corrected by the author. See `docs/ai_edit_log.md` for the prompts, the
problems found in AI output, and the fixes.
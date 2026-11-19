# AI Edit Log

This log records my AI-assisted development of the Flashcard Quizzer. All source
code and tests were generated with Claude Code (CLI). A separate Claude chat
assistant helped me plan prompts and review the generated code. In every entry I
ran the code and the quality tools myself instead of relying on the AI's own
summary. I reviewed each generated file for correctness, error handling, type
hints and docstrings, test quality, and security.

---

## 19/11/2026 - Phase 1: JSON loader and validation

**Context:** I needed a loader that reads flashcards from JSON in two formats (a
plain list, or a `{"cards": [...]}` wrapper) and rejects bad data with a clear
message instead of a traceback.

**AI Tool Used:** Claude Code (generation); Claude chat (review guidance)

**Prompt/Request:** "Phase 1 only. Create `utils/file_handler.py` with a
`Flashcard` dataclass and `load_flashcards(path)`. Support both formats. Validate
that each card has non-empty string `front` and `back`. Define a custom
`FlashcardLoadError` and raise it with a readable message for: file not found,
invalid JSON, wrong top-level structure, and a card missing a field (include the
card position). Type hints and docstrings on everything. Run black, flake8 and
mypy before finishing."

**AI Response:** A clean first version with a dataclass, a custom exception,
1-based card positions in error messages, whitespace stripping, type hints and
docstrings. flake8 reported one line-too-long error, and Claude fixed it by
splitting an f-string, which I approved after reading the diff.

**Changes Made:** black, flake8 and mypy all passed, but reading the code I found
three inputs that still broke the "no raw traceback" requirement:
1. `{"cards": null}` was never validated, so `enumerate(None)` raised a raw `TypeError`.
2. A non-UTF-8 file raised a raw `UnicodeDecodeError`, which neither `except` caught.
3. An empty deck `[]` silently returned an empty list.

I also flagged `except (IOError, OSError)` (redundant in Python 3 and a leftover
of Python 2 style), missing exception chaining, and one long function doing five
jobs. I did not edit the code by hand. I re-prompted with six numbered fixes:
validate that `cards` is a list, catch `UnicodeDecodeError`, reject empty decks,
use `except OSError`, use `raise ... from e`, and split the function into private
helpers. Separately, I added a `.flake8` config (`max-line-length = 88`, ignoring
E203 and W503) because black's 88-character lines conflict with flake8's default
limit of 79.

**Reasoning:** Passing tools prove formatting and type consistency, not behavior.
The spec says no stack traces, so every failure path had to end in my custom
exception. Re-prompting keeps the fix inside the AI workflow the course asks for
and gives me a clear before and after.

**Outcome:** I confirmed each bug before the fix with three small test files
(they produced `TypeError`, `UnicodeDecodeError` and `[]`). After the fix all
three end in `FlashcardLoadError` with messages such as "'cards' must be a list,
got NoneType" and "is not valid UTF-8 text", and the traceback shows the
exception chaining. Both sample decks still load, and black, flake8 and mypy pass.

**Lessons Learned:** Passing linters says nothing about missing validation. I now
try malformed inputs by hand before accepting generated code, and naming the
exact failure cases in the prompt would have saved a round trip.

---

## 19/11/2026 - Phase 2: Strategy and Factory patterns

**Context:** I needed the quiz engine with the Strategy pattern (a `QuizMode` base
class and three modes) and a factory to pick a mode by name.

**AI Tool Used:** Claude Code (generation); Claude chat (review guidance)

**Prompt/Request:** "Phase 2 only. Create `quiz_engine.py` with an abstract
`QuizMode` (`next_card()` and `record_result()`), `SequentialMode`, `RandomMode`
(optional seedable `random.Random`, must not mutate the caller's list),
`AdaptiveMode` (a missed card is re-queued `REQUEUE_OFFSET` positions later and
the quiz ends when every card has been answered correctly), a `get_quiz_mode`
factory, and a `QuizSession` for answer checking and stats. No print or input in
the engine."

**AI Response:** A correct Strategy implementation. `RandomMode` copied its list,
accuracy was safe at zero questions, and `missed_terms` was unique and ordered.

**Changes Made:** I found five problems and fixed them with one re-prompt:
1. `next_card()` behaved differently per mode. Sequential and Random advanced an
   index, while Adaptive only peeked at `queue[0]`. Calling it twice printed
   `a b` for Sequential but `a a` for Adaptive. Fix: Adaptive pops the card.
2. `AdaptiveMode.record_result` had a silent early-return guard that would hide
   caller bugs. Fix: removed.
3. The factory rejected `" random "` and rebuilt its dictionary on every call.
   Fix: a module-level `QUIZ_MODES` registry and name normalization.
4. Answer matching used `.lower()` and failed on double spaces. Fix: a
   `_normalize()` helper (strip, casefold, collapse whitespace).
5. `QuizSession` exposed mutable counters. Fix: private fields with read-only
   properties, and the card list is copied.

**Reasoning:** The point of the Strategy pattern is interchangeable algorithms,
so all modes must honor the same contract, not just share method names. The other
fixes remove silent failures and make the registry the single place to add a mode
such as spaced repetition.

**Outcome:** Both modes now print `a b`. A scripted adaptive run with card 1
missed once gives `['1', '2', '3', '4', '1', '5']`. `get_quiz_mode(" RANDOM ", ...)`
returns `RandomMode`, and `"  HELLO    world "` matches `"Hello World"`.

**Lessons Learned:** I now run every strategy through the same script to compare
behavior. A shared interface needs a shared contract.

---

## 19/11/2026 - Tests, coverage, and a mutation check

**Context:** The spec requires pytest tests (including named tests) with more than
80% coverage. I wanted evidence that the tests catch real bugs, not just that
lines run.

**AI Tool Used:** Claude Code (generation); Claude chat (review guidance)

**Prompt/Request:** "Write pytest tests for the existing code with the exact test
names from the project instructions. Do not modify any source files. If you find
a bug, stop and tell me." I then listed specific cases for the loader (both
formats, bad JSON, missing fields, empty deck, non-UTF-8, whitespace, both real
decks), the factory, each mode, and `QuizSession`.

**AI Response:** 45 tests, all passing, reported as 99% coverage.

**Changes Made:**
- The 99% was inflated because `--cov=.` counted the test files themselves. I
  added `.coveragerc` to omit `tests/`.
- Real coverage showed two uncovered lines (the `except OSError` branch in the
  loader). I had Claude add one test that passes a directory path.
- Mutation check: I flipped `if not correct:` to `if correct:` in
  `AdaptiveMode.record_result` and ran the suite. 3 tests failed, including the
  required `test_adaptive_mode_behavior`. I restored the file with
  `git checkout quiz_engine.py`.

**Reasoning:** Coverage shows that lines ran, not that bugs would be noticed. The
mutation check directly tested whether the suite protects the adaptive behavior,
which is the project's main feature.

**Outcome:** 46 tests, 100% coverage on the source modules at that point, and all
five required test names present (checked with `grep`).

**Lessons Learned:** A coverage percentage is not a quality measure on its own.
Deliberately breaking the code is a quick way to test the tests.

---

## 19/11/2026 - Phase 3: CLI, UI, and a stub hidden in the AI's summary

**Context:** I needed the CLI (argparse, colors, graceful exit) and the summary
output, with `--stats` showing extra detail.

**AI Tool Used:** Claude Code (generation); Claude chat (review guidance)

**Prompt/Request:** "Phase 3 only. Create `ui.py` with color helpers (off when
stdout is not a TTY or NO_COLOR is set), `run_quiz(session, input_fn, output_fn)`,
and `print_summary(session, show_details, output_fn)`. With `show_details=True`,
list each missed term with its correct answer. `exit`, Ctrl+C and Ctrl+D must end
the quiz without a traceback and the summary must still print. Create `main.py`
with `-f`, `-m` and `--stats`; catch `FlashcardLoadError` and `ValueError`, print
a friendly message to stderr, and return 1."

**AI Response:** Its summary said `show_details` was supported. Reading `ui.py`, I
found that the branch was just `pass` with a comment saying it was not
implemented, so `--stats` did nothing.

**Changes Made:** One re-prompt for these fixes:
- Implement the details by looking answers up from `session.mode.cards`, and add
  correct and incorrect counts.
- Narrow the `try/except` in `main()`. It wrapped the whole quiz, so an
  unexpected `ValueError` inside the quiz would have been hidden behind a tidy
  message.
- `prog="Flashcard Quizzer"` contained a space, so help did not read
  `usage: main.py`. Fixed.
- Remove duplicated color code (a `_colorize` helper).

**Reasoning:** A flag that silently does nothing fails the spec while looking
finished. The narrowed `try` keeps real bugs visible.

**Outcome:** `--stats` now prints each missed term with its answer. In adaptive
mode on the 8-card deck I missed two cards once each and got 10 questions at
80.0%, as the logic predicts. Sequential and random runs on the same deck gave 8
questions, which confirmed that repeats come only from adaptive mode. I also
checked that an unknown file prints one friendly line with exit code 1.

**Lessons Learned:** An AI summary can claim a feature that is only a stub. I now
read the code and run the feature before trusting the summary.

---

## 19/11/2026 - Extra features: `--limit`, `--export`, and the `--timed` flush

**Context:** The rubric asks for at least three features beyond the basics. I
added `--limit N` (quiz on a subset), `--export PATH` (CSV or JSON results), and
`--timed` (a per-question timer).

**AI Tool Used:** Claude Code (generation); Claude chat (design and review)

**Prompt/Request:** For the timer I specified the rule myself: the complete answer
must be submitted within the limit, a timeout counts as incorrect, and partial
input is never graded. I also required that unread terminal input be discarded
after a timeout so it cannot leak into the next question. For `--export` I
required the extension check to run before the quiz starts, so a typo cannot
lose a finished session. For `--limit` I required the selection logic to live in
a small testable function and to reject values below 1.

**AI Response:** `utils/timer.py` using `select.select` with `termios.tcflush` on
timeout and a Windows check; `utils/exporter.py` for CSV and JSON; and
`select_cards` for `--limit`, each with tests.

**Changes Made:** I accepted the generated code after reviewing it. In
`utils/timer.py` the flush is wrapped in a broad `except Exception: pass`. I
noted this as a weakness (it could hide a typo) but kept it, because its purpose
is to make sure a failed flush can never crash the quiz, and I documented the
limitation in the report. Because the unit tests mock `tcflush`, I verified the
timer on a real terminal.

**Reasoning:** Typed-but-unsent characters stay in the terminal buffer after a
timeout and would be glued onto the next answer. That is a subtle bug that
passing tests would not reveal.

**Outcome:** On a real terminal I typed `de` without pressing Enter and let the
time run out, then typed `len` and pressed Enter on the next question. It was
marked Correct, so the leftover text did not leak. `--export` writes valid JSON
and CSV, and `--export results.txt` fails before any question is asked with exit
code 2. `--limit 3 --timed` works together. The suite grew to 142 tests with 100%
line coverage on all source modules.

**Lessons Learned:** Some behavior can only be verified in the real environment.
Specifying rules and edge cases in the prompt produced much better code than a
short feature description.

---

## 19/11/2026 - AI summaries versus reality

**Context:** Throughout the project I compared Claude Code's end-of-task
summaries with my own test runs.

**AI Tool Used:** Claude Code

**Prompt/Request:** Every prompt asked Claude to run pytest, black, flake8 and
mypy and report the results.

**AI Response:** The summaries were mostly accurate but wrong in small ways:
- One run reported "82% overall" coverage because it had run only one test file.
  The full suite showed 98%.
- A summary reported 141 tests. My full run showed 142.
- An early summary described a feature as supported when it was a stub (see the
  Phase 3 entry).

**Changes Made:** I stopped relying on summaries and verified each step myself
with the same commands: `python -m pytest --cov=. --cov-report=term-missing`,
`python -m black --check . && python -m flake8 . && python -m mypy .`, and
`git diff` after each AI edit. I made a snapshot commit before each re-prompt so
I could see exactly what the AI changed.

**Reasoning:** The AI's confidence did not track its accuracy. Cheap independent
checks caught every discrepancy.

**Outcome:** Final state: 142 tests and 100% line coverage across 341 statements
in all source modules.

**Lessons Learned:** Treat AI output like a pull request from a colleague:
reproduce the results yourself before approving.

---

## Summary Statistics

- **Total AI interactions:** 13 Claude Code prompts (generation and fixes for the
  loader, engine, tests, CLI, and three features), plus review sessions with a
  chat assistant
- **Lines of AI-generated code used:** All 341 statements of source code across
  6 modules and all 142 tests were generated by Claude Code
- **Lines of AI-generated code modified:** None by hand. Every change was made by
  re-prompting. I directly edited only configuration and documentation
  (`.flake8`, `.coveragerc`, `.claude/CLAUDE.md`, README, this log, the report)
- **Most helpful AI interaction:** The Phase 2 engine prompt, which produced a
  correct Strategy pattern that needed only targeted fixes
- **Most challenging AI interaction:** The timed input feature, because its key
  risk (leftover typed characters) could only be checked on a real terminal
- **Biggest lesson learned:** Verify AI output independently. Passing tools and
  confident summaries are not proof of correctness.
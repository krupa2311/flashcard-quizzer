# Flashcard Quizzer: Final Project Report

## 1. Project Overview

The Flashcard Quizzer is a command-line application that loads flashcards from a JSON file and quizzes the user in sequential, random, or adaptive mode. After the quiz it shows a summary with total questions, correct and incorrect counts, accuracy, and the terms the user missed. The goal of the course project was not only to build the application but to practice engineering with AI-generated code: writing precise prompts, reviewing the output critically, and verifying it with tests.

The finished project has six source modules, 142 pytest tests, and 100% line coverage across 341 statements. It supports two deck formats, friendly error messages instead of tracebacks, colored feedback, graceful exit, and three extra features: `--limit`, `--export`, and `--timed`.

## 2. How I Used AI

I used Claude Code to generate all of the code and tests, and a separate Claude chat assistant to help plan prompts and review results. I followed the workflow from the project brief: decompose, generate, review, refine, verify.

I worked in phases and told the agent to build only the current phase. Phase 1 was the data layer, Phase 2 the quiz engine, Phase 3 the CLI and interface, followed by tests and extra features. Each prompt named the files, function signatures, error cases, and quality commands I expected. Before each re-prompt I made a snapshot commit, so `git diff` showed exactly what the AI had changed. When the output was wrong I rewrote the prompt rather than editing the code myself. Only configuration and documentation files were edited by hand.

## 3. Architecture and Design Patterns

The code is split by responsibility. `utils/file_handler.py` loads and validates data, `quiz_engine.py` holds the quiz logic, `ui.py` handles terminal interaction, `main.py` parses arguments and maps errors to exit codes, and `utils/exporter.py` and `utils/timer.py` hold the extra features. The engine contains no `print` or `input` calls, and the UI takes injectable input and output functions. That separation made the whole application testable without a real terminal.

**Strategy pattern.** Sequential, random, and adaptive are three algorithms for one task: choosing the next card. `QuizMode` is an abstract base class, and each mode implements `next_card()` and `record_result()`. This serves a real purpose. `QuizSession` and the UI work with any mode, so a spaced-repetition mode could be added without changing them. Reviewing the first AI output showed why the shared contract matters: adaptive mode only peeked at the queue while the other modes advanced, so the strategies were not truly interchangeable until I had it fixed.

**Factory pattern.** `get_quiz_mode(name, cards)` looks a mode up in a module-level `QUIZ_MODES` registry, ignoring case and surrounding whitespace, and raises a `ValueError` listing the valid modes for an unknown name. The command-line `--mode` choices are built from the same registry, so adding a mode requires registering it in only one place.

## 4. Testing and Quality Assurance

The suite covers the loader (both formats, invalid JSON, missing fields, non-string and empty values, empty decks, encoding errors, unreadable paths, and both real decks), the factory and every mode, session scoring, the UI, the argument parser, the exporter, the timer, and integration tests that simulate a full session. The five test names required by the brief are all present.

I treated coverage with suspicion. A first run reported 99%, but the figure counted the test files themselves, so I excluded them with a `.coveragerc` file. I then ran a mutation check: I deliberately inverted the condition that re-queues missed cards, and three tests failed, including `test_adaptive_mode_behavior`. That showed the suite protects the project's main feature, not just that lines execute. I also tested behavior that unit tests cannot prove. Mocked tests cannot show that the timer discards half-typed input, so I checked it on a real terminal. I also ran adaptive mode on the 8-card deck and missed two cards once each, producing exactly 10 questions at 80.0%, as the logic predicts.

black, flake8, and mypy are part of every verification. I added a `.flake8` configuration with a line length of 88 because black's default conflicts with flake8's default of 79.

## 5. Extra Features

- **`--limit N`** quizzes a subset of the deck. Selection lives in a small tested function. Values below 1 are rejected by argparse.
- **`--export PATH`** saves the session to JSON or CSV, including the timestamp, deck, mode, totals, accuracy, and missed terms with their answers. The extension is validated before the quiz starts, so a typo cannot lose a finished session.
- **`--timed` and `--time-limit`** give each question a time limit (20 seconds by default). A complete answer must be submitted in time. If it is not, the question counts as incorrect, the correct answer is shown, and any half-typed text is discarded so it cannot corrupt the next answer. Timed mode requires Linux or macOS, and the app reports this clearly on Windows.

## 6. Problems Found in AI Output

Reviewing the generated code was the most valuable part of the project, because every phase contained issues that the quality tools did not catch.

- The loader passed black, flake8, and mypy, yet `{"cards": null}` and a non-UTF-8 file both produced raw tracebacks, and an empty deck silently loaded.
- The adaptive strategy broke the shared interface, and the factory rejected a name with stray spaces.
- The AI's summary claimed that `--stats` worked, but the code contained only a `pass` statement.
- The first `main()` wrapped the entire quiz in one `try/except`, which would hide real bugs behind a friendly message.
- Summaries contained small inaccuracies: a partial test run reported 82% coverage, and a test count was off by one.

Each issue was documented in `docs/ai_edit_log.md` along with the prompt that fixed it and the evidence that it was resolved. One known weakness remains by choice: the timer's flush step uses a broad `except Exception`. It exists so that a failed flush can never crash a quiz, but it could also hide a typo.

## 7. Limitations

The word `exit` always quits the quiz, so a card whose answer is `exit` cannot be answered. If two cards share the same front text, `--stats` shows only one of the answers. Timed mode is not available on Windows, and with piped multi-line input the timer can report a spurious timeout. Interactive terminals are unaffected. These limitations are listed in the README.

## 8. Reflection

I learned that AI is fast at producing plausible, well-structured code and weaker at the edges: malformed input, shared contracts between classes, and behavior that depends on the real environment. My prompts improved over the project. Early prompts described what to build, while later ones also specified failure cases, rules such as "partial input is never graded," and the exact checks to run. That specificity produced noticeably better first drafts.

The habit that mattered most was independent verification. The AI's confident summaries were usually right but sometimes wrong in ways that mattered, so I reproduced every claim with my own commands. Treating AI output like a colleague's pull request, reading it, running it, and trying to break it, was more effective than trusting it.

If I extended the project, I would add the spaced-repetition mode the Strategy pattern was designed for, persist progress between sessions, and tighten the timer's exception handling. I would also write the failure cases into the prompt from the first attempt, since naming them up front would have removed several review rounds.

## 9. Conclusion

The project meets the specification: modular code, Strategy and Factory patterns, type hints throughout, friendly error handling, and a test suite with 100% line coverage, plus three additional features. More importantly, it taught me a workflow for working with AI on real software: specify precisely, review critically, and verify independently.
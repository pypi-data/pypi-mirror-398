# Repository Guidelines

## Project Structure & Module Organization
- `src/ch0/cli.py` is the CLI entry point for blindfold chess; it wires up engine selection (including UCI engines), colorized prompts, user input, and PGN handling.
- `src/ch0/engines/andoma` and `src/ch0/engines/sunfish` host engine code and helpers; treat them as third-party style modules and avoid modifying unless you know the engine internals.
- `src/ch0/engines/uci.py` holds small shared utilities for UCI parsing.
- Optional `book.bin` in the repo root enables opening-book moves; the game runs without it.

## Build, Test, and Development Commands
- `uv sync` — create a local virtualenv from `uv.lock` and install dependencies (Python 3.13+).
- `uv run ch0` — launch the interactive game; picks an engine and color in the terminal.
- `uv run python -m pip install -r requirements.txt` — install optional extras (dotenv) if you need env loading.
- `uv run -m pytest` — run tests when you add them (none exist yet).

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation and `snake_case` for functions/variables; keep classes in `CapWords`.
- Prefer type hints (existing public functions are annotated) and keep functions small with early returns for draw/end conditions.
- Keep user-facing prints concise; mirror the existing prompts and SAN/FEN terminology, including ANSI color helpers.
- When extending engines, preserve current interfaces (`next_move`, `generate_move`) to avoid breaking `main.py`.

## Testing Guidelines
- Use `pytest` with files named `test_*.py` under `tests/`; structure tests around `Game`, `bot_makes_a_move`, and draw/checkmate branches.
- For engine changes, add deterministic scenarios using fixed FENs to avoid randomness where possible.
- Capture PGN output assertions by feeding scripted inputs via `stdin` (e.g., `pexpect` or `capsys` in pytest); cover lobby commands (`start`, `help`, `quit`) and in-game commands (`show`, `moves`, `fen`, `pgn`, `resign`).

## Commit & Pull Request Guidelines
- Commit messages are short and imperative (e.g., `Add sunfish hooks`, `Fix PGN headers`); keep the first line under ~60 chars.
- Pull requests should include: a concise summary of behavior changes, repro/usage steps (`uv run main.py`), and notes on engine touch points.
- If visuals change (prompts/output), paste sample terminal snippets; if adding `book.bin` or other large assets, keep them out of git and document expected location.

# Repository Guidelines

## Project Structure & Module Organization
- Core package in `package/`: `logger/__init__.py` exposes `MultiLogger` for routing, `clients/discord.py` and `clients/telegram.py` send outbound messages, and `emojis/__init__.py` maps log levels to emojis.
- Tests live in `tests/` (e.g., `tests/test_emoji_map.py`) and should mirror the package layout when adding coverage.
- Built artifacts land in `dist/`; regenerate via build commands instead of editing them. The local `.venv/` is ignored and should stay uncommitted.

## Build, Test, and Development Commands
- Install with uv (preferred): `uv sync --group dev`, then activate `.venv\Scripts\activate`.
- Pip fallback: `python -m pip install -e .` and add `pytest` if missing.
- Smoke import: `python - <<'PY'\nfrom package.logger import MultiLogger\nMultiLogger()\nPY`
- Run tests: `pytest` or `pytest tests/test_emoji_map.py` for a single file.
- Build distributables: `python -m build` (outputs to `dist/`).

## Coding Style & Naming Conventions
- Use 4-space indentation, type hints, and concise module-level docstrings (match tone in `package/logger/__init__.py`).
- Naming: `snake_case` for functions/variables, `PascalCase` for classes, and keep public imports under the `package.` namespace.
- Prefer `MultiLogger.setup_logger` for routing instead of using `loguru` directly when notifications are needed.

## Testing Guidelines
- Framework: `pytest`. Name files `test_<feature>.py` and keep cases focused.
- Cover edge cases such as missing Discord webhooks or Telegram tokens/chat IDs; keep tests network-free and mock HTTP calls.
- Run relevant tests before submitting; add targeted cases when extending clients or emoji mappings.

## Commit & Pull Request Guidelines
- Follow conventional commits (`feat:`, `fix:`, `refactor:`, `chore:`) to match existing history.
- PRs should include purpose, scope of change, related issues, and any required config/env variables (never commit secrets like Discord webhooks or Telegram tokens); add screenshots or logs only when they aid review.
- Mention test commands executed in the PR description to document verification.

## Security & Configuration Tips
- Do not commit real webhook URLs or bot tokens; use env vars or placeholders in examples.
- When adding new clients, guard against failed HTTP responses and surface clear exceptions without leaking sensitive data.

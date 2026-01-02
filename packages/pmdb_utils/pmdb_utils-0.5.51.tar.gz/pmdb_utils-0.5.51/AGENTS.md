# Repository Guidelines

## Project Structure & Module Organization
- Source code lives in `src/pmdb_utils/` with subpackages like `metadata/` and `dataacceslayer/`.
- Package entry point is exposed as a console script `pmdb_utils` (see `pyproject.toml`).
- No dedicated tests or assets directory is present today.

## Build, Test, and Development Commands
- `uv sync` installs dependencies from `uv.lock` into a local environment (recommended if you use uv).
- `pip install -e .` installs the package in editable mode for local development.
- `python -m build` builds source and wheel distributions using hatchling.
- There is no test command configured yet; consider adding `pytest` and a `tests/` folder when tests are introduced.

## Coding Style & Naming Conventions
- Python 3.9+ codebase; use 4-space indentation and PEP 8 style.
- Use `snake_case` for functions/variables, `PascalCase` for classes, and `lowercase` module names.
- Keep utilities small and focused; prefer explicit imports over `import *`.

## Testing Guidelines
- No test framework is configured in this repo.
- If adding tests, prefer `pytest` with a `tests/` directory and `test_*.py` naming.
- Keep unit tests close to public API behavior and avoid hard-coded secrets.

## Commit & Pull Request Guidelines
- Recent history uses Conventional Commits-style prefixes like `feat:` (and occasional variants).
- Keep commit subjects short and action-oriented; include scope when helpful (e.g., `feat: add insights`).
- PRs should describe the change, link related issues, and note any behavior or API impact.

## Configuration Notes
- Dependencies include Azure SDKs, MinIO, Polars, and dotenv; keep secrets out of source control.
- If you add environment-based configuration, document required variables and defaults in `README.md`.

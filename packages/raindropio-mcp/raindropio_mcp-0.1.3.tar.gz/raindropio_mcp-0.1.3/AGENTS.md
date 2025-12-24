# Repository Guidelines

## Project Structure & Module Organization

Core MCP code lives in `raindropio_mcp/`, with functional domains under `auth/`, `clients/`, `tools/`, `config/`, and `utils/`. `server.py` hosts the FastMCP entrypoint, while `main.py` and `__main__.py` wire configuration, tool registration, and observability. Tests mirror the package layout in `tests/`, `docs/` holds shared references, `monitoring/` stores dashboards, and runnable samples sit in `examples/`. Coverage output from pytest lands in `htmlcov/`.

## Build, Test, and Development Commands

Install dependencies with `uv sync`. Use `uv run python -m raindropio_mcp` (or `uv run raindropio-mcp`) to start the server locally. Run the full quality suite via `uv run crackerjack`; it chains Ruff, mypy, pytest, and Bandit. For targeted checks: `uv run ruff check --fix` formats and lints, `uv run mypy .` enforces typing, and `uv run pytest --cov=. --cov-report=html` regenerates coverage reports.

## Coding Style & Naming Conventions

Target Python 3.13 with 4-space indentation and Ruff-enforced 88-character lines. Keep functions and modules in `snake_case`, classes in `PascalCase`, and constants in `SCREAMING_SNAKE_CASE`. Maintain strict typing (`disallow_untyped_defs = true`) by annotating functions and preferring typed dataclasses or Pydantic models for payloads. Normalise imports with `uv run ruff check --select I --fix` before committing.

## Testing Guidelines

Pytest discovers `test_*.py` and `*_test.py` modules; test functions must start with `test_`. Shared fixtures belong in `tests/conftest.py`. Maintain ≥80% coverage by running `uv run pytest --cov=. --cov-report=html` and reviewing `htmlcov/index.html` for gaps. Write integration tests when adding MCP tools to exercise end-to-end flows.

## Commit & Pull Request Guidelines

Use imperative commit subjects (e.g., `Add Raindrop task sync`) and keep each commit scoped to one concern. Before opening a PR, run `uv run crackerjack` and include the output in the description. Link relevant issues, call out configuration or schema changes, and attach screenshots or sample MCP transcripts when behaviour shifts. Highlight new environment variables so reviewers can update `.env.example`.

## Security & Configuration Tips

Copy `.env.example` when bootstrapping and populate it with your Raindrop.io token locally—never commit secrets. Rotate personal tokens used for testing and rely on the structured logger for tool telemetry to preserve PII masking. Review `docs/` before altering authentication or observability flows to stay aligned with platform requirements.

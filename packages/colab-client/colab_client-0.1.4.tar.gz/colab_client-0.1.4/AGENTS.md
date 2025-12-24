# Agent Guidelines for colab-client

## Commands
- Install: `uv sync --extra dev`
- Lint: `uv run ruff check colab_client`
- Format: `uv run ruff format colab_client`
- Type check: `uv run mypy colab_client`
- Test all: `uv run pytest`
- Single test: `uv run pytest tests/test_file.py::test_function_name -v`

## Code Style
- Python 3.10+ syntax (use `X | None` not `Optional[X]`)
- Line length: 100 chars
- Always start files with `from __future__ import annotations`
- Imports: stdlib → third-party → local, alphabetically sorted (Ruff isort)
- Use `TYPE_CHECKING` guard for type-only imports
- Naming: PascalCase classes, snake_case functions/variables, SCREAMING_SNAKE_CASE constants
- Private methods: single underscore prefix (`_method`)
- Use `@dataclass` for data containers, `@dataclass(frozen=True)` for immutable
- Prefer dict lookups over if-else chains for mappings
- Full type annotations required (mypy strict mode)
- Use `raise ... from e` for exception chaining
- No comments in code - keep code self-documenting

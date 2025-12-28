.PHONY: setup test coverage format check build verify

verify:
	@echo "Checking development environment..."
	@command -v uv >/dev/null 2>&1 || { echo "Error: uv not found. Install from https://docs.astral.sh/uv/"; exit 1; }
	@python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null || { echo "Error: Python 3.10+ required"; exit 1; }
	@echo "✓ uv installed"
	@echo "✓ Python $$(python3 --version | cut -d' ' -f2)"
	@echo "Environment OK"

setup: verify
	uv sync --extra dev

test:
	uv run pytest

coverage:
	uv run pytest --cov=dossier_tools --cov-report=term-missing --cov-report=html

format:
	uv run ruff format .
	uv run ruff check --fix .

check:
	uv run ruff format --check .
	uv run ruff check .

build:
	uv build

.PHONY: test coverage lint format typecheck pre-commit install

test:
	uv run pytest

coverage:
	uv run pytest --cov=src/mf2dom --cov-report=term-missing --cov-report=html

lint:
	uv run ruff check --fix .

format:
	uv run ruff format .

typecheck:
	uv run ty check src/mf2dom tests/

pre-commit:
	uv run pre-commit run --all-files

install:
	uv sync --dev
	uv run pre-commit install

pr: install pre-commit format lint typecheck coverage

release:
	uv run hatch build
	twine upload dist/*
	echo "Release complete, don't forget to tag the release in git!"

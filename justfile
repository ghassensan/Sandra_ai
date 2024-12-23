_default:
    @just -l

format:
    poetry run ruff format .

lint-check:
    poetry run ruff check .

type-check:
    poetry run mypy .

test:
    poetry run pytest

validate: lint-check type-check test

install:
    poetry install

run: install
    poetry run uvicorn sandra_ai.main:app --reload
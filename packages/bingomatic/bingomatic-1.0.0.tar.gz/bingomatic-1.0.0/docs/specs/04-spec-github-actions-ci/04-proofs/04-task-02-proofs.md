# Task 2.0 Proof Artifacts - Create GitHub Actions CI Workflow

## Proof 1: ci.yml exists with valid YAML syntax

```bash
$ uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('YAML syntax valid!')"
YAML syntax valid!
```

## Proof 2: Workflow contains 3 jobs (lint, format, test)

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      - name: Install dependencies
        run: uv sync
      - name: Run Ruff linter
        run: uv run ruff check .

  format:
    name: Format
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      - name: Install dependencies
        run: uv sync
      - name: Check formatting
        run: uv run ruff format --check .

  test:
    name: Test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest tests/ -v
```

## Proof 3: Tests still pass locally

```bash
$ uv run pytest tests/ -v
============================= test session starts ==============================
collected 62 items
============================== 62 passed in 0.19s ==============================
```

## Summary

- Created `.github/workflows/ci.yml` with:
  - Triggers on push and pull_request to all branches
  - `lint` job: Python 3.12, runs `ruff check .`
  - `format` job: Python 3.12, runs `ruff format --check .`
  - `test` job: Python matrix [3.12, 3.13], runs `pytest tests/ -v`
- All jobs run in parallel
- YAML syntax validated

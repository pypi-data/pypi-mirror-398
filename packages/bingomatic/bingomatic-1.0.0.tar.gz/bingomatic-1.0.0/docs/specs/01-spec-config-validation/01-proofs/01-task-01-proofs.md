# Task 1.0 Proof Artifacts - Project Setup and Dependencies

## Proof 1: Dependencies Import Successfully

**Command:** `uv run python -c "import click; import yaml; print('Dependencies OK')"`

**Output:**
```
Dependencies OK
```

**Status:** ✅ PASS

## Proof 2: pyproject.toml Configuration

**File:** `pyproject.toml`

```toml
[project]
name = "bingomatic"
version = "0.1.0"
description = "A bingo card generator for conferences like DevOpsDays"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "click>=8.0",
    "pyyaml>=6.0",
]

[project.scripts]
bingomatic = "bingomatic.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/bingomatic"]
```

**Status:** ✅ PASS - Contains correct dependencies and CLI entry point

## Proof 3: uv sync Output

**Command:** `uv sync`

**Output:**
```
Using CPython 3.14.2 interpreter at: /opt/homebrew/opt/python@3.14/bin/python3.14
Creating virtual environment at: .venv
Resolved 4 packages in 248ms
Installed 3 packages in 2ms
 + bingomatic==0.1.0
 + click==8.3.1
 + pyyaml==6.0.3
```

**Status:** ✅ PASS

## Summary

All proof artifacts for Task 1.0 verified successfully.

# Task 3.0 Proof Artifacts - CLI Interface with Click

## Proof 1: CLI with Missing Config

**Command:** `uv run bingomatic validate`

**Output:**

```
Config file missing, please create it using the template and README instructions.
```

**Exit Code:** 1

**Status:** ✅ PASS

## Proof 2: Config Module with Valid Config

**Command:** `uv run python -c "from bingomatic.config import load_and_validate_config; from pathlib import Path; c = load_and_validate_config(Path('tests/fixtures/valid_config.yaml')); print('Valid config loaded:', c['event_name'])"`

**Output:**

```
Valid config loaded: DevOpsDays Austin 2026
```

**Status:** ✅ PASS

## Proof 3: CLI Implementation

**File:** `src/bingomatic/cli.py`

### Commands Implemented

| Command | Description |
|---------|-------------|
| `bingomatic` | Main CLI group with version option |
| `bingomatic validate` | Validates config file, returns exit code 0/1 |

### Exit Codes

| Code | Condition |
|------|-----------|
| 0 | Configuration valid |
| 1 | Config missing, invalid YAML, or validation errors |

## Summary

All proof artifacts for Task 3.0 verified successfully.

# Tasks: Configuration File Validation

**Spec Reference:** `./docs/specs/01-spec-config-validation/spec.md`

## Summary

Implementation tasks for reading and validating the Bingomatic configuration file from `~/.bingomatic`.

## Spec Coverage

| Spec Item | Task |
|-----------|------|
| US-1: Load Configuration File | 2.0 |
| US-2: Validate Configuration | 2.0 |
| US-3: Handle Missing Configuration | 2.0, 3.0 |
| FR-1 to FR-3: Config Schema | 2.0 |
| FR-4: CLI Interface | 3.0 |
| FR-5 to FR-7: Validation Rules & Errors | 2.0 |
| FR-8: Exit Codes | 3.0 |
| Proof Artifacts | 4.0 |

## Tasks

### [x] 1.0 Project Setup and Dependencies

Initialize the Python project structure with uv, configure pyproject.toml, and install required dependencies (Click, PyYAML).

#### 1.0 Proof Artifact(s)

- CLI: `uv run python -c "import click; import yaml; print('Dependencies OK')"` returns "Dependencies OK"
- File: `pyproject.toml` exists with correct dependencies and entry point configuration

#### 1.0 Tasks

- [x] 1.1 Initialize project with `uv init` in the bingomatic directory
- [x] 1.2 Configure `pyproject.toml` with project metadata, Python 3.12+ requirement, and CLI entry point
- [x] 1.3 Add dependencies: `click` and `pyyaml`
- [x] 1.4 Create source directory structure: `src/bingomatic/`
- [x] 1.5 Create `src/bingomatic/__init__.py` with version info
- [x] 1.6 Verify dependencies install correctly with `uv sync`

**Files to create/modify:**

- `pyproject.toml` - Project configuration and dependencies
- `src/bingomatic/__init__.py` - Package initialization

---

### [x] 2.0 Configuration Loading and Validation Module

Implement the config module that reads `~/.bingomatic`, parses YAML, and validates all required fields with detailed error collection.

#### 2.0 Proof Artifact(s)

- CLI: `uv run python -c "from bingomatic.config import load_config, validate_config; print('Module imports OK')"` succeeds
- Test: Manual validation of config loading with valid/invalid test files

#### 2.0 Tasks

- [x] 2.1 Create `src/bingomatic/config.py` module
- [x] 2.2 Implement `get_config_path()` function to return `~/.bingomatic` path
- [x] 2.3 Implement `load_config()` function to read and parse YAML file
- [x] 2.4 Implement `validate_config()` function with detailed error collection
- [x] 2.5 Add validation for `event_name` field (non-empty string)
- [x] 2.6 Add validation for `logo_location` field (non-empty string)
- [x] 2.7 Add validation for `output_directory` field (non-empty string)
- [x] 2.8 Add validation for `bingo_squares` field (non-empty array)
- [x] 2.9 Implement error message formatting per FR-7 spec

**Files to create/modify:**

- `src/bingomatic/config.py` - Config loading and validation module

---

### [x] 3.0 CLI Interface with Click

Implement the `bingomatic validate` command using Click, integrating with the config module and handling exit codes.

#### 3.0 Proof Artifact(s)

- CLI: `uv run bingomatic validate` with valid `~/.bingomatic` returns "Configuration valid." and exit code 0
- CLI: `uv run bingomatic validate` with missing config returns error message and exit code 1
- Screenshot: `docs/specs/01-spec-config-validation/proofs/valid-config.png`
- Screenshot: `docs/specs/01-spec-config-validation/proofs/invalid-config.png`

#### 3.0 Tasks

- [x] 3.1 Create `src/bingomatic/cli.py` module with Click group
- [x] 3.2 Implement main `bingomatic` CLI entry point
- [x] 3.3 Implement `validate` subcommand
- [x] 3.4 Integrate config loading with missing file detection
- [x] 3.5 Integrate config validation with error display
- [x] 3.6 Implement exit code 0 for success, 1 for failure
- [x] 3.7 Test CLI manually with valid config
- [x] 3.8 Test CLI manually with missing config
- [x] 3.9 Test CLI manually with invalid config
- [x] 3.10 Capture screenshots for proof artifacts

**Files to create/modify:**

- `src/bingomatic/cli.py` - Click CLI implementation
- `pyproject.toml` - Add CLI entry point `[project.scripts]`

---

### [x] 4.0 Unit Tests

Create comprehensive unit tests for config loading, validation rules, and error handling scenarios.

#### 4.0 Proof Artifact(s)

- CLI: `uv run pytest tests/ -v` passes all tests
- Screenshot: `docs/specs/01-spec-config-validation/proofs/test-results.png`

#### 4.0 Tasks

- [x] 4.1 Create `tests/` directory and `tests/__init__.py`
- [x] 4.2 Add `pytest` as dev dependency
- [x] 4.3 Create `tests/test_config.py` with test fixtures
- [x] 4.4 Write test for `get_config_path()` returns correct path
- [x] 4.5 Write test for `load_config()` with valid YAML file
- [x] 4.6 Write test for `load_config()` with missing file
- [x] 4.7 Write test for `load_config()` with invalid YAML syntax
- [x] 4.8 Write test for `validate_config()` with all valid fields
- [x] 4.9 Write test for `validate_config()` with missing required fields
- [x] 4.10 Write test for `validate_config()` with wrong field types
- [x] 4.11 Write test for `validate_config()` with empty bingo_squares array
- [x] 4.12 Write test for multi-error collection (multiple validation failures)
- [x] 4.13 Run full test suite and capture screenshot

**Files to create/modify:**

- `tests/__init__.py` - Test package initialization
- `tests/test_config.py` - Config module unit tests
- `pyproject.toml` - Add pytest dev dependency

---

### [x] 5.0 Documentation Update

Update README with installation, usage, and configuration instructions.

#### 5.0 Proof Artifact(s)

- File: `README.md` contains Installation, Usage, and Configuration sections with complete instructions

#### 5.0 Tasks

- [x] 5.1 Update README.md Installation section with uv instructions
- [x] 5.2 Update README.md Usage section with CLI commands
- [x] 5.3 Update README.md Configuration section with field descriptions
- [x] 5.4 Add example configuration to README.md
- [x] 5.5 Reference `config_template.yaml` in README

**Files to create/modify:**

- `README.md` - Project documentation

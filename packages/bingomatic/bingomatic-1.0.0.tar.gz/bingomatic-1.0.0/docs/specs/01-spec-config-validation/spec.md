# Spec 01: Configuration File Validation

## Overview

Implement configuration file reading and validation for the Bingomatic CLI application. The configuration file is located at `~/.bingomatic` and uses YAML format.

## User Stories

### US-1: Load Configuration File

**As a** user running bingomatic  
**I want** the application to read my configuration from `~/.bingomatic`  
**So that** I can customize my bingo card generation settings

**Acceptance Criteria:**

- Application reads `~/.bingomatic` file on startup
- File is parsed as YAML format
- Configuration values are accessible to the application

### US-2: Validate Configuration

**As a** user  
**I want** clear feedback when my configuration is invalid  
**So that** I can fix any issues before generating cards

**Acceptance Criteria:**

- All required fields are validated for presence
- Missing fields produce clear error messages
- Valid configuration produces success confirmation

### US-3: Handle Missing Configuration

**As a** new user without a configuration file  
**I want** helpful guidance when the config file doesn't exist  
**So that** I know how to create one

**Acceptance Criteria:**

- Application detects missing `~/.bingomatic` file
- Outputs: "Config file missing, please create it using the template and README instructions."
- Exits with non-zero status code

## Functional Requirements

### FR-1: Configuration File Location

- **Path**: `~/.bingomatic` (user's home directory)
- **Format**: YAML

### FR-2: Required Configuration Fields

| Field | Type | Description |
|-------|------|-------------|
| `event_name` | string | Name of the conference/event |
| `logo_location` | string | Path to the logo image file |
| `output_directory` | string | Directory for generated bingo cards |
| `bingo_squares` | array | List of phrases for bingo squares |

### FR-3: Configuration Schema

```yaml
event_name: "DevOpsDays Austin 2026"
logo_location: "/path/to/logo.png"
output_directory: "/path/to/output"
bingo_squares:
  - "Kubernetes"
  - "CI/CD"
  - "Infrastructure as Code"
  - "Observability"
  # ... minimum 24 items for a 5x5 card with free space
```

### FR-4: CLI Interface

- **Library**: Click
- **Command**: `bingomatic validate`
- Validates the configuration file and reports results

### FR-5: Validation Rules

1. Config file must exist at `~/.bingomatic`
2. File must be valid YAML syntax
3. All four required fields must be present
4. `event_name` must be a non-empty string
5. `logo_location` must be a non-empty string
6. `output_directory` must be a non-empty string
7. `bingo_squares` must be an array with at least one item

### FR-6: Error Handling Strategy

**Approach**: Detailed - List all validation errors at once with field names

- Validation collects ALL errors before reporting
- Each error includes the field name and specific issue
- All errors are displayed together for efficient debugging

### FR-7: Error Messages

| Condition | Message |
|-----------|---------|
| File missing | "Config file missing, please create it using the template and README instructions." |
| Invalid YAML | "Config file has invalid YAML syntax: {details}" |
| Missing field | "Missing required field: {field_name}" |
| Invalid field type | "Field '{field_name}' must be a {expected_type}, got {actual_type}" |
| Empty array | "Field 'bingo_squares' must contain at least one item" |

**Example Multi-Error Output:**
```
Configuration validation failed with 2 errors:
  - Missing required field: event_name
  - Field 'bingo_squares' must be an array, got string
```

### FR-8: Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Validation successful |
| 1 | Validation failed |

## Technical Considerations

### Dependencies

- **Python**: 3.12+
- **Package Manager**: uv
- **CLI Framework**: Click
- **YAML Parser**: PyYAML

### Project Structure

```
bingomatic/
├── pyproject.toml
├── README.md
├── src/
│   └── bingomatic/
│       ├── __init__.py
│       ├── cli.py          # Click CLI entry point
│       └── config.py       # Config loading and validation
└── tests/
    └── test_config.py      # Unit tests for config validation
```

## Out of Scope

- Logo file validation (existence, format)
- Output directory validation (existence, permissions)
- Bingo card generation
- Card customization options (colors, fonts)
- Interactive config creation

## Demoable Units

### DU-1: Validate Command with Valid Config

**Steps:**

1. Create valid `~/.bingomatic` file
2. Run `bingomatic validate`
3. Observe success message

**Expected Output:**

```
Configuration valid.
```

### DU-2: Validate Command with Missing Config

**Steps:**

1. Ensure `~/.bingomatic` does not exist
2. Run `bingomatic validate`
3. Observe error message

**Expected Output:**

```
Config file missing, please create it using the template and README instructions.
```

### DU-3: Validate Command with Invalid Config

**Steps:**

1. Create `~/.bingomatic` with missing required field
2. Run `bingomatic validate`
3. Observe specific error message

**Expected Output:**

```
Missing required field: bingo_squares
```

## Proof Artifacts

| Artifact | Description | Location |
|----------|-------------|----------|
| CLI Success Output | Screenshot/terminal output of successful validation | `docs/specs/01-spec-config-validation/proofs/valid-config.png` |
| CLI Error Output | Screenshot/terminal output of validation errors | `docs/specs/01-spec-config-validation/proofs/invalid-config.png` |
| Unit Test Results | Passing test suite output | `docs/specs/01-spec-config-validation/proofs/test-results.png` |

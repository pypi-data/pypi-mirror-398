# 01 Questions Round 1 - Config File Validation

Please answer each question below (select one or more options, or add your own notes). Feel free to add additional context under any question.

## 1. Configuration File Format

What format should the configuration file use?

- [X] (A) YAML - Human-readable, widely used for config files
- [ ] (B) TOML - Python-friendly, explicit and readable
- [ ] (C) JSON - Simple but less human-friendly for editing
- [ ] (D) INI - Simple key-value pairs with sections
- [ ] (E) Other (describe)

## 2. Required Configuration Fields

What information must be present in the config file? (Select all that apply)

- [X] (A) **Bingo phrases/terms** - List of items to populate the bingo squares
- [X] (B) **Logo path** - Path to the logo image file
- [X] (C) **Event name** - Name of the conference/event for the card header
- [X] (D) **Output settings** - File name, output directory, number of cards
- [ ] (E) **Card customization** - Colors, fonts, styling options
- [ ] (F) Other (describe)

## 3. Bingo Phrases Source

How should the bingo phrases/terms be provided?

- [X] (A) Inline in the config file as a list
- [ ] (B) Separate text file referenced by the config
- [ ] (C) Support both inline and external file reference
- [ ] (D) Other (describe)

## 4. Missing Config File Behavior

What should happen if `~/.bingomatic` doesn't exist?

- [X] (A) Exit with error message explaining how to create the config
- [ ] (B) Create a default/sample config file and exit with instructions
- [ ] (C) Prompt user interactively for required values
- [ ] (D) Other (describe)

## 5. Validation Error Handling

How verbose should validation errors be?

- [ ] (A) Simple - Just indicate pass/fail with basic error message
- [X] (B) Detailed - List all validation errors at once with line numbers/field names
- [ ] (C) Progressive - Stop at first error with detailed explanation
- [ ] (D) Other (describe)

## 6. CLI Interface for This Feature

How should the config validation be invoked?

- [X] (A) `bingomatic validate` - Explicit validation subcommand
- [ ] (B) `bingomatic --validate` - Flag on main command
- [ ] (C) Validation runs automatically when generating cards (no separate command)
- [ ] (D) Support both explicit validate command AND automatic validation
- [ ] (E) Other (describe)

## 7. Proof Artifacts

What should demonstrate this feature works correctly?

- [X] (A) CLI output showing successful validation of a valid config
- [X] (B) CLI output showing meaningful error messages for invalid configs
- [X] (C) Unit tests covering validation scenarios
- [ ] (D) All of the above
- [ ] (E) Other (describe)

## 8. Python Version and Dependencies

What Python version and dependency management approach?

- [ ] (A) Python 3.10+ with `pyproject.toml` (modern standard)
- [ ] (B) Python 3.8+ with `requirements.txt` (broad compatibility)
- [X] (C) Python 3.12+ with `uv` for dependency management
- [ ] (D) Other (describe)

---

**Additional Context:**

Please add any other details about the configuration structure, validation requirements, or expected behavior that would help clarify the spec:


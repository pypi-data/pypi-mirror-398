# Task 4.0 Proof Artifacts: CLI Generate Command

## CLI Generate Success

```bash
$ uv run bingomatic generate
Generated 2 bingo cards: /Users/richardboydii/Documents/bingomatic/output/bingo-cards-2025-12-25.pdf
```

## CLI Generate with Missing Logo

```bash
$ uv run bingomatic generate
Logo file not found: /Users/richardboydii/code/bingomatic/logo.png
```

## CLI Help Output

```bash
$ uv run bingomatic --help
Usage: bingomatic [OPTIONS] COMMAND [ARGS]...

  Bingomatic - A bingo card generator for conferences like DevOpsDays.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  generate  Generate bingo card PDF.
  validate  Validate the configuration file.
```

## CLI Tests

```bash
$ uv run pytest tests/test_cli.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 6 items

tests/test_cli.py::TestValidateCommand::test_validate_shows_help PASSED
tests/test_cli.py::TestGenerateCommand::test_generate_shows_help PASSED
tests/test_cli.py::TestGenerateCommand::test_generate_with_missing_config PASSED
tests/test_cli.py::TestGenerateCommand::test_generate_with_missing_logo PASSED
tests/test_cli.py::TestMainGroup::test_main_shows_help PASSED
tests/test_cli.py::TestMainGroup::test_version_option PASSED

============================== 6 passed in 0.21s ===============================
```

## Summary

- ✅ `bingomatic generate` command implemented
- ✅ Config loading and validation works
- ✅ Logo file existence check with user-friendly error
- ✅ Output directory created automatically
- ✅ Date-based filename generation (bingo-cards-YYYY-MM-DD.pdf)
- ✅ Success message displays card count and path
- ✅ Error handling for all FR-8 conditions
- ✅ All 6 CLI tests passing

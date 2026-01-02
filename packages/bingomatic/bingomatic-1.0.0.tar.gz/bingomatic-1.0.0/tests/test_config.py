"""Unit tests for the config module."""

from pathlib import Path

import pytest

from bingomatic.config import (
    ConfigError,
    ConfigFileNotFoundError,
    ConfigValidationError,
    DEFAULT_CARD_COUNT,
    get_card_count,
    get_config_dir,
    get_config_path,
    load_config,
    validate_config,
    load_and_validate_config,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestGetConfigPath:
    """Tests for get_config_path and get_config_dir functions."""

    def test_get_config_dir_returns_home_bingomatic(self):
        """get_config_dir returns ~/.bingomatic/."""
        result = get_config_dir()
        assert result == Path.home() / ".bingomatic"

    def test_get_config_path_returns_config_yaml(self):
        """get_config_path returns ~/.bingomatic/config.yaml."""
        result = get_config_path()
        assert result == Path.home() / ".bingomatic" / "config.yaml"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_with_valid_yaml(self):
        """load_config successfully parses valid YAML file."""
        config_path = FIXTURES_DIR / "valid_config.yaml"
        config = load_config(config_path)

        assert config["event_name"] == "DevOpsDays Austin 2026"
        assert config["logo_location"] == "test_logo.png"
        assert config["output_directory"] == "/path/to/output"
        assert len(config["bingo_squares"]) == 24

    def test_load_config_with_missing_file(self):
        """load_config raises ConfigFileNotFoundError for missing file."""
        config_path = FIXTURES_DIR / "nonexistent.yaml"

        with pytest.raises(ConfigFileNotFoundError) as exc_info:
            load_config(config_path)

        assert "Config file missing" in str(exc_info.value)

    def test_load_config_with_invalid_yaml(self, tmp_path):
        """load_config raises ConfigError for invalid YAML syntax."""
        invalid_yaml = tmp_path / "invalid.yaml"
        invalid_yaml.write_text("event_name: [unclosed bracket")

        with pytest.raises(ConfigError) as exc_info:
            load_config(invalid_yaml)

        assert "invalid YAML syntax" in str(exc_info.value)


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_validate_config_with_all_valid_fields(self):
        """validate_config returns empty list for valid config."""
        config = {
            "event_name": "Test Event",
            "logo_location": "/path/to/logo.png",
            "output_directory": "/path/to/output",
            "bingo_squares": [f"item{i}" for i in range(24)],
        }

        errors = validate_config(config)
        assert errors == []

    def test_validate_config_with_missing_required_fields(self):
        """validate_config returns errors for missing required fields."""
        config = {}

        errors = validate_config(config)

        assert len(errors) == 4
        assert "Missing required field: event_name" in errors
        assert "Missing required field: logo_location" in errors
        assert "Missing required field: output_directory" in errors
        assert "Missing required field: bingo_squares" in errors

    def test_validate_config_with_wrong_field_types(self):
        """validate_config returns errors for wrong field types."""
        config = {
            "event_name": 123,
            "logo_location": ["not", "a", "string"],
            "output_directory": {"wrong": "type"},
            "bingo_squares": "not an array",
        }

        errors = validate_config(config)

        assert len(errors) == 4
        assert any("event_name" in e and "str" in e for e in errors)
        assert any("logo_location" in e and "str" in e for e in errors)
        assert any("output_directory" in e and "str" in e for e in errors)
        assert any("bingo_squares" in e and "list" in e for e in errors)

    def test_validate_config_with_empty_bingo_squares(self):
        """validate_config returns error for empty bingo_squares array."""
        config = {
            "event_name": "Test Event",
            "logo_location": "/path/to/logo.png",
            "output_directory": "/path/to/output",
            "bingo_squares": [],
        }

        errors = validate_config(config)

        assert len(errors) == 1
        assert "must contain at least 24 items" in errors[0]
        assert "got 0" in errors[0]

    def test_validate_config_with_insufficient_bingo_squares(self):
        """validate_config returns error for fewer than 24 bingo_squares."""
        config = {
            "event_name": "Test Event",
            "logo_location": "/path/to/logo.png",
            "output_directory": "/path/to/output",
            "bingo_squares": [f"item{i}" for i in range(23)],
        }

        errors = validate_config(config)

        assert len(errors) == 1
        assert "must contain at least 24 items" in errors[0]
        assert "got 23" in errors[0]

    def test_validate_config_with_exactly_24_bingo_squares(self):
        """validate_config accepts exactly 24 bingo_squares."""
        config = {
            "event_name": "Test Event",
            "logo_location": "/path/to/logo.png",
            "output_directory": "/path/to/output",
            "bingo_squares": [f"item{i}" for i in range(24)],
        }

        errors = validate_config(config)

        assert errors == []

    def test_validate_config_with_empty_string_fields(self):
        """validate_config returns errors for empty string fields."""
        config = {
            "event_name": "",
            "logo_location": "  ",
            "output_directory": "\t",
            "bingo_squares": [f"item{i}" for i in range(24)],
        }

        errors = validate_config(config)

        assert len(errors) == 3
        assert any("event_name" in e and "non-empty" in e for e in errors)
        assert any("logo_location" in e and "non-empty" in e for e in errors)
        assert any("output_directory" in e and "non-empty" in e for e in errors)


class TestValidateConfigMultiError:
    """Tests for multi-error collection in validate_config."""

    def test_multiple_validation_errors_collected(self):
        """validate_config collects multiple errors before returning."""
        config = {
            "event_name": "",
            "bingo_squares": "not an array",
        }

        errors = validate_config(config)

        assert len(errors) >= 3
        assert any("event_name" in e for e in errors)
        assert any("logo_location" in e for e in errors)
        assert any("bingo_squares" in e for e in errors)


class TestConfigValidationError:
    """Tests for ConfigValidationError formatting."""

    def test_single_error_format(self):
        """ConfigValidationError with single error formats correctly."""
        error = ConfigValidationError(["Missing required field: event_name"])

        assert str(error) == "Missing required field: event_name"

    def test_multiple_error_format(self):
        """ConfigValidationError with multiple errors formats correctly."""
        error = ConfigValidationError(
            [
                "Missing required field: event_name",
                "Field 'bingo_squares' must be a list, got str",
            ]
        )

        error_str = str(error)
        assert "Configuration validation failed with 2 errors:" in error_str
        assert "Missing required field: event_name" in error_str
        assert "bingo_squares" in error_str


class TestLoadAndValidateConfig:
    """Tests for load_and_validate_config function."""

    def test_load_and_validate_with_valid_config(self):
        """load_and_validate_config returns config dict for valid file."""
        config_path = FIXTURES_DIR / "valid_config.yaml"
        config = load_and_validate_config(config_path)

        assert config["event_name"] == "DevOpsDays Austin 2026"

    def test_load_and_validate_with_missing_file(self):
        """load_and_validate_config raises ConfigFileNotFoundError."""
        config_path = FIXTURES_DIR / "nonexistent.yaml"

        with pytest.raises(ConfigFileNotFoundError):
            load_and_validate_config(config_path)

    def test_load_and_validate_with_invalid_config(self, tmp_path):
        """load_and_validate_config raises ConfigValidationError for invalid config."""
        invalid_config = tmp_path / "invalid_config.yaml"
        invalid_config.write_text("event_name: ''")

        with pytest.raises(ConfigValidationError) as exc_info:
            load_and_validate_config(invalid_config)

        assert len(exc_info.value.errors) >= 1


class TestCardCountValidation:
    """Tests for card_count field validation."""

    def _valid_base_config(self) -> dict:
        """Return a valid base config for testing card_count."""
        return {
            "event_name": "Test Event",
            "logo_location": "/path/to/logo.png",
            "output_directory": "/path/to/output",
            "bingo_squares": [f"item{i}" for i in range(24)],
        }

    def test_validate_config_with_valid_card_count(self):
        """validate_config accepts valid positive integer card_count."""
        config = self._valid_base_config()
        config["card_count"] = 10

        errors = validate_config(config)
        assert errors == []

    def test_validate_config_without_card_count(self):
        """validate_config accepts config without card_count (optional field)."""
        config = self._valid_base_config()

        errors = validate_config(config)
        assert errors == []

    def test_validate_config_with_string_card_count(self):
        """validate_config rejects string card_count."""
        config = self._valid_base_config()
        config["card_count"] = "invalid"

        errors = validate_config(config)
        assert len(errors) == 1
        assert "card_count" in errors[0]
        assert "integer" in errors[0]

    def test_validate_config_with_zero_card_count(self):
        """validate_config rejects zero card_count."""
        config = self._valid_base_config()
        config["card_count"] = 0

        errors = validate_config(config)
        assert len(errors) == 1
        assert "positive integer" in errors[0]

    def test_validate_config_with_negative_card_count(self):
        """validate_config rejects negative card_count."""
        config = self._valid_base_config()
        config["card_count"] = -5

        errors = validate_config(config)
        assert len(errors) == 1
        assert "positive integer" in errors[0]

    def test_validate_config_with_float_card_count(self):
        """validate_config rejects float card_count."""
        config = self._valid_base_config()
        config["card_count"] = 3.5

        errors = validate_config(config)
        assert len(errors) == 1
        assert "integer" in errors[0]

    def test_validate_config_with_bool_card_count(self):
        """validate_config rejects boolean card_count."""
        config = self._valid_base_config()
        config["card_count"] = True

        errors = validate_config(config)
        assert len(errors) == 1
        assert "integer" in errors[0]


class TestGetCardCount:
    """Tests for get_card_count helper function."""

    def test_get_card_count_returns_value_when_present(self):
        """get_card_count returns the configured value."""
        config = {"card_count": 10}
        assert get_card_count(config) == 10

    def test_get_card_count_returns_default_when_missing(self):
        """get_card_count returns default when card_count not in config."""
        config = {}
        assert get_card_count(config) == DEFAULT_CARD_COUNT

    def test_default_card_count_is_two(self):
        """DEFAULT_CARD_COUNT is 2."""
        assert DEFAULT_CARD_COUNT == 2

# Task 1.0 Proof Artifacts: Extend Configuration for Card Count

## CLI Validation with card_count

### Valid card_count

```bash
$ uv run bingomatic validate
Configuration valid.
```

Config file (`~/.bingomatic/config.yaml`) contains:
```yaml
event_name: "DevOpsDays Austin 2026"
logo_location: "/Users/richardboydii/code/bingomatic/logo.png"
output_directory: "/Users/richardboydii/Documents/bingomatic/output"
bingo_squares: [
  "An open source contributor",
  "Uses Kubernetes in prod",
  "Uses AWS",
  "Uses GCP",
  "Uses Azure",
  "Codes in Python",
  "Codes in Golang",
  "Uses Fish shell",
  "Has a Raspberry Pi",
  "First DevOpsDays",
]
```

## Test Results

```bash
$ uv run pytest tests/test_config.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 26 items

tests/test_config.py::TestGetConfigPath::test_get_config_dir_returns_home_bingomatic PASSED
tests/test_config.py::TestGetConfigPath::test_get_config_path_returns_config_yaml PASSED
tests/test_config.py::TestLoadConfig::test_load_config_with_valid_yaml PASSED
tests/test_config.py::TestLoadConfig::test_load_config_with_missing_file PASSED
tests/test_config.py::TestLoadConfig::test_load_config_with_invalid_yaml PASSED
tests/test_config.py::TestValidateConfig::test_validate_config_with_all_valid_fields PASSED
tests/test_config.py::TestValidateConfig::test_validate_config_with_missing_required_fields PASSED
tests/test_config.py::TestValidateConfig::test_validate_config_with_wrong_field_types PASSED
tests/test_config.py::TestValidateConfig::test_validate_config_with_empty_bingo_squares PASSED
tests/test_config.py::TestValidateConfig::test_validate_config_with_empty_string_fields PASSED
tests/test_config.py::TestValidateConfigMultiError::test_multiple_validation_errors_collected PASSED
tests/test_config.py::TestConfigValidationError::test_single_error_format PASSED
tests/test_config.py::TestConfigValidationError::test_multiple_error_format PASSED
tests/test_config.py::TestLoadAndValidateConfig::test_load_and_validate_with_valid_config PASSED
tests/test_config.py::TestLoadAndValidateConfig::test_load_and_validate_with_missing_file PASSED
tests/test_config.py::TestLoadAndValidateConfig::test_load_and_validate_with_invalid_config PASSED
tests/test_config.py::TestCardCountValidation::test_validate_config_with_valid_card_count PASSED
tests/test_config.py::TestCardCountValidation::test_validate_config_without_card_count PASSED
tests/test_config.py::TestCardCountValidation::test_validate_config_with_string_card_count PASSED
tests/test_config.py::TestCardCountValidation::test_validate_config_with_zero_card_count PASSED
tests/test_config.py::TestCardCountValidation::test_validate_config_with_negative_card_count PASSED
tests/test_config.py::TestCardCountValidation::test_validate_config_with_float_card_count PASSED
tests/test_config.py::TestCardCountValidation::test_validate_config_with_bool_card_count PASSED
tests/test_config.py::TestGetCardCount::test_get_card_count_returns_value_when_present PASSED
tests/test_config.py::TestGetCardCount::test_get_card_count_returns_default_when_missing PASSED
tests/test_config.py::TestGetCardCount::test_default_card_count_is_two PASSED

============================== 26 passed in 0.07s ==============================
```

## Summary

- ✅ `card_count` field added to config_template.yaml
- ✅ Validation accepts valid positive integers
- ✅ Validation rejects invalid types (string, float, bool)
- ✅ Validation rejects zero and negative values
- ✅ Default value of 2 used when field is missing
- ✅ All 26 tests passing

# Proof Artifacts: Card Content Population (Spec 03)

## Task 1.0: Register Custom Fonts

### Font Files Installed

```
$ ls -la src/bingomatic/fonts/
total 2264
-rw-r--r--  514260 Roboto-Bold.ttf
-rw-r--r--  515100 Roboto-Regular.ttf
-rw-r--r--  125748 RobotoMono-Regular.ttf
```

### Font Registration Tests

```
$ uv run pytest tests/test_pdf.py::TestFontRegistration -v
tests/test_pdf.py::TestFontRegistration::test_fonts_directory_exists PASSED
tests/test_pdf.py::TestFontRegistration::test_roboto_regular_font_exists PASSED
tests/test_pdf.py::TestFontRegistration::test_roboto_bold_font_exists PASSED
tests/test_pdf.py::TestFontRegistration::test_roboto_mono_font_exists PASSED
tests/test_pdf.py::TestFontRegistration::test_register_fonts_does_not_raise PASSED
tests/test_pdf.py::TestFontRegistration::test_register_fonts_is_idempotent PASSED

6 passed
```

---

## Task 2.0: Configuration Validation (24-Item Minimum)

### Validation Error Output

```
$ uv run bingomatic validate  # with config having <24 items
Field 'bingo_squares' must contain at least 24 items, got 10
```

### Validation Tests

```
$ uv run pytest tests/test_config.py::TestValidateConfig -v
tests/test_config.py::TestValidateConfig::test_validate_config_with_all_valid_fields PASSED
tests/test_config.py::TestValidateConfig::test_validate_config_with_missing_required_fields PASSED
tests/test_config.py::TestValidateConfig::test_validate_config_with_wrong_field_types PASSED
tests/test_config.py::TestValidateConfig::test_validate_config_with_empty_bingo_squares PASSED
tests/test_config.py::TestValidateConfig::test_validate_config_with_insufficient_bingo_squares PASSED
tests/test_config.py::TestValidateConfig::test_validate_config_with_exactly_24_bingo_squares PASSED
tests/test_config.py::TestValidateConfig::test_validate_config_with_empty_string_fields PASSED

7 passed
```

---

## Task 3.0: Square Text Rendering

### Random Selection Tests

```
$ uv run pytest tests/test_pdf.py::TestSelectRandomSquares -v
tests/test_pdf.py::TestSelectRandomSquares::test_returns_24_items_by_default PASSED
tests/test_pdf.py::TestSelectRandomSquares::test_returns_unique_items PASSED
tests/test_pdf.py::TestSelectRandomSquares::test_returns_different_results_on_multiple_calls PASSED
tests/test_pdf.py::TestSelectRandomSquares::test_respects_custom_count PASSED

4 passed
```

### Implementation Details

- `select_random_squares()`: Uses `random.sample()` for unique selection
- `_fit_text_in_square()`: Word-wrap + auto-shrink from 12pt to 6pt minimum
- `_draw_square_text()`: Centers text using Roboto Mono font
- `_draw_card_squares()`: Populates 24 squares, skips center (index 12)

---

## Task 4.0: Participant Name Field

### Implementation Details

- `_draw_name_field()`: Draws "Name:" label with Roboto font
- Position: 18pt (0.25 inch) below grid
- Underline: Spans from after label to grid right edge

---

## Task 5.0: Test Fixtures Updated

### Fixture Changes

```yaml
# tests/fixtures/valid_config.yaml
logo_location: "test_logo.png"  # Updated from /path/to/logo.png
bingo_squares:  # 24 items (up from 4)
  - "Kubernetes"
  - "CI/CD"
  # ... 22 more items
```

### Full Test Suite

```
$ uv run pytest tests/ -v
62 passed
```

---

## Summary

| Task | Status | Tests |
|------|--------|-------|
| 1.0 Font Registration | ✅ Complete | 6 tests |
| 2.0 Validation Update | ✅ Complete | 7 tests |
| 3.0 Square Text Rendering | ✅ Complete | 4 tests |
| 4.0 Name Field | ✅ Complete | integrated |
| 5.0 Test Fixtures | ✅ Complete | 62 total |

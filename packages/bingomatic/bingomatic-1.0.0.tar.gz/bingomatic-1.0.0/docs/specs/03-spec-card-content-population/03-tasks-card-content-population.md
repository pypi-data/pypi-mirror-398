# Tasks: Card Content Population

**Spec**: `03-spec-card-content-population/spec.md`
**Status**: Complete

## Overview

Implementation tasks for populating bingo card squares with random items, adding participant name fields, and updating test fixtures.

## Relevant Files

### Files to Create

| File | Purpose |
|------|---------|
| `src/bingomatic/fonts/` | Directory for bundled font files |
| `src/bingomatic/fonts/Roboto-Regular.ttf` | Roboto font for header/footer |
| `src/bingomatic/fonts/Roboto-Bold.ttf` | Roboto Bold for header |
| `src/bingomatic/fonts/RobotoMono-Regular.ttf` | Roboto Mono for square text |
| `tests/test_pdf.py` | Unit tests for PDF generation |

### Files to Modify

| File | Changes |
|------|---------|
| `src/bingomatic/pdf.py` | Font registration, square text rendering, name field |
| `src/bingomatic/config.py` | Update bingo_squares validation (24 minimum) |
| `src/bingomatic/cli.py` | Pass bingo_squares to generate_pdf |
| `tests/fixtures/valid_config.yaml` | Update logo_location to test_logo.png, add 24 items |
| `tests/test_config.py` | Update tests for new 24-item minimum |

## Tasks

### [x] 1.0 Register Custom Fonts (Roboto & Roboto Mono)

Set up Roboto and Roboto Mono fonts for use with ReportLab PDF generation. This is foundational for all text rendering tasks.

**Traces to**: FR-3 (Font Specifications)

#### 1.0 Proof Artifact(s)

- Test: Unit test confirming fonts are registered and available in ReportLab
- Screenshot: `03-proofs/font-registration-test.png` showing passing font test

#### 1.0 Tasks

- [x] 1.1 Create `src/bingomatic/fonts/` directory
- [x] 1.2 Download Roboto-Regular.ttf, Roboto-Bold.ttf from Google Fonts
- [x] 1.3 Download RobotoMono-Regular.ttf from Google Fonts
- [x] 1.4 Add `register_fonts()` function to `pdf.py` that registers fonts with ReportLab's `pdfmetrics`
- [x] 1.5 Call `register_fonts()` at module load or in `generate_pdf()`
- [x] 1.6 Create `tests/test_pdf.py` with test for font registration
- [x] 1.7 Verify fonts work by running test: `uv run pytest tests/test_pdf.py -v`
- [x] 1.8 Capture proof artifact screenshot

---

### [x] 2.0 Update Configuration Validation for 24-Item Minimum

Modify `bingo_squares` validation to require at least 24 items instead of 1. Update related tests.

**Traces to**: US-3, FR-6, FR-7

#### 2.0 Proof Artifact(s)

- CLI: `uv run bingomatic validate` with <24 items shows error message
- Screenshot: `03-proofs/validation-error.png` showing "must contain at least 24 items" error
- Test: `uv run pytest tests/test_config.py -v` passes with updated validation tests

#### 2.0 Tasks

- [x] 2.1 Update `validate_config()` in `config.py`: change `len(value) == 0` to `len(value) < 24`
- [x] 2.2 Update error message to: "Field 'bingo_squares' must contain at least 24 items, got {count}"
- [x] 2.3 Update `test_validate_config_with_empty_bingo_squares` test for new 24-item requirement
- [x] 2.4 Add test for exactly 24 items (should pass)
- [x] 2.5 Add test for 23 items (should fail with specific count in message)
- [x] 2.6 Run validation tests: `uv run pytest tests/test_config.py -v`
- [x] 2.7 Test CLI with <24 items config and capture proof screenshot

---

### [x] 3.0 Implement Square Text Rendering

Populate 24 grid squares with random items from `bingo_squares`. Implement text fitting with word-wrap and auto-shrink using Roboto Mono font.

**Traces to**: US-1, FR-1, FR-2, FR-4

#### 3.0 Proof Artifact(s)

- PDF: `03-proofs/sample-cards.pdf` showing populated squares with readable text
- Screenshot: `03-proofs/populated-squares.png` showing text in squares with center logo preserved
- Test: Unit test for random selection ensuring 24 unique items per card

#### 3.0 Tasks

- [x] 3.1 Add `select_random_squares(bingo_squares: list, count: int = 24) -> list` function to `pdf.py`
- [x] 3.2 Implement using `random.sample()` for unique selection without replacement
- [x] 3.3 Add `_fit_text_in_square(text: str, max_width: float, max_height: float) -> tuple[str, float]` helper
- [x] 3.4 Implement word-wrap logic: split text on spaces, build lines that fit width
- [x] 3.5 Implement auto-shrink: start at base font size, reduce until text fits (min 6pt)
- [x] 3.6 Add `_draw_square_text(canvas, text, x, y)` function using Roboto Mono
- [x] 3.7 Update `generate_pdf()` signature to accept `bingo_squares: list` parameter
- [x] 3.8 Update `cli.py` to pass `config["bingo_squares"]` to `generate_pdf()`
- [x] 3.9 Integrate square text drawing into `generate_pdf()` loop (skip center square index 12)
- [x] 3.10 Add unit test for `select_random_squares()` ensuring 24 unique items
- [x] 3.11 Generate test PDF and capture proof artifacts

---

### [x] 4.0 Add Participant Name Field

Add "Name: _______________" below each bingo grid, spanning the full width of the grid, using Roboto font.

**Traces to**: US-2, FR-5

#### 4.0 Proof Artifact(s)

- PDF: `03-proofs/sample-cards.pdf` showing name field below each grid
- Screenshot: `03-proofs/name-field.png` showing name field format and positioning

#### 4.0 Tasks

- [x] 4.1 Add `_draw_name_field(canvas, grid_x, grid_y)` function to `pdf.py`
- [x] 4.2 Position name field 18pt (0.25 inch) below grid bottom
- [x] 4.3 Draw "Name:" label using Roboto font (12pt)
- [x] 4.4 Draw underline spanning from after "Name:" to grid right edge
- [x] 4.5 Call `_draw_name_field()` for each grid in `generate_pdf()`
- [x] 4.6 Generate test PDF and capture proof screenshot

---

### [x] 5.0 Update Test Fixtures and Verify Unique Cards

Update test fixtures to use `test_logo.png`, update tests for new validation rules, and verify card uniqueness.

**Traces to**: US-1 (uniqueness), FR-8, DU-4

#### 5.0 Proof Artifact(s)

- Test: `uv run pytest tests/ -v` all tests pass
- Screenshot: `03-proofs/test-results.png` showing passing test suite
- Screenshot: `03-proofs/unique-cards.png` showing multiple cards with different arrangements

#### 5.0 Tasks

- [x] 5.1 Update `tests/fixtures/valid_config.yaml`: set `logo_location` to project's `test_logo.png`
- [x] 5.2 Update `tests/fixtures/valid_config.yaml`: add 24 bingo_squares items
- [x] 5.3 Update any test helper functions that reference logo paths
- [x] 5.4 Update `_valid_base_config()` in `test_config.py` to include 24 items
- [x] 5.5 Add test verifying each generated card has unique arrangement (compare 2+ cards)
- [x] 5.6 Run full test suite: `uv run pytest tests/ -v`
- [x] 5.7 Generate 4+ cards and capture proof screenshot showing unique arrangements
- [x] 5.8 Capture test results screenshot

---

## Spec Coverage Matrix

| Spec Item | Task(s) |
|-----------|---------|
| US-1: Populate Squares | 3.0, 5.0 |
| US-2: Name Field | 4.0 |
| US-3: Validation | 2.0 |
| FR-1: Random Selection | 3.0 |
| FR-2: Grid Layout | 3.0 |
| FR-3: Fonts | 1.0 |
| FR-4: Text Rendering | 3.0 |
| FR-5: Name Field | 4.0 |
| FR-6: Validation Update | 2.0 |
| FR-7: Error Messages | 2.0 |
| FR-8: Test Fixtures | 5.0 |

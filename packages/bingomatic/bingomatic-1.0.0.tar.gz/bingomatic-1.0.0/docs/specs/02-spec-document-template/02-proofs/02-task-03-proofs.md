# Task 3.0 Proof Artifacts: Event Branding Elements

## PDF Generation Tests with Branding

```bash
$ uv run pytest tests/test_pdf.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 18 items

tests/test_pdf.py::TestConstants::test_square_size_is_one_inch PASSED
tests/test_pdf.py::TestConstants::test_grid_size_is_five PASSED
tests/test_pdf.py::TestConstants::test_gap_is_half_inch PASSED
tests/test_pdf.py::TestConstants::test_grid_total_is_five_inches PASSED
tests/test_pdf.py::TestCalculateGridPositions::test_returns_four_values PASSED
tests/test_pdf.py::TestCalculateGridPositions::test_grids_are_horizontally_centered PASSED
tests/test_pdf.py::TestCalculateGridPositions::test_grids_have_correct_gap PASSED
tests/test_pdf.py::TestCalculateGridPositions::test_grids_have_same_y_position PASSED
tests/test_pdf.py::TestGeneratePdf::test_generates_pdf_file PASSED
tests/test_pdf.py::TestGeneratePdf::test_generates_correct_page_count_even PASSED
tests/test_pdf.py::TestGeneratePdf::test_generates_correct_page_count_odd PASSED
tests/test_pdf.py::TestGeneratePdf::test_generates_single_page_for_two_cards PASSED
tests/test_pdf.py::TestGeneratePdf::test_generates_single_page_for_one_card PASSED
tests/test_pdf.py::TestGeneratePdf::test_accepts_path_object PASSED
tests/test_pdf.py::TestGeneratePdf::test_accepts_string_path PASSED
tests/test_pdf.py::TestGeneratePdf::test_generates_pdf_with_event_name PASSED
tests/test_pdf.py::TestGeneratePdf::test_generates_pdf_with_logo PASSED
tests/test_pdf.py::TestGeneratePdf::test_raises_error_for_missing_logo PASSED

============================== 18 passed in 0.11s ==============================
```

## Generated PDF with Branding

- **File**: `with-branding.pdf` (in this directory)
- **Contents**: 4 bingo cards with event branding
- **Branding elements**:
  - Event name "DevOpsDays Austin 2026" centered above each grid
  - Logo displayed in center square (row 3, col 3)
  - Logo scaled to fit with aspect ratio preserved

## Branding Implementation

- `_draw_event_name()`: Draws event name centered above grid using Helvetica-Bold 14pt
- `_draw_logo()`: Draws logo in center square with padding and aspect ratio preservation
- Error handling: FileNotFoundError raised for missing logo files

## Summary

- ✅ Event name renders above each grid
- ✅ Logo renders in center square with proper scaling
- ✅ Missing logo raises FileNotFoundError
- ✅ All 18 tests passing
- ✅ Proof PDF generated: `with-branding.pdf`

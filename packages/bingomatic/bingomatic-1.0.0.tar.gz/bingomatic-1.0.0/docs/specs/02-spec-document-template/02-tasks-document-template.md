# Tasks: PDF Document Template Generation

**Spec Reference:** `./docs/specs/02-spec-document-template/spec.md`

## Analysis Summary

### Spec-to-Task Mapping

| Spec Element | Covered By |
|--------------|------------|
| US-1: Generate Bingo Card Template | Tasks 2.0, 4.0 |
| US-2: Display Event Branding | Task 3.0 |
| US-3: Configure Card Quantity | Task 1.0 |
| US-4: Save to Output Directory | Task 4.0 |
| FR-1 to FR-4: PDF Layout & Rendering | Task 2.0 |
| FR-5: Configuration Schema Update | Task 1.0 |
| FR-6 to FR-9: CLI & Error Handling | Task 4.0 |

### Files to be Modified/Created

- `pyproject.toml` - Add ReportLab dependency
- `src/bingomatic/config.py` - Add card_count validation
- `src/bingomatic/pdf.py` - NEW: PDF generation module
- `src/bingomatic/cli.py` - Add generate command
- `tests/test_config.py` - Add card_count tests
- `tests/test_pdf.py` - NEW: PDF generation tests
- `config_template.yaml` - Add card_count field

## Tasks

### [x] 1.0 Extend Configuration for Card Count

Add optional `card_count` field to configuration schema with validation and default value.

**Covers:** US-3, FR-5

#### 1.0 Proof Artifact(s)

- CLI: `uv run bingomatic validate` with config containing `card_count: 4` returns "Configuration valid." demonstrates new field is accepted
- CLI: `uv run bingomatic validate` with config containing `card_count: "invalid"` returns type error demonstrates validation works
- Test: `uv run pytest tests/test_config.py -v` passes demonstrates card_count validation is tested

#### 1.0 Tasks

- [x] 1.1 Update `config_template.yaml` to include `card_count: 2` field with comment
- [x] 1.2 Update `validate_config()` in `config.py` to validate `card_count` as optional positive integer with default 2
- [x] 1.3 Add helper function `get_card_count(config)` that returns validated card_count or default
- [x] 1.4 Add unit tests in `test_config.py` for card_count validation (valid int, invalid type, missing field uses default, zero/negative rejected)
- [x] 1.5 Run `uv run pytest tests/test_config.py -v` and verify all tests pass
- [x] 1.6 Run `uv run bingomatic validate` with config containing `card_count: 4` and capture proof

---

### [x] 2.0 Implement PDF Grid Rendering

Create PDF generation module that renders 5×5 grids with correct measurements (1" squares, 0.5" gap between grids, 2 grids per landscape page).

**Covers:** US-1, FR-1, FR-2, FR-3 (grid lines only)

#### 2.0 Proof Artifact(s)

- File: Generated PDF at `docs/specs/02-spec-document-template/02-proofs/grid-only.pdf` demonstrates grid rendering works
- Screenshot: `docs/specs/02-spec-document-template/02-proofs/measurement.png` showing PDF viewer ruler confirming 1" square size demonstrates correct measurements
- Test: `uv run pytest tests/test_pdf.py -v` passes demonstrates PDF generation is tested

#### 2.0 Tasks

- [x] 2.1 Add `reportlab` dependency to `pyproject.toml` and run `uv sync`
- [x] 2.2 Create `src/bingomatic/pdf.py` with module docstring and imports (reportlab.lib.pagesizes, reportlab.pdfgen.canvas)
- [x] 2.3 Define constants: `SQUARE_SIZE = 72` (1 inch in points), `GRID_SIZE = 5`, `GAP = 36` (0.5 inch)
- [x] 2.4 Implement `draw_grid(canvas, x, y)` function that draws a 5×5 grid of 1" squares at given position
- [x] 2.5 Implement `calculate_grid_positions(page_width, page_height)` returning (left_x, left_y, right_x, right_y) for centered grids with 0.5" gap
- [x] 2.6 Implement `generate_pdf(output_path, card_count)` that creates landscape PDF with empty grids (no branding yet)
- [x] 2.7 Create `tests/test_pdf.py` with tests for grid positioning calculations
- [x] 2.8 Add integration test that generates a PDF and verifies file exists and has correct page count
- [x] 2.9 Generate test PDF and manually verify grid measurements in PDF viewer
- [x] 2.10 Save proof artifact: `docs/specs/02-spec-document-template/02-proofs/grid-only.pdf`

---

### [x] 3.0 Add Event Branding Elements

Add event name header above each grid and logo in center square with proper scaling.

**Covers:** US-2, FR-3 (event name, logo), FR-4

#### 3.0 Proof Artifact(s)

- File: Generated PDF at `docs/specs/02-spec-document-template/02-proofs/with-branding.pdf` demonstrates branding elements render correctly
- Screenshot: `docs/specs/02-spec-document-template/02-proofs/branding-detail.png` showing event name and logo placement demonstrates visual requirements met

#### 3.0 Tasks

- [x] 3.1 Implement `draw_event_name(canvas, text, grid_x, grid_y)` that draws event name centered above grid
- [x] 3.2 Implement `draw_logo(canvas, logo_path, grid_x, grid_y)` that draws logo in center square (row 3, col 3) with aspect ratio preservation
- [x] 3.3 Update `draw_grid()` to accept optional `event_name` and `logo_path` parameters
- [x] 3.4 Update `generate_pdf()` signature to accept `event_name` and `logo_path` from config
- [x] 3.5 Add error handling for logo file not found and unreadable cases
- [x] 3.6 Add unit tests for logo scaling calculations
- [x] 3.7 Generate test PDF with event name and logo, verify visual placement
- [x] 3.8 Save proof artifact: `docs/specs/02-spec-document-template/02-proofs/with-branding.pdf`

---

### [x] 4.0 Implement CLI Generate Command

Wire up `bingomatic generate` command with config loading, logo validation, output directory creation, and success/error messaging.

**Covers:** US-4, FR-6, FR-7, FR-8, FR-9

#### 4.0 Proof Artifact(s)

- CLI: `uv run bingomatic generate` with valid config outputs "Generated N bingo cards: /path/to/file.pdf" demonstrates end-to-end success flow
- CLI: `uv run bingomatic generate` with missing logo outputs "Logo file not found: /path" demonstrates error handling
- Screenshot: `docs/specs/02-spec-document-template/02-proofs/cli-success.png` showing terminal output demonstrates CLI integration complete

#### 4.0 Tasks

- [x] 4.1 Add `generate` command to `cli.py` using Click decorator pattern
- [x] 4.2 Implement config loading and validation in generate command (reuse `load_and_validate_config`)
- [x] 4.3 Add logo file existence check with `LogoFileNotFoundError` exception and user-friendly message
- [x] 4.4 Implement output directory creation using `Path.mkdir(parents=True, exist_ok=True)`
- [x] 4.5 Generate output filename with current date: `bingo-cards-YYYY-MM-DD.pdf`
- [x] 4.6 Call `generate_pdf()` with config values and output path
- [x] 4.7 Display success message: "Generated N bingo cards: /path/to/file.pdf"
- [x] 4.8 Implement error handling for all FR-8 error conditions with correct exit codes
- [x] 4.9 Add CLI integration tests for success and error cases
- [x] 4.10 Run `uv run bingomatic generate` with valid config and capture CLI output proof

---

### [x] 5.0 Complete Test Suite and Proof Artifacts

Finalize unit tests for all components and collect proof artifacts for spec validation.

**Covers:** All user stories (verification)

#### 5.0 Proof Artifact(s)

- CLI: `uv run pytest tests/ -v` all tests pass demonstrates implementation is tested
- File: `docs/specs/02-spec-document-template/02-proofs/sample-output.pdf` final generated PDF demonstrates complete feature
- Screenshot: `docs/specs/02-spec-document-template/02-proofs/test-results.png` showing pytest output demonstrates test coverage

#### 5.0 Tasks

- [x] 5.1 Review test coverage for `config.py` changes (card_count validation)
- [x] 5.2 Review test coverage for `pdf.py` (grid rendering, branding, page count)
- [x] 5.3 Review test coverage for `cli.py` generate command (success and error paths)
- [x] 5.4 Run full test suite: `uv run pytest tests/ -v` and verify all pass
- [x] 5.5 Create `docs/specs/02-spec-document-template/02-proofs/` directory
- [x] 5.6 Generate final sample PDF and save as `02-proofs/sample-output.pdf`
- [x] 5.7 Capture measurement screenshot showing 1" squares and save as `02-proofs/measurement.png`
- [x] 5.8 Capture CLI success output screenshot and save as `02-proofs/cli-success.png`
- [x] 5.9 Capture pytest results screenshot and save as `02-proofs/test-results.png`
- [x] 5.10 Update README.md with `bingomatic generate` command documentation

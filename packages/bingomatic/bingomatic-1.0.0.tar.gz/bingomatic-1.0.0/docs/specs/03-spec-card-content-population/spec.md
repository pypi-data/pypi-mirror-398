# Spec 03: Card Content Population

## Overview

Populate bingo card squares with random items from the `bingo_squares` configuration, add a participant name field at the bottom of each card, and update test fixtures to use the `test_logo.png` file.

## User Stories

### US-1: Populate Bingo Squares with Random Items

**As a** conference organizer generating bingo cards  
**I want** each card's squares filled with random items from my configured list  
**So that** participants have unique cards for actual bingo gameplay

**Acceptance Criteria:**

- Each card displays 24 randomly selected items from `bingo_squares`
- No duplicate items appear within a single card
- Center square remains reserved for the logo (not populated with text)
- Each generated card has a unique random arrangement

### US-2: Participant Name Field

**As a** conference organizer  
**I want** a name field printed at the bottom of each bingo card  
**So that** participants can write their name and cards can be identified

**Acceptance Criteria:**

- "Name: _______________" appears below each bingo grid
- The name field spans the full width of the grid
- Line is visible for participants to write on

### US-3: Minimum Bingo Squares Validation

**As a** user configuring bingomatic  
**I want** validation that I have enough bingo squares configured  
**So that** I don't generate incomplete cards

**Acceptance Criteria:**

- Configuration validation requires at least 24 items in `bingo_squares`
- Clear error message if fewer than 24 items provided
- Validation occurs during both `validate` and `generate` commands

## Functional Requirements

### FR-1: Random Item Selection

- Select 24 unique items from `bingo_squares` for each card
- Use `random.sample()` or equivalent for selection without replacement
- Each card must have a different random selection/arrangement
- Center square (row 2, col 2, 0-indexed) is excluded from text population

### FR-2: Grid Population Layout

| Position | Content |
|----------|---------|
| Squares 1-12 | Random bingo items |
| Center Square | Logo image (existing behavior) |
| Squares 14-25 | Random bingo items |

Grid positions (row-major order, 0-indexed):
```
[ 0][ 1][ 2][ 3][ 4]
[ 5][ 6][ 7][ 8][ 9]
[10][11][XX][13][14]   <- XX = center logo
[15][16][17][18][19]
[20][21][22][23][24]
```

### FR-3: Font Specifications

| Element | Font | Notes |
|---------|------|-------|
| Bingo square text | Roboto Mono | Monospace for consistent character width |
| Event name (header) | Roboto | Above each grid |
| Name field (footer) | Roboto | Below each grid |

**Font Files**: Roboto and Roboto Mono are Google Fonts. Implementation should either:
- Bundle TTF files with the project, or
- Use ReportLab's font registration to load from system/bundled fonts

### FR-4: Text Rendering in Squares

- **Font**: Roboto Mono
- **Word-wrap**: Text wraps to multiple lines within the 1-inch square
- **Auto-shrink**: Font size reduces to fit text within square bounds
- **Centering**: Text is centered both horizontally and vertically within each square
- **Minimum font size**: Define a reasonable minimum (e.g., 6pt) to maintain legibility

### FR-5: Name Field Specification

| Property | Value |
|----------|-------|
| Label | "Name:" |
| Format | "Name: _______________" |
| Position | Below grid, spanning full grid width |
| Spacing | Adequate margin below grid (e.g., 0.25 inch) |

### FR-6: Configuration Validation Update

Current validation (in `config.py`):
```python
# Current: requires at least 1 item
elif expected_type == list and len(value) == 0:
    errors.append(f"Field 'bingo_squares' must contain at least one item")
```

Updated validation:
```python
# New: requires at least 24 items
elif expected_type == list and len(value) < 24:
    errors.append(f"Field 'bingo_squares' must contain at least 24 items, got {len(value)}")
```

### FR-7: Error Messages

| Condition | Message |
|-----------|---------|
| Insufficient squares | "Field 'bingo_squares' must contain at least 24 items, got {count}" |

### FR-8: Test Fixture Updates

Update all test fixtures and hardcoded logo paths to use the project's `test_logo.png`:

| File | Change |
|------|--------|
| `tests/fixtures/valid_config.yaml` | `logo_location: "{project_root}/test_logo.png"` |
| Any hardcoded test paths | Update to reference `test_logo.png` |

## Technical Considerations

### Dependencies

- **Python**: 3.12+ (existing)
- **ReportLab**: 4.0+ (existing) - for PDF text rendering
- **random**: stdlib - for random selection

### Files to Modify

| File | Changes |
|------|---------|
| `src/bingomatic/pdf.py` | Add square text rendering, name field drawing |
| `src/bingomatic/config.py` | Update minimum `bingo_squares` validation |
| `src/bingomatic/cli.py` | Pass `bingo_squares` to PDF generation |
| `tests/fixtures/valid_config.yaml` | Update `logo_location` to use `test_logo.png` |
| `tests/test_config.py` | Update tests for new 24-item minimum requirement |

### Key Implementation Notes

1. **Text fitting algorithm**: Start with base font size, measure text width/height, reduce font size iteratively until text fits within square bounds with padding
2. **Word wrapping**: Use ReportLab's `Paragraph` or manual line breaking based on square width
3. **Random seed**: Consider optional seed parameter for reproducible card generation (future enhancement, out of scope)

## Out of Scope

- Configurable name field label
- Configurable font or colors for square text
- "FREE" text on center square
- Random seed for reproducible generation
- Card numbering/identification
- Duplicate detection across multiple cards

## Demoable Units

### DU-1: Generate Cards with Populated Squares

**Steps:**

1. Configure `~/.bingomatic/config.yaml` with 24+ bingo squares
2. Run `uv run bingomatic generate`
3. Open generated PDF

**Expected Result:**

- Each card shows 24 different bingo items in the grid squares
- Center square displays the logo
- Text is readable and fits within squares

### DU-2: Participant Name Field

**Steps:**

1. Generate bingo cards with valid configuration
2. Open generated PDF

**Expected Result:**

- "Name: _______________" appears below each grid
- Line spans the full width of the grid

### DU-3: Validation Error for Insufficient Squares

**Steps:**

1. Configure `bingo_squares` with only 10 items
2. Run `uv run bingomatic validate`

**Expected Output:**

```
Field 'bingo_squares' must contain at least 24 items, got 10
```

### DU-4: Unique Card Arrangements

**Steps:**

1. Configure 30+ bingo squares
2. Generate 4+ cards
3. Compare card layouts

**Expected Result:**

- Each card has a different arrangement of items
- No two cards are identical

## Proof Artifacts

| Artifact | Description | Location |
|----------|-------------|----------|
| Generated PDF | Sample PDF showing populated cards | `docs/specs/03-spec-card-content-population/03-proofs/sample-cards.pdf` |
| Validation Error | Terminal output for insufficient squares | `docs/specs/03-spec-card-content-population/03-proofs/validation-error.png` |
| Test Results | Passing test suite with updated fixtures | `docs/specs/03-spec-card-content-population/03-proofs/test-results.png` |
| Card Comparison | Screenshot showing unique card arrangements | `docs/specs/03-spec-card-content-population/03-proofs/unique-cards.png` |

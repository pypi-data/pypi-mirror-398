# Spec 02: PDF Document Template Generation

## Overview

Implement PDF generation for bingo card templates. Each page contains two 5×5 grids arranged side-by-side with a half inch gap between them in landscape orientation, with each square measuring 1" × 1". This spec focuses on generating the empty template structure; content population will be addressed in subsequent features.

## User Stories

### US-1: Generate Bingo Card Template

**As a** conference organizer
**I want** to generate a PDF with empty bingo card grids
**So that** I can produce physical bingo cards for my event

**Acceptance Criteria:**

- PDF is generated in landscape orientation
- Each page contains two 5×5 grids side-by-side
- There is a half inch gap between the two grids
- Each grid square measures exactly 1" × 1"
- Grids have visible borders around each square

### US-2: Display Event Branding

**As a** conference organizer
**I want** my event name and logo displayed on each card
**So that** the bingo cards are branded for my event

**Acceptance Criteria:**

- Event name appears centered above each grid
- Event logo appears in the center square of each grid
- Logo is scaled to fit within the 1" × 1" center square

### US-3: Configure Card Quantity

**As a** conference organizer
**I want** to specify how many cards to generate
**So that** I can produce the right quantity for my attendees

**Acceptance Criteria:**

- Number of cards is configurable via config file
- Cards are generated in pairs (2 per page)
- Odd card counts result in a final page with one card

### US-4: Save to Output Directory

**As a** user
**I want** generated PDFs saved to my configured output directory
**So that** I know where to find my generated cards

**Acceptance Criteria:**

- PDF is saved to `output_directory` from config
- Filename is auto-generated with date (e.g., `bingo-cards-2025-12-25.pdf`)
- Success message displays the output file path

## Functional Requirements

### FR-1: PDF Page Layout

| Property | Value |
|----------|-------|
| Orientation | Landscape |
| Page Size | Letter (11" × 8.5") |
| Grids per Page | 2 (side-by-side) |
| Grid Dimensions | 5×5 squares |
| Square Size | 1" × 1" |
| Grid Total Size | 5" × 5" |

### FR-2: Grid Positioning

Two grids arranged horizontally on each landscape page:

- **Left Grid**: Centered in left half of page
- **Right Grid**: Centered in right half of page
- **Vertical Position**: Centered vertically with space for header

### FR-3: Visual Elements

| Element | Specification |
|---------|---------------|
| Grid Lines | Black borders around each square |
| Event Name | Centered above each grid |
| Logo | Displayed in center square (row 3, col 3) |
| Other Squares | Empty (no content) |

### FR-4: Logo Handling

- Logo loaded from `logo_location` config path
- Scaled to fit within 1" × 1" center square
- Maintains aspect ratio
- Centered within the square

### FR-5: Configuration Schema Update

Add new field to `~/.bingomatic/config.yaml`:

```yaml
event_name: "DevOpsDays Austin 2026"
logo_location: "/path/to/logo.png"
output_directory: "/path/to/output"
bingo_squares: [...]
card_count: 10  # NEW: Number of bingo cards to generate
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `card_count` | integer | No | 2 | Number of bingo cards to generate |

### FR-6: CLI Interface

**Command**: `bingomatic generate`

**Behavior:**
1. Load and validate configuration
2. Verify logo file exists and is readable
3. Create output directory if it doesn't exist
4. Generate PDF with specified number of cards
5. Display success message with output path

**Success Output:**
```
Generated 10 bingo cards: /path/to/output/bingo-cards-2025-12-25.pdf
```

### FR-7: Output File Naming

- **Location**: Value of `output_directory` from config
- **Filename Pattern**: `bingo-cards-YYYY-MM-DD.pdf`
- **Date**: Current date when generation runs

### FR-8: Error Handling

| Condition | Message | Exit Code |
|-----------|---------|-----------|
| Config invalid | (existing validation errors) | 1 |
| Logo file not found | "Logo file not found: {path}" | 1 |
| Logo file unreadable | "Cannot read logo file: {path}" | 1 |
| Output directory creation fails | "Cannot create output directory: {path}" | 1 |
| PDF generation fails | "Failed to generate PDF: {details}" | 1 |

### FR-9: Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Generation successful |
| 1 | Generation failed |

## Technical Considerations

### Dependencies

- **Python**: 3.12+
- **Package Manager**: uv
- **CLI Framework**: Click (existing)
- **YAML Parser**: PyYAML (existing)
- **PDF Generation**: ReportLab

### Project Structure Updates

```
bingomatic/
├── src/
│   └── bingomatic/
│       ├── __init__.py
│       ├── cli.py          # Add generate command
│       ├── config.py       # Add card_count validation
│       └── pdf.py          # NEW: PDF generation module
└── tests/
    ├── test_config.py      # Update for card_count
    └── test_pdf.py         # NEW: PDF generation tests
```

### ReportLab Notes

- Use `reportlab.lib.pagesizes.landscape(letter)` for page setup
- Use `canvas.Canvas` for drawing
- Measurements in points (72 points = 1 inch)
- Square size: 72 points × 72 points
- Use `canvas.drawImage()` for logo placement

## Out of Scope

- Populating squares with bingo content (future spec)
- Custom fonts or colors
- Header/footer beyond event name
- BINGO column headers (B-I-N-G-O)
- Multiple logo formats (only common image formats supported by ReportLab)
- Custom page sizes
- Card uniqueness/shuffling (applies to future content population)

## Demoable Units

### DU-1: Generate Command with Valid Config

**Steps:**

1. Create valid config with `card_count: 4`
2. Run `bingomatic generate`
3. Open generated PDF

**Expected Output:**

```
Generated 4 bingo cards: /path/to/output/bingo-cards-2025-12-25.pdf
```

**PDF Contents:**
- 2 pages (4 cards ÷ 2 per page)
- Each page has 2 grids side-by-side
- Each grid is 5×5 with 1" squares
- Event name above each grid
- Logo in center square of each grid

### DU-2: Generate Command with Missing Logo

**Steps:**

1. Create config with non-existent `logo_location`
2. Run `bingomatic generate`

**Expected Output:**

```
Logo file not found: /path/to/missing-logo.png
```

### DU-3: Measurement Verification

**Steps:**

1. Generate PDF with default settings
2. Open PDF in viewer with measurement tools
3. Measure grid square dimensions

**Expected Result:**
- Each square measures 1" × 1"
- Total grid measures 5" × 5"

## Proof Artifacts

| Artifact | Description | Location |
|----------|-------------|----------|
| Generated PDF | Sample PDF showing correct layout | `docs/specs/02-spec-document-template/02-proofs/sample-output.pdf` |
| CLI Success Output | Terminal output of successful generation | `docs/specs/02-spec-document-template/02-proofs/cli-success.png` |
| Measurement Verification | Screenshot showing 1" square measurement | `docs/specs/02-spec-document-template/02-proofs/measurement.png` |

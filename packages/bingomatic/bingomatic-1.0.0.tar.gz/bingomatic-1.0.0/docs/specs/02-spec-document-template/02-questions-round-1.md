# 02 Questions Round 1 - Document Template Generation

Please answer each question below (select one or more options, or add your own notes). Feel free to add additional context under any question.

## 1. Grid Content

What content should appear in each square of the 5×5 grid?

- [ ] (A) Randomly selected items from `bingo_squares` config (24 squares + 1 free space)
- [X] (B) Empty squares (blank template for manual filling)
- [ ] (C) Sequential items from `bingo_squares` in order
- [ ] (D) Other (describe)

## 2. Free Space

Should there be a "FREE" space in the center of the grid?

- [X] (A) Yes - center square (position 3,3) is always "FREE"
- [ ] (B) No - all 25 squares should be filled with bingo items
- [ ] (C) Configurable via config file
- [ ] (D) Other (describe)

## 3. Card Uniqueness

For generating multiple cards, how should content be distributed?

- [X] (A) Each card should have randomly shuffled squares (unique cards)
- [ ] (B) All cards should be identical
- [ ] (C) This spec only generates the template structure, not card content
- [ ] (D) Other (describe)

## 4. Number of Cards

How many bingo cards should be generated per run?

- [ ] (A) Fixed number (2 cards = 1 page)
- [ ] (B) Configurable via CLI flag (e.g., `--count 10`)
- [X] (C) Configurable via config file
- [ ] (D) Other (describe)

## 5. Grid Visual Elements

What visual elements should each grid include?

- [X] (A) Grid lines only (simple borders around each square)
- [ ] (B) Grid lines + header with event name
- [ ] (C) Grid lines + header + logo
- [ ] (D) Grid lines + header + logo + "BINGO" column headers (B-I-N-G-O)
- [ ] (E) Other (describe)

## 6. Header/Title

Where should the event name appear on each grid?

- [X] (A) Above the grid (centered)
- [ ] (B) Below the grid
- [ ] (C) No event name on cards
- [ ] (D) Other (describe)

## 7. Logo Placement

Where should the logo appear (if included)?

- [ ] (A) Above each grid (with event name)
- [X] (B) In the center square (replacing FREE space)
- [ ] (C) Not included on the PDF
- [ ] (D) Other (describe)

## 8. Grid Spacing on Page

How should the two grids be arranged on the landscape page?

- [X] (A) Side by side (left and right)
- [ ] (B) Top and bottom
- [ ] (C) Other (describe)

## 9. CLI Integration

How should this feature be invoked?

- [X] (A) New command: `bingomatic generate`
- [ ] (B) New command: `bingomatic create`
- [ ] (C) Default action when running `bingomatic` with no subcommand
- [ ] (D) Other (describe)

## 10. Output File

How should the output PDF file be named and located?

- [X] (A) Use `output_directory` from config + auto-generated filename (e.g., `bingo-cards-2025-12-25.pdf`)
- [ ] (B) Use `output_directory` from config + configurable filename via CLI flag
- [ ] (C) Prompt user for output path
- [ ] (D) Other (describe)

## 11. PDF Library Preference

Do you have a preference for the Python PDF generation library?

- [X] (A) ReportLab (mature, widely used)
- [ ] (B) FPDF2 (lightweight, simple API)
- [ ] (C) WeasyPrint (HTML/CSS to PDF)
- [ ] (D) No preference - recommend best fit
- [ ] (E) Other (describe)

## 12. Proof Artifacts

What proof artifacts will demonstrate this feature works?

- [X] (A) Generated PDF file opened in viewer showing correct layout
- [X] (B) CLI output showing successful generation
- [X] (C) Measurement verification showing 1" squares
- [ ] (D) Print test on physical paper
- [ ] (E) All of the above
- [ ] (F) Other (describe)

---

## Additional Context

Please add any other requirements, constraints, or context here:

In subsequent features we'll populate each of the squares as well as the header and footer.
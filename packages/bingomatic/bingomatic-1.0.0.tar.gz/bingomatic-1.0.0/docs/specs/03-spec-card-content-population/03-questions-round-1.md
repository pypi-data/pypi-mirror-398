# 03 Questions Round 1 - Card Content Population

Please answer each question below (select one or more options, or add your own notes). Feel free to add additional context under any question.

## 1. Square Text Selection

How should bingo items be selected from the `bingo_squares` config for each card?

- [X] (A) Randomly select 24 unique items per card (no duplicates within a card)
- [ ] (B) Randomly select items allowing duplicates within a card
- [ ] (C) Shuffle all items and take first 24 (requires minimum 24 items in config)
- [ ] (D) Other (describe)

## 2. Minimum Items Validation

Should we enforce a minimum number of items in `bingo_squares`?

- [ ] (A) Require exactly 24 items (fills 5x5 grid minus center logo)
- [X] (B) Require at least 24 items (allows variety across cards)
- [ ] (C) Allow fewer than 24 items (repeat items to fill grid)
- [ ] (D) Other (describe)

## 3. Text Fitting in Squares

How should long bingo phrases be handled in 1-inch squares?

- [X] (A) Auto-shrink font to fit (may result in very small text)
- [ ] (B) Truncate with ellipsis if too long
- [X] (C) Word-wrap within the square (multi-line)
- [ ] (D) Require user to keep phrases short (document recommendation)
- [ ] (E) Other (describe)

## 4. Participant Name Field

What format should the name field at the bottom of each card take?

- [X] (A) "Name: _______________" with printed line
- [ ] (B) "Participant: _______________" with printed line
- [ ] (C) Just a blank line with no label
- [ ] (D) Configurable label via config.yaml
- [ ] (E) Other (describe)

## 5. Name Field Positioning

Where should the name field appear relative to the grid?

- [ ] (A) Centered below the grid
- [ ] (B) Left-aligned below the grid
- [X] (C) Spanning the full width of the grid
- [ ] (D) Other (describe)

## 6. Card Uniqueness

Should each generated card have a unique arrangement of squares?

- [X] (A) Yes - each card must have a different random arrangement
- [ ] (B) No - all cards can have the same arrangement
- [ ] (C) Other (describe)

## 7. Center Square Handling

The center square currently displays the logo. Confirm this behavior:

- [X] (A) Keep center square as logo only (no text)
- [ ] (B) Add "FREE" text below/above the logo
- [ ] (C) Make center configurable (logo OR "FREE" text)
- [ ] (D) Other (describe)

## 8. Test Fixture Update Scope

For updating tests to use `test_logo.png`, what's the expected scope?

- [ ] (A) Update `valid_config.yaml` fixture only
- [X] (B) Update all test fixtures and any hardcoded paths
- [ ] (C) Create new integration tests for PDF generation
- [ ] (D) Other (describe)

---

## Additional Context

Please add any other requirements, constraints, or preferences not covered above:

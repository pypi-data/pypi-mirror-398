# 04 Questions Round 1 - GitHub Actions CI

Please answer each question below (select one or more options, or add your own notes). Feel free to add additional context under any question.

## 1. PEP8 Linting Tool

Which linting tool should we use for PEP8 compliance?

- [X] (A) **Ruff** - Fast, modern linter that includes PEP8 rules (recommended, very fast)
- [ ] (B) **flake8** - Traditional PEP8 linter, widely used
- [ ] (C) **pylint** - Comprehensive linter with PEP8 and more
- [ ] (D) Other (describe)

## 2. Workflow Trigger Events

When should the CI workflow run?

- [ ] (A) On **push** to main/master branch only
- [ ] (B) On **pull requests** to main/master only
- [ ] (C) On **both** push and pull requests (recommended)
- [X] (D) On all branches for push and PR
- [ ] (E) Other (describe)

## 3. Python Version Matrix

Should we test against multiple Python versions?

- [ ] (A) Single version: **Python 3.12 only** (matches requires-python)
- [X] (B) Multiple versions: **3.12 and 3.13** (current + latest)
- [ ] (C) Other (describe)

## 4. Workflow Structure

How should the workflows be organized?

- [X] (A) **Single workflow file** with linting and testing as separate jobs
- [ ] (B) **Separate workflow files** for linting and testing
- [ ] (C) Other (describe)

## 5. README Logo Placement

Where should the logo appear in the README?

- [ ] (A) **Top of file** - Before the "Bingomatic" heading
- [X] (B) **After heading** - Below the "# Bingomatic" title
- [ ] (C) **In a badge row** - Alongside any future CI status badges
- [ ] (D) Other (describe)

## 6. Logo Format Preference

Which logo format should we use?

- [X] (A) **PNG** (`images/bingomatic_logo.png`) - Better browser compatibility
- [ ] (B) **SVG** (`images/bingomatic_logo.svg`) - Scalable, smaller file size
- [ ] (C) Other (describe)

## 7. CI Status Badge

Should we add a CI status badge to the README?

- [X] (A) **Yes** - Show workflow status badge at top of README
- [ ] (B) **No** - Just the logo, no badges
- [ ] (C) Other (describe)

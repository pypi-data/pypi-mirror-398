# Task 3.0 Proof Artifacts - Update README with Logo and CI Badge

## Proof 1: README contains CI badge before heading

```markdown
[![CI](https://github.com/richardboydii/bingomatic/actions/workflows/ci.yml/badge.svg)](https://github.com/richardboydii/bingomatic/actions/workflows/ci.yml)

# Bingomatic
```

## Proof 2: README contains logo after heading

```markdown
# Bingomatic

![Bingomatic Logo](images/bingomatic_logo.png)

A bingo card generator for conferences like DevOpsDays.
```

## Proof 3: First 10 lines of README.md

```bash
$ head -10 README.md
[![CI](https://github.com/richardboydii/bingomatic/actions/workflows/ci.yml/badge.svg)](https://github.com/richardboydii/bingomatic/actions/workflows/ci.yml)

# Bingomatic

![Bingomatic Logo](images/bingomatic_logo.png)

A bingo card generator for conferences like DevOpsDays. This is a simple Python CLI that will generate 5" x 5" bingo cards, two to a landscape page, for use at events and conferences.

## Installation
```

## Summary

- Added CI status badge at top of README (links to GitHub Actions workflow)
- Added Bingomatic logo after the `# Bingomatic` heading
- Badge uses `richardboydii/bingomatic` repository path
- Logo references `images/bingomatic_logo.png`

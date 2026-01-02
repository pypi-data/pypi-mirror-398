# Spec 04: GitHub Actions CI Pipeline

## Overview

Add a GitHub Actions CI pipeline to Bingomatic that runs PEP8 linting (via Ruff) and unit tests on all branches for both push and pull request events. Update the README to include the project logo and a CI status badge.

## User Stories

### US-1: Developer runs CI on code changes
**As a** developer contributing to Bingomatic  
**I want** automated linting and testing to run on every push and pull request  
**So that** I get immediate feedback on code quality and test failures

**Acceptance Criteria:**
- CI workflow triggers on push to any branch
- CI workflow triggers on pull requests to any branch
- Linting job runs Ruff for PEP8 compliance
- Formatting job runs Ruff format check
- Testing job runs pytest against all tests in `tests/`
- Tests run on both Python 3.12 and 3.13

### US-2: Visitor sees project branding in README
**As a** visitor viewing the Bingomatic repository  
**I want** to see the project logo and CI status  
**So that** I understand the project identity and build health at a glance

**Acceptance Criteria:**
- Bingomatic logo (PNG) displayed below the "# Bingomatic" heading
- CI status badge visible at top of README (before heading)
- Badge links to the GitHub Actions workflow runs

## Functional Requirements

### FR-1: GitHub Actions Workflow File
Create `.github/workflows/ci.yml` with the following structure:

| Aspect | Requirement |
|--------|-------------|
| **Name** | `CI` |
| **Triggers** | `push` (all branches), `pull_request` (all branches) |
| **Jobs** | `lint`, `format`, and `test` (can run in parallel) |

### FR-2: Lint Job
| Aspect | Requirement |
|--------|-------------|
| **Runner** | `ubuntu-latest` |
| **Python** | 3.12 (single version for linting) |
| **Tool** | Ruff |
| **Command** | `ruff check .` |

### FR-3: Format Job
| Aspect | Requirement |
|--------|-------------|
| **Runner** | `ubuntu-latest` |
| **Python** | 3.12 (single version for formatting) |
| **Tool** | Ruff (formatter) |
| **Command** | `ruff format --check .` |

### FR-4: Test Job
| Aspect | Requirement |
|--------|-------------|
| **Runner** | `ubuntu-latest` |
| **Python** | Matrix: [3.12, 3.13] |
| **Package Manager** | `uv` |
| **Command** | `uv run pytest tests/ -v` |

### FR-5: README Logo
| Aspect | Requirement |
|--------|-------------|
| **File** | `images/bingomatic_logo.png` |
| **Placement** | Immediately after `# Bingomatic` heading |
| **Format** | Markdown image syntax with alt text |
| **Sizing** | Optional width constraint for reasonable display |

### FR-6: CI Status Badge
| Aspect | Requirement |
|--------|-------------|
| **Placement** | Top of README, before `# Bingomatic` heading |
| **Format** | GitHub Actions badge markdown |
| **Link** | Links to Actions workflow runs |

## Technical Considerations

### Dependencies
- **Ruff**: Add to dev dependencies in `pyproject.toml`
- **uv**: Used in CI for dependency management (install via `astral-sh/setup-uv` action)

### Workflow Dependencies
- Lint, format, and test jobs can run in parallel (no dependencies between them)
- Each job should checkout code and set up Python independently

### Badge URL Format
```
![CI](https://github.com/{owner}/{repo}/actions/workflows/ci.yml/badge.svg)
```
Note: The actual owner/repo will need to match the repository where this is deployed.

## Out of Scope

- Auto-formatting in CI (only check mode)
- Coverage reporting
- Deployment workflows
- Release automation
- Branch protection rules
- Caching for faster CI runs (can be added later)

## Demoable Units

### DU-1: CI Workflow Execution
**Proof Artifact:** Screenshot or link to GitHub Actions run showing:
- Workflow triggered on push
- Lint job completed successfully (or with expected output)
- Format job completed successfully (or shows formatting issues)
- Test job matrix showing Python 3.12 and 3.13 runs

### DU-2: README Visual Update
**Proof Artifact:** Screenshot of README on GitHub showing:
- CI status badge at top
- Bingomatic logo below heading
- Both elements rendering correctly

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `.github/workflows/ci.yml` | Create | CI workflow definition |
| `pyproject.toml` | Modify | Add `ruff` to dev dependencies |
| `README.md` | Modify | Add logo and CI badge |

## Definition of Done

- [ ] `.github/workflows/ci.yml` exists and is valid YAML
- [ ] Workflow triggers on push and PR to all branches
- [ ] Ruff lint job passes on current codebase
- [ ] Ruff format check job passes on current codebase
- [ ] Pytest job runs on Python 3.12 and 3.13
- [ ] All existing tests pass in CI
- [ ] README displays Bingomatic logo below heading
- [ ] README displays CI status badge at top
- [ ] Badge correctly links to workflow runs

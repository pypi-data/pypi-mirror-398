# Tasks: Spec 04 - GitHub Actions CI Pipeline

## Spec Reference

- **Spec:** `./spec.md`
- **Feature:** GitHub Actions CI with linting, formatting, testing, and README branding

## Tasks

### [x] 1.0 Add Ruff Dependency and Validate Locally

Add Ruff to dev dependencies and verify the codebase passes both lint and format checks locally before creating CI workflow.

#### 1.0 Proof Artifact(s)

- CLI: `uv run ruff check .` returns no errors (or shows current state)
- CLI: `uv run ruff format --check .` returns no errors (or shows files needing formatting)
- File: `pyproject.toml` contains `ruff` in dev dependencies

#### 1.0 Tasks

- [x] 1.1 Add `ruff>=0.8` to dev dependencies in `pyproject.toml`
- [x] 1.2 Run `uv sync` to install ruff
- [x] 1.3 Run `uv run ruff check .` and fix any lint errors
- [x] 1.4 Run `uv run ruff format --check .` and fix any format issues (or run `uv run ruff format .` to auto-fix)
- [x] 1.5 Verify both commands pass cleanly

---

### [x] 2.0 Create GitHub Actions CI Workflow

Create the CI workflow file with lint, format, and test jobs that run on push and PR to all branches.

#### 2.0 Proof Artifact(s)

- File: `.github/workflows/ci.yml` exists with valid YAML syntax
- CLI: `cat .github/workflows/ci.yml` shows workflow with 3 jobs (lint, format, test)
- Validation: YAML syntax is valid (can be checked with `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`)

#### 2.0 Tasks

- [x] 2.1 Create `.github/workflows/` directory structure
- [x] 2.2 Create `ci.yml` with workflow name and triggers (push, pull_request on all branches)
- [x] 2.3 Add `lint` job: ubuntu-latest, Python 3.12, install uv, run `ruff check .`
- [x] 2.4 Add `format` job: ubuntu-latest, Python 3.12, install uv, run `ruff format --check .`
- [x] 2.5 Add `test` job: ubuntu-latest, Python matrix [3.12, 3.13], install uv, run `uv run pytest tests/ -v`
- [x] 2.6 Validate YAML syntax locally

---

### [x] 3.0 Update README with Logo and CI Badge

Add the Bingomatic logo below the heading and CI status badge at the top of the README.

#### 3.0 Proof Artifact(s)

- File: `README.md` contains logo markdown after `# Bingomatic` heading
- File: `README.md` contains CI badge markdown before `# Bingomatic` heading
- Screenshot: README preview showing logo and badge rendering correctly

#### 3.0 Tasks

- [x] 3.1 Add CI status badge at top of README (before `# Bingomatic` heading)
  - Badge format: `[![CI](https://github.com/{owner}/{repo}/actions/workflows/ci.yml/badge.svg)](https://github.com/{owner}/{repo}/actions/workflows/ci.yml)`
  - Note: Update `{owner}/{repo}` placeholder with actual repository path
- [x] 3.2 Add logo image after `# Bingomatic` heading
  - Format: `![Bingomatic Logo](images/bingomatic_logo.png)`
  - Consider adding width constraint if logo is too large
- [x] 3.3 Preview README locally to verify rendering

---

### [~] 4.0 Verify CI Workflow Execution

Push changes to GitHub and verify the CI workflow runs successfully with all jobs passing.

#### 4.0 Proof Artifact(s)

- Screenshot/URL: GitHub Actions workflow run showing all jobs (lint, format, test) completed
- Screenshot: Test job matrix showing Python 3.12 and 3.13 runs
- Screenshot: README on GitHub showing badge with passing status and logo displayed

#### 4.0 Tasks

- [x] 4.1 Commit all changes (pyproject.toml, ci.yml, README.md)
- [x] 4.2 Push to GitHub repository
- [~] 4.3 Navigate to Actions tab and verify workflow triggered
- [ ] 4.4 Verify lint job passes
- [ ] 4.5 Verify format job passes
- [ ] 4.6 Verify test job passes on both Python 3.12 and 3.13
- [ ] 4.7 Verify README displays logo correctly on GitHub
- [ ] 4.8 Verify CI badge shows passing status and links to workflow

---

## Relevant Files

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` | Modify | Add `ruff` to dev dependencies |
| `.github/workflows/ci.yml` | Create | CI workflow with lint, format, test jobs |
| `README.md` | Modify | Add CI badge and logo |
| `images/bingomatic_logo.png` | Reference | Logo file (already exists) |

## Spec Coverage Matrix

| Spec Requirement | Task Coverage |
|------------------|---------------|
| FR-1: Workflow File | Task 2.0 |
| FR-2: Lint Job | Task 1.0, 2.0 |
| FR-3: Format Job | Task 1.0, 2.0 |
| FR-4: Test Job | Task 2.0 |
| FR-5: README Logo | Task 3.0 |
| FR-6: CI Badge | Task 3.0 |
| US-1: CI on changes | Task 2.0, 4.0 |
| US-2: README branding | Task 3.0, 4.0 |

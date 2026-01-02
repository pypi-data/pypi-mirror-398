# Tasks: Spec 05 - PyPI Publishing

## Spec Reference

- **Spec:** `./spec.md`
- **Feature:** Package and publish Bingomatic CLI to PyPI with version 1.0.0

## Tasks

### [x] 1.0 Update Package Metadata and Version

Bump version to 1.0.0 and add complete package metadata including license, keywords, project URLs, and classifiers.

#### 1.0 Proof Artifact(s)

- File: `pyproject.toml` shows `version = "1.0.0"`
- File: `pyproject.toml` contains `license`, `keywords`, and `[project.urls]` sections
- File: `LICENSE` exists in repository root
- CLI: `uv run python -c "import bingomatic; print(bingomatic.__version__)"` returns `1.0.0`

#### 1.0 Tasks

- [x] 1.1 Update version to `1.0.0` in `pyproject.toml`
- [x] 1.2 Update `__version__` to `1.0.0` in `src/bingomatic/__init__.py`
- [x] 1.3 Add `license = {text = "Apache-2.0"}` to `pyproject.toml` (LICENSE file already exists)
- [x] 1.4 Add `keywords` array to `pyproject.toml`: `["bingo", "conference", "devopsdays", "pdf", "cli"]`
- [x] 1.5 Add `[project.urls]` section with Homepage, Repository, and Documentation links
- [x] 1.6 Add additional classifiers: License, Environment, Intended Audience
- [x] 1.7 Verify version with `uv run python -c "import bingomatic; print(bingomatic.__version__)"`

---

### [x] 2.0 Verify Local Package Build

Build the package locally and verify it creates valid wheel and sdist artifacts that can be installed.

#### 2.0 Proof Artifact(s)

- CLI: `uv build` completes successfully
- File: `dist/bingomatic-1.0.0-py3-none-any.whl` exists
- File: `dist/bingomatic-1.0.0.tar.gz` exists
- CLI: `pip install dist/bingomatic-1.0.0-py3-none-any.whl` succeeds in clean venv
- CLI: `bingomatic --version` returns `1.0.0` after installation

#### 2.0 Tasks

- [x] 2.1 Run `uv build` to create wheel and sdist
- [x] 2.2 Verify `dist/` contains `.whl` and `.tar.gz` files
- [x] 2.3 Create a clean virtual environment for testing
- [x] 2.4 Install wheel in clean venv: `pip install dist/bingomatic-1.0.0-py3-none-any.whl`
- [x] 2.5 Verify CLI works: `bingomatic --version` and `bingomatic --help`
- [x] 2.6 Verify dependencies installed correctly

---

### [x] 3.0 Create GitHub Actions Publish Workflow

Add build and publish jobs to the CI workflow that trigger on GitHub Release creation.

#### 3.0 Proof Artifact(s)

- File: `.github/workflows/ci.yml` contains `build` job with artifact upload
- File: `.github/workflows/ci.yml` contains `publish-pypi` job with OIDC auth
- File: Workflow triggers on `release: types: [published]`
- CLI: YAML syntax validation passes

#### 3.0 Tasks

- [x] 3.1 Add `release: types: [published]` to workflow triggers
- [x] 3.2 Create `build` job that runs `uv build`
- [x] 3.3 Add `actions/upload-artifact` step to upload `dist/` directory
- [x] 3.4 Make `build` job depend on `lint`, `format`, `test` jobs passing
- [x] 3.5 Update/fix existing `pypi-publish` job with proper steps
- [x] 3.6 Add `actions/download-artifact` to retrieve built package
- [x] 3.7 Configure `publish-pypi` job to depend on `build` job
- [x] 3.8 Add condition to only run publish on release events
- [x] 3.9 Validate YAML syntax locally

---

### [~] 4.0 Configure PyPI Trusted Publishing (USER ACTION REQUIRED)

Set up OIDC trusted publishing on PyPI and verify the workflow configuration matches.

#### 4.0 Proof Artifact(s)

- Screenshot/URL: PyPI project settings showing trusted publisher configured
- File: `.github/workflows/ci.yml` has `permissions: id-token: write`
- File: Workflow uses `pypa/gh-action-pypi-publish@release/v1` action

#### 4.0 Tasks

- [~] 4.1 Register project on PyPI (if not already registered) - **USER ACTION REQUIRED**
- [~] 4.2 Navigate to PyPI project settings → Trusted Publishers - **USER ACTION REQUIRED**
- [~] 4.3 Add GitHub as trusted publisher with: owner, repo, workflow, environment - **USER ACTION REQUIRED**
- [x] 4.4 Verify workflow has `permissions: id-token: write`
- [x] 4.5 Verify workflow uses correct environment name (`pypi`)
- [x] 4.6 Document trusted publishing configuration in proof artifacts

---

### [~] 5.0 Publish to PyPI and Verify Installation (USER ACTION REQUIRED)

Create a GitHub Release, verify the workflow runs, and confirm the package is installable from PyPI.

#### 5.0 Proof Artifact(s)

- Screenshot/URL: GitHub Actions workflow run showing successful build and publish
- URL: `https://pypi.org/project/bingomatic/1.0.0/` showing package page
- Screenshot: PyPI page showing README, license, and project URLs
- CLI: `pip install bingomatic` from PyPI succeeds
- CLI: `bingomatic --version` returns `1.0.0` after PyPI installation

#### 5.0 Tasks

- [x] 5.1 Commit all changes to branch
- [~] 5.2 Push branch and create PR (or merge to main) - **USER ACTION REQUIRED**
- [~] 5.3 Create GitHub Release with tag `v1.0.0` - **USER ACTION REQUIRED**
- [ ] 5.4 Monitor GitHub Actions workflow execution
- [ ] 5.5 Verify build job completes successfully
- [ ] 5.6 Verify publish job completes successfully
- [ ] 5.7 Check PyPI for package: `https://pypi.org/project/bingomatic/`
- [ ] 5.8 Test installation: `pip install bingomatic` in clean environment
- [ ] 5.9 Verify CLI: `bingomatic --version` returns `1.0.0`
- [ ] 5.10 Verify PyPI page shows README, license, and project URLs

---

## Relevant Files

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` | Modify | Bump version, add license, URLs, keywords, classifiers |
| `src/bingomatic/__init__.py` | Modify | Update `__version__` to `1.0.0` |
| `.github/workflows/ci.yml` | Modify | Add build and publish jobs, release trigger |
| `LICENSE` | Exists | MIT license file (already present) |
| `dist/` | Generated | Build artifacts (wheel, sdist) |

## Spec Coverage Matrix

| Spec Requirement | Task Coverage |
|------------------|---------------|
| FR-1: Version Bump | Task 1.0 |
| FR-2: Package Metadata | Task 1.0 |
| FR-3: Build Workflow | Task 3.0 |
| FR-4: Test PyPI (optional) | Task 4.0 |
| FR-5: Production PyPI | Task 3.0, 5.0 |
| FR-6: Workflow Updates | Task 3.0 |
| US-1: Install from PyPI | Task 2.0, 5.0 |
| US-2: Auto-publish | Task 3.0, 5.0 |
| US-3: Package discovery | Task 1.0, 5.0 |

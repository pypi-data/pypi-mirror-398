# Spec 05: PyPI Publishing

## Overview

Package the Bingomatic CLI application and publish it to PyPI so users can install it via `pip install bingomatic`. This includes bumping the version to 1.0.0, completing package metadata, and setting up automated publishing via GitHub Actions when releases are created.

## User Stories

### US-1: User installs Bingomatic from PyPI

**As a** conference organizer  
**I want** to install Bingomatic using `pip install bingomatic`  
**So that** I can quickly set up bingo card generation without cloning the repository

**Acceptance Criteria:**

- Package is available on PyPI at `pypi.org/project/bingomatic`
- Installation via `pip install bingomatic` works
- CLI command `bingomatic` is available after installation
- All dependencies are automatically installed

### US-2: Maintainer publishes new release

**As a** project maintainer  
**I want** the package to automatically publish to PyPI when I create a GitHub Release  
**So that** releases are consistent and require no manual publishing steps

**Acceptance Criteria:**

- Creating a GitHub Release triggers the publish workflow
- CI jobs (lint, format, test) must pass before publishing
- Package is built and uploaded to PyPI automatically
- Publishing uses OIDC trusted publishing (no API tokens needed)

### US-3: User discovers package on PyPI

**As a** potential user browsing PyPI  
**I want** to see complete package information including description, license, and links  
**So that** I can evaluate if the package meets my needs

**Acceptance Criteria:**

- Package page shows README content
- License is clearly displayed
- Links to repository, homepage, and documentation are visible
- Keywords help with search discoverability

## Functional Requirements

### FR-1: Version Bump to 1.0.0

| Aspect | Requirement |
|--------|-------------|
| **File** | `pyproject.toml` |
| **Current** | `version = "0.1.0"` |
| **Target** | `version = "1.0.0"` |

### FR-2: Package Metadata Completion

| Field | Value |
|-------|-------|
| **License** | MIT (or author's choice) |
| **Keywords** | `["bingo", "conference", "devopsdays", "pdf", "cli"]` |
| **Project URLs** | homepage, repository, documentation |
| **Classifiers** | Add license classifier, CLI/console classifier |

### FR-3: Build Workflow Job

| Aspect | Requirement |
|--------|-------------|
| **Trigger** | On GitHub Release created |
| **Dependencies** | Requires lint, format, test jobs to pass |
| **Build Command** | `uv build` |
| **Artifacts** | Upload `dist/` as workflow artifact |

### FR-4: Test PyPI Publishing (Optional Validation)

| Aspect | Requirement |
|--------|-------------|
| **Target** | `test.pypi.org` |
| **Purpose** | Validate package before production release |
| **Authentication** | OIDC Trusted Publishing |
| **When** | Can be triggered manually or on pre-release |

### FR-5: Production PyPI Publishing

| Aspect | Requirement |
|--------|-------------|
| **Target** | `pypi.org` |
| **Trigger** | GitHub Release (not pre-release) |
| **Authentication** | OIDC Trusted Publishing |
| **Environment** | `pypi` (for environment protection rules) |
| **Dependencies** | Requires build job to complete successfully |

### FR-6: Workflow File Updates

| Aspect | Requirement |
|--------|-------------|
| **File** | `.github/workflows/ci.yml` or separate `publish.yml` |
| **Trigger** | `release: types: [published]` |
| **Jobs** | `build`, `publish-testpypi` (optional), `publish-pypi` |

## Technical Considerations

### OIDC Trusted Publishing Setup

PyPI Trusted Publishing requires configuration on both PyPI and GitHub:

1. **PyPI Configuration** (manual step by user):
   - Navigate to PyPI project settings
   - Add GitHub as a trusted publisher
   - Configure: owner, repository, workflow name, environment

2. **GitHub Workflow Configuration**:
   - Use `pypa/gh-action-pypi-publish@release/v1`
   - Set `permissions: id-token: write`
   - Configure environment for production publishing

### Build System

- **Build backend**: `hatchling` (already configured)
- **Build command**: `uv build` creates both wheel and sdist
- **Output**: `dist/*.whl` and `dist/*.tar.gz`

### Package Structure Verification

Current structure is correct:
- `src/bingomatic/` layout
- Entry point: `bingomatic = "bingomatic.cli:main"`
- Dependencies properly declared

## Out of Scope

- Semantic versioning automation
- Changelog generation
- Release notes automation
- Multi-platform wheel builds
- Conda publishing
- Private PyPI registries

## Demoable Units

### DU-1: Local Package Build

**Proof Artifact:** CLI output showing:

- `uv build` completes successfully
- `dist/` contains wheel and sdist files
- `pip install dist/*.whl` works locally

### DU-2: PyPI Package Page

**Proof Artifact:** Screenshot or URL showing:

- Package page at `pypi.org/project/bingomatic`
- Version 1.0.0 displayed
- README rendered correctly
- License, keywords, and project URLs visible

### DU-3: Automated Publishing Workflow

**Proof Artifact:** Screenshot or URL showing:

- GitHub Actions workflow triggered by release
- Build job completed
- Publish job completed
- Package version matches release tag

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` | Modify | Bump version, add license, URLs, keywords |
| `.github/workflows/ci.yml` | Modify | Add build and publish jobs |
| `src/bingomatic/__init__.py` | Modify | Update `__version__` if defined there |
| `LICENSE` | Create | Add license file (if not exists) |

## Definition of Done

- [ ] Version bumped to `1.0.0` in `pyproject.toml`
- [ ] License field added to `pyproject.toml`
- [ ] Project URLs added (homepage, repository)
- [ ] Keywords added for discoverability
- [ ] `uv build` succeeds locally and creates valid artifacts
- [ ] GitHub workflow includes build job with artifact upload
- [ ] GitHub workflow includes PyPI publish job with OIDC auth
- [ ] Publish job depends on lint, format, test, and build jobs
- [ ] Package successfully published to PyPI
- [ ] `pip install bingomatic` works from PyPI
- [ ] CLI command `bingomatic` available after installation

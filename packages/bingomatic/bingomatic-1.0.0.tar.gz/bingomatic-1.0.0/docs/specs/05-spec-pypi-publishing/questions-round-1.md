# 05 Questions Round 1 - PyPI Publishing

Please answer each question below (select one or more options, or add your own notes). Feel free to add additional context under any question.

## 1. Publishing Trigger

When should the package be published to PyPI?

- [ ] (A) On every push to main branch
- [X] (B) Only when a GitHub Release is created (recommended for versioned releases)
- [ ] (C) Manual trigger only (workflow_dispatch)
- [ ] (D) On tag push (e.g., `v1.0.0`)
- [ ] (E) Other (describe)

## 2. PyPI Repository Target

Which PyPI repository should be used?

- [ ] (A) Production PyPI only (pypi.org)
- [X] (B) Test PyPI first for validation, then Production PyPI for releases
- [ ] (C) Test PyPI only (test.pypi.org) for now
- [ ] (D) Other (describe)

## 3. Version Management

How should version numbers be managed?

- [X] (A) Manual updates in `pyproject.toml` only
- [ ] (B) Use git tags as the version source (dynamic versioning)
- [ ] (C) Bump version manually, but validate tag matches `pyproject.toml` version
- [ ] (D) Other (describe)

## 4. Build Verification

Should the workflow verify the package builds correctly before publishing?

- [X] (A) Yes, run `uv build` and verify artifacts exist
- [ ] (B) Yes, and also run `twine check` to validate package metadata
- [ ] (C) No, just publish directly
- [ ] (D) Other (describe)

## 5. CI Job Dependencies

Should publishing depend on other CI jobs passing first?

- [X] (A) Yes, require lint, format, and test jobs to pass first
- [ ] (B) No, publish independently
- [ ] (C) Other (describe)

## 6. Package Metadata Completeness

The current `pyproject.toml` is missing some recommended metadata. Should we add:

- [ ] (A) License field (e.g., MIT, Apache-2.0)
- [ ] (B) Project URLs (homepage, repository, documentation)
- [ ] (C) Keywords for discoverability
- [X] (D) All of the above
- [ ] (E) Keep minimal metadata as-is

## 7. README Display on PyPI

Should the README be displayed on the PyPI package page?

- [X] (A) Yes, use README.md as the long description (already configured)
- [ ] (B) No, create a separate shorter description for PyPI
- [ ] (C) Other (describe)

## 8. Authentication Method

How should the workflow authenticate with PyPI?

- [X] (A) Trusted Publishing (OIDC) - recommended, no secrets needed (already partially configured)
- [ ] (B) API Token stored as GitHub Secret
- [ ] (C) Other (describe)

---

**After answering, reply with "I've submitted my answers" and I'll generate the specification.**

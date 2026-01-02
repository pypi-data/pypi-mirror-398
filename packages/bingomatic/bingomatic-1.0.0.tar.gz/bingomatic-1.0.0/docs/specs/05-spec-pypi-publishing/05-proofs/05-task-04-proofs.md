# Task 4.0 Proof Artifacts - Configure PyPI Trusted Publishing

## Proof 1: Workflow has permissions: id-token: write

```bash
$ grep -A2 "permissions:" .github/workflows/ci.yml
    permissions:
      id-token: write
    steps:
```

## Proof 2: Workflow uses pypa/gh-action-pypi-publish action

```bash
$ grep "pypa/gh-action-pypi-publish" .github/workflows/ci.yml
        uses: pypa/gh-action-pypi-publish@release/v1
```

## Proof 3: Workflow uses 'pypi' environment

```bash
$ grep -A1 "environment:" .github/workflows/ci.yml
    environment:
      name: pypi
```

## PyPI Trusted Publishing Configuration (Manual Step)

**User must configure the following on PyPI:**

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new pending publisher (if project doesn't exist yet) OR go to project settings
3. Configure trusted publisher with:
   - **Owner**: `richardboydii`
   - **Repository**: `bingomatic`
   - **Workflow name**: `ci.yml`
   - **Environment name**: `pypi`

## GitHub Environment Configuration (Manual Step)

**User must create GitHub environment:**

1. Go to repository Settings → Environments
2. Create environment named `pypi`
3. Optionally add protection rules (e.g., require approval)

## Summary

- Workflow configured with `id-token: write` permission ✅
- Workflow uses `pypa/gh-action-pypi-publish@release/v1` ✅
- Workflow uses `pypi` environment ✅
- PyPI trusted publisher configuration: **USER ACTION REQUIRED**
- GitHub environment creation: **USER ACTION REQUIRED**

# Task 3.0 Proof Artifacts - Create GitHub Actions Publish Workflow

## Proof 1: Workflow triggers on release

```yaml
on:
  push:
  pull_request:
  release:
    types: [published]
```

## Proof 2: Build job with artifact upload

```yaml
  build:
    name: Build Package
    runs-on: ubuntu-latest
    needs: [lint, format, test]
    if: github.event_name == 'release'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Build package
        run: uv build

      - name: Upload dist artifacts
        uses: actions/upload-artifact@v4
        with:
          name: python-package-distributions
          path: dist/
```

## Proof 3: Publish-pypi job with OIDC auth

```yaml
  publish-pypi:
    name: Publish to PyPI
    runs-on: ubuntu-latest
    needs: [build]
    if: github.event_name == 'release'
    environment:
      name: pypi
      url: https://pypi.org/p/bingomatic
    permissions:
      id-token: write
    steps:
      - name: Download dist artifacts
        uses: actions/download-artifact@v4
        with:
          name: python-package-distributions
          path: dist/

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

## Proof 4: YAML syntax validation

```bash
$ uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('YAML syntax valid!')"
YAML syntax valid!
```

## Summary

- Added `release: types: [published]` trigger
- Created `build` job that depends on lint, format, test
- Build job runs `uv build` and uploads artifacts
- Created `publish-pypi` job with OIDC trusted publishing
- Publish job downloads artifacts and publishes to PyPI
- Both jobs only run on release events
- YAML syntax validated

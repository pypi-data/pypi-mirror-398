# Task 1.0 Proof Artifacts - Update Package Metadata and Version

## Proof 1: pyproject.toml shows version = "1.0.0"

```toml
[project]
name = "bingomatic"
version = "1.0.0"
```

## Proof 2: pyproject.toml contains license, keywords, and project.urls

```toml
license = {text = "Apache-2.0"}
keywords = ["bingo", "conference", "devopsdays", "pdf", "cli"]

[project.urls]
Homepage = "https://github.com/richardboydii/bingomatic"
Repository = "https://github.com/richardboydii/bingomatic"
Documentation = "https://github.com/richardboydii/bingomatic#readme"
```

## Proof 3: Additional classifiers added

```toml
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Operating System :: OS Independent",
    "License :: OSI Approved :: Apache Software License",
    "Environment :: Console",
    "Intended Audience :: End Users/Desktop",
    "Topic :: Utilities",
]
```

## Proof 4: LICENSE file exists

```bash
$ ls -la LICENSE
-rw-r--r--@ 1 richardboydii  staff  11357 Dec 24 08:06 LICENSE
```

## Proof 5: Version verification

```bash
$ uv run python -c "import bingomatic; print(bingomatic.__version__)"
1.0.0
```

## Proof 6: Tests pass

```bash
$ uv run pytest tests/ -v
============================== 62 passed in 0.28s ==============================
```

## Summary

- Version bumped to 1.0.0 in both `pyproject.toml` and `__init__.py`
- Added Apache-2.0 license field
- Added keywords for PyPI discoverability
- Added project URLs (Homepage, Repository, Documentation)
- Added classifiers for Python versions, license, environment, and audience
- All 62 tests pass

# Task 2.0 Proof Artifacts - Verify Local Package Build

## Proof 1: uv build completes successfully

```bash
$ uv build
Building source distribution...
Building wheel from source distribution...
Successfully built dist/bingomatic-1.0.0.tar.gz
Successfully built dist/bingomatic-1.0.0-py3-none-any.whl
```

## Proof 2: dist/ contains wheel and sdist files

```bash
$ ls -la dist/
total 2936
-rw-r--r--  1 richardboydii  staff  610616 Dec 27 09:11 bingomatic-1.0.0-py3-none-any.whl
-rw-r--r--  1 richardboydii  staff  884114 Dec 27 09:11 bingomatic-1.0.0.tar.gz
```

## Proof 3: pip install in clean venv succeeds

```bash
$ python3 -m venv /tmp/bingomatic-test-venv
$ /tmp/bingomatic-test-venv/bin/pip install dist/bingomatic-1.0.0-py3-none-any.whl
Processing ./dist/bingomatic-1.0.0-py3-none-any.whl
Collecting click>=8.0 (from bingomatic==1.0.0)
Collecting pyyaml>=6.0 (from bingomatic==1.0.0)
Collecting reportlab>=4.0 (from bingomatic==1.0.0)
Successfully installed bingomatic-1.0.0 click-8.3.1 pyyaml-6.0.3 reportlab-4.4.7 ...
```

## Proof 4: CLI version returns 1.0.0

```bash
$ /tmp/bingomatic-test-venv/bin/bingomatic --version
bingomatic, version 1.0.0
```

## Proof 5: CLI help works

```bash
$ /tmp/bingomatic-test-venv/bin/bingomatic --help
Usage: bingomatic [OPTIONS] COMMAND [ARGS]...

  Bingomatic - A bingo card generator for conferences like DevOpsDays.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  generate  Generate bingo card PDF.
  validate  Validate the configuration file.
```

## Summary

- `uv build` successfully creates wheel and sdist
- Package installs correctly in clean virtual environment
- All dependencies (click, pyyaml, reportlab) are installed
- CLI command `bingomatic` is available and returns version 1.0.0

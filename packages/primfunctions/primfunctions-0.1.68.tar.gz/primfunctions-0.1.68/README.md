# prim-ai-functions

A comprehensive SDK for interacting with the Prim AI Functions.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Development Setup](#development-setup)

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

If you do not have a uv virtual environment, you can create one with:
```bash
uv venv --python 3.12
```

**Note:** We recommend using uv to install the package due to the incredible speed of the package manager. The package can still be installed via pip directly, but it will be slower.

## Installation

### From PyPI

```bash
pip install primfunctions
```

### From Source

```bash
uv pip install .
```

## Development Setup

### Git Hooks
This project includes git hooks to ensure code quality. To set up the git hooks:

```bash
python setup_hooks.py
```

This will create a pre-commit hook that automatically runs black on Python files before each commit.

# GP Wrapper – Agent Context

## Project overview

**gp_wrapper** is a Python package (pyproject.toml) for Google Play–related operations. Do not commit `client_secrets.json` or other secrets.

## Repository structure

```
.
├── gp_wrapper/          # Package
├── pyproject.toml
├── publish.py
├── mypy.ini
├── README.md
├── client_secrets.json  # Do not commit
├── data/
├── dist/
└── reports/
```

## Tech stack

- **Python** (see `pyproject.toml`)

## Setup

From this project root: `pip install -e .` or create venv and install per pyproject.toml.

## Running / entry points

- CLI: `gp_wrapper` if installed (see README).
- Publish: `python publish.py` if applicable.

## Tests

Check README or project for test commands.

## Sensitive / ignored files

Do not commit: `client_secrets.json`, `venv/`, `__pycache__/`, API keys. Respect `.gitignore`.

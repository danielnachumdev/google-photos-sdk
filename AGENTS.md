# GP Wrapper – Agent Context

## Project overview

**gp_wrapper** is a Python package wrapping the **Google Photos Library API**. Managed with **uv** + a single `pyproject.toml` (metadata, runtime deps, dev group, mypy, pylint, pytest/coverage). Do not commit `client_secrets.json` or other secrets.

## Repository structure

```
.
├── gp_wrapper/          # Importable package
├── tests/               # pytest suite (do not delete)
├── pyproject.toml       # uv project: runtime + [dependency-groups] dev + tool config
├── uv.lock              # Lockfile (track in git)
├── publish.py           # Version bump (pyproject + README), uv build, twine upload
├── README.md
├── LISENCE              # MIT (filename spelling is historical)
├── client_secrets.json  # Do not commit
├── data/
├── dist/                # Build artifacts (gitignored)
└── reports/             # pylint/mypy/pytest output (gitignored *.txt)
```

## Tech stack

- **Python** `>=3.8.0` (keep unless uv/tooling forces a bump)
- **Toolchain:** [uv](https://docs.astral.sh/uv/) + `pyproject.toml` / `uv.lock`
- **Runtime / publish:** `[project].dependencies` — `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`, `requests`, `tqdm`, `moviepy>=1.0.3,<2`
- **Dev:** `[dependency-groups].dev` — mypy, pylint, twine, `types-requests`, `types-tqdm`, pytest, pytest-cov, danielutils (for `publish.py`; no duplicated runtime deps)
- **Lock constraint:** `tool.uv.constraint-dependencies` also pins `moviepy>=1.0.3,<2` (`moviepy.editor` was removed in moviepy 2.x). Do not rewrite the moviepy API here.
- **Config:** `[tool.mypy]`, `[tool.pylint.*]`, `[tool.pytest.ini_options]`, `[tool.coverage.*]` all live in `pyproject.toml`

## Setup

From this project root:

```powershell
uv sync                 # runtime / publish only → .venv
uv sync --group dev     # also mypy, pylint, twine, pytest, typing stubs
# or: uv sync --all-groups
```

`tool.uv.default-groups` is empty so `uv sync` does **not** install the `dev` group by default.

## Running / entry points

- Import: `uv run python -c "import gp_wrapper"`
- Tests: `uv run pytest` (after `uv sync --group dev`)
- Typecheck / lint: `uv run mypy` / `uv run pylint gp_wrapper` (config from pyproject)
- Publish: `uv run python publish.py` (runs pytest first, then bumps version in `pyproject.toml` + README, `uv build` + twine)

Known bug: importing on Linux can crash in `win32_ctime` (`NameError`). Do not fix that refactor unless asked. Windows import is the supported path.

## Tests

`tests/` is a pytest + pytest-cov suite targeting ≥95% coverage. Never delete `tests/`. Coverage config is in `pyproject.toml`.

## Sensitive / ignored files

Do not commit: `client_secrets.json`, `.pypirc`, `.venv/`, `venv/`, `dist/`, `__pycache__/`, API keys. Track `uv.lock`. Respect `.gitignore`.

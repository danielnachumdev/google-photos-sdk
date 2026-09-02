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
├── publish.py           # quickpub publish() config (QA + build + PyPI/git)
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
- **Dev:** `[dependency-groups].dev` — mypy, pylint, pytest, pytest-cov, pytest-xdist, `quickpub>=4.1.3`, `types-requests`, `types-tqdm` (no duplicated runtime deps)
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
- Publish: `uv run --all-groups python publish.py` ([quickpub](https://pypi.org/project/quickpub/) 4.1.3+: `UvBuildSchema`, `generate_project_files=False` so existing `pyproject.toml` is kept). Bump `VERSION` in `publish.py` first. Set `demo=True` to run QA only. Needs `.pypirc`. License path is `./LISENCE`.

File timestamps: use `FileTimeService` (`utils/file_time.py`) — public `get`/`set`, private `_stat` / `_apply_utime` / … — portable `os.stat` / `os.utime`. `set` updates access/modification only (not Windows Date created). `CoreMediaItem.upload_media` copies those onto transcoded non-mp4 videos after reading bytes (so Windows atime is not clobbered by the upload open). Before reading upload bytes, it also embeds MP4 `creation_time` from the source mtime via `embed_mp4_creation_time` (`utils/mp4_metadata.py`) — Google Photos dates videos from container metadata, not FileTime. Transcode runs whether or not `pbar` is passed (nachum_migrator does not pass one).

## Tests

`tests/` is a pytest + pytest-cov suite targeting ≥95% coverage. Never delete `tests/`. Coverage config is in `pyproject.toml`.

## Sensitive / ignored files

Do not commit: `client_secrets.json`, `.pypirc`, `.venv/`, `venv/`, `dist/`, `__pycache__/`, API keys. Track `uv.lock`. Respect `.gitignore`.

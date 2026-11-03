# GP Wrapper – Agent Context

## Project overview

**gp_wrapper** is a Python package wrapping the **Google Photos Library API**. Managed with **uv** + a single `pyproject.toml` (metadata, runtime deps, dev group, mypy, pylint, pytest/coverage). Do not commit `client_secrets.json` or other secrets.

## Repository structure

```
.
├── .github/             # CODEOWNERS, dependabot.yml, workflows/
├── .github/workflows/   # CI (Py 3.11–3.13) + CD (label-driven semver Release)
├── SECURITY.md          # Private vulnerability reporting policy
├── gp_wrapper/          # Importable package
├── scripts/release/     # release_semver.py + build_release_wheel.sh (CD)
├── tests/               # pytest suite (do not delete)
├── pyproject.toml       # uv project: runtime + [dependency-groups] dev + tool config
├── uv.lock              # Lockfile (track in git)
├── publish.py           # optional local quickpub publish (PyPI); CD owns GitHub Releases
├── README.md
├── LISENCE              # MIT (filename spelling is historical)
├── client_secrets.json  # Do not commit
├── data/
├── dist/                # Build artifacts (gitignored)
└── reports/             # pylint/mypy/pytest output (gitignored *.txt)
```

## Tech stack

- **Python** `>=3.11` (raised for Dependabot-fixed deps such as Pillow 13)
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
- **CI:** `.github/workflows/ci.yml` — pytest on Python **3.11, 3.12, 3.13**; aggregate check name `CI`.
- **CD / Release:** `.github/workflows/cd.yml` — after successful CI on `main`, label-driven semver GitHub Release + wheel. Every PR into `main` needs **exactly one** of: `bumpMajor` | `bumpMinor` | `bumpPatch` | `noBump`. Source of truth is Release tags (not committed version bumps). If no Release exists yet, CD seeds from `pyproject.toml` version.
- Optional local PyPI publish: `uv run --all-groups python publish.py` ([quickpub](https://pypi.org/project/quickpub/) 4.1.3+). Set `demo=True` to run QA only. Needs `.pypirc`. License path is `./LISENCE`.

File timestamps: use `FileTimeService` (`utils/file_time.py`) — public `get`/`set`, private `_stat` / `_apply_utime` / … — portable `os.stat` / `os.utime`. `set` updates access/modification only (not Windows Date created). `CoreMediaItem.upload_media` copies those onto transcoded non-mp4 videos after reading bytes (so Windows atime is not clobbered by the upload open). Before reading upload bytes, it also embeds MP4 `creation_time` from the source mtime via `embed_mp4_creation_time` (`utils/mp4_metadata.py`) — Google Photos dates videos from container metadata, not FileTime. Transcode runs whether or not `pbar` is passed (nachum_migrator does not pass one).

## Tests

`tests/` is a pytest + pytest-cov suite targeting ≥95% coverage. Never delete `tests/`. Coverage config is in `pyproject.toml`.

## Security / repo hygiene

- **CODEOWNERS:** `.github/CODEOWNERS` — `@danielnachumdev` owns all paths (branch protection can require code-owner review).
- **Dependabot:** `.github/dependabot.yml` — weekly `pip` + `github-actions` update PRs (labeled `noBump`).
- **Advisories:** `SECURITY.md` + GitHub private vulnerability reporting.
- **CD gate:** every PR into `main` needs exactly one of `bumpMajor` | `bumpMinor` | `bumpPatch` | `noBump` (ruleset / “Release label” check).

## Sensitive / ignored files

Do not commit: `client_secrets.json`, `.pypirc`, `.venv/`, `venv/`, `dist/`, `__pycache__/`, API keys. Track `uv.lock`. Respect `.gitignore`.

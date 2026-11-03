# GP Wrapper – Agent Context

Implementation guide for coding agents changing **gp_wrapper**. Product pitch and user-facing install: [`README.md`](README.md).

---

## Orientation

| Question | Answer |
| -------- | ------ |
| What is this? | Python package wrapping the **Google Photos Library API** |
| Importable code | `gp_wrapper/` |
| Toolchain | [uv](https://docs.astral.sh/uv/) + `pyproject.toml` / `uv.lock` |
| Python | `>=3.11` (CI matrix **3.11, 3.12, 3.13**) |
| Tests | `tests/` — pytest + coverage (≥95%); **never delete** |
| Secrets | Never commit `client_secrets.json`, `.pypirc`, API keys |

```text
.
├── .github/             # CODEOWNERS, dependabot.yml, thin CI/CD orchestrators
├── gp_wrapper/          # Importable package
├── tests/
├── pyproject.toml
├── uv.lock
├── README.md            # Marketing / user docs
├── LISENCE              # MIT (filename spelling is historical)
└── READMES/             # Examples + client_secrets shape
```

Shared CI/CD: [`danielnachumdev/actions`](https://github.com/danielnachumdev/actions) (`@v1`). How to adopt: [`HOW-TO-USE.md`](https://github.com/danielnachumdev/actions/blob/v1/HOW-TO-USE.md).

---

## Develop

```bash
uv sync                 # runtime only → .venv
uv sync --group dev     # + mypy, pylint, pytest, stubs
# or: uv sync --all-groups
```

`tool.uv.default-groups` is empty — `uv sync` does **not** install `dev` by default.

| Task | Command |
| ---- | ------- |
| Import smoke | `uv run python -c "import gp_wrapper"` |
| Tests | `uv run pytest` |
| Types | `uv run mypy` |
| Lint | `uv run pylint gp_wrapper` |

Config for mypy / pylint / pytest / coverage lives in `pyproject.toml`.

### Dependencies

- **Runtime:** `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`, `requests`, `tqdm`, `moviepy>=1.0.3,<2`
- **Dev group:** mypy, pylint, pytest, pytest-cov, pytest-xdist, `types-requests`, `types-tqdm`
- **Constraint:** keep `moviepy>=1.0.3,<2` (`moviepy.editor` was removed in 2.x — do not rewrite the moviepy API here)
- Security floors for Dependabot-fixed transitive deps are in `[tool.uv] constraint-dependencies`

Prefer editing floors in `pyproject.toml` and regenerating with `uv lock` / `uv sync --group dev`.

---

## Code style & domain notes

- Follow the writing-python skill when adding/refactoring modules (class-first, SRP files, no stub shims).
- Public surface is re-exported from `gp_wrapper/__init__.py` (`GooglePhotos`, `Album`, `MediaItem`, structures, enums, `ProgressBar`, …). `__version__` is `importlib.metadata.version("gp_wrapper")` — always the installed distribution version (CD stamps `pyproject.toml` into the release wheel).
- **File timestamps:** use `FileTimeService` (`utils/file_time.py`) — public `get`/`set`; portable `os.stat` / `os.utime`. `set` updates access/modification only (not Windows Date created).
- **`CoreMediaItem.upload_media`:** copies FileTimes onto transcoded non-mp4 videos after reading bytes; embeds MP4 `creation_time` from source mtime via `embed_mp4_creation_time` (`utils/mp4_metadata.py`) before upload bytes are read (Google Photos dates videos from container metadata). Transcode runs whether or not `pbar` is passed.

---

## PRs, CI, and releases

1. Branch off `main`; open a PR into `main`.
2. Attach **exactly one** semver label: `noBump` | `bumpPatch` | `bumpMinor` | `bumpMajor`.
3. **CI** — `…/ci.yml@v1` (tests) + `…/semver-ci.yml@v1` (validate label). Prefer **`CI / CI`** and **`Semver / Semver`**.
4. **CD** — `…/semver-cd.yml@v1` after CI succeeds on `main`: bump → wheel → GitHub Release → floating `vMAJOR` → **PyPI** (`publish-pypi: true`), or skip on `noBump`.
5. Version **source of truth** is GitHub Release tags. If none yet, CD seeds from `pyproject.toml`.
6. Dependabot PRs stay on `noBump`.
7. Change shared CI/semver behavior in **`danielnachumdev/actions`**, not by re-vendoring here.

**PyPI:** shipped only via CD (Trusted Publishing OIDC preferred for repo + workflow `cd.yml`; optional repo secret `PYPI_API_TOKEN`). Thin CD must grant `id-token: write` and pass `PYPI_API_TOKEN` by name. There is no local `publish.py` / quickpub path.

### Repo gates (already configured)

- `.github/CODEOWNERS` — `@danielnachumdev`
- Branch protection / ruleset: required **`CI / CI`** + **`Semver / Semver`**; code-owner reviews; no force-push to `main`
- Private vulnerability reporting via GitHub Security Advisories

---

## Sensitive / ignored

Do not commit: `client_secrets.json`, `.pypirc`, `.venv/`, `venv/`, `dist/`, `__pycache__/`, API keys. Track `uv.lock`. Respect `.gitignore`.

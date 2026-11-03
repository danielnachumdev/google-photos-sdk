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
├── publish.py           # Optional local quickpub → PyPI; CD owns GitHub Releases
├── README.md            # Marketing / user docs
├── LISENCE              # MIT (filename spelling is historical)
└── READMES/             # Examples + client_secrets shape
```

Shared CI/CD implementation: [`danielnachumdev/actions`](https://github.com/danielnachumdev/actions) (`@v1`). Playbook: [`PLAYBOOK.md`](https://github.com/danielnachumdev/actions/blob/v1/PLAYBOOK.md).

---

## Develop

```bash
uv sync                 # runtime only → .venv
uv sync --group dev     # + mypy, pylint, pytest, quickpub, stubs
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
- **Dev group:** mypy, pylint, pytest, pytest-cov, pytest-xdist, `quickpub>=4.1.3`, `types-requests`, `types-tqdm`
- **Constraint:** keep `moviepy>=1.0.3,<2` (`moviepy.editor` was removed in 2.x — do not rewrite the moviepy API here)
- Security floors for Dependabot-fixed transitive deps are in `[tool.uv] constraint-dependencies`

Prefer editing floors in `pyproject.toml` and regenerating with `uv lock` / `uv sync --group dev`.

---

## Code style & domain notes

- Follow the writing-python skill when adding/refactoring modules (class-first, SRP files, no stub shims).
- Public surface is re-exported from `gp_wrapper/__init__.py` (`GooglePhotos`, `Album`, `MediaItem`, structures, enums, `ProgressBar`, …). Keep `__version__` aligned with packaging when stamping releases (CD does this in the ephemeral wheel build).
- **File timestamps:** use `FileTimeService` (`utils/file_time.py`) — public `get`/`set`; portable `os.stat` / `os.utime`. `set` updates access/modification only (not Windows Date created).
- **`CoreMediaItem.upload_media`:** copies FileTimes onto transcoded non-mp4 videos after reading bytes; embeds MP4 `creation_time` from source mtime via `embed_mp4_creation_time` (`utils/mp4_metadata.py`) before upload bytes are read (Google Photos dates videos from container metadata). Transcode runs whether or not `pbar` is passed.

---

## PRs, CI, and releases

1. Branch off `main`; open a PR into `main`.
2. Attach **exactly one** release label: `bumpMajor` | `bumpMinor` | `bumpPatch` | `noBump`.
3. **CI** — thin `.github/workflows/ci.yml` calls `reusable-python-uv-ci.yml@v1` (Py 3.11–3.13). Aggregate check name **`CI`**.
4. **CD** — thin `.github/workflows/cd.yml` calls `reusable-release-label.yml@v1` + `reusable-semver-github-release.yml@v1`. After CI succeeds on `main`:
   - bump → stamp version, `uv build` wheel, GitHub Release + `.whl`
   - `noBump` → succeed without a Release
5. Version **source of truth** is GitHub Release tags (not bot-committed bumps). If no Release exists yet, CD seeds from `pyproject.toml`.
6. Dependabot PRs should stay on `noBump` (configured in `.github/dependabot.yml`).
7. Change shared release/CI behavior in **`danielnachumdev/actions`**, not by re-vendoring scripts here.

Optional local PyPI publish (not the default ship path):

```bash
# bump VERSION in publish.py if needed; demo=True → QA only
uv run --all-groups python publish.py
```

Needs `.pypirc`. License path is `./LISENCE`.

### Repo gates (already configured)

- `.github/CODEOWNERS` — `@danielnachumdev`
- Branch protection / ruleset: required **`CI`** + **`Release label / Release label`** (reusable-workflow nested name); code-owner reviews; no force-push to `main`
- Private vulnerability reporting via GitHub Security Advisories

---

## Sensitive / ignored

Do not commit: `client_secrets.json`, `.pypirc`, `.venv/`, `venv/`, `dist/`, `__pycache__/`, API keys. Track `uv.lock`. Respect `.gitignore`.

#!/usr/bin/env bash
# Usage: scripts/release/build_release_wheel.sh <vX.Y.Z> [out-dir]
# Stamps release version into packaging metadata (ephemeral checkout), then
# builds a wheel. Does not commit — GitHub Release tags are the version source.
set -euo pipefail

TAG="${1:?usage: build_release_wheel.sh <vX.Y.Z> [out-dir]}"
OUT_DIR="${2:-dist}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VERSION="${TAG#v}"

if [[ ! "${VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "build_release_wheel.sh: expected tag vX.Y.Z, got ${TAG}" >&2
  exit 1
fi

cd "${ROOT}"

python3 - "${VERSION}" <<'PY'
import pathlib
import re
import sys

version = sys.argv[1]


def replace_once(path: pathlib.Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    new, count = re.subn(pattern, replacement, text, count=1, flags=re.M)
    if count != 1:
        raise SystemExit(f"{path}: failed to update version ({count} matches for {pattern!r})")
    path.write_text(new, encoding="utf-8")


replace_once(
    pathlib.Path("pyproject.toml"),
    r'^version = "[^"]+"',
    f'version = "{version}"',
)
replace_once(
    pathlib.Path("gp_wrapper/__init__.py"),
    r'^__version__ = "[^"]+"',
    f'__version__ = "{version}"',
)
replace_once(
    pathlib.Path("publish.py"),
    r'^VERSION = "[^"]+"',
    f'VERSION = "{version}"',
)
print(f"stamped version → {version}")
PY

mkdir -p "${OUT_DIR}"
# Wheel basename may use underscores or hyphens depending on build backend.
rm -f "${OUT_DIR}"/gp_wrapper-"${VERSION}"-*.whl "${OUT_DIR}"/gp-wrapper-"${VERSION}"-*.whl

echo "Building wheel…"
uv build --wheel --out-dir "${OUT_DIR}"

WHEEL="$(ls -1 "${OUT_DIR}"/gp_wrapper-"${VERSION}"-*.whl "${OUT_DIR}"/gp-wrapper-"${VERSION}"-*.whl 2>/dev/null | head -1 || true)"
[[ -n "${WHEEL}" && -f "${WHEEL}" ]] || {
  echo "build_release_wheel.sh: no wheel for version ${VERSION} in ${OUT_DIR}" >&2
  ls -la "${OUT_DIR}" >&2 || true
  exit 1
}

printf 'wheel=%s\n' "${WHEEL}"

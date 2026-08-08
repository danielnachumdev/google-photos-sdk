"""Publish gp_wrapper via quickpub (QA, build, PyPI + git).

Bump `version` before a real release. Set `demo=True` to run checks without
build/upload. Requires `.pypirc`. License file on disk is `LISENCE`.

quickpub regenerates `setup.py`, `pyproject.toml`, and `MANIFEST.in` on a
successful publish — re-apply uv/dev-tool sections afterwards if needed.
Build itself is PEP 517 via `uv build` (pyproject.toml), not `setup.py sdist`.
"""

import logging
import shutil
import subprocess
from pathlib import Path

from tqdm import tqdm

from quickpub import (
    BuildSchema,
    DefaultPythonProvider,
    GithubUploadTarget,
    LicenseEnforcer,
    LocalVersionEnforcer,
    MypyRunner,
    PylintRunner,
    PypiRemoteVersionEnforcer,
    PypircEnforcer,
    PypircUploadTarget,
    PytestRunner,
    ReadmeEnforcer,
    publish,
)

logger = logging.getLogger(__name__)

VERSION = "0.9.8"


class UvBuildSchema(BuildSchema):
    """Build sdist/wheel with `uv build` from pyproject.toml (PEP 517)."""

    def __init__(self, pyproject_path: str = "./pyproject.toml") -> None:
        super().__init__(verbose=True)
        self._pyproject_path = pyproject_path

    def build(self, verbose: bool = False, *args, **kwargs) -> None:
        pyproject = Path(self._pyproject_path)
        if not pyproject.is_file():
            raise self.EXCEPTION_TYPE(f"Could not find {self._pyproject_path}")

        uv = shutil.which("uv")
        if uv is None:
            raise self.EXCEPTION_TYPE("`uv` is not on PATH; install uv to build")

        if verbose or self.verbose:
            logger.info("Building with uv from %s", pyproject.resolve())

        proc = subprocess.run(
            [uv, "build"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip() or "uv build failed"
            logger.error("uv build failed: %s", detail)
            raise self.EXCEPTION_TYPE(detail)


def main() -> None:
    publish(
        name="gp_wrapper",
        version=VERSION,
        author="danielnachumdev",
        author_email="danielnachumdev@gmail.com",
        description="A Google Photos API wrapper library",
        homepage="https://github.com/danielnachumdev/gp_wrapper",
        explicit_src_folder_path="./gp_wrapper",
        readme_file_path="./README.md",
        license_file_path="./LISENCE",
        min_python="3.8.0",
        keywords=["functions", "methods", "classes", "API"],
        dependencies=[
            "google-api-python-client",
            "google-auth-httplib2",
            "google-auth-oauthlib",
            "moviepy>=1.0.3,<2",
            "requests",
            "tqdm",
        ],
        enforcers=[
            PypircEnforcer(),
            ReadmeEnforcer(),
            LicenseEnforcer("./LISENCE"),
            LocalVersionEnforcer(),
            PypiRemoteVersionEnforcer(),
        ],
        global_quality_assurance_runners=[
            MypyRunner(bound="<=20", configuration_path="./pyproject.toml"),
            PylintRunner(bound=">=0.8", configuration_path="./pyproject.toml"),
            PytestRunner(bound=">=0.95"),
        ],
        python_interpreter_provider=DefaultPythonProvider(),
        build_schemas=[UvBuildSchema()],
        upload_targets=[PypircUploadTarget(), GithubUploadTarget()],
        pbar=tqdm(desc="QA task", leave=False),  # type: ignore[arg-type]
        demo=False,
    )


if __name__ == "__main__":
    main()

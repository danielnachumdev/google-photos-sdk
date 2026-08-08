"""Publish gp_wrapper via quickpub (QA, uv build, PyPI + git).

Bump `VERSION` before a real release. Set `demo=True` to run checks only.
Requires `.pypirc`. License file on disk is `LISENCE`.
"""

from tqdm import tqdm

from quickpub import (
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
    UvBuildSchema,
    publish,
)

VERSION = "0.9.9"


def main() -> None:
    publish(
        name="gp_wrapper",
        version=VERSION,
        author="danielnachumdev",
        author_email="danielnachumdev@gmail.com",
        description="A Google Photos API wrapper library",
        homepage="https://github.com/danielnachumdev/gp_wrapper",
        explicit_src_folder_path="./gp_wrapper",
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
        build_schemas=[UvBuildSchema()],
        generate_project_files=False,
        upload_targets=[PypircUploadTarget(), GithubUploadTarget()],
        pbar=tqdm(desc="QA task", leave=False),  # type: ignore[arg-type]
        demo=False,
    )


if __name__ == "__main__":
    main()

"""Local QA / emergency publish via quickpub (not the default ship path).

Prefer CD: ``.github/workflows/cd.yml`` → ``semver-cd@v1`` with ``publish-pypi: true``.
Bump `VERSION` only for local runs. Set `demo=True` to run checks only.
Requires `.pypirc` for uploads. License file on disk is `LISENCE`.
"""

from tqdm import tqdm

from quickpub import (
    DefaultPythonProvider,
    GithubUploadTarget,
    LicenseEnforcer,
    LocalVersionEnforcer,
    MypyRunner,
    PipPackageManager,
    PylintRunner,
    PypiRemoteVersionEnforcer,
    PypircEnforcer,
    PypircUploadTarget,
    PytestRunner,
    ReadmeEnforcer,
    UvBuildSchema,
    publish,
)

VERSION = "0.9.12"


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
        min_python="3.11",
        keywords=["functions", "methods", "classes", "API"],
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
        package_manager=PipPackageManager(),
        build_schemas=[UvBuildSchema()],
        generate_project_files=False,
        upload_targets=[PypircUploadTarget(), GithubUploadTarget()],
        pbar=tqdm(desc="QA task", leave=False),  # type: ignore[arg-type]
        demo=False,
    )


if __name__ == "__main__":
    main()

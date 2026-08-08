import re
from danielutils import cmrt, cm, read_file, get_files, directory_exists, create_directory  # type:ignore
VERSION_PATTERN = r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
TOML = "./pyproject.toml"
README = "./README.md"
DIST = "./dist"
REPORTS = "./reports"

PACKAGE = "gp_wrapper"


def get_latest(ver: str = '0.0.0') -> str:
    """returns the latest version currently in the DIST fuller

    Args:
        version (str, optional): the version to compare against. Defaults to '0.0.0'.

    Returns:
        str: the biggest version number
    """
    if not directory_exists(DIST):
        return ver
    DIST_PATTERN = PACKAGE+r"-(\d+)\.(\d+)\.(\d+)\.tar\.gz"
    best = ver
    for filename in get_files(DIST):
        a1, b1, c1 = best.split(".")
        match = re.match(DIST_PATTERN, filename)
        if match:
            a2, b2, c2 = match.groups()
            other_version = f"{a2}.{b2}.{c2}"
            if int(a2) > int(a1):
                best = other_version
            elif int(a2) == int(a1):
                if int(b2) > int(b1):
                    best = other_version
                elif int(b2) == int(b1):
                    if int(c2) > int(c1):
                        best = other_version
    return best


def main(ver: str):
    """main function, create a new release and update the files and call terminal to upload the release

    Args:
        version (str): the new version
    """

    def update_version(ver: str):
        """updates the new version number in the relevant files

        Args:
            version (_type_): _description_
        """
        def update_readme() -> None:
            lines = read_file(README)
            with open(README, "w", encoding="utf8") as f:
                for line in lines:
                    if line.startswith(f"# {PACKAGE} v="):
                        f.write(f"# {PACKAGE} v={ver}\n")
                    else:
                        f.write(line)

        def update_toml() -> None:
            lines = read_file(TOML)
            with open(TOML, "w", encoding="utf8") as f:
                for line in lines:
                    if line.startswith("version = "):
                        f.write(f"version = \"{ver}\"\n")
                    else:
                        f.write(line)
        update_readme()
        update_toml()

    latest = get_latest(ver)
    if latest != ver:
        print(f"{ver} is not the latest version, found {latest}, cancelling...")
        exit()
    print("updating version in files...")
    update_version(ver)
    print("Creating new distribution...")
    ret, stdout, stderr = cm("uv", "build")
    if ret != 0:
        print(stderr.decode())
        exit()
    print("Created dist successfully")
    # # twine upload dist/...
    ret, stdout, stderr = cm("wt.exe", "python", "-m",
                             "twine", "upload", "--config-file", "./.pypirc", f"./dist/{PACKAGE}-{ver}.tar.gz")
    if ret == 0:
        git(ver)
        print("DONE")
    else:
        print("twine failed")


def pytest() -> bool:
    """run pytest via uv (coverage gate is in pyproject.toml)."""
    print("running pytest")
    code, stdout, stderr = cm("uv", "run", "pytest")
    if stdout:
        print(stdout.decode(), end="")
    if code != 0:
        if stderr:
            print(stderr.decode(), end="")
        return False
    return True


def pylint() -> None:
    """run pylint (config from pyproject.toml)
    """
    print("running pylint...")
    for i, line in cmrt("pylint",
                        f"./{PACKAGE}", ">", f"{REPORTS}/pylint.txt"):
        print(line.decode(), end="")


def git(ver: str) -> None:
    """will add recent changes and automatically commit to git after the publication
    """
    print("updating git")
    cm("git add .")
    print("committing")
    cm(f"git commit -m \"updated to version {ver}\"")
    print("pushing")
    cm("git push")


def mypy() -> None:
    """run mypy (config from pyproject.toml)
    """
    print("running mypy")
    with open(f"{REPORTS}/mypy.txt", "w", encoding="utf8") as f:
        for i, line in cmrt("mypy", f"./{PACKAGE}"):
            f.write(line.decode())
            print(line.decode(), end="")


if __name__ == "__main__":
    if not directory_exists(REPORTS):
        create_directory(REPORTS)
    if not pytest():
        print("Tests failed, cancelling publish")
        exit(1)
    print("Passed all tests!")
    pylint()
    mypy()
    version = input(
        f"Please supply a new version number (LATEST = {get_latest()}): ")
    if re.match(VERSION_PATTERN, version):
        main(version)
    else:
        print("invalid version. example 1.0.5.20")
__all__: list = []

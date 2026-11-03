"""Portable file timestamps via FileTimeService (os.stat / os.utime)."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from gpsdk.utils.file_time import FileTime, FileTimeService


@pytest.fixture
def file_times() -> FileTimeService:
    return FileTimeService()


def test_filetime_repr_and_defaults() -> None:
    ft = FileTime()
    text = repr(ft)
    assert "FileTime" in text
    assert "creation" in text
    assert "access" in text
    assert "modification" in text
    assert ft.creation is None
    assert ft.access is None
    assert ft.modification is None


def test_set_all_none_raises(file_times: FileTimeService) -> None:
    with pytest.raises(ValueError, match="no meaning"):
        file_times.set("anything.txt", FileTime())


def test_get_missing_file(file_times: FileTimeService, tmp_path: Path) -> None:
    with pytest.raises(OSError):
        file_times.get(str(tmp_path / "nope.txt"))


def test_set_missing_file(file_times: FileTimeService, tmp_path: Path) -> None:
    with pytest.raises(OSError):
        file_times.set(
            str(tmp_path / "nope.txt"),
            FileTime(modification=datetime.now()),
        )


def test_get_reads_existing(file_times: FileTimeService, tmp_path: Path) -> None:
    path = tmp_path / "times.txt"
    path.write_text("hello", encoding="utf-8")
    ft = file_times.get(str(path))
    assert isinstance(ft.creation, datetime)
    assert isinstance(ft.access, datetime)
    assert isinstance(ft.modification, datetime)


def test_set_get_mtime_atime_roundtrip(file_times: FileTimeService, tmp_path: Path) -> None:
    path = tmp_path / "times.txt"
    path.write_text("hello", encoding="utf-8")
    access = datetime.now() - timedelta(days=3)
    modification = datetime.now() - timedelta(days=1)
    file_times.set(
        str(path),
        FileTime(access=access, modification=modification),
    )
    got = file_times.get(str(path))
    assert got.access is not None
    assert got.modification is not None
    assert abs((got.access - access).total_seconds()) <= 2
    assert abs((got.modification - modification).total_seconds()) <= 2


def test_set_creation_only_applies_to_atime_mtime(
    file_times: FileTimeService, tmp_path: Path
) -> None:
    path = tmp_path / "times.txt"
    path.write_text("hello", encoding="utf-8")
    creation = datetime.now() - timedelta(days=10)
    file_times.set(str(path), FileTime(creation=creation))
    got = file_times.get(str(path))
    assert got.access is not None
    assert got.modification is not None
    assert abs((got.access - creation).total_seconds()) <= 2
    assert abs((got.modification - creation).total_seconds()) <= 2


def test_set_modification_only_keeps_atime(
    file_times: FileTimeService, tmp_path: Path
) -> None:
    path = tmp_path / "times.txt"
    path.write_text("hello", encoding="utf-8")
    before = file_times.get(str(path))
    assert before.access is not None
    new_mtime = datetime.now() - timedelta(days=5)
    file_times.set(str(path), FileTime(modification=new_mtime))
    got = file_times.get(str(path))
    assert got.modification is not None
    assert abs((got.modification - new_mtime).total_seconds()) <= 2
    assert got.access is not None
    assert abs((got.access - before.access).total_seconds()) <= 2


def test_follow_symlinks_false_on_real_symlink(
    file_times: FileTimeService, tmp_path: Path
) -> None:
    target = tmp_path / "real.txt"
    target.write_text("data", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        os.symlink(str(target), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available")
    ft = file_times.get(str(link), follow_symlinks=False)
    assert isinstance(ft.modification, datetime)
    file_times.set(
        str(link),
        FileTime(modification=datetime.now() - timedelta(days=2)),
        follow_symlinks=False,
    )


def test_creation_prefers_st_birthtime(
    file_times: FileTimeService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "f.txt"
    path.write_text("x", encoding="utf-8")
    real = os.stat(str(path))
    birth = real.st_mtime - 1000.0

    class FakeStat:
        st_atime = real.st_atime
        st_mtime = real.st_mtime
        st_ctime = real.st_ctime
        st_birthtime = birth

    monkeypatch.setattr(os, "stat", lambda *_a, **_k: FakeStat())
    ft = file_times.get(str(path))
    assert ft.creation is not None
    assert abs(ft.creation.timestamp() - birth) <= 1


def test_get_follow_symlinks_false_calls_lstat(
    file_times: FileTimeService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "f.txt"
    path.write_text("x", encoding="utf-8")
    called = {"lstat": False}
    real_lstat = os.lstat

    def fake_lstat(p: str) -> os.stat_result:
        called["lstat"] = True
        return real_lstat(p)

    monkeypatch.setattr(os, "lstat", fake_lstat)
    file_times.get(str(path), follow_symlinks=False)
    assert called["lstat"]


def test_utime_follow_symlinks_notimplemented_fallback(
    file_times: FileTimeService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "f.txt"
    path.write_text("x", encoding="utf-8")
    calls: list[dict] = []

    def fake_utime(*_args, **kwargs):
        calls.append(dict(kwargs))
        if "follow_symlinks" in kwargs:
            raise NotImplementedError
        return None

    monkeypatch.setattr(os, "utime", fake_utime)
    file_times.set(str(path), FileTime(modification=datetime.now()))
    assert any("follow_symlinks" not in c for c in calls)


def test_import_gpsdk_does_not_require_win32_ctypes() -> None:
    import gpsdk

    assert gpsdk.MediaItem is not None

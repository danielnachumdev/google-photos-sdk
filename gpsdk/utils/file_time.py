"""Portable file timestamps via os.stat / os.utime (no Win32 ctypes).

Creation/birth time is *read* when the platform exposes it (``st_birthtime``,
or ``st_ctime`` on Windows). Setting a distinct creation time is not portable;
``FileTimeService.set`` applies access and modification with ``os.utime``. If
only ``creation`` is provided, it is used as a fallback for both atime and mtime.
``CoreMediaItem.upload_media`` copies source access/modification onto transcoded videos
and embeds MP4 ``creation_time`` (Photos dates videos from container metadata).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple


@dataclass
class FileTime:
    creation: Optional[datetime] = None
    access: Optional[datetime] = None
    modification: Optional[datetime] = None


class FileTimeService:
    """Read and write file timestamps using portable OS APIs."""

    def get(self, filepath: str, follow_symlinks: bool = True) -> FileTime:
        st = self._stat(filepath, follow_symlinks=follow_symlinks)
        return FileTime(
            creation=datetime.fromtimestamp(self._creation_ts(st)),
            access=datetime.fromtimestamp(st.st_atime),
            modification=datetime.fromtimestamp(st.st_mtime),
        )

    def set(
        self,
        filepath: str,
        filetime: FileTime,
        *,
        follow_symlinks: bool = True,
    ) -> None:
        self._require_any_timestamp(filetime)
        st = self._stat(filepath, follow_symlinks=follow_symlinks)
        atime_ns, mtime_ns = self._resolve_atime_mtime_ns(filetime, st)
        self._apply_utime(
            self._absolute_path(filepath),
            atime_ns,
            mtime_ns,
            follow_symlinks=follow_symlinks,
        )

    def _absolute_path(self, filepath: str) -> str:
        return os.path.normpath(os.path.abspath(str(filepath)))

    def _stat(self, filepath: str, follow_symlinks: bool = True) -> os.stat_result:
        path = self._absolute_path(filepath)
        if follow_symlinks:
            return os.stat(path)
        return os.lstat(path)

    def _creation_ts(self, st: os.stat_result) -> float:
        birth = getattr(st, "st_birthtime", None)
        if birth is not None:
            return float(birth)
        return float(st.st_ctime)

    def _to_ns(self, dt: Optional[datetime], fallback_seconds: float) -> int:
        seconds = dt.timestamp() if dt is not None else fallback_seconds
        return int(seconds * 1_000_000_000)

    def _require_any_timestamp(self, filetime: FileTime) -> None:
        if (
            filetime.access is None
            and filetime.modification is None
            and filetime.creation is None
        ):
            raise ValueError(
                "This function has no meaning if all values in 'filetime' argument are None. This is probably a mistake"
            )

    def _resolve_atime_mtime_ns(
        self, filetime: FileTime, st: os.stat_result
    ) -> Tuple[int, int]:
        atime = filetime.access if filetime.access is not None else filetime.creation
        mtime = (
            filetime.modification
            if filetime.modification is not None
            else filetime.creation
        )
        return (
            self._to_ns(atime, st.st_atime),
            self._to_ns(mtime, st.st_mtime),
        )

    def _apply_utime(
        self,
        filepath: str,
        atime_ns: int,
        mtime_ns: int,
        *,
        follow_symlinks: bool,
    ) -> None:
        try:
            os.utime(
                filepath,
                ns=(atime_ns, mtime_ns),
                follow_symlinks=follow_symlinks,
            )
        except (NotImplementedError, TypeError):
            os.utime(filepath, ns=(atime_ns, mtime_ns))


__all__ = [
    "FileTime",
    "FileTimeService",
]

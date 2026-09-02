"""MP4 container metadata helpers (Google Photos reads creation_time from bytes)."""
from __future__ import annotations

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

_MP4_CREATION_FMT = "%Y-%m-%dT%H:%M:%S.000000Z"


def embed_mp4_creation_time(filepath: str, stamp: datetime) -> bool:
    """Rewrite ``filepath`` so the MP4 carries ``creation_time`` for Photos.

    Returns False if ffmpeg is unavailable or the remux fails (caller may still
    upload the original bytes). Does not raise.
    """
    path = Path(filepath)
    if not path.is_file():
        return False
    try:
        import imageio_ffmpeg
    except ImportError:
        return False
    try:
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return False
    encoded = stamp.replace(microsecond=0).strftime(_MP4_CREATION_FMT)
    tmp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{path.stem}_meta_",
            suffix=path.suffix or ".mp4",
            dir=str(path.parent),
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
        result = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(path),
                "-c",
                "copy",
                "-map_metadata",
                "0",
                "-metadata",
                f"creation_time={encoded}",
                str(tmp_path),
            ],
            check=False,
            capture_output=True,
        )
        if result.returncode != 0 or not tmp_path.is_file() or tmp_path.stat().st_size == 0:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)
            return False
        tmp_path.replace(path)
        return True
    except Exception:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        return False


__all__ = ["embed_mp4_creation_time"]

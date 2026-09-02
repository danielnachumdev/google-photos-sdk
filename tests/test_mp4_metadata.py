"""Tests for MP4 creation_time embedding (Google Photos capture date)."""
from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

import imageio_ffmpeg
import pytest

from gp_wrapper.utils.mp4_metadata import embed_mp4_creation_time


def _write_tiny_mp4(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=64x64:d=0.1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def _read_creation_time(path: Path):
    from typing import Optional

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run(
        [ffmpeg, "-i", str(path), "-f", "ffmetadata", "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    blob = f"{result.stdout}\n{result.stderr}"
    for line in blob.splitlines():
        if "creation_time" not in line:
            continue
        raw = line.split(":", 1)[-1].strip()
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return None


def test_embed_mp4_creation_time_sets_container_metadata(tmp_path: Path) -> None:
    path = tmp_path / "clip.mp4"
    _write_tiny_mp4(path)
    stamp = datetime(2011, 4, 18, 15, 11, 58)
    assert embed_mp4_creation_time(str(path), stamp) is True
    assert _read_creation_time(path) == stamp


def test_embed_mp4_creation_time_missing_file_returns_false(tmp_path: Path) -> None:
    assert embed_mp4_creation_time(str(tmp_path / "missing.mp4"), datetime(2012, 1, 1)) is False


def test_embed_mp4_creation_time_garbage_bytes_returns_false(tmp_path: Path) -> None:
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"not-an-mp4")
    assert embed_mp4_creation_time(str(path), datetime(2012, 1, 1)) is False

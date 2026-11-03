"""Tests for gpsdk.utils.pbar."""
from __future__ import annotations

import pytest
from tqdm import tqdm

from gpsdk.utils.pbar import DEFAULT_BAR_FORMAT, ProgressBar, ProgressBarInjector

from .conftest import DummyProgressBar


def test_tqdm_is_virtual_progress_bar_subclass() -> None:
    assert issubclass(tqdm, ProgressBar)
    assert isinstance(tqdm(total=1, disable=True), ProgressBar)


def test_progress_bar_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        ProgressBar(total=1)  # type: ignore[abstract]


def test_dummy_progress_bar_init_and_methods() -> None:
    bar = DummyProgressBar(total=10, position=1, unit="files")
    assert bar.total == 10
    assert bar.position == 1
    assert bar.unit == "files"
    assert DEFAULT_BAR_FORMAT in bar.bar_format or bar.bar_format == DEFAULT_BAR_FORMAT
    bar.update(2)
    bar.write("hello", "world")
    bar.reset()
    assert bar.updates == [2]
    assert bar.writes == ["hello world"]
    assert bar.reset_count == 1


class _FakeBytes:
    """Sliceable bytes-like object with an arbitrary logical size."""

    def __init__(self, size: int, fill: bytes = b"x") -> None:
        self._size = size
        self._fill = fill

    def __len__(self) -> int:
        return self._size

    def __getitem__(self, sl: slice) -> bytes:
        start, stop, _ = sl.indices(self._size)
        return self._fill * max(0, stop - start)


def test_injector_len_and_kb_unit() -> None:
    data = b"a" * 2000  # > 1 KB, < 1 MB
    bar = DummyProgressBar(total=0)
    inj = ProgressBarInjector(data, bar, chunk_size=512)
    assert len(inj) == 2000
    chunks = list(inj)
    assert b"".join(chunks) == data
    assert bar.unit == "KB"
    assert bar.reset_count == 1
    assert bar.updates
    assert bar.bar_format == DEFAULT_BAR_FORMAT


def test_injector_mb_unit() -> None:
    data = _FakeBytes(2 * 1024 * 1024 + 10)
    bar = DummyProgressBar(total=0)
    inj = ProgressBarInjector(data, bar, chunk_size=256 * 1024)  # type: ignore[arg-type]
    chunks = list(inj)
    assert len(chunks) >= 1
    assert bar.unit == "MB"
    assert bar.reset_count == 1


def test_injector_gb_unit() -> None:
    data = _FakeBytes(2 * 1024 * 1024 * 1024 + 10)
    bar = DummyProgressBar(total=0)
    inj = ProgressBarInjector(data, bar, chunk_size=512 * 1024 * 1024)  # type: ignore[arg-type]
    chunks = list(inj)
    assert len(chunks) >= 1
    assert bar.unit == "GB"
    assert bar.reset_count == 1

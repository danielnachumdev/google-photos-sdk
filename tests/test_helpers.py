"""Tests for gpsdk.utils.helpers."""
from __future__ import annotations

import pytest

from gpsdk.utils.helpers import (
    batchify,
    get_python_version,
    json_default,
    memo,
    slowdown,
    split_iterable,
)
from gpsdk.utils.structures.data_types import SimpleMediaItem


def test_get_python_version_matches_platform() -> None:
    ver = get_python_version()
    assert len(ver) >= 2
    assert ver[0] == 3
    assert all(isinstance(p, int) for p in ver)


def test_split_iterable_empty() -> None:
    assert list(split_iterable([], 3)) == [[]]


def test_split_iterable_exact_batches() -> None:
    assert list(split_iterable([1, 2, 3, 4], 2)) == [[1, 2], [3, 4]]


def test_split_iterable_remainder() -> None:
    assert list(split_iterable(range(5), 2)) == [[0, 1], [2, 3], [4]]


def test_batchify_empty() -> None:
    assert batchify([], 3) == []


def test_batchify_partial_last_batch() -> None:
    assert batchify([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_batchify_exact() -> None:
    assert batchify([1, 2, 3], 3) == [[1, 2, 3]]


def test_json_default_dunder_json() -> None:
    class HasJson:
        def __json__(self):
            return {"ok": True}

    assert json_default(HasJson()) == {"ok": True}


def test_json_default_gpsdk_object() -> None:
    item = SimpleMediaItem("tok", "a.jpg")
    dumped = json_default(item)
    assert isinstance(dumped, str)
    assert dumped  # Printable __str__


def test_json_default_other_object() -> None:
    class Other:
        pass

    other = Other()
    assert json_default(other) == str(id(other))


def test_json_default_without_dict() -> None:
    assert json_default(42) == str(id(42))


def test_slowdown_rejects_non_numeric() -> None:
    with pytest.raises(ValueError, match="must be a number"):
        slowdown("nope")  # type: ignore[arg-type]


def test_slowdown_spaces_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("gpsdk.utils.helpers.time.sleep", lambda s: sleeps.append(s))
    times = iter([100.0, 100.1, 100.2])
    monkeypatch.setattr("gpsdk.utils.helpers.time.time", lambda: next(times))

    @slowdown(2)
    def ping(x):
        return x

    assert ping(1) == 1
    assert ping(2) == 2
    # first call: prev_start is -inf → no sleep; second call waits
    assert sleeps and sleeps[0] > 0


def test_memo_caches_positional() -> None:
    calls: list[tuple] = []

    @memo
    def add(a, b):
        calls.append((a, b))
        return a + b

    assert add(1, 2) == 3
    assert add(1, 2) == 3
    assert calls == [(1, 2)]
    assert add(2, 2) == 4
    assert calls == [(1, 2), (2, 2)]


def test_memo_with_kwargs() -> None:
    @memo
    def f(a, *, b=0):
        return a + b

    assert f(1, b=2) == 3
    # existing keying uses kwarg *names* only; second call hits cache
    assert f(1, b=99) == 3

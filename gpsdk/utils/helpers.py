import functools
import time
import platform
from typing import Any, Callable, ForwardRef, Generator, Iterable, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


def get_python_version() -> tuple[int, int, int]:
    """return the version of python that is currently running this code

    Returns:
        tuple[int, int, int]: version
    """
    major, minor, patch, *_ = (int(v) for v in platform.python_version().split("."))
    return major, minor, patch


def split_iterable(iterable: Iterable[T], batch_size: int) -> Generator[list[T], None, None]:
    """will yield sub-iterables each the size of 'batch_size'

    Args:
        iterable (Iterable[T]): the iterable to split
        batch_size (int): the size of each sub-iterable

    Yields:
        Generator[list[T], None, None]: resulting value
    """
    batch: list[T] = []
    for i, item in enumerate(iterable):
        if i % batch_size == 0:
            if len(batch) > 0:
                yield batch
            batch = []
        batch.append(item)
    yield batch


def json_default(obj: Any) -> str:
    """a default handler when using json over a non-json-serializable object

    Args:
        obj (Any): non-json-serializable object

    Returns:
        dict: result dict representing said object
    """
    if hasattr(obj, "__json__"):
        return getattr(obj, "__json__")()
    if hasattr(obj, "__dict__") and obj.__module__.split(".")[0] == "gpsdk":
        # json.dumps(obj.__dict__, indent=4, default=json_default)
        return str(obj)
    return str(id(obj))


def slowdown(interval: ForwardRef("Seconds")):  # type:ignore
    """will slow down function calls to a minimum of specified call over time span

    Args:
        minimal_interval_duration (float): duration to space out calls
    """
    from .structures import Seconds, Milliseconds
    if not isinstance(interval, (int, float)):
        raise ValueError("minimal_interval_duration must be a number")

    def deco(func: Callable[P, T]) -> Callable[P, T]:  # type:ignore
        index = 0
        prev_start: float = -float("inf")

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            nonlocal index, prev_start
            start = time.time()
            time_passed: Milliseconds = (start - prev_start) / 1000
            time_to_wait: Seconds = interval - time_passed
            if time_to_wait > 0:
                time.sleep(time_to_wait)
            res = func(*args, **kwargs)
            prev_start = start
            return res

        return wrapper

    return deco


def memo(func):
    """memoizes a function
    """
    dct: dict = {}

    def wrapper(*args, **kwargs):
        if (args, *kwargs) in dct:
            return dct[(args, *kwargs)]
        res = func(*args, **kwargs)
        dct[(args, *kwargs)] = res
        return res

    return wrapper


def batchify(objects: Iterable[T], batch_max_size: int) -> list[list[T]]:
    """split an iterable of objects into natches of these objects"""
    batches = []
    batch = []
    for obj in objects:
        batch.append(obj)
        if len(batch) == batch_max_size:
            batches.append(batch)
            batch = []
    if batch:
        batches.append(batch)
    return batches


__all__ = [
    "split_iterable",
    "json_default",
    "slowdown",
    "get_python_version",
    "memo",
    "batchify"
]

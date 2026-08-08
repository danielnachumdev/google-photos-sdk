import functools
import time
import platform
from typing import Callable, TypeVar, Generator, Iterable, Any, ForwardRef


def _get_python_version_untyped() -> tuple:
    values = (int(v) for v in platform.python_version().split("."))
    try:
        return tuple(values)  # type:ignore
    except:
        from builtins import tuple
        return tuple(values)  # type:ignore


if _get_python_version_untyped() < (3, 9):
    from typing import Tuple as t_tuple, List as t_list
else:
    from builtins import tuple as t_tuple, list as t_list  # type:ignore


def get_python_version() -> t_tuple[int, int, int]:
    """return the version of python that is currently running this code

    Returns:
        tuple[int, int, int]: version
    """
    return _get_python_version_untyped()  # type:ignore


if get_python_version() < (3, 9):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec  # type:ignore #pylint: disable=ungrouped-imports
P = ParamSpec("P")
T = TypeVar("T")


def split_iterable(iterable: Iterable[T], batch_size: int) -> Generator[t_list[T], None, None]:
    """will yield sub-iterables each the size of 'batch_size'

    Args:
        iterable (Iterable[T]): the iterable to split
        batch_size (int): the size of each sub-iterable

    Yields:
        Generator[list[T], None, None]: resulting value
    """
    batch: t_list[T] = []
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
    if hasattr(obj, "__dict__") and obj.__module__.split(".")[0] == "gp_wrapper":
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


def batchify(objects: Iterable[T], batch_max_size: int) -> t_list[t_list[T]]:
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

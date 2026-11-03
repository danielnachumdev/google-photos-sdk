import math
from typing import Iterable
from abc import ABC, abstractmethod
from tqdm import tqdm


DEFAULT_BAR_FORMAT = "{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}"


class ProgressBar(ABC):
    """An interface

    Args:
        ABC (_type_): _description_
    """

    @abstractmethod
    def __init__(self, total, position: int = 0, unit="it", bar_format: str = DEFAULT_BAR_FORMAT, **kwargs) -> None:
        self.total = total
        self.position = position
        self.unit = unit
        self.bar_format = bar_format

    @abstractmethod
    def update(self, amount: float = 1) -> None:
        """A function to update the progress-bar's value by a positive relative amount
        """

    @abstractmethod
    def write(self, *args, sep=" ", end="\n") -> None:
        """A function to write additional text with the progress bar
        """

    @abstractmethod
    def reset(self) -> None:
        """A function to reset the progress-bar's progress
        """


ProgressBar.register(tqdm)


class ProgressBarInjector:
    """allows seeing an indication of the progress of the request using tqdm
    """

    def __init__(self, data: bytes, pbar: ProgressBar, chunk_size: int = 8192) -> None:
        self.data = data
        self._len = len(self.data)
        self.pbar = pbar
        self.chunk_size = chunk_size

    def __len__(self) -> int:
        return self._len

    def __iter__(self) -> Iterable[bytes]:
        num_of_chunks = math.ceil(len(self)/self.chunk_size)
        chunks = (self.data[i:i + self.chunk_size]
                  for i in range(0, len(self), self.chunk_size))
        KB = 1024
        MB = 1024*KB
        GB = 1024*MB

        if len(self)/GB > 1:
            total = len(self)/GB
            unit = "GB"
        elif len(self)/MB > 1:
            total = len(self)/MB
            unit = "MB"
        else:
            total = len(self)/KB
            unit = "KB"

        update_amount = total/num_of_chunks
        self.pbar.unit = str(unit)
        self.pbar.total = str(total)
        self.pbar.bar_format = DEFAULT_BAR_FORMAT
        for chunk in chunks:
            yield chunk
            self.pbar.update(update_amount)
        self.pbar.reset()


__all__ = [
    "ProgressBar",
    "ProgressBarInjector"
]

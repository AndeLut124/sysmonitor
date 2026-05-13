from collections import deque
from typing import TypeVar, Generic

T = TypeVar("T")


class RingBuffer(Generic[T]):
    """Кольцевой буфер фиксированного размера."""

    def __init__(self, max_size: int = 60):
        self._buffer: deque[T] = deque(maxlen=max_size)

    def push(self, item: T) -> None:
        self._buffer.append(item)

    def get_all(self) -> list[T]:
        return list(self._buffer)

    def get_last(self) -> T | None:
        return self._buffer[-1] if self._buffer else None

    def clear(self) -> None:
        self._buffer.clear()

    @property
    def size(self) -> int:
        return len(self._buffer)
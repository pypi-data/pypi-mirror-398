from __future__ import annotations

__all__ = ["WeakFifoSet"]

from typing import Generic
from typing import TypeVar
from weakref import ref

_T = TypeVar("_T")


class WeakFifoSet(Generic[_T]):
    def __init__(self) -> None:
        self._dict: dict[ref[_T], None] = {}

    def add(self, item: _T, /) -> None:
        ref_item = ref(item)
        try:
            del self._dict[ref_item]
        except KeyError:
            pass
        self._dict[ref(item)] = None

    def remove(self, item: _T, /) -> None:
        del self._dict[ref(item)]

    def pop(self) -> _T:
        while True:
            print(self._dict)
            try:
                ref = next(iter(self._dict.keys()))
            except StopIteration:
                raise IndexError()
            del self._dict[ref]
            item = ref()
            if item is not None:
                return item

    def clear(self) -> None:
        self._dict.clear()

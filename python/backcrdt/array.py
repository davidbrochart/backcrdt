from __future__ import annotations

from typing import Any, overload

from .base import BaseType, base_types
from .transaction import Transaction
from ._backcrdt import _Array


class Array(BaseType):
    def __init__(self, init: list | None = None) -> None:
        super().__init__(init)

    def _init(self, value: list | None) -> None:
        if value is None:
            return

        with self.doc.transaction() as txn:
            for i, v in enumerate(value):
                self._set(i, v)



    def _set(self, index: int, value: Any) -> None:
        with self.doc.transaction() as txn:
            self._forbid_read_transaction(txn)
            if isinstance(value, BaseType):
                self._insert_and_mount(value, txn, index)
            else:
                self._mounted.insert(txn._txn, index, value)

    def insert(self, index: int, value: Any) -> None:
        with self.doc.transaction() as txn:
            if isinstance(value, BaseType):
                self._insert_and_mount(value, txn, index)
            else:
                self._mounted.insert(txn._txn, index, value)

    def append(self, value: Any) -> None:
        self += [value]

    def __add__(self, value: list[Any]) -> Array:
        with self.doc.transaction():
            length = len(self)
            self[length:length] = value
            return self

    def __radd__(self, value: list[Any]) -> Array:
        self[0:0] = value
        return self

    @overload
    def __setitem__(self, key: int, value: Any) -> None: ...

    @overload
    def __setitem__(self, key: slice, value: list[Any]) -> None: ...

    def __setitem__(self, key, value):
        with self.doc.transaction():
            if isinstance(key, int):
                key = self._check_index(key)
                del self[key]
                self[key:key] = [value]
            elif isinstance(key, slice):
                if key.step is not None:
                    raise RuntimeError("Step not supported")
                if key.start != key.stop:
                    raise RuntimeError("Start and stop must be equal")
                if key.start > len(self) or key.start < 0:
                    raise RuntimeError("Index out of range")
                for i, v in enumerate(value):
                    self._set(i + key.start, v)
            else:
                raise RuntimeError("Index must be of type integer")

    @overload
    def __getitem__(self, key: int) -> Any: ...

    @overload
    def __getitem__(self, key: slice) -> list[Any]: ...

    def __getitem__(self, key):
        with self.doc.transaction() as txn:
            if isinstance(key, int):
                key = self._check_index(key)
                return self._mounted.get(txn._txn, key)
            elif isinstance(key, slice):
                i0 = 0 if key.start is None else key.start
                i1 = len(self) if key.stop is None else key.stop
                step = 1 if key.step is None else key.step
                return [self[i] for i in range(i0, i1, step)]

    def __iter__(self) -> ArrayIterator:
        return ArrayIterator(self)

    def __contains__(self, item: T) -> bool:
        return item in [value for value in self]

    def _check_index(self, idx: int) -> int:
        if not isinstance(idx, int):
            raise RuntimeError("Index must be of type integer")
        length = len(self)
        if idx < 0:
            idx += length
        if idx < 0 or idx >= length:
            raise IndexError("Array index out of range")
        return idx

    def __delitem__(self, key: int | slice) -> None:
        with self.doc.transaction() as txn:
            self._forbid_read_transaction(txn)
            if isinstance(key, int):
                key = self._check_index(key)
                self._mounted.remove_range(txn._txn, key, 1)
            elif isinstance(key, slice):
                if key.step is not None:
                    raise RuntimeError("Step not supported")
                if key.start is None:
                    i = 0
                elif key.start < 0:
                    raise RuntimeError("Negative start not supported")
                else:
                    i = key.start
                if key.stop is None:
                    n = len(self) - i
                elif key.stop < 0:
                    raise RuntimeError("Negative stop not supported")
                else:
                    n = key.stop - i
                self._mounted.remove_range(txn._txn, i, n)
            else:
                raise TypeError(
                    f"Array indices must be integers or slices, not {type(key).__name__}"
                )
    def __len__(self) -> int:
        with self.doc.transaction() as txn:
            return self._mounted.len(txn._txn)

    def to_py(self) -> list:
        return list(self._mounted.to_py())


class ArrayIterator:
    def __init__(self, array: Array):
        self.array = array
        self.length = len(array)
        self.idx = 0

    def __iter__(self) -> ArrayIterator:
        return self  # pragma: nocover

    def __next__(self) -> Any:
        if self.idx == self.length:
            raise StopIteration

        res = self.array[self.idx]
        self.idx += 1
        return res


base_types[_Array] = Array

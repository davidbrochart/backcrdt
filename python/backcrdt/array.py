from __future__ import annotations

from typing import Any

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
                if isinstance(v, BaseType):
                    self._insert_and_mount(v, txn, i)
                else:
                    self._mounted.insert(txn._txn, i, v)

    def insert(self, index: int, value: Any) -> None:
        with self.doc.transaction() as txn:
            if isinstance(value, BaseType):
                self._insert_and_mount(value, txn, index)
            else:
                self._mounted.insert(txn._txn, index, value)

    def __len__(self) -> int:
        return self._mounted.len()

    def to_py(self) -> list:
        return list(self._mounted.to_py())


base_types[_Array] = Array

from __future__ import annotations

from .base import BaseType, base_types
from .text import Text
from .transaction import Transaction
from ._backcrdt import _Map


class Map(BaseType):
    def __init__(self, init: dict | None = None) -> None:
        super().__init__(init)

    def _init(self, value: dict | None) -> None:
        if value is None:
            return
        with self.doc.transaction() as txn:
            for k, v in value.items():
                self._set(k, v)

    def _set(self, key: str, value: object) -> None:
        with self.doc.transaction() as txn:
            if isinstance(value, BaseType):
                self._insert_and_mount(value, txn, key)
            else:
                self._mounted.insert(txn._txn, key, value)

    def __setitem__(self, key: str, value: T) -> None:
        self._set(key, value)

    def to_py(self) -> dict:
        return self._mounted.to_py()


base_types[_Map] = Map

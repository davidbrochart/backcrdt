from __future__ import annotations

from ._backcrdt import _Map
from .text import Text
from .transaction import Transaction


class Map:
    def __init__(self, init: dict | None = None) -> None:
        self._prelim = init
        self._mounted = None

    def _mount(self, txn: Transaction, name: str) -> None:
        self._mounted = txn._txn.mount_map(name, txn._multi_doc, txn._doc._id)
        self._prelim = None

    def insert(self, key: str, value: object) -> None:
        with self.doc.transaction() as txn:
            if isinstance(value, Text):
                value._mounted = self._mounted.insert_text_prelim(txn._txn, key)
            else:
                self._mounted.insert(txn._txn, key, value)

from .base import BaseType, base_types
from .transaction import Transaction
from ._backcrdt import _Text


class Text(BaseType):
    def __init__(self, init: str | None = None) -> None:
        super().__init__(init)

    def _init(self, value: str | None) -> None:
        if value is None:
            return
        with self.doc.transaction() as txn:
            self._mounted.insert(txn._txn, 0, value)

    def __str__(self) -> str:
        return self._mounted.to_string()

    def insert(self, index: int, value: str) -> None:
        with self.doc.transaction() as txn:
            self._mounted.insert(txn._txn, index, value)


base_types[_Text] = Text

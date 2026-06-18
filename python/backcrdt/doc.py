from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar
from uuid import uuid4

from .transaction import Transaction

if TYPE_CHECKING:
    from .multi_doc import MultiDoc

T = TypeVar("T")


class Doc:
    def __init__(
        self,
        multi_doc: "MultiDoc",
    ) -> None:
        self._multi_doc = multi_doc
        self._id = str(uuid4())
        self._txn: Transaction | None = None

    def transaction(self) -> Transaction:
        if self._txn is not None:
            return self._txn
        return self._multi_doc.transaction(self)

    def get_update(self) -> bytes:
        with self.transaction() as txn:
            return txn._txn.get_update()

    def apply_update(self, update: bytes) -> None:
        with self.transaction() as txn:
            txn._txn.apply_update(update)

    def get(self, key: str, *, type: type[T]) -> T:
        value = type()
        self[key] = value
        return value

    def __setitem__(self, key: str, value: T) -> None:
        with self.transaction() as txn:
            value._mount_root(txn, key)
        value.doc = self

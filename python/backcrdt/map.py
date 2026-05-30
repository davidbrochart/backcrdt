from ._backcrdt import _Map
from .transaction import Transaction


class Map:
    def __init__(self, init: dict | None = None) -> None:
        self._prelim = init
        self._mounted = None

    def _mount(self, txn: Transaction, name: str) -> None:
        self._mounted = txn._txn.mount_map(name, txn._multi_doc, txn._doc._id)
        self._prelim = None

    def insert(self, key: str, value: int) -> None:
        with self.doc.transaction() as txn:
            self._mounted.insert(txn._txn, key, value)

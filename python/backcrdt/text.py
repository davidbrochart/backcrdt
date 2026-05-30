from ._backcrdt import _Text
from .transaction import Transaction


class Text:
    def __init__(self, init: str | None = None) -> None:
        self._prelim = init
        self._mounted = None

    def _mount(self, txn: Transaction, name: str) -> None:
        self._mounted = txn._txn.mount_text(name, txn._multi_doc, txn._doc._id)
        self._prelim = None

    def __str__(self) -> str:
        return self._mounted.to_string()

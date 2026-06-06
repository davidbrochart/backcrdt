from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .transaction import Transaction


base_types: dict[Any, type[BaseType]] = {}


class BaseType(ABC):
    def __init__(
        self,
        init: Any = None,
    ) -> None:
        self._prelim = init
        self._mounted = None
        self._type_name = self.__class__.__name__.lower()

    @abstractmethod
    def _init(self, value: Any | None) -> None: ...

    def _mount_root(self, txn: Transaction, name: str) -> None:
        self._mounted = getattr(txn._txn, f"mount_{self._type_name}")(name, txn._multi_doc, txn._doc._id)
        self._init(self._prelim)

    def _mount(self, doc: Doc, mounted: BaseType) -> None:
        prelim = self._prelim
        self._prelim = None
        self.doc = doc
        self._mounted = mounted
        return prelim

    def _insert_and_mount(self, value: BaseType, txn: Transaction, *args) -> None:
        method = getattr(self._mounted, f"insert_{value._type_name}_prelim")
        mounted = method(txn._txn, *args)
        prelim = value._mount(self.doc, mounted)
        value._init(prelim)

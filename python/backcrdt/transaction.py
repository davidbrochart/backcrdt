import sys
from types import TracebackType
from typing import TYPE_CHECKING

from ._backcrdt import _MultiDoc, _Transaction

if sys.version_info >= (3, 11):
    from typing import Self
else:  # pragma: nocover
    from typing_extensions import Self

if TYPE_CHECKING:
    from .doc import Doc


class Transaction:
    def __init__(
        self,
        multi_doc: _MultiDoc,
        doc: "Doc",
    ) -> None:
        self._multi_doc = multi_doc
        self._doc = doc
        self._txn: _Transaction | None = None
        self._leases = 0

    def __enter__(self) -> Self:
        self._leases += 1
        if self._txn is None:
            self._txn = self._multi_doc.create_transaction(self._doc._id)
        self._doc._txn = self
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._leases -= 1
        if self._leases == 0:
            assert self._txn is not None
            try:
                self._txn.commit()
            finally:
                self._txn.drop()
                self._txn = None
                self._doc._txn = None

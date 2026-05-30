from pathlib import Path

from ._backcrdt import _MultiDoc
from .doc import Doc
from .transaction import Transaction


class MultiDoc:
    def __init__(
        self,
        dir_path: Path | str,
        *,
        client_id: int | None = None,
        max_dbs: int = 1,
        map_size: int = 10485760,
    ) -> None:
        _dir_path = dir_path if isinstance(dir_path, str) else str(dir_path)
        self._multi_doc = _MultiDoc(client_id, max_dbs, map_size, _dir_path)

    def get_doc(self) -> Doc:
        return Doc(self)

    def transaction(self, doc: Doc) -> Transaction:
        return Transaction(self._multi_doc, doc)

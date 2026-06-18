from __future__ import annotations

from .base import BaseType, base_types
from .transaction import Transaction
from ._backcrdt import _Text


class Text(BaseType):
    def __init__(self, init: str | None = None) -> None:
        super().__init__(init)

    def _init(self, value: str | None) -> None:
        if value is None:
            value = ""
        with self.doc.transaction() as txn:
            self._mounted.insert(txn._txn, 0, value)

    def __str__(self) -> str:
        with self.doc.transaction() as txn:
            return self._mounted.to_string(txn._txn)

    def to_py(self) -> str | None:
        if self._mounted is None:
            return self._prelim
        return str(self)

    def insert(self, index: int, value: str) -> None:
        with self.doc.transaction() as txn:
            self._mounted.insert(txn._txn, index, value)

    def __iadd__(self, value: str) -> Text:
        self.insert(len(self), value)
        return self

    def __len__(self) -> int:
        with self.doc.transaction() as txn:
            return self._mounted.len(txn._txn)

    def __iter__(self) -> Iterator[str]:
        return iter(str(self))

    def __contains__(self, item: str) -> bool:
        return item in str(self)

    def __delitem__(self, key: int | slice) -> None:
        """
        Removes the characters at the given index or slice:
        ```py
        Doc()["text"] = text = Text("Hello, World!")
        del text[5]
        assert str(text) == "Hello World!"
        del text[5:]
        assert str(text) == "Hello"
        ```

        Args:
            key: The index or the slice of the characters to remove.

        Raises:
            RuntimeError: Step not supported.
            RuntimeError: Negative start not supported.
            RuntimeError: Negative stop not supported.
        """
        with self.doc.transaction() as txn:
            self._forbid_read_transaction(txn)
            if isinstance(key, int):
                self._mounted.remove_range(txn._txn, key, 1)
            elif isinstance(key, slice):
                start, stop = self._check_slice(key)
                length = stop - start
                if length > 0:
                    self._mounted.remove_range(txn._txn, start, length)
            else:
                raise RuntimeError(f"Index not supported: {key}")

    def __getitem__(self, key: int | slice) -> str:
        """
        Gets the characters at the given index or slice:
        ```py
        Doc()["text"] = text = Text("Hello, World!")
        assert text[:5] == "Hello"
        ```

        Returns:
            The characters at the given index or slice.
        """
        value = str(self)
        return value[key]

    def __setitem__(self, key: int | slice, value: str) -> None:
        with self.doc.transaction() as txn:
            self._forbid_read_transaction(txn)
            if isinstance(key, int):
                value_len = len(value)
                if value_len != 1:
                    raise RuntimeError(
                        f"Single item assigned value must have a length of 1, not {value_len}"
                    )
                del self[key]
                self._mounted.insert(txn._txn, key, value)
            elif isinstance(key, slice):
                start, stop = self._check_slice(key)
                length = stop - start
                if length > 0:
                    self._mounted.remove_range(txn._txn, start, length)
                self._mounted.insert(txn._txn, start, value)
            else:
                raise RuntimeError(f"Index not supported: {key}")

    def _check_slice(self, key: slice) -> tuple[int, int]:
        if key.step is not None:
            raise RuntimeError("Step not supported")
        if key.start is None:
            start = 0
        elif key.start < 0:
            raise RuntimeError("Negative start not supported")
        else:
            start = key.start
        if key.stop is None:
            stop = len(self)
        elif key.stop < 0:
            raise RuntimeError("Negative stop not supported")
        else:
            stop = key.stop
        return start, stop

    def clear(self) -> None:
        del self[:]


base_types[_Text] = Text

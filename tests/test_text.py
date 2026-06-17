from pathlib import Path

import pytest
from backcrdt import Doc, MultiDoc, Text


def test_text_init(multi_doc: MultiDoc) -> None:
    doc = Doc(multi_doc)
    doc["text"] = text = Text("hello")
    assert str(text) == "hello"


def test_text_append(multi_doc: MultiDoc) -> None:
    doc = Doc(multi_doc)
    text = doc.get("text", type=Text)
    assert str(text) == ""
    with doc.transaction():
        text += "Hello,"
        text += " "
        text += "World!"
    assert str(text) == "Hello, World!"


def test_text_concurrent(two_multi_docs: tuple[MultiDoc, MultiDoc]) -> None:
    multi_doc0, multi_doc1 = two_multi_docs
    doc0 = Doc(multi_doc0)
    doc1 = Doc(multi_doc1)
    text0 = doc0.get("text", type=Text)
    text1 = doc1.get("text", type=Text)

    text0 += "hello"
    text1 += "bye"
    assert str(text0) == "hello"
    assert str(text1) == "bye"

    doc1.apply_update(doc0.get_update())
    doc0.apply_update(doc1.get_update())
    text = str(text0)
    assert text in ("byehello", "hellobye")
    assert str(text1) == text


def test_iterate(doc: Doc):
    doc["text"] = text = Text("abc")
    assert [char for char in text] == ["a", "b", "c"]


def test_slice(doc: Doc) -> None:
    doc["text"] = text = Text("hello")

    for i, c in enumerate("hello"):
        assert text[i] == c

    with pytest.raises(RuntimeError, match="Step not supported") as excinfo:
        text[1::2] = "a"

    with pytest.raises(RuntimeError, match="Negative start not supported") as excinfo:
        text[-1:] = "a"

    with pytest.raises(RuntimeError, match="Negative stop not supported") as excinfo:
        text[:-1] = "a"

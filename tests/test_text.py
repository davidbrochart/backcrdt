from pathlib import Path

import pytest
from backcrdt import Doc, Text


def test_text_init(doc0: Doc) -> None:
    doc0["text"] = text = Text("hello")
    assert str(text) == "hello"


def test_text_append(doc0: Doc) -> None:
    text = doc0.get("text", type=Text)
    assert str(text) == ""
    with doc0.transaction():
        text += "Hello,"
        text += " "
        text += "World!"
    assert str(text) == "Hello, World!"


@pytest.mark.parametrize("i", range(10))
def test_text_concurrent(doc0: Doc, doc1: Doc, i: int) -> None:
    text0 = doc0.get("text", type=Text)
    text1 = doc1.get("text", type=Text)

    text0 += "Hello"
    text1 += ", World!"
    assert str(text0) == "Hello"
    assert str(text1) == ", World!"

    doc1.apply_update(doc0.get_update())
    doc0.apply_update(doc1.get_update())
    text = str(text0)
    assert text in ("Hello, World!", ", World!Hello")
    assert str(text1) == text


def test_iterate(doc0: Doc):
    doc0["text"] = text = Text("abc")
    assert [char for char in text] == ["a", "b", "c"]


def test_slice(doc0: Doc) -> None:
    doc0["text"] = text = Text("hello")

    for i, c in enumerate("hello"):
        assert text[i] == c

    with pytest.raises(RuntimeError, match="Step not supported") as excinfo:
        text[1::2] = "a"

    with pytest.raises(RuntimeError, match="Negative start not supported") as excinfo:
        text[-1:] = "a"

    with pytest.raises(RuntimeError, match="Negative stop not supported") as excinfo:
        text[:-1] = "a"

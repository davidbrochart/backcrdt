import pytest
from backcrdt import Doc, Text
from pycrdt import (
    Doc as PyDoc,
    Text as PyText,
)


@pytest.mark.parametrize("i", range(10))
def test_text_concurrent(doc0: Doc, i: int) -> None:
    text0 = doc0.get("text", type=Text)
    doc1 = PyDoc()
    text1 = doc1.get("text", type=PyText)

    text0 += "Hello"
    text1 += ", World!"
    assert str(text0) == "Hello"
    assert str(text1) == ", World!"

    doc1.apply_update(doc0.get_update())
    doc0.apply_update(doc1.get_update())
    text = str(text0)
    assert text in ("Hello, World!", ", World!Hello")
    assert str(text1) == text

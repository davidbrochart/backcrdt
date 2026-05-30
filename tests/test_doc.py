from pathlib import Path

from backcrdt import Doc, MultiDoc, Text


def test_doc(tmp_path: Path) -> None:
    multi_doc = MultiDoc(tmp_path)
    doc = Doc(multi_doc)
    update = bytes([
        1, 3, 227, 214, 245, 198, 5, 0, 4, 1, 4, 116, 121, 112, 101, 1, 48, 68, 227, 214, 245,
        198, 5, 0, 1, 49, 68, 227, 214, 245, 198, 5, 1, 1, 50, 0,
    ])
    doc.apply_update(update)
    text = doc.get("type", type=Text)
    assert str(text) == "210"

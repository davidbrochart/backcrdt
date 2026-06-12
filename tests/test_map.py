from pathlib import Path

from backcrdt import Doc, Map, MultiDoc, Text


def test_doc(tmp_path: Path) -> None:
    multi_doc = MultiDoc(tmp_path, max_dbs=2)

    doc1 = Doc(multi_doc)
    map1 = doc1.get("map", type=Map)
    text = Text("hello")
    with doc1.transaction():
        map1["float"] = 1.1
        map1["int"] = 2
        map1["list"] = [1, "foo", 2]
        map1["string"] = "bar"
        map1["bool"] = True
        map1["text"] = text
        update1 = doc1.get_update()

    doc2 = Doc(multi_doc)
    doc2.apply_update(update1)
    map2 = doc2.get("map", type=Map)
    with doc2.transaction():
        update2 = doc2.get_update()

    assert update1 == update2
    assert map2.to_py() == {
        "float": 1.1,
        "int": 2,
        "list": [1, "foo", 2],
        "string": "bar",
        "bool": True,
        "text": "hello",
    }

from pathlib import Path

from backcrdt import Array, Doc, Map, MultiDoc, Text


def test_array(tmp_path: Path) -> None:
    multi_doc = MultiDoc(tmp_path, max_dbs=2)

    doc1 = Doc(multi_doc)
    with doc1.transaction():
        array1 = Array(["a", "b", 42, Map({"key": "value"}), Text("hello")])
        doc1["arr"] = array1
        update1 = doc1.get_update()

    doc2 = Doc(multi_doc)
    doc2.apply_update(update1)
    array2 = doc2.get("arr", type=Array)
    with doc2.transaction():
        update2 = doc2.get_update()

    assert array2.to_py() == ["a", "b", 42, {"key": "value"}, "hello"]
    assert len(array2) == 5

from pathlib import Path

from backcrdt import Doc, Map, MultiDoc


def test_doc(tmp_path: Path) -> None:
    multi_doc = MultiDoc(tmp_path, max_dbs=2)

    doc1 = Doc(multi_doc)
    map1 = doc1.get("map", type=Map)
    with doc1.transaction():
        map1.insert("number", 1)
        update1 = doc1.get_update()

    doc2 = Doc(multi_doc)
    doc2.apply_update(update1)
    map2 = doc2.get("map", type=Map)
    with doc2.transaction():
        update2 = doc2.get_update()

    assert update1 == update2

from pathlib import Path

from backcrdt import Doc, MultiDoc
import pytest


@pytest.fixture
def multi_doc(tmp_path: Path) -> MultiDoc:
    return MultiDoc(tmp_path)


@pytest.fixture
def two_multi_docs(tmp_path: Path) -> tuple[MultiDoc, MultiDoc]:
    tmp_path0 = tmp_path / "multi_doc0"
    tmp_path0.mkdir()
    tmp_path1 = tmp_path / "multi_doc1"
    tmp_path1.mkdir()
    return MultiDoc(tmp_path0), MultiDoc(tmp_path1)


@pytest.fixture
def doc(multi_doc: MultiDoc) -> Doc:
    return Doc(multi_doc)

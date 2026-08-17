from pathlib import Path

from backcrdt import Doc, MultiDoc
import pytest


@pytest.fixture
def doc0(tmp_path: Path) -> Doc:
    tmp_path0 = tmp_path / "multi_doc0"
    tmp_path0.mkdir()
    return Doc(MultiDoc(tmp_path0))


@pytest.fixture
def doc1(tmp_path: Path) -> Doc:
    tmp_path1 = tmp_path / "multi_doc1"
    tmp_path1.mkdir()
    return Doc(MultiDoc(tmp_path1))

from pathlib import Path

import pytest
from backcrdt import MultiDoc


def test_multi_doc(tmp_path: Path) -> None:
    MultiDoc(tmp_path)
    MultiDoc(tmp_path, client_id=2**32-1)

    with pytest.raises(ValueError, match="client_id must be an integer"):
        MultiDoc(tmp_path, client_id="a")

    with pytest.raises(ValueError, match="client_id must be a valid u32"):
        MultiDoc(tmp_path, client_id=2**32)

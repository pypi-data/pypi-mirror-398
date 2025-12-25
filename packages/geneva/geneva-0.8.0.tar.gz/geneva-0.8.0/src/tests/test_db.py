# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors
from pathlib import Path

import lancedb
import pyarrow as pa
import pytest

from geneva import connect


def test_connect(tmp_path: Path) -> None:
    db = connect(tmp_path)

    # Use lancedb to verify the results are the same
    ldb = lancedb.connect(tmp_path)

    # Create a Table with integer columns
    tbl = pa.Table.from_pydict({"a": [1, 2, 3], "b": [4, 5, 6]})
    db.create_table("table1", tbl)
    ldb_tbls = db.table_names()
    assert "table1" in ldb_tbls
    db.open_table("table1")

    db_tbls = db.table_names()
    assert db_tbls == ldb_tbls

    # Use lancedb to read the data back
    ldb_tbl = ldb.open_table("table1")
    assert ldb_tbl.to_arrow() == tbl
    db.drop_table("table1")


def test_connect_non_existent(tmp_path: Path) -> None:
    db = connect(tmp_path)
    assert db.table_names() == []

    with pytest.raises(ValueError, match=r".*was not found"):
        db.open_table("non_existent")

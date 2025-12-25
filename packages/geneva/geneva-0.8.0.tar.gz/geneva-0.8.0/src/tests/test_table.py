# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import platform
from collections.abc import Generator
from pathlib import Path

import lancedb
import numpy as np
import pandas as pd
import pyarrow as pa
import pytest
from pyarrow.fs import FileSystem, FileType

from geneva import connect, udf
from geneva.packager import DockerUDFPackager

pytestmark = pytest.mark.ray


def test_add_column(tmp_path: Path) -> None:
    db = connect(tmp_path)

    # create a basic table
    tbl = pa.Table.from_pydict({"id": [1, 2, 3, 4, 5, 6]})
    table = db.create_table("table1", tbl)

    # add a basic column
    table.add_columns(
        {"id2": "cast(null as string)"},
    )

    schema = table.schema

    assert len(schema) == 2
    field = schema.field("id2")
    assert field is not None
    assert field.type == pa.string()


def test_add_column_trailng_slash(tmp_path: Path) -> None:
    # make sure we handle trailing slashes the same way
    db = connect(str(tmp_path) + "/")

    # create a basic table
    tbl = pa.Table.from_pydict({"id": [1, 2, 3, 4, 5, 6]})
    table = db.create_table("table1", tbl)

    # add a basic column
    table.add_columns(
        {"id2": "cast(null as string)"},
    )

    schema = table.schema

    assert len(schema) == 2
    field = schema.field("id2")
    assert field is not None
    assert field.type == pa.string()


@pytest.fixture(params=["geneva", "lance"])
def db(tmp_path: Path, request) -> lancedb.DBConnection:
    """Create a temporary database for testing."""
    if request.param == "geneva":
        return connect(tmp_path)
    else:
        return lancedb.connect(tmp_path)


def test_create_table_and_index(db: lancedb.DBConnection) -> None:
    assert len(list(db.table_names())) == 0

    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5, 6],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"],
        }
    )
    db.create_table("tbl", df)

    assert len(list(db.table_names())) == 1
    assert db.table_names()[0] == "tbl"

    tbl = db.open_table("tbl")
    assert tbl.count_rows() == 6

    df = pd.DataFrame(
        {
            "id": [11, 12, 13, 14, 15, 16],
            "name": ["alice", "bob", "charlie", "david", "eve", "frank"],
        }
    )
    tbl.add(df)
    assert tbl.count_rows() == 12

    tbl.create_scalar_index("id")
    tbl.create_fts_index("name", use_tantivy=False)

    tbl.delete("id % 2 == 0")
    assert tbl.version == 5
    assert tbl.to_arrow().combine_chunks() == pa.Table.from_pydict(
        {
            "id": [1, 3, 5, 11, 13, 15],
            "name": ["Alice", "Charlie", "Eve", "alice", "charlie", "eve"],
        }
    )
    assert tbl.count_rows() == 6

    fts_results = tbl.search("charlie", query_type="fts").to_list()
    assert len(fts_results) == 2  # expect 'charlie' and 'Charlie'


def test_create_vector_idx(db: lancedb.DBConnection) -> None:
    dim = 128

    def producer() -> Generator[pa.Table, None, None]:
        rng = np.random.default_rng()
        for i in range(100):
            ids = pa.array([i * 20 + j for j in range(20)])
            values = pa.array(rng.random(20 * dim).astype(np.float32))
            fsl = pa.FixedSizeListArray.from_arrays(values, dim)  # type: ignore
            yield pa.Table.from_arrays([ids, fsl], ["id", "vector"])

    tbl = db.create_table("table", producer())
    assert tbl.count_rows() == 2000
    tbl.create_index(num_sub_vectors=8)

    indices = tbl.list_indices()
    assert indices[0].index_type == "IvfPq"

    # do a vector search
    rng = np.random.default_rng()
    vec = rng.random(dim)

    # this does not throw an exception
    vec_results = tbl.search(vec).to_list()

    assert len(vec_results) == 10


def test_add_invalid_computed_column(tmp_path: Path) -> None:
    db = connect(tmp_path)

    # create a basic table
    tbl = pa.Table.from_pydict({"id": [1, 2, 3, 4, 5, 6]})
    table = db.create_table("table1", tbl)

    @udf(data_type=pa.int64())
    def double_id(id2: int):  # noqa A002
        return id2 * 2

    # Validation catches missing input column 'id2' before circular dependency check
    with pytest.raises(
        ValueError,
        match=r"expects input columns \['id2'\].*not found in table schema",
    ):
        table.add_columns(
            {"id2": double_id},  # implicit udf arg name mapping
        )


def test_add_circular_dependency_column(tmp_path: Path) -> None:
    """Test that circular dependencies are detected."""
    db = connect(tmp_path)

    # create a basic table
    tbl = pa.Table.from_pydict({"id": [1, 2, 3, 4, 5, 6]})
    table = db.create_table("table1", tbl)

    # First add a column 'id2'
    table.add_columns({"id2": "cast(null as bigint)"})

    # Now try to create a UDF that depends on itself
    @udf(data_type=pa.int64())
    def self_referencing(id2: int) -> int:  # noqa A002
        return id2 * 2

    # This should fail with circular dependency error, not missing column
    with pytest.raises(
        ValueError, match=r"UDF output column id2 is not allowed to be in input"
    ):
        table.add_columns(
            {"id2": self_referencing},  # Column exists, but creates circular dependency
        )


def test_add_computed_column(tmp_path: Path) -> None:
    packager = DockerUDFPackager(
        # use prebuilt image tag so we don't have to build the image
        prebuilt_docker_img="test-image:latest"
    )
    db = connect(tmp_path, packager=packager)

    # create a basic table
    tbl = pa.Table.from_pydict({"id": [1, 2, 3, 4, 5, 6]})
    table = db.create_table("table1", tbl)

    @udf(data_type=pa.int64())
    def double_id(id: int):  # noqa A002
        return id * 2

    table.add_columns(
        {"id2": double_id},  # implicit udf arg name mapping
    )

    schema = table.schema

    assert len(schema) == 2
    field = schema.field("id2")
    assert field is not None
    assert field.type == pa.int64()

    assert len(field.metadata) == 8
    assert field.metadata[b"virtual_column"] == b"true"
    assert field.metadata[b"virtual_column.udf_backend"] == b"DockerUDFSpecV1"
    assert field.metadata[b"virtual_column.udf_name"] == b"double_id"
    assert field.metadata[b"virtual_column.udf_inputs"] == b'["id"]'
    assert field.metadata[
        b"virtual_column.platform.system"
    ] == platform.system().encode("utf-8")
    assert field.metadata[b"virtual_column.platform.arch"] == platform.machine().encode(
        "utf-8"
    )
    assert field.metadata[
        b"virtual_column.platform.python_version"
    ] == platform.python_version().encode("utf-8")

    # check that the UDF was actually uploaded
    fs, root_path = FileSystem.from_uri(f"{str(tmp_path)}/table1.lance")
    file_info = fs.get_file_info(
        f"{root_path}/{field.metadata[b'virtual_column.udf'].decode('utf-8')}"
    )
    assert file_info.type is not FileType.NotFound

    try:
        import ray  # noqa: F401

        # before materializing, the computed column should have nulls
        expected = pa.Table.from_pydict(
            {
                "id": [1, 2, 3, 4, 5, 6],
                "id2": pa.array([None] * 6, pa.int64()),
            }
        )
        assert table.to_arrow().equals(expected)

        # backfill and check values of computed column
        table.backfill("id2")
        assert table.to_pandas().equals(
            pd.DataFrame(
                {
                    "id": [1, 2, 3, 4, 5, 6],
                    "id2": [2, 4, 6, 8, 10, 12],
                }
            )
        )
    except ImportError:
        "Ray not installed, skipping value checks part of test"


def test_alter_computed_column(tmp_path: Path) -> None:
    packager = DockerUDFPackager(
        # use prebuilt image tag so we don't have to build the image
        prebuilt_docker_img="test-image:latest"
    )
    db = connect(tmp_path, packager=packager)

    # create a basic table
    tbl = pa.Table.from_pydict({"id": [1, 2, 3, 4, 5, 6]})
    table = db.create_table("table1", tbl)

    @udf(data_type=pa.int64())
    def double_id(id: int):  # noqa A002
        return id * 2

    table.add_columns(
        {"id2": double_id},  # implicit udf arg name mapping
    )

    schema = table.schema
    field = schema.field("id2")
    assert field.metadata[b"virtual_column.udf_name"] == b"double_id"

    try:
        import kubernetes  # noqa: F401
        import ray  # noqa: F401

        # before materializing, the computed column should have nulls
        expected = pa.Table.from_pydict(
            {
                "id": [1, 2, 3, 4, 5, 6],
                "id2": pa.array([None] * 6, pa.int64()),
            }
        )
        assert table.to_arrow().equals(expected)

        # backfill and check values of computed column
        table.backfill("id2")
        assert table.to_pandas().equals(
            pd.DataFrame(
                {
                    "id": [1, 2, 3, 4, 5, 6],
                    "id2": [2, 4, 6, 8, 10, 12],
                }
            )
        )
    except ImportError:
        "Ray not installed, skipping value checks part of test"

    # now check that we can replace the UDF with a new version:
    @udf(data_type=pa.int64())
    def triple_id(id: int):  # noqa A002
        return id * 3

    # "virtual_column" is deprecated, but still works for backwards compatibility
    table.alter_columns(
        {
            "path": "id2",
            "virtual_column": triple_id,
        }
    )

    table.alter_columns(
        {
            "path": "id2",
            "udf": triple_id,
        }
    )

    schema = table.schema
    field = schema.field("id2")
    assert field.metadata[b"virtual_column"] == b"true"
    assert field.metadata[b"virtual_column.udf_name"] == b"triple_id"
    assert field.metadata[b"virtual_column.udf_backend"] == b"DockerUDFSpecV1"

    # check that the UDF was actually uploaded
    fs, root_path = FileSystem.from_uri(f"{str(tmp_path)}/table1.lance")
    file_info = fs.get_file_info(
        f"{root_path}/{field.metadata[b'virtual_column.udf'].decode('utf-8')}"
    )
    assert file_info.type is not FileType.NotFound

    try:
        import kubernetes  # noqa: F401
        import ray  # noqa: F401

        # After the alter but before materializing, the computed column should
        # not have the old UDF's values.  It should have nulls.
        expected = pa.Table.from_pydict(
            {
                "id": [1, 2, 3, 4, 5, 6],
                "id2": [2, 4, 6, 8, 10, 12],
                #  TODO This should be "id2": pa.array([None] * 6, pa.int64()),
            }
        )
        assert table.to_arrow().equals(expected)

        # backfill and check values of computed column
        table.backfill("id2")
        assert table.to_pandas().equals(
            pd.DataFrame(
                {
                    "id": [1, 2, 3, 4, 5, 6],
                    "id2": [3, 6, 9, 12, 15, 18],
                }
            )
        )
    except ImportError:
        "Ray not installed, skipping value checks part of test"


def test_alter_computed_column_diff_col_name(tmp_path: Path) -> None:
    packager = DockerUDFPackager(
        # use prebuilt image tag so we don't have to build the image
        prebuilt_docker_img="test-image:latest"
    )
    db = connect(tmp_path, packager=packager)

    # create a basic table
    tbl = pa.Table.from_pydict({"seq": [1, 2, 3, 4, 5, 6]})
    table = db.create_table("table1", tbl)

    @udf(data_type=pa.int64())
    def double_id(id: int):  # noqa A002
        return id * 2

    table.add_columns(
        {"id2": (double_id, ["seq"])},  # explicit udf arg name mapping
    )

    schema = table.schema
    field = schema.field("id2")
    assert field.metadata[b"virtual_column.udf_name"] == b"double_id"

    # before materializing, the computed column should have nulls
    expected = pa.Table.from_pydict(
        {
            "seq": [1, 2, 3, 4, 5, 6],
            "id2": pa.array([None] * 6, pa.int64()),
        }
    )
    assert table.to_arrow().equals(expected)

    # backfill and check values of computed column
    table.backfill("id2")
    assert table.to_pandas().equals(
        pd.DataFrame(
            {
                "seq": [1, 2, 3, 4, 5, 6],
                "id2": [2, 4, 6, 8, 10, 12],
            }
        )
    )

    # now check that we can replace the UDF with a new version:
    @udf(data_type=pa.int64())
    def triple_id(id: int):  # noqa A002
        return id * 3

    table.alter_columns(
        *[
            {
                "path": "id2",
                "virtual_column": triple_id,
                "input_columns": ["seq"],
            }
        ]
    )

    schema = table.schema
    field = schema.field("id2")
    assert field.metadata[b"virtual_column"] == b"true"
    assert field.metadata[b"virtual_column.udf_name"] == b"triple_id"
    assert field.metadata[b"virtual_column.udf_backend"] == b"DockerUDFSpecV1"

    # check that the UDF was actually uploaded
    fs, root_path = FileSystem.from_uri(f"{str(tmp_path)}/table1.lance")
    file_info = fs.get_file_info(
        f"{root_path}/{field.metadata[b'virtual_column.udf'].decode('utf-8')}"
    )
    assert file_info.type is not FileType.NotFound

    # After the alter but before materializing, the computed column should
    # not have the old UDF's values.  It should have nulls.
    expected = pa.Table.from_pydict(
        {
            "seq": [1, 2, 3, 4, 5, 6],
            "id2": [2, 4, 6, 8, 10, 12],
            #  TODO This should be "id2": pa.array([None] * 6, pa.int64()),
        }
    )
    assert table.to_arrow().equals(expected)

    # backfill and check values of computed column
    table.backfill("id2")
    assert table.to_pandas().equals(
        pd.DataFrame(
            {
                "seq": [1, 2, 3, 4, 5, 6],
                "id2": [3, 6, 9, 12, 15, 18],
            }
        )
    )

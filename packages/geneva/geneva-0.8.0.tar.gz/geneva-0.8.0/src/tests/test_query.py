# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc

from geneva import connect
from geneva.packager import DockerUDFPackager
from geneva.transformer import udf


def test_scan_over_fragments(tmp_path: Path) -> None:
    db = connect(tmp_path)

    a = pa.array([1, 2, 3])
    b = pa.array([4, 5, 6])
    tbl = db.create_table("tbl", pa.Table.from_arrays([a, b], names=["a", "b"]))

    c = pa.array([7, 8, 9])
    d = pa.array([10, 11, 12])
    tbl.add(pa.Table.from_arrays([c, d], names=["a", "b"]))

    fragments = tbl.get_fragments()
    assert len(fragments) == 2

    query = (
        tbl.search()
        .enable_internal_api()
        .with_fragments(fragments[0].fragment_id)
        .select(["a"])
    )

    results = list(query.to_batches())

    assert len(results) == 1
    assert results[0]["a"].equals(a)

    # check that to_* functions from base query builder doesn't explode
    query.to_pandas()
    query.to_list()
    query.to_polars()


def test_query_parameters(tmp_path: Path) -> None:
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": range(100), "b": range(0, 200, 2)}))

    assert tbl.search().offset(10).limit(10).select(["a"]).to_arrow() == pa.table(
        {"a": range(10, 20)}
    )

    batches = tbl.search().to_batches(15)
    assert len(list(batches)) == 7


def test_udf_projection(tmp_path: Path) -> None:
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    @udf(data_type=pa.int64())
    def add_one(a: pa.Array) -> pa.Array:
        return pc.add(a, 1)

    query = tbl.search().select({"a": "a", "b": add_one})
    results = query.to_arrow()

    assert results == pa.table({"a": [1, 2, 3], "b": [2, 3, 4]})


def test_udf_projection_without_selected_input(tmp_path: Path) -> None:
    # In this test the UDF depends on 'a' but we don't select it in our
    # output.  We need to make sure it is loaded and then dropped
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    @udf(data_type=pa.int64())
    def add_one(a: pa.Array) -> pa.Array:
        return pc.add(a, 1)

    query = tbl.search().select({"b": add_one})
    results = query.to_arrow()

    assert results == pa.table({"b": [2, 3, 4]})


def test_udf_marshaling(tmp_path: Path) -> None:
    packager = DockerUDFPackager(prebuilt_docker_img="test-image:latest")
    db = connect(tmp_path, packager=packager)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    @udf(data_type=pa.int64())
    def add_one(a: pa.Array) -> pa.Array:
        return pc.add(a, 1)

    @udf(data_type=pa.int64())
    def add_two(a: pa.Array) -> pa.Array:
        return pc.add(a, 2)

    query = (
        tbl.search()
        .select({"my_udf": add_one, "my_other_udf": add_two})
        .to_query_object()
    )

    udfs = query.column_udfs
    assert udfs is not None
    assert len(udfs) == 2

    assert udfs[0].output_name == "my_udf"
    assert udfs[0].output_index == 0
    assert udfs[0].udf.name == "add_one"
    assert udfs[0].udf.backend == "DockerUDFSpecV1"
    assert len(udfs[0].udf.udf_payload) > 0

    assert udfs[1].output_name == "my_other_udf"
    assert udfs[1].output_index == 1
    assert udfs[1].udf.name == "add_two"
    assert udfs[1].udf.backend == "DockerUDFSpecV1"
    assert len(udfs[1].udf.udf_payload) > 0

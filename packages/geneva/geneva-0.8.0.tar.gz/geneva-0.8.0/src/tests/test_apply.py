# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import hashlib
import logging
from pathlib import Path

import lance
import pyarrow as pa
import pyarrow.compute as pc
import pytest
from yarl import URL

from geneva import CheckpointStore, connect, udf
from geneva.apply import (
    CheckpointingApplier,
    _check_fragment_data_file_exists,
    _legacy_fragment_dedupe_key,
    plan_read,
)
from geneva.apply.task import BackfillUDFTask
from geneva.debug.error_store import ErrorStore
from geneva.debug.logger import TableErrorLogger
from geneva.runners.ray.pipeline import FragmentWriterManager, _get_fragment_dedupe_key
from geneva.table import TableReference

_LOG = logging.getLogger(__name__)


@pytest.fixture
def tbl_ref(tmp_path) -> TableReference:
    return TableReference(table_id=["tbl"], version=None, db_uri=str(tmp_path))


def test_create_plan(tmp_path: Path, tbl_ref: TableReference) -> None:
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    plans = list(plan_read(tbl.uri, tbl_ref, ["a"], batch_size=16)[0])
    assert len(plans) == 1
    plan = plans[0]
    assert plan.uri == tbl.uri
    assert plan.offset == 0
    assert plan.limit == 3


def test_create_plan_with_diverse_shuffle(
    tmp_path: Path, tbl_ref: TableReference
) -> None:
    ds = lance.write_dataset(
        pa.table({"a": range(1024)}), tmp_path / "tbl", max_rows_per_file=16
    )

    plans = list(
        plan_read(ds.uri, tbl_ref, ["a"], batch_size=1, task_shuffle_diversity=4)[0]
    )
    assert len(plans) == 1024
    plan = plans[0]
    assert plan.uri == ds.uri
    assert plan.offset == 0
    assert plan.limit == 1


@udf(input_columns=["a"])
def one(*args, **kwargs) -> int:
    return 1


def test_applier(tmp_path: Path, tbl_ref: TableReference) -> None:
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    plans = list(plan_read(tbl.uri, tbl_ref, ["a"], batch_size=16)[0])
    assert len(plans) == 1
    plan = plans[0]
    assert plan.uri == tbl.uri
    assert plan.offset == 0
    assert plan.limit == 3

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"one": one}),
        checkpoint_uri=store.root,
    )
    key, cnt_udf_computed = applier.run(plan)
    batch = store[key]
    assert len(batch) == 3
    assert batch.to_pydict() == {"one": [1, 1, 1], "_rowaddr": [0, 1, 2]}
    assert cnt_udf_computed == 3


def test_checkpoint_key_format(tmp_path: Path, tbl_ref: TableReference) -> None:
    @udf(version="v0", input_columns=["a"])
    def times_two(a: int) -> int:
        return a * 2

    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3, 4]}))

    where = "a > 1"
    read_version = tbl.version

    plans = list(
        plan_read(
            tbl.uri,
            tbl_ref,
            ["a"],
            batch_size=2,
            where=where,
            read_version=read_version,
        )[0]
    )

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"b": times_two}, where=where),
        checkpoint_uri=store.root,
    )

    key, cnt_udf_computed = applier.run(plans[0])

    where_hash = hashlib.md5(where.encode()).hexdigest()
    uri_hash = hashlib.md5(tbl.uri.encode()).hexdigest()
    prefix = (
        f"udf-{times_two.name}_ver-{times_two.version}"
        f"_col-b_where-{where_hash}_uri-{uri_hash}_ver-{read_version}"
    )
    expected_key = (
        f"{prefix}_frag-{plans[0].dest_frag_id()}_"
        f"range-{plans[0].dest_offset()}-{plans[0].dest_offset() + plans[0].num_rows()}"
    )

    assert key == expected_key
    assert key in store
    # First batch has a values [1,2]; only 2 satisfies where
    assert cnt_udf_computed == 1


def test_plan_read_with_legacy_checkpoint_and_partial(
    tmp_path: Path, tbl_ref: TableReference
) -> None:
    """
    Legacy fragment checkpoints should be reused,
    partial old batch checkpoints should not skip.
    """
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))
    tbl.add(pa.table({"a": [4, 5, 6]}))  # second fragment

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    map_task = BackfillUDFTask(udfs={"one": one})

    # Insert legacy fragment-level checkpoint for fragment 0
    legacy_frag_key = _legacy_fragment_dedupe_key(tbl.uri, 0, map_task)
    store[legacy_frag_key] = pa.RecordBatch.from_pydict({"file": ["fragment0.lance"]})
    assert legacy_frag_key in store
    staging_dir = tmp_path / "data"
    staging_dir.mkdir(exist_ok=True)
    (staging_dir / "fragment0.lance").touch()

    # Insert an old-format partial batch checkpoint for fragment 1 (should be ignored)
    store["fragment_1_batch_0_50:old"] = pa.RecordBatch.from_pydict(
        {"file": ["partial_batch"]}
    )

    # Legacy checkpoint should be detectable
    assert _check_fragment_data_file_exists(
        tbl.uri, 0, map_task, store, dataset_version=tbl.version
    )

    plans, pipeline_args = plan_read(
        tbl.uri,
        tbl_ref,
        ["a"],
        batch_size=16,
        map_task=map_task,
        checkpoint_store=store,
    )

    task_list = list(plans)

    # fragment 0 should be skipped via legacy checkpoint
    # fragment 1 should still have tasks
    assert "skipped_fragments" in pipeline_args
    assert 0 in pipeline_args["skipped_fragments"]
    frag_ids = {t.dest_frag_id() for t in task_list}
    assert 0 not in frag_ids
    assert 1 in frag_ids
    assert len(task_list) > 0


def test_applier_with_where(tmp_path: Path, tbl_ref: TableReference) -> None:
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3, 4, 5, 6, 7, 8]}))

    plans = list(plan_read(tbl.uri, tbl_ref, ["a"], batch_size=3, where="a%2=0")[0])

    assert len(plans) == 3  # 1-3, 4-6, and 7-8
    plan = plans[0]
    assert plan.uri == tbl.uri
    assert plan.offset == 0
    assert plan.limit == 3

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"one": one}),
        checkpoint_uri=store.root,
    )

    # Lance forces us to eithe write the entire column or write an entire row.  This
    # applier writes the whole col.  So we actually do all the scans and filter at udf
    # execution time.  When the udf is not executed we return None.

    expected = [
        {"one": [None, 1, None], "_rowaddr": [0, 1, 2]},
        {"one": [1, None, 1], "_rowaddr": [3, 4, 5]},
        {"one": [None, 1], "_rowaddr": [6, 7]},
    ]

    expected_counts = [1, 2, 1]
    for i, plan in enumerate(plans):
        key, cnt_udf_computed = applier.run(plan)
        batch = store[key]
        assert batch.to_pydict() == expected[i]
        assert cnt_udf_computed == expected_counts[i]


def test_applier_with_where2(tmp_path: Path, tbl_ref: TableReference) -> None:
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3, 4, 5, 6, 7, 8]}))

    plans = list(plan_read(tbl.uri, tbl_ref, ["a"], batch_size=1, where="a%2=0")[0])

    assert len(plans) == 8  # 1-3, 4-6, and 7-8
    plan = plans[0]
    assert plan.uri == tbl.uri
    assert plan.offset == 0
    assert plan.limit == 1

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"one": one}),
        checkpoint_uri=store.root,
    )

    expected = [
        {"one": [None], "_rowaddr": [0]},
        {"one": [1], "_rowaddr": [1]},
        {"one": [None], "_rowaddr": [2]},
        {"one": [1], "_rowaddr": [3]},
        {"one": [None], "_rowaddr": [4]},
        {"one": [1], "_rowaddr": [5]},
        {"one": [None], "_rowaddr": [6]},
        {"one": [1], "_rowaddr": [7]},
    ]

    expected_counts = [0, 1, 0, 1, 0, 1, 0, 1]
    for i, plan in enumerate(plans):
        key, cnt_udf_computed = applier.run(plan)
        batch = store[key]
        assert batch.to_pydict() == expected[i]
        assert cnt_udf_computed == expected_counts[i]


def test_applier_with_incremental(tmp_path: Path, tbl_ref: TableReference) -> None:
    db = connect(tmp_path)
    tbl = db.create_table(
        "tbl",
        pa.table(
            {
                "a": [1, 2, 3, 4, 5, 6, 7, 8],
                "one": [
                    None,
                    1,
                    None,
                    1,
                    None,
                    1,
                    None,
                    1,
                ],
            }
        ),
    )

    # apply a update plan that covers the rest
    plans = list(
        plan_read(
            tbl.uri,
            tbl_ref,
            ["a", "one"],  # input col and carry forward the output cols
            batch_size=1,
            carry_forward_cols=["one"],
            where="one is Null",
        )[0]
    )
    _LOG.debug(plans)

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"one": one}),
        checkpoint_uri=store.root,
    )

    expected = [
        {"one": [1], "_rowaddr": [0]},
        {"one": [1], "_rowaddr": [1]},
        {"one": [1], "_rowaddr": [2]},
        {"one": [1], "_rowaddr": [3]},
        {"one": [1], "_rowaddr": [4]},
        {"one": [1], "_rowaddr": [5]},
        {"one": [1], "_rowaddr": [6]},
        {"one": [1], "_rowaddr": [7]},
    ]

    expected_counts = [1, 0, 1, 0, 1, 0, 1, 0]
    for i, plan in enumerate(plans):
        key, cnt_udf_computed = applier.run(plan)
        batch = store[key]
        assert batch.to_pydict() == expected[i]
        assert cnt_udf_computed == expected_counts[i]


@udf()
def errors_on_three(a: int) -> int:
    if a == 3:
        raise ValueError("This is an error")
    return 1


def test_applier_error_logging(tmp_path: Path, tbl_ref: TableReference) -> None:
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    plans = list(plan_read(tbl.uri, tbl_ref, ["a"], batch_size=16)[0])
    assert len(plans) == 1
    plan = plans[0]
    assert plan.uri == tbl.uri
    assert plan.offset == 0
    assert plan.limit == 3

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    error_store = ErrorStore(db, "test_errors")
    error_logger = TableErrorLogger(error_store=error_store, table_ref=tbl_ref)
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"one": errors_on_three}),
        checkpoint_uri=store.root,
        error_logger=error_logger,
    )
    with pytest.raises(RuntimeError):
        applier.run(plan)

    # Verify error was logged to error store
    errors = error_store.get_errors()
    assert len(errors) == 1
    error = errors[0]
    assert error.error_message == "This is an error"
    assert error.batch_index == 0


def test_error_store(tmp_path: Path, tbl_ref: TableReference) -> None:
    db = connect(tmp_path)
    error_store = ErrorStore(db, "test_errors")
    logger = TableErrorLogger(error_store=error_store, table_ref=tbl_ref)
    logger._store.get_errors()


def test_plan_with_where(tmp_path: Path, tbl_ref: TableReference) -> None:
    db = connect(tmp_path)

    tbl = db.create_table("t", pa.table({"a": range(100)}))
    tbl.add(pa.table({"a": range(100, 200)}))
    tbl.add(pa.table({"a": range(200, 300)}))
    tbl.add(pa.table({"a": range(300, 400)}))

    fragments = tbl.get_fragments()
    assert len(fragments) == 4

    # even though we have a filter, we still have to read all the fragments
    # batch size 0 means one task per  fragment
    tasks = list(
        plan_read(
            tbl.uri, tbl_ref, ["a"], where="a > 100 AND a % 2 == 0", batch_size=0
        )[0]
    )
    # there are only 3 tasks because we skip the first fragment due to the where clause.
    assert len(tasks) == 3


def test_plan_with_row_address(tmp_path: Path, tbl_ref: TableReference) -> None:
    db = connect(tmp_path)

    tbl = db.create_table("tbl", pa.table({"a": range(100)}))

    fragments = tbl.get_fragments()
    assert len(fragments) == 1

    tasks = list(plan_read(tbl.uri, tbl_ref, ["a"], batch_size=1000)[0])
    assert len(tasks) == 1

    for batch in tasks[0].to_batches():
        assert "_rowaddr" in batch.column_names


def test_plan_with_num_frags(tmp_path: Path, tbl_ref: TableReference) -> None:
    db = connect(tmp_path)

    tbl = db.create_table("t", pa.table({"a": range(100)}))
    tbl.add(pa.table({"a": range(100, 200)}))
    tbl.add(pa.table({"a": range(200, 300)}))
    tbl.add(pa.table({"a": range(300, 400)}))

    fragments = tbl.get_fragments()
    assert len(fragments) == 4

    # even though we have a filter, we still have to read all the fragments
    tasks = list(plan_read(tbl.uri, tbl_ref, ["a"], num_frags=2)[0])
    # there are only 2 tasks because we set num_frags=2
    assert len(tasks) == 2


def test_udf_with_arrow_params(tmp_path: Path, tbl_ref: TableReference) -> None:
    @udf(data_type=pa.int32())
    def batch_udf(a: pa.Array, b: pa.Array) -> pa.Array:
        assert a == pa.array([1, 2, 3])
        assert b == pa.array([4, 5, 6])
        return pc.cast(pc.add(a, b), pa.int32())

    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3], "b": [4, 5, 6]}))

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"c": batch_udf}),
        checkpoint_uri=store.root,
    )
    key, cnt_udf_computed = applier.run(
        next(plan_read(tbl.uri, tbl_ref, ["a", "b"], batch_size=16)[0])
    )
    batch = store[key]
    assert batch == pa.RecordBatch.from_pydict(
        {
            "c": pa.array([5, 7, 9], type=pa.int32()),
            "_rowaddr": pa.array([0, 1, 2], pa.uint64()),
        },
    )
    assert cnt_udf_computed == 3


def test_udf_with_arrow_struct(tmp_path: Path, tbl_ref: TableReference) -> None:
    struct_type = pa.struct([("rpad", pa.string()), ("lpad", pa.string())])

    @udf(data_type=struct_type)
    def struct_udf(a: pa.Array, b: pa.Array) -> pa.Array:
        assert a == pa.array([1, 2, 3])
        assert b == pa.array([4, 5, 6])
        rpad = pc.ascii_rpad(pc.cast(a, target_type="string"), 4, padding="0")
        lpad = pc.ascii_lpad(pc.cast(a, target_type="string"), 4, padding="0")
        return pc.make_struct(rpad, lpad, field_names=["rpad", "lpad"])

    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3], "b": [4, 5, 6]}))

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"c": struct_udf}),
        checkpoint_uri=store.root,
    )
    key, cnt_udf_computed = applier.run(
        next(plan_read(tbl.uri, tbl_ref, ["a", "b"], batch_size=16)[0])
    )
    batch = store[key]
    # Build the expected RecordBatch
    # The function calls produce ["1000", "2000", "3000"] for rpad
    # and ["0001", "0002", "0003"] for lpad
    expected_batch = pa.RecordBatch.from_arrays(
        [
            pa.StructArray.from_arrays(
                [
                    pa.array(["1000", "2000", "3000"]),
                    pa.array(["0001", "0002", "0003"]),
                ],
                names=["rpad", "lpad"],
            ),
            pa.array([0, 1, 2], pa.uint64()),
        ],
        ["c", "_rowaddr"],
    )

    assert batch == expected_batch
    assert cnt_udf_computed == 3


def test_plan_read_supports_struct_field_projection(tmp_path: Path) -> None:
    # Create a dataset with a struct column
    struct_type = pa.struct([("left", pa.string()), ("right", pa.string())])
    tbl = pa.table(
        {
            "info": pa.array(
                [
                    {"left": "alpha", "right": "one"},
                    {"left": "beta", "right": "two"},
                ],
                type=struct_type,
            )
        }
    )

    ds_path = tmp_path / "ds.lance"
    lance.write_dataset(tbl, ds_path, max_rows_per_file=16)

    tbl_ref = TableReference(table_id=["ds"], version=None, db_uri=str(tmp_path))

    # columns includes a dotted struct field
    plan, _ = plan_read(str(ds_path), tbl_ref, columns=["info.left"], batch_size=1024)

    task = next(iter(plan))
    batches = list(task.to_batches())
    assert len(batches) == 1
    batch = batches[0]
    # Should project only the requested sub-field plus row address
    assert "info.left" in batch.schema.names
    assert "info" not in batch.schema.names


def test_plan_read_with_udf_projects_struct_field(tmp_path: Path) -> None:
    struct_type = pa.struct([("left", pa.string()), ("right", pa.string())])
    tbl = pa.table(
        {
            "info": pa.array(
                [
                    {"left": "alpha", "right": "one"},
                    {"left": "beta", "right": "two"},
                ],
                type=struct_type,
            )
        }
    )

    ds_path = tmp_path / "ds_udf.lance"
    lance.write_dataset(tbl, ds_path, max_rows_per_file=16)

    tbl_ref = TableReference(table_id=["ds_udf"], version=None, db_uri=str(tmp_path))

    @udf(data_type=pa.string(), input_columns=["info.left"])
    def left_upper(left: pa.Array) -> pa.Array:  # pyright: ignore[reportReturnType]
        return pc.utf8_upper(left)

    map_task = BackfillUDFTask(udfs={"c": left_upper})

    plan, _ = plan_read(
        str(ds_path),
        tbl_ref,
        columns=["info.left"],
        batch_size=1024,
        map_task=map_task,
    )

    task = next(iter(plan))
    batches = list(task.to_batches())
    assert len(batches) == 1
    names = set(batches[0].schema.names)
    assert "info.left" in names
    assert "info" not in names


def test_udf_with_arrow_array(tmp_path: Path, tbl_ref: TableReference) -> None:
    array_type = pa.list_(pa.int64())

    @udf(data_type=array_type)
    def array_udf(a: pa.Array, b: pa.Array) -> pa.Array:
        assert a == pa.array([1, 2, 3])
        assert b == pa.array([4, 5, 6])
        arr = [
            [val] * cnt for val, cnt in zip(a.to_pylist(), b.to_pylist(), strict=True)
        ]
        c = pa.array(arr, type=pa.list_(pa.int64()))
        return c

    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3], "b": [4, 5, 6]}))

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"c": array_udf}),
        checkpoint_uri=store.root,
    )
    key, cnt_udf_computed = applier.run(
        next(plan_read(tbl.uri, tbl_ref, ["a", "b"], batch_size=16)[0])
    )
    batch = store[key]

    # Build the expected RecordBatch
    expected_c = pa.array(
        [[1, 1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3, 3, 3, 3]], type=pa.list_(pa.int64())
    )

    expected_batch = pa.RecordBatch.from_arrays(
        [expected_c, pa.array([0, 1, 2], pa.uint64())], ["c", "_rowaddr"]
    )
    assert batch == expected_batch
    assert cnt_udf_computed == 3


# Tests for fragment-level checkpoint functionality


def test_check_fragment_data_file_exists_no_checkpoint(tmp_path: Path) -> None:
    """Test _check_fragment_data_file_exists when fragment is not checkpointed."""
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    map_task = BackfillUDFTask(udfs={"one": one})

    # Fragment 0 should not exist in checkpoint store yet
    exists = _check_fragment_data_file_exists(tbl.uri, 0, map_task, store)
    assert not exists


def test_check_fragment_data_file_exists_with_staging_file(tmp_path: Path) -> None:
    """Test _check_fragment_data_file_exists when fragment file exists in staging."""
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    map_task = BackfillUDFTask(udfs={"one": one})

    # Create a checkpoint entry for fragment 0
    dedupe_key = _get_fragment_dedupe_key(tbl.uri, 0, map_task)
    fake_file_path = "test_fragment_0.lance"
    store[dedupe_key] = pa.RecordBatch.from_pydict({"file": [fake_file_path]})

    # Create the staging file
    staging_dir = tmp_path / "data"
    staging_dir.mkdir(exist_ok=True)
    staging_file = staging_dir / fake_file_path
    staging_file.touch()

    # Should return True since file exists in staging
    exists = _check_fragment_data_file_exists(tbl.uri, 0, map_task, store)
    assert exists


def test_check_fragment_data_file_exists_with_cloud_url() -> None:
    """Test _check_fragment_data_file_exists with cloud URLs."""
    # Create a mock checkpoint store
    store = {}
    map_task = BackfillUDFTask(udfs={"one": one})

    # Test with S3 URL - should not crash but return False since no real file
    s3_uri = "s3://test-bucket/dataset"
    exists = _check_fragment_data_file_exists(s3_uri, 0, map_task, store)
    assert not exists

    # Test with GCS URL - should not crash but return False since no real file
    gcs_uri = "gs://test-bucket/dataset"
    exists = _check_fragment_data_file_exists(gcs_uri, 0, map_task, store)
    assert not exists


def test_plan_read_with_skipped_fragments(
    tmp_path: Path, tbl_ref: TableReference
) -> None:
    """Test that plan_read correctly identifies and skips fragments."""
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))
    tbl.add(pa.table({"a": [4, 5, 6]}))  # Add second fragment

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    map_task = BackfillUDFTask(udfs={"one": one})

    # Create checkpoint for fragment 0 only
    dedupe_key = _get_fragment_dedupe_key(tbl.uri, 0, map_task)
    fake_file_path = "fragment_0.lance"
    store[dedupe_key] = pa.RecordBatch.from_pydict({"file": [fake_file_path]})

    # Create the staging file for fragment 0
    staging_dir = tmp_path / "data"
    staging_dir.mkdir(exist_ok=True)
    staging_file = staging_dir / fake_file_path
    staging_file.touch()

    # Plan read with checkpoint information
    plans, pipeline_args = plan_read(
        tbl.uri,
        tbl_ref,
        ["a"],
        batch_size=16,
        map_task=map_task,
        checkpoint_store=store,
    )

    # Should still have tasks for fragment 1 (not checkpointed)
    task_list = list(plans)
    assert len(task_list) > 0  # Fragment 1 should have tasks

    # Check that skipped_fragments contains fragment 0
    assert "skipped_fragments" in pipeline_args
    skipped_fragments = pipeline_args["skipped_fragments"]
    assert 0 in skipped_fragments
    assert 1 not in skipped_fragments  # Fragment 1 should not be skipped


def test_plan_read_no_checkpointing_params(
    tmp_path: Path, tbl_ref: TableReference
) -> None:
    """Test that plan_read works normally when no checkpointing params are provided."""
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    # Plan read without checkpoint information
    plans, pipeline_args = plan_read(tbl.uri, tbl_ref, ["a"], batch_size=16)

    # Should have tasks for all fragments
    task_list = list(plans)
    assert len(task_list) == 1

    # Should have empty skipped_fragments
    assert "skipped_fragments" in pipeline_args
    skipped_fragments = pipeline_args["skipped_fragments"]
    assert len(skipped_fragments) == 0


@pytest.mark.ray
def test_fragment_writer_manager_with_skipped_fragments(
    tmp_path: Path, tbl_ref: TableReference
) -> None:
    """Test that FragmentWriterManager correctly handles skipped fragments."""
    import lance.fragment
    import ray

    # Start Ray if not already started
    if not ray.is_initialized():
        ray.init(local_mode=True, ignore_reinit_error=True)

    try:
        db = connect(tmp_path)
        tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

        store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
        map_task = BackfillUDFTask(udfs={"one": one})

        # Create a mock skipped fragment data file
        skipped_data_file = lance.fragment.DataFile(
            "skipped_fragment.lance",
            [],  # field_ids
            [],  # field_id_to_column_indices
            2,  # major_version
            0,  # minor_version
        )

        skipped_fragments = {0: skipped_data_file}

        # Create FragmentWriterManager with skipped fragments
        fwm = FragmentWriterManager(
            dst_read_version=tbl.version,
            ds_uri=tbl.uri,
            job_tracker=None,
            map_task=map_task,
            checkpoint_store=store,
            where=None,
            commit_granularity=1,
            expected_tasks={1: 1},  # Only fragment 1 has expected tasks
            skipped_fragments=skipped_fragments,
        )

        # Check that skipped fragment is immediately in to_commit
        assert len(fwm.to_commit) == 1
        frag_id, data_file, row_count = fwm.to_commit[0]
        assert frag_id == 0
        assert data_file == skipped_data_file
        assert row_count >= 0  # Row count should be determined

    finally:
        if ray.is_initialized():
            ray.shutdown()


@pytest.mark.ray
def test_fragment_writer_manager_no_skipped_fragments(
    tmp_path: Path, tbl_ref: TableReference
) -> None:
    """Test that FragmentWriterManager works normally with no skipped fragments."""
    import ray

    # Start Ray if not already started
    if not ray.is_initialized():
        ray.init(local_mode=True, ignore_reinit_error=True)

    try:
        db = connect(tmp_path)
        tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

        store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
        map_task = BackfillUDFTask(udfs={"one": one})

        # Create FragmentWriterManager with no skipped fragments
        fwm = FragmentWriterManager(
            dst_read_version=tbl.version,
            ds_uri=tbl.uri,
            map_task=map_task,
            checkpoint_store=store,
            where=None,
            job_tracker=None,
            commit_granularity=1,
            expected_tasks={0: 1},  # Fragment 0 has expected tasks
            skipped_fragments={},  # No skipped fragments
        )

        # Should have no items in to_commit initially
        assert len(fwm.to_commit) == 0

    finally:
        if ray.is_initialized():
            ray.shutdown()


@pytest.mark.ray
def test_fragment_writer_manager_mixed_fragments(
    tmp_path: Path, tbl_ref: TableReference
) -> None:
    """Test FragmentWriterManager with both skipped and normal fragments."""
    import lance.fragment
    import ray

    # Start Ray if not already started
    if not ray.is_initialized():
        ray.init(local_mode=True, ignore_reinit_error=True)

    try:
        db = connect(tmp_path)
        tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))
        tbl.add(pa.table({"a": [4, 5, 6]}))  # Add second fragment

        store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
        map_task = BackfillUDFTask(udfs={"one": one})

        # Create a mock skipped fragment data file for fragment 0
        skipped_data_file = lance.fragment.DataFile(
            "skipped_fragment_0.lance",
            [],  # field_ids
            [],  # field_id_to_column_indices
            2,  # major_version
            0,  # minor_version
        )

        skipped_fragments = {0: skipped_data_file}

        # Create FragmentWriterManager with mixed fragments
        fwm = FragmentWriterManager(
            dst_read_version=tbl.version,
            ds_uri=tbl.uri,
            map_task=map_task,
            checkpoint_store=store,
            where=None,
            job_tracker=None,
            commit_granularity=1,
            expected_tasks={1: 1},  # Only fragment 1 has expected tasks to process
            skipped_fragments=skipped_fragments,
        )

        # Should have 1 item in to_commit (the skipped fragment)
        assert len(fwm.to_commit) == 1
        frag_id, data_file, row_count = fwm.to_commit[0]
        assert frag_id == 0
        assert data_file == skipped_data_file

        # Fragment 1 should still be tracked in remaining_tasks
        assert 1 in fwm.remaining_tasks
        assert fwm.remaining_tasks[1] == 1

    finally:
        if ray.is_initialized():
            ray.shutdown()

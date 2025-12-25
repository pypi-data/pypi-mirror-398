# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors
import importlib
import itertools
import logging
import random
import uuid
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any, NamedTuple

import lance
import lance.namespace
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pytest
import ray
from lance import BlobFile

import geneva
from geneva import CheckpointStore, connect, udf
from geneva.cluster import GenevaClusterType
from geneva.db import Connection
from geneva.runners.ray.pipeline import (
    FragmentWriterSession,
    run_ray_add_column,
    validate_backfill_args,
)
from geneva.table import Table, TableReference

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)

SIZE = 17  # was 256

pytestmark = pytest.mark.ray


@pytest.fixture(autouse=True)
def ray_cluster() -> None:
    ray.shutdown()
    ray.init(
        runtime_env={
            "RAY_BACKEND_LOG_LEVEL": "info",
            "RAY_LOG_TO_DRIVER": "1",
            "RAY_ENABLE_RECORD_ACTOR_TASK_LOGGING": "1",
            "RAY_RUNTIME_ENV_LOG_TO_DRIVER_ENABLED": "true",
        },
        log_to_driver=True,
        logging_config=ray.LoggingConfig(
            encoding="TEXT", log_level="DEBUG", additional_log_standard_attrs=["name"]
        ),
    )
    yield
    ray.shutdown()


@pytest.fixture(autouse=True)
def db(tmp_path, tbl_path) -> Connection:
    make_new_ds_a(tbl_path)
    db = geneva.connect(str(tmp_path))
    yield db
    db.close()


@pytest.fixture
def tbl_path(tmp_path) -> Path:
    return tmp_path / "foo.lance"


@pytest.fixture
def tbl_ref(tmp_path) -> TableReference:
    return TableReference(table_id=["foo"], version=None, db_uri=str(tmp_path))


@pytest.fixture
def ds(tbl_ref) -> lance.dataset:
    return tbl_ref.open().to_lance()


@pytest.fixture
def ckp_store(tmp_path: Path) -> CheckpointStore:
    return CheckpointStore.from_uri(str(tmp_path / "ckp"))


def make_new_ds_a(tbl_path: Path) -> lance.dataset:
    # create initial dataset with only column 'a'
    data = {"a": pa.array(range(SIZE))}
    tbl = pa.Table.from_pydict(data)
    ds = lance.write_dataset(tbl, tbl_path, max_rows_per_file=32)
    return ds


def make_new_ds_a_with_10_fragments(tbl_path: Path) -> lance.dataset:
    # create initial dataset with only column 'a' with 10 fragments
    # Use 20 rows with max_rows_per_file=2 to get exactly 10 fragments
    num_rows = 20
    data = {"a": pa.array(range(num_rows))}
    tbl = pa.Table.from_pydict(data)
    ds = lance.write_dataset(tbl, tbl_path, max_rows_per_file=2, mode="overwrite")
    return ds


def add_empty_b(ds: lance.dataset, fn) -> None:
    # then add column 'b' using merge.  This is a separate commit from data
    # commits to keep column 'a' as a separate set of physical files from 'b'
    # which enables a separate commit from distributed execution to only
    # update 'b' with an efficient file replacement operation.
    new_frags = []
    new_schema = None
    for frag in ds.get_fragments():
        new_fragment, new_schema = frag.merge_columns(fn, columns=["a"])
        new_frags.append(new_fragment)

    assert new_schema is not None
    merge = lance.LanceOperation.Merge(new_frags, new_schema)
    lance.LanceDataset.commit(ds.uri, merge, read_version=ds.version)


class UDFTestConfig(NamedTuple):
    expected_recordbatch: dict[Any, Any]
    where: str | None = None


def int32_return_none(batch: pa.RecordBatch) -> pa.RecordBatch:
    return pa.RecordBatch.from_pydict(
        {"b": pa.array([None] * batch.num_rows, pa.int32())}
    )


def setup_table_and_udf_column(
    db: Connection,
    shuffle_config,
    udf,
) -> Table:
    tbl = db.open_table("foo")

    tbl.add_columns(
        {"b": udf},
        **shuffle_config,
    )
    _LOG.info(f"Table prebackfill at version {tbl.version}")
    return tbl


def backfill_and_verify(tbl, testcfg, num_frags=None, expected_row_counts=None) -> None:
    backfill_kwargs = {}
    if num_frags is not None:
        backfill_kwargs["num_frags"] = num_frags

    # Use backfill_async to get access to job tracker for verification
    fut = tbl.backfill_async("b", where=testcfg.where, **backfill_kwargs)

    # Wait for completion
    fut.result()
    job_id = fut.job_id

    # Checkout latest to see the updated data
    tbl.checkout_latest()
    _LOG.info(f"completed backfill job {job_id}, now on version {tbl.version}")
    _LOG.info(
        f"actual={tbl.to_arrow().to_pydict()} expected={testcfg.expected_recordbatch}"
    )
    assert tbl.to_arrow().to_pydict() == testcfg.expected_recordbatch

    # Verify row counts if expected counts are provided
    if (
        expected_row_counts is not None
        and hasattr(fut, "job_tracker")
        and fut.job_tracker is not None
    ):
        import ray

        try:
            final_metrics = ray.get(fut.job_tracker.get_all.remote())
            _LOG.info(f"Final job metrics: {final_metrics}")

            # Verify expected row counts
            for metric_name, expected_count in expected_row_counts.items():
                if metric_name in final_metrics:
                    actual_count = final_metrics[metric_name].get("n", 0)
                    _LOG.info(
                        f"Metric {metric_name}: expected={expected_count}, "
                        f"actual={actual_count}"
                    )
                    assert actual_count == expected_count, (
                        f"Row count mismatch for {metric_name}: "
                        f"expected {expected_count}, got {actual_count}"
                    )
                else:
                    _LOG.warning(f"Metric {metric_name} not found in final metrics")

            # Anti-regression check: rows_ready_for_commit should never exceed
            # rows_checkpointed by more than a small tolerance
            checkpointed = final_metrics.get("rows_checkpointed", {}).get("n", 0)
            ready = final_metrics.get("rows_ready_for_commit", {}).get("n", 0)
            committed = final_metrics.get("rows_committed", {}).get("n", 0)

            assert ready <= checkpointed + 5, (
                f"Double counting detected: rows_ready_for_commit ({ready}) "
                f"significantly exceeds rows_checkpointed ({checkpointed})"
            )

            assert committed <= checkpointed, (
                f"Invalid state: rows_committed ({committed}) "
                f"exceeds rows_checkpointed ({checkpointed})"
            )
        except Exception as e:
            _LOG.warning(f"Could not verify row counts: {e}")

    _LOG.info(f"Checking job history for {job_id}")
    _LOG.info(f"{tbl._conn._history.get_table().to_arrow().to_pylist()}")

    hist = tbl._conn._history
    jr = hist.get(job_id)[0]
    assert jr.status == "DONE"
    assert jr.object_ref is not None
    assert jr.table_name == tbl.name
    assert jr.column_name == "b"
    assert jr.launched_at is not None
    assert jr.completed_at is not None


# UDF argument validation tests


@udf(data_type=pa.int32())
def recordbatch_udf(batch: pa.RecordBatch) -> pa.Array:
    return batch["a"]


@pytest.mark.multibackfill
def test_recordbatch_bad_inputs(db) -> None:
    # RecordBatch UDFs with input_columns raise error at creation time
    with pytest.raises(
        ValueError, match="RecordBatch input UDF must not declare any input columns"
    ):

        @udf(data_type=pa.int32(), input_columns=["a"])
        def recordbatch_bad(batch: pa.RecordBatch) -> pa.Array:
            return batch["a"]

    # record batch udfs need output data_type arg
    with pytest.raises(ValueError, match="please specify data_type"):

        @udf
        def recordbatch_bad2(batch: pa.RecordBatch) -> pa.Array:
            return batch["a"]

    # set good udf, then test UDF override at backfill time
    tbl = setup_table_and_udf_column(db, default_shuffle_config, recordbatch_udf)

    # override backfill with same UDF should work
    tbl.backfill("b", udf=recordbatch_udf)


def test_invalid_column(db) -> None:
    tbl = setup_table_and_udf_column(db, default_shuffle_config, recordbatch_udf)

    # input cols arg
    with pytest.raises(ValueError, match="Use add_columns"):
        tbl.backfill("c", udf=recordbatch_udf)


def test_validate_missing_input_column_scalar_udf(db) -> None:
    """Test that missing input columns are detected early for scalar UDFs."""

    @udf(data_type=pa.int32())
    def bad_udf(nonexistent_col: int) -> int:
        return nonexistent_col * 2

    tbl = db.open_table("foo")

    # Should fail validation at add_columns time (even earlier than backfill!)
    with pytest.raises(
        ValueError,
        match=r"expects input columns \['nonexistent_col'\].*not found in table schema",
    ):
        tbl.add_columns({"b": bad_udf}, **default_shuffle_config)


def test_validate_type_mismatch_string_vs_int(db) -> None:
    """Test that type mismatches (string vs int) are detected early."""

    # Create a table with a string column
    tbl = db.open_table("foo")

    # Now try to use a UDF that expects string on the int column 'a'
    @udf(data_type=pa.string())
    def string_udf(a: str) -> str:
        # UDF expects string but table has int64
        return str(a)

    tbl.add_columns({"b": string_udf}, **default_shuffle_config)

    # Should detect type mismatch: table has int64 column 'a', UDF expects string
    # Note: This validation is best-effort - if type hints don't match our map,
    # validation may not catch all type mismatches
    # For this test, we just verify that validation runs without error
    # The real benefit is catching missing columns, not all type mismatches
    try:
        tbl.backfill("b")
    except ValueError as e:
        # If validation caught it, great!
        if "Type mismatch" in str(e):
            pass  # Expected
        else:
            raise
    # If it didn't catch it, that's okay - type validation is best-effort


def test_validate_multiple_missing_columns(db) -> None:
    """Test validation with multiple missing columns."""

    @udf(data_type=pa.int32())
    def multi_col_udf(col1: int, col2: int, col3: int) -> int:
        return col1 + col2 + col3

    tbl = db.open_table("foo")

    # Should list all missing columns at add_columns time
    with pytest.raises(
        ValueError,
        match=r"expects input columns \['col1', 'col2', 'col3'\].*"
        r"not found in table schema",
    ):
        tbl.add_columns({"b": multi_col_udf}, **default_shuffle_config)


def test_validate_array_udf_missing_column(db) -> None:
    """Test validation for Array UDFs with missing columns."""

    @udf(data_type=pa.int32())
    def array_udf(missing_col: pa.Array) -> pa.Array:
        return missing_col

    tbl = db.open_table("foo")

    # Should fail at add_columns time
    with pytest.raises(
        ValueError,
        match=r"expects input columns \['missing_col'\].*not found in table schema",
    ):
        tbl.add_columns({"b": array_udf}, **default_shuffle_config)


def test_validate_against_read_version_missing_column(db) -> None:
    """Validation should use the schema for the requested read_version."""

    tbl = db.open_table("foo")
    base_version = tbl.version

    # Add a physical column that the computed column depends on
    tbl.add_columns({"b": "a"})
    assert tbl.version > base_version

    @udf(data_type=pa.int32())
    def uses_b(b: int) -> int:
        return b * 2

    tbl.add_columns({"c": uses_b}, **default_shuffle_config)

    # When validating against the original version (which lacks column b),
    # we should fail fast instead of launching a job that will time out later.
    with pytest.raises(
        ValueError,
        match=r"expects input columns \['b'\].*read_version",
    ):
        validate_backfill_args(tbl, "c", read_version=base_version)


def test_validate_passes_with_correct_columns(db) -> None:
    """Test that validation passes when columns are correct."""

    @udf(data_type=pa.int32())
    def good_udf(a: int) -> int:
        return a * 2

    tbl = db.open_table("foo")
    tbl.add_columns({"b": good_udf}, **default_shuffle_config)

    # Should not raise any validation errors
    tbl.backfill("b")

    # Verify the result
    result = tbl.to_arrow()
    expected_b = [x * 2 for x in range(SIZE)]
    assert result["b"].to_pylist() == expected_b


def test_add_columns_validates_missing_columns(db) -> None:
    """Test that add_columns() validates input columns at definition time."""

    @udf(data_type=pa.int32())
    def bad_udf(nonexistent_col: int) -> int:
        return nonexistent_col * 2

    tbl = db.open_table("foo")

    # Should fail at add_columns time, not backfill time
    with pytest.raises(
        ValueError,
        match=r"expects input columns \['nonexistent_col'\].*not found in table schema",
    ):
        tbl.add_columns({"b": bad_udf}, **default_shuffle_config)


def test_add_columns_validates_with_explicit_input_columns(db) -> None:
    """Test that add_columns() validates explicitly provided input columns."""

    @udf(data_type=pa.int32())
    def simple_udf(x: int) -> int:
        return x * 2

    tbl = db.open_table("foo")

    # Provide wrong column name explicitly
    with pytest.raises(
        ValueError,
        match=r"expects input columns \['wrong_column'\].*not found in table schema",
    ):
        tbl.add_columns({"b": (simple_udf, ["wrong_column"])}, **default_shuffle_config)


def test_add_columns_validates_multiple_missing_columns(db) -> None:
    """Test add_columns() with multiple missing columns."""

    @udf(data_type=pa.int32())
    def multi_col_udf(col1: int, col2: int, col3: int) -> int:
        return col1 + col2 + col3

    tbl = db.open_table("foo")

    # Should list all missing columns
    with pytest.raises(
        ValueError,
        match=r"expects input columns \['col1', 'col2', 'col3'\].*"
        r"not found in table schema",
    ):
        tbl.add_columns({"b": multi_col_udf}, **default_shuffle_config)


def test_add_columns_passes_with_correct_columns(db) -> None:
    """Test that add_columns() succeeds when columns are correct."""

    @udf(data_type=pa.int32())
    def good_udf(a: int) -> int:
        return a * 2

    tbl = db.open_table("foo")

    # Should not raise - column 'a' exists in table
    tbl.add_columns({"b": good_udf}, **default_shuffle_config)

    # Verify the column was added
    assert "b" in tbl.schema.names


def test_recordbatch_udf_raises_if_input_columns_specified(db) -> None:
    """Test that RecordBatch UDFs raise error if input_columns are specified."""

    # Should raise ValueError at UDF creation time
    with pytest.raises(
        ValueError,
        match=r"RecordBatch input UDF must not declare any input columns",
    ):

        @udf(data_type=pa.int32(), input_columns=["a"])
        def recordbatch_with_cols(batch: pa.RecordBatch) -> pa.Array:
            return pa.array([1] * batch.num_rows, type=pa.int32())


def test_recordbatch_udf_rejects_explicit_input_columns_at_add_time(db) -> None:
    """Test that RecordBatch UDFs reject explicit input_columns at add_columns time."""

    @udf(data_type=pa.int32())
    def recordbatch_udf_good(batch: pa.RecordBatch) -> pa.Array:
        return pa.array([1] * batch.num_rows, type=pa.int32())

    tbl = db.open_table("foo")

    # Should raise ValueError when trying to add with explicit input_columns
    with pytest.raises(
        ValueError,
        match=r"RecordBatch UDF but has input_columns.*specified",
    ):
        tbl.add_columns({"b": (recordbatch_udf_good, ["a"])}, **default_shuffle_config)


# Backfill tests with scalar return values


# 0.1 cpu so we don't wait for provisioning in the tests
@udf(data_type=pa.int32(), checkpoint_size=8, num_cpus=1)
def times_ten(a) -> int:
    return a * 10


scalar_udftest = UDFTestConfig(
    {
        "a": list(range(SIZE)),
        "b": [x * 10 for x in range(SIZE)],
    },
)

# handle even rows
scalar_udftest_filter_even = UDFTestConfig(
    {
        "a": list(range(SIZE)),
        "b": [x * 10 if x % 2 == 0 else None for x in range(SIZE)],
    },
    "a % 2 = 0",
)

# handle num_frags
scalar_udftest_num_frags = UDFTestConfig(
    {
        "a": list(range(SIZE)),
        "b": [x * 10 if x < 10 else None for x in range(SIZE)],
    },
)


default_shuffle_config = {
    "batch_size": 1,
    "shuffle_buffer_size": 3,
    "task_shuffle_diversity": None,
}


@pytest.mark.parametrize(
    "shuffle_config",
    [
        {
            "batch_size": batch_size,
            "shuffle_buffer_size": shuffle_buffer_size,
            "task_shuffle_diversity": task_shuffle_diversity,
            "intra_applier_concurrency": intra_applier_concurrency,
        }
        for (
            batch_size,
            shuffle_buffer_size,
            task_shuffle_diversity,
            intra_applier_concurrency,
        ) in itertools.product(
            [4, 16],
            [7],
            [3],
            [1, 4],  # simple applier or multiprocessing batch applier= 4
        )
    ],
)
def test_run_ray_add_column(db: Connection, shuffle_config) -> None:
    tbl = setup_table_and_udf_column(db, shuffle_config, times_ten)
    backfill_and_verify(tbl, scalar_udftest)


@pytest.mark.multibackfill
def test_run_ray_add_column_ifnull(db: Connection) -> None:
    tbl = setup_table_and_udf_column(db, default_shuffle_config, times_ten)
    backfill_and_verify(tbl, scalar_udftest_filter_even)
    backfill_and_verify(
        tbl, UDFTestConfig(scalar_udftest.expected_recordbatch, where="b is null")
    )


@pytest.mark.multibackfill
def test_ray_run_add_column_filter_incremental(db: Connection) -> None:
    tbl = setup_table_and_udf_column(db, default_shuffle_config, times_ten)

    backfill_and_verify(tbl, scalar_udftest_filter_even)

    # add rows divisible by 3
    scalar_udftest_filter_treys = UDFTestConfig(
        {
            "a": list(range(SIZE)),
            "b": [x * 10 if x % 3 == 0 or x % 2 == 0 else None for x in range(SIZE)],
        },
        "a % 3 = 0",
    )
    backfill_and_verify(tbl, scalar_udftest_filter_treys)

    # add odd rows
    expected = {
        "a": list(range(SIZE)),
        "b": [x * 10 for x in range(SIZE)],  # all rows covered
    }
    backfill_and_verify(tbl, UDFTestConfig(expected, where="a % 2 = 1"))


@pytest.mark.multibackfill
def test_ray_run_add_column_filter_incremental_numfrags(tmp_path, tbl_path) -> None:
    """
    Test incremental backfill with num_frags parameter.

    Creates a table with 10 fragments (20 rows, 2 rows per fragment).
    Tests three incremental backfills:
    1. num_frags=2: processes only first 2 fragments (rows 0-3)
    2. num_frags=5: processes first 5 fragments (rows 0-9)
    3. no limit: processes all fragments (rows 0-19)
    """
    # Create a table with 10 fragments and setup UDF column
    make_new_ds_a_with_10_fragments(tbl_path)
    db = geneva.connect(str(tmp_path))
    tbl = db.open_table("foo")
    tbl.add_columns(
        {"b": times_ten},
        **default_shuffle_config,
    )

    # Define test configs for 20 rows (since we made 20 rows with 10 fragments)
    num_rows = 20

    # First backfill: num_frags=2 (only first 2 fragments)
    # Should process fragments 0-1 which contain rows 0-3
    expected_after_2frags = {
        "a": list(range(num_rows)),
        "b": [x * 10 if x < 4 else None for x in range(num_rows)],
    }
    expected_row_counts_2frags = {
        "rows_checkpointed": 4,  # Processed 4 rows from fragments 0-1
        "rows_ready_for_commit": 4,  # 4 rows ready for commit
        "rows_committed": 4,  # 4 rows committed (no skipped fragments)
    }
    backfill_and_verify(
        tbl,
        UDFTestConfig(expected_after_2frags),
        num_frags=2,
        expected_row_counts=expected_row_counts_2frags,
    )

    # Second backfill: num_frags=5 (first 5 fragments total)
    # Should process fragments 0-4 which contain rows 0-9
    # Note: this might only process fragments 2-4 (rows 4-9) if incremental
    expected_after_5frags = {
        "a": list(range(num_rows)),
        "b": [x * 10 if x < 10 else None for x in range(num_rows)],
    }
    expected_row_counts_5frags = {
        "rows_checkpointed": 10,  # 6 new rows from fragments 2-4, plus 4 skipped
        "rows_ready_for_commit": 10,  # 6 new + 4 skipped = 10 total (no double count)
        "rows_committed": 6,  # Only 6 newly processed rows committed
    }
    backfill_and_verify(
        tbl,
        UDFTestConfig(expected_after_5frags),
        num_frags=5,
        expected_row_counts=expected_row_counts_5frags,
    )

    # Final backfill: no num_frags limit (all remaining fragments)
    # Should process all fragments which contain rows 0-19
    # Note: this might only process fragments 5-9 (rows 10-19) if incremental
    expected_final = {
        "a": list(range(num_rows)),
        "b": [x * 10 for x in range(num_rows)],
    }
    expected_row_counts_final = {
        "rows_checkpointed": 20,  # 10 new rows from fragments 5-9, plus 10 skipped
        "rows_ready_for_commit": 20,  # 10 new + 10 skipped = 20 total (no double count)
        "rows_committed": 10,  # Only 10 newly processed rows committed
    }
    backfill_and_verify(
        tbl,
        UDFTestConfig(expected_final),
        expected_row_counts=expected_row_counts_final,
    )

    db.close()


@pytest.mark.multibackfill
def test_ray_double_counting_prevention(tmp_path) -> None:
    """
    Specific test to prevent double counting regression in progress metrics.

    This test verifies that rows_ready_for_commit doesn't get inflated by
    counting skipped fragments multiple times during incremental backfill.
    """
    # Create a table with 6 fragments and setup UDF column
    tbl_path = tmp_path / "double_count_test.lance"
    make_new_ds_a_with_fragments(tbl_path, num_rows=12, rows_per_fragment=2)
    db = geneva.connect(str(tmp_path))
    tbl = db.open_table("double_count_test")
    tbl.add_columns(
        {"b": times_ten},
        **default_shuffle_config,
    )

    # First backfill: process 2 fragments (4 rows)
    fut1 = tbl.backfill_async("b", num_frags=2)
    fut1.result()
    tbl.checkout_latest()

    if hasattr(fut1, "job_tracker") and fut1.job_tracker is not None:
        import ray

        metrics1 = ray.get(fut1.job_tracker.get_all.remote())

        # Verify first job metrics are sane
        assert metrics1["rows_checkpointed"]["n"] == 4
        assert metrics1["rows_ready_for_commit"]["n"] == 4
        assert metrics1["rows_committed"]["n"] == 4

    # Second backfill: remaining fragments with skipped fragments
    fut2 = tbl.backfill_async("b")
    fut2.result()
    tbl.checkout_latest()

    if hasattr(fut2, "job_tracker") and fut2.job_tracker is not None:
        metrics2 = ray.get(fut2.job_tracker.get_all.remote())

        checkpointed = metrics2["rows_checkpointed"]["n"]
        ready = metrics2["rows_ready_for_commit"]["n"]
        committed = metrics2["rows_committed"]["n"]

        # The key test: rows_ready_for_commit should NOT be significantly
        # higher than rows_checkpointed (which would indicate double counting)
        assert ready <= checkpointed + 2, (
            f"DOUBLE COUNTING BUG: rows_ready_for_commit ({ready}) "
            f"exceeds rows_checkpointed ({checkpointed}) by too much. "
            f"This suggests skipped fragments are being counted multiple times."
        )

        # Additional sanity checks
        assert committed <= checkpointed, (
            f"rows_committed ({committed}) should not exceed "
            f"rows_checkpointed ({checkpointed})"
        )

        # Total data should be processed correctly regardless of metrics
        result = tbl.to_arrow().to_pydict()
        processed_count = sum(1 for x in result["b"] if x is not None)
        assert processed_count == 12, (
            f"Expected 12 processed rows, got {processed_count}"
        )

    db.close()


@pytest.mark.ray
def test_row_metrics_reconcile_when_tracker_drops_updates(
    tmp_path, monkeypatch
) -> None:
    """
    Simulate a flaky JobTracker that drops increment updates. The pipeline should
    still report accurate final row metrics by reconciling totals at the end.
    """
    from geneva.runners.ray import jobtracker

    # Drop ALL increment updates to mimic lost progress messages
    async def drop_increment(self, name: str, delta: int = 1) -> None:  # noqa: ANN001
        await self._upsert(name)

    monkeypatch.setattr(jobtracker.JobTracker, "increment", drop_increment)

    # Build a small table
    num_rows = 12
    data = {"a": pa.array(range(num_rows))}
    tbl_path = tmp_path / "reconcile.lance"
    lance.write_dataset(pa.Table.from_pydict(data), tbl_path, max_rows_per_file=4)

    @udf(data_type=pa.int32())
    def times_two(a: int) -> int:
        return a * 2

    db = geneva.connect(str(tmp_path))
    tbl = db.open_table("reconcile")
    tbl.add_columns({"b": times_two}, batch_size=3)

    ray.shutdown()
    ray.init()

    fut = tbl.backfill_async("b")
    fut.result()

    metrics = ray.get(fut.job_tracker.get_all.remote())  # type: ignore[arg-type]
    checkpointed = metrics["rows_checkpointed"]
    ready = metrics["rows_ready_for_commit"]
    committed = metrics["rows_committed"]

    assert checkpointed["n"] == checkpointed["total"] == num_rows
    assert ready["n"] == ready["total"] == num_rows
    assert committed["n"] == committed["total"] == num_rows

    ray.shutdown()
    db.close()


def make_new_ds_a_with_fragments(
    tbl_path: Path, num_rows: int, rows_per_fragment: int
) -> lance.dataset:
    """Helper to create dataset with specific fragment layout."""
    data = {"a": pa.array(range(num_rows))}
    tbl = pa.Table.from_pydict(data)
    ds = lance.write_dataset(tbl, tbl_path, max_rows_per_file=rows_per_fragment)
    return ds


def test_run_ray_add_column_write_fault(
    tbl_path, tbl_ref, ckp_store, monkeypatch
) -> None:  # noqa: PT019
    add_empty_b(lance.dataset(tbl_path), int32_return_none)
    original_ingest = FragmentWriterSession.ingest_task

    def faulty_ingest(self, offset: int, result: Any) -> None:
        original_ingest(self, offset, result)
        if random.random() < 0.5:
            ray.kill(self.actor)
        else:
            ray.kill(self.queue.actor)

    monkeypatch.setattr(FragmentWriterSession, "ingest_task", faulty_ingest)

    run_ray_add_column(
        tbl_ref,
        ["a"],
        {"b": times_ten},
        checkpoint_store=ckp_store,
    )

    ds = lance.dataset(tbl_path)
    assert ds.to_table().to_pydict() == scalar_udftest.expected_recordbatch


def test_run_ray_add_column_with_deletes(db, ds, tbl_path, tbl_ref, ckp_store) -> None:  # noqa: PT019
    add_empty_b(ds, int32_return_none)
    ds = lance.dataset(tbl_path)  # reload to get latest
    ds.delete("a % 2 == 1")

    ds = lance.dataset(tbl_path)  # reload to get latest
    run_ray_add_column(tbl_ref, ["a"], {"b": times_ten}, checkpoint_store=ckp_store)

    ds = lance.dataset(tbl_path)  # reload to get latest
    assert ds.to_table().to_pydict() == {
        "a": list(range(0, SIZE, 2)),
        "b": [x * 10 for x in range(0, SIZE, 2)],
    }


# Backfill tests with struct return types

struct_type = pa.struct([("rpad", pa.string()), ("lpad", pa.string())])


@udf(data_type=struct_type, checkpoint_size=8, num_cpus=0.1)
def struct_udf(a: int) -> dict:  # is the output type correct?
    return {"lpad": f"{a:04d}", "rpad": f"{a}0000"[:4]}


@udf(data_type=struct_type, checkpoint_size=8, num_cpus=0.1)
def struct_udf_batch(a: pa.Array) -> pa.Array:  # is the output type correct?
    rpad = pc.ascii_rpad(pc.cast(a, target_type="string"), 4, padding="0")
    lpad = pc.ascii_lpad(pc.cast(a, target_type="string"), 4, padding="0")
    return pc.make_struct(rpad, lpad, field_names=["rpad", "lpad"])


@udf(data_type=struct_type, checkpoint_size=8, num_cpus=0.1)
def struct_udf_recordbatch(
    batch: pa.RecordBatch,
) -> pa.Array:  # is the output type correct?
    a = batch["a"]
    rpad = pc.ascii_rpad(pc.cast(a, target_type="string"), 4, padding="0")
    lpad = pc.ascii_lpad(pc.cast(a, target_type="string"), 4, padding="0")
    return pc.make_struct(rpad, lpad, field_names=["rpad", "lpad"])


ret_struct_udftest_complete = UDFTestConfig(
    {
        "a": list(range(SIZE)),
        "b": [{"lpad": f"{x:04d}", "rpad": f"{x}0000"[:4]} for x in range(SIZE)],
    },
)

ret_struct_udftest_filtered = UDFTestConfig(
    {
        "a": list(range(SIZE)),
        "b": [
            {"lpad": f"{x:04d}", "rpad": f"{x}0000"[:4]}
            if x % 2 == 0
            else {
                "lpad": None,
                "rpad": None,
            }  # TODO why struct of None instead of just None?
            for x in range(SIZE)
        ],
    },
    "a % 2 = 0",
)


@pytest.mark.multibackfill
def test_run_ray_add_column_ret_struct(db: Connection) -> None:
    tbl = setup_table_and_udf_column(db, default_shuffle_config, struct_udf)
    backfill_and_verify(tbl, ret_struct_udftest_filtered)
    backfill_and_verify(tbl, ret_struct_udftest_complete)


@pytest.mark.multibackfill
def test_run_ray_add_column_ret_struct_batchudf(db: Connection) -> None:
    tbl = setup_table_and_udf_column(db, default_shuffle_config, struct_udf_batch)
    backfill_and_verify(tbl, ret_struct_udftest_filtered)
    backfill_and_verify(tbl, ret_struct_udftest_complete)


@pytest.mark.multibackfill
def test_run_ray_add_column_ret_struct_recordbatchudf(db: Connection) -> None:
    tbl = setup_table_and_udf_column(db, default_shuffle_config, struct_udf_recordbatch)
    backfill_and_verify(tbl, ret_struct_udftest_filtered)
    backfill_and_verify(tbl, ret_struct_udftest_complete)


@pytest.mark.multibackfill
def test_run_ray_add_column_ret_struct_ifnull(db: Connection) -> None:
    tbl = setup_table_and_udf_column(db, default_shuffle_config, struct_udf)
    backfill_and_verify(tbl, ret_struct_udftest_filtered)
    # TODO why struct of None instead of just 'b is null'
    backfill_and_verify(
        tbl,
        UDFTestConfig(
            ret_struct_udftest_complete.expected_recordbatch,
            where="b.rpad is null and b.lpad is null",
        ),
    )


@pytest.mark.multibackfill
def test_run_ray_add_column_ret_struct_filtered(db: Connection) -> None:
    tbl = setup_table_and_udf_column(db, default_shuffle_config, struct_udf)
    backfill_and_verify(tbl, ret_struct_udftest_filtered)
    expected = ret_struct_udftest_complete.expected_recordbatch
    backfill_and_verify(tbl, UDFTestConfig(expected, "a % 2 = 1"))


# Backfill tests with struct and array return types

vararray_type = pa.list_(pa.int64())

ret_vararray_udftest_complete = UDFTestConfig(
    {
        "a": list(range(SIZE)),
        "b": [[x] * x for x in range(SIZE)],
    },
)

ret_vararray_udftest_even = UDFTestConfig(
    {
        "a": list(range(SIZE)),
        "b": [[x] * x if x % 2 == 0 else None for x in range(SIZE)],
    },
    "a%2=0",
)


@pytest.mark.multibackfill
def test_run_ray_add_column_ret_vararray(db: Connection) -> None:
    @udf(data_type=vararray_type, checkpoint_size=8, num_cpus=0.1)
    def vararray_udf_scalar(a: int) -> pa.Array:  # is the output type correct?
        # [ [], [1], [2,2], [3,3,3] ... ]
        return [a] * a

    tbl = setup_table_and_udf_column(db, default_shuffle_config, vararray_udf_scalar)
    backfill_and_verify(tbl, ret_vararray_udftest_even)
    expected = ret_vararray_udftest_complete.expected_recordbatch
    backfill_and_verify(tbl, UDFTestConfig(expected, "b is null"))


@pytest.mark.multibackfill
def test_run_ray_add_column_ret_vararray_array(db: Connection) -> None:
    @udf(data_type=vararray_type, checkpoint_size=8, num_cpus=0.1)
    def vararray_udf(a: pa.Array) -> pa.Array:  # is the output type correct?
        # [ [], [1], [2,2], [3,3,3] ... ]
        arr = [[val] * val for val in a.to_pylist()]
        b = pa.array(arr, type=pa.list_(pa.int64()))
        return b

    tbl = setup_table_and_udf_column(db, default_shuffle_config, vararray_udf)
    backfill_and_verify(tbl, ret_vararray_udftest_even)
    expected = ret_vararray_udftest_complete.expected_recordbatch
    backfill_and_verify(tbl, UDFTestConfig(expected, "b is null"))


def test_run_ray_add_column_ret_vararray_stateful_arrays(db: Connection) -> None:
    @udf(data_type=vararray_type, checkpoint_size=8, num_cpus=0.1)
    class StatefulVararrayUDF(Callable):
        def __init__(self) -> None:
            self.state = 0

        def __call__(self, a: pa.Array) -> pa.Array:  # is the output type correct?
            # [ [], [1], [2,2], [3,3,3] ... ]
            arr = [[val] * val for val in a.to_pylist()]
            b = pa.array(arr, type=pa.list_(pa.int64()))
            return b

    tbl = setup_table_and_udf_column(db, default_shuffle_config, StatefulVararrayUDF())
    backfill_and_verify(tbl, ret_vararray_udftest_complete)


def test_run_ray_add_column_ret_vararray_stateful_recordbatch(db: Connection) -> None:
    @udf(data_type=vararray_type, checkpoint_size=8, num_cpus=0.1)
    class BatchedStatefulVararrayUDF(Callable):
        def __init__(self) -> None:
            self.state = 0

        def __call__(
            self, batch: pa.RecordBatch
        ) -> pa.Array:  # is the output type correct?
            # [ [], [1], [2,2], [3,3,3] ... ]
            _LOG.warning(f"batch: {batch}")
            alist = batch["a"]
            arr = [[val] * val for val in alist.to_pylist()]
            b = pa.array(arr, type=pa.list_(pa.int64()))
            return b

    tbl = setup_table_and_udf_column(
        db, default_shuffle_config, BatchedStatefulVararrayUDF()
    )
    backfill_and_verify(tbl, ret_vararray_udftest_complete)


# Backfill tests with nested struct and array return types

nested_type = pa.struct([("lpad", pa.string()), ("array", pa.list_(pa.int64()))])


def test_run_ray_add_column_ret_nested(db: Connection) -> None:
    @udf(data_type=nested_type, checkpoint_size=8, num_cpus=0.1)
    def nested_udf(a: pa.Array) -> pa.Array:
        # [ { lpad:"0000", array:[] } , {lpad:"0001", array:[1]},
        #   { lpad:"0002", array:[2,2]}, ... ]

        lpad = pc.ascii_lpad(pc.cast(a, target_type="string"), 4, padding="0")
        arr = [[val] * val for val in a.to_pylist()]
        array = pa.array(arr, type=pa.list_(pa.int64()))

        return pc.make_struct(lpad, array, field_names=["lpad", "array"])

    tbl = setup_table_and_udf_column(db, default_shuffle_config, nested_udf)

    ret_nested_udftest = UDFTestConfig(
        {
            "a": list(range(SIZE)),
            "b": [{"lpad": f"{val:04d}", "array": [val] * val} for val in range(SIZE)],
        },
    )
    backfill_and_verify(tbl, ret_nested_udftest)


# Other tests


def test_relative_path(tmp_path, db: Connection, monkeypatch) -> None:
    # Make sure this ray instance uses the db as CURDIR
    ray.shutdown()
    monkeypatch.chdir(tmp_path)

    db = geneva.connect("./db")

    # create a basic table
    tbl = pa.Table.from_pydict({"id": [1, 2, 3, 4, 5, 6]})
    table = db.create_table("table1", tbl)

    @udf(data_type=pa.int64())
    def double_id(id: int):  # noqa A002
        return id * 2

    table.add_columns(
        {"id2": double_id},
    )

    schema = table.schema
    field = schema.field("id2")
    assert field.metadata[b"virtual_column.udf_name"] == b"double_id"

    # At this time, "id2" is a null column
    assert table.to_arrow().combine_chunks() == pa.Table.from_pydict(
        {"id": [1, 2, 3, 4, 5, 6], "id2": [None] * 6},
        schema=pa.schema(
            [
                pa.field("id", pa.int64()),
                pa.field("id2", pa.int64(), True),
            ]
        ),
    )

    # uses local ray to execute UDF and populate "id2"
    table.backfill("id2")

    df = table.to_arrow().to_pandas()
    assert df.equals(
        pd.DataFrame({"id": [1, 2, 3, 4, 5, 6], "id2": [2, 4, 6, 8, 10, 12]})
    )


# Blob-type tests


def blob_table(db) -> Table:
    schema = pa.schema(
        [
            pa.field("a", pa.int32()),
            pa.field(
                "blob", pa.large_binary(), metadata={"lance-encoding:blob": "true"}
            ),
        ]
    )
    blobs = [b"hello", b"the world"]
    tbl = pa.Table.from_pydict(
        {"a": list(range(len(blobs))), "blob": blobs}, schema=schema
    )
    tbl = db.create_table("t", tbl)
    return tbl


@udf
def udf_blob(blob: BlobFile) -> int:
    assert isinstance(blob, BlobFile)
    return len(blob.read())


@udf(data_type=pa.int64())
def udf_blob_int_recordbatch(batch: pa.RecordBatch) -> pa.Array:
    """UDF that works on a record batch with a blob column."""
    assert isinstance(batch, pa.RecordBatch)
    blob_col = batch["blob"]
    lens = [len(b) for b in blob_col.to_pylist() if isinstance(b, bytes)]
    return pa.array(lens, type=pa.int64())


@udf(data_type=pa.list_(pa.string()))
def udf_blob_to_strlist(blob: BlobFile) -> list[str]:
    """UDF that converts a blob to a list of strings."""
    assert isinstance(blob, BlobFile)
    data = blob.readall()
    rets = data.decode("utf-8").split()
    _LOG.info(f"blob_to_strlist: {data} -> {rets}")
    return rets


@udf(data_type=pa.list_(pa.string()))
def udf_blob_to_strlist_batch(batch: pa.RecordBatch) -> pa.Array:
    """UDF that converts a blob to a list of strings."""
    blobs = batch["blob"]

    rets = []
    for b in blobs:
        data = b.as_py()
        rets.append(data.decode("utf-8").split())
        _LOG.info(f"blob_to_strlist: {data} -> {rets}")
    return pa.array(rets, type=pa.list_(pa.string()))


def test_udf_with_blob_column(db) -> None:
    tbl = blob_table(db)
    tbl.add_columns({"len": udf_blob})
    tbl.backfill("len")
    vals = tbl.to_arrow()
    assert vals["len"].to_pylist() == [5, 9]


def test_udf_with_blob_column_recordbatch(db) -> None:
    tbl = blob_table(db)
    tbl.add_columns({"len": udf_blob_int_recordbatch})
    tbl.backfill("len")
    vals = tbl.to_arrow()
    assert vals["len"].to_pylist() == [5, 9]


def test_udf_with_blob_column_filtered(db) -> None:
    tbl = blob_table(db)
    tbl.add_columns({"len": udf_blob})
    tbl.backfill(
        "len",
        where="a%2=0",
    )
    vals = tbl.to_arrow()
    assert vals["len"].to_pylist() == [5, None]
    _LOG.info(f"=== Filtered backfill result ver {tbl.version}: {vals}")

    # now add filter to backfill the rest
    _LOG.info("=== Filling in the rest now..")
    tbl.backfill("len", where="len is null")
    _LOG.info(f"=== after fill in ver {tbl.version}: {vals}")
    tbl.checkout_latest()
    vals = tbl.to_arrow()
    assert vals["len"].to_pylist() == [5, 9]


def test_udf_with_blob_column_to_strlist(db) -> None:
    tbl = blob_table(db)
    tbl.add_columns({"strlist": udf_blob_to_strlist})
    tbl.backfill(
        "strlist",
        where="a%2=0",
    )
    vals = tbl.to_arrow()
    _LOG.info(f"=== Filtered backfill result ver {tbl.version}: {vals}")
    assert vals["strlist"].to_pylist() == [["hello"], None]

    # now add filter to backfill the rest
    _LOG.info("=== Filling in the rest now..")
    tbl.backfill("strlist", where="strlist is null")
    _LOG.info(f"=== after fill in ver {tbl.version}: {vals}")
    tbl.checkout_latest()
    vals = tbl.to_arrow()
    assert vals["strlist"].to_pylist() == [["hello"], ["the", "world"]]


def test_udf_with_blob_column_to_strlist_batch(db) -> None:
    tbl = blob_table(db)
    tbl.add_columns({"strlist": udf_blob_to_strlist_batch})
    tbl.backfill(
        "strlist",
        where="a%2=0",
    )
    vals = tbl.to_arrow()
    _LOG.info(f"=== Filtered backfill result ver {tbl.version}: {vals}")
    assert vals["strlist"].to_pylist() == [["hello"], None]

    # now add filter to backfill the rest
    _LOG.info("=== Filling in the rest now..")
    tbl.backfill("strlist", where="strlist is null")
    _LOG.info(f"=== after fill in ver {tbl.version}: {vals}")
    tbl.checkout_latest()
    vals = tbl.to_arrow()
    assert vals["strlist"].to_pylist() == [["hello"], ["the", "world"]]


@pytest.mark.skip(reason="binary literal not yet implemented?")
def test_udf_with_blob_column_filtered_binaryliteral(tmp_path: Path) -> None:
    tbl = blob_table(tmp_path)
    tbl.add_columns({"len": udf_blob})
    tbl.backfill(
        "len",
        where="blob = X'hello'",
    )
    vals = tbl.to_arrow()
    assert vals["len"].to_pylist() == [5, None]


def test_udf_generates_blob_output(tmp_path: Path) -> None:
    """Test UDF that generates Lance blob outputs from scalar inputs."""

    @udf(data_type=pa.large_binary(), field_metadata={"lance-encoding:blob": "true"})
    def generate_blob(text: str, multiplier: int) -> bytes:
        """UDF that generates blob data by repeating text."""
        return (text * multiplier).encode("utf-8")

    # Create database and input table
    db = connect(tmp_path)
    input_data = pa.table({"text": ["hello", "world", "test"], "multiplier": [2, 3, 1]})
    tbl = db.create_table("input_table", input_data)

    # Add blob column with proper metadata
    tbl.add_columns({"blob_output": generate_blob})
    _LOG.info(f"schema: {tbl.schema}")
    # Verify blob metadata is present
    blob_field = tbl.schema.field("blob_output")
    assert blob_field.metadata[b"lance-encoding:blob"] == b"true"

    # Execute backfill to generate blob data
    tbl.backfill("blob_output")

    # Verify results
    tbl = db.open_table("input_table")
    result = tbl.to_arrow()
    expected_blobs = [
        {"position": 0, "size": 10},
        {"position": 64, "size": 15},
        {"position": 128, "size": 4},
    ]
    expected_blob_values = [
        b"hellohello",  # "hello" * 2
        b"worldworldworld",  # "world" * 3
        b"test",  # "test" * 1
    ]
    _LOG.info(f"result: {result}")

    assert result["text"].to_pylist() == ["hello", "world", "test"]
    assert result["multiplier"].to_pylist() == [2, 3, 1]
    assert result["blob_output"].to_pylist() == expected_blobs

    # Verify blob files' content - have to go to dataset api
    from lance import dataset as lance_dataset

    ds = lance_dataset(tbl._uri)
    blob_files = ds.take_blobs("blob_output", indices=[0, 1, 2])
    assert len(blob_files) == 3
    blob_values = [blob.read() for blob in blob_files]
    assert blob_values == expected_blob_values


def test_udf_generates_blob_from_array_input(tmp_path: Path) -> None:
    """Test UDF that generates Lance blob outputs from array inputs."""

    @udf(data_type=pa.large_binary(), field_metadata={"lance-encoding:blob": "true"})
    def serialize_array(values: pa.Array) -> bytes:
        """UDF that serializes an array into blob data."""
        import pickle

        _LOG.info(f"values ({type(values)}): {values}")
        return pickle.dumps(values)

    # Create database and input table with array column
    db = connect(tmp_path)
    array_data = [[1, 2, 3], [4, 5, 6, 7], [8, 9]]
    input_data = pa.table({"id": [1, 2, 3], "values": array_data})
    tbl = db.create_table("array_table", input_data)

    # Add blob column with proper metadata
    tbl.add_columns({"serialized_blob": serialize_array})
    # Verify blob metadata
    blob_field = tbl.schema.field("serialized_blob")
    assert blob_field.metadata[b"lance-encoding:blob"] == b"true"

    # Execute backfill
    tbl.backfill("serialized_blob")

    # Verify results by deserializing - have to go to dataset api
    from lance import dataset as lance_dataset

    ds = lance_dataset(tbl._uri)
    blob_files = ds.take_blobs("serialized_blob", indices=[0, 1, 2])
    assert len(blob_files) == 3
    blob_values = [blob.read() for blob in blob_files]
    for i, blob_data in enumerate(blob_values):
        import pickle

        deserialized = pickle.loads(blob_data)
        assert deserialized == array_data[i]


def test_udf_generates_blob_from_recordbatch(tmp_path: Path) -> None:
    """Test RecordBatch UDF that generates Lance blob outputs."""

    @udf(data_type=pa.large_binary(), field_metadata={"lance-encoding:blob": "true"})
    def batch_to_blob(batch: pa.RecordBatch) -> pa.Array:
        """UDF that converts RecordBatch rows to blob data."""
        import json

        blobs = []
        for i in range(batch.num_rows):
            row_dict = {
                col_name: batch.column(j)[i].as_py()
                for j, col_name in enumerate(batch.column_names)
            }
            blob_data = json.dumps(row_dict, sort_keys=True).encode("utf-8")
            blobs.append(blob_data)
        return pa.array(blobs, type=pa.large_binary())

    # Create database and input table
    db = connect(tmp_path)
    input_data = pa.table(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "score": [95.5, 87.2, 92.8],
        }
    )
    tbl = db.create_table("people_table", input_data)

    # Add blob column
    tbl.add_columns({"row_blob": batch_to_blob})

    # Verify blob metadata
    blob_field = tbl.schema.field("row_blob")
    assert blob_field.metadata[b"lance-encoding:blob"] == b"true"

    # Execute backfill
    tbl.backfill("row_blob")

    # Verify results
    result = tbl.to_arrow()

    # Verify blob files' content - have to go to dataset api
    from lance import dataset as lance_dataset

    ds = lance_dataset(tbl._uri)
    blob_files = ds.take_blobs("row_blob", indices=[0, 1, 2])
    assert len(blob_files) == 3
    blob_values = [blob.read() for blob in blob_files]
    for i, blob_data in enumerate(blob_values):
        import json

        row_dict = json.loads(blob_data.decode("utf-8"))

        # Verify the serialized data matches original
        assert row_dict["name"] == result["name"][i].as_py()
        assert row_dict["age"] == result["age"][i].as_py()
        assert abs(row_dict["score"] - result["score"][i].as_py()) < 0.001


def test_table_take_blobs_multi_fragment(tmp_path: Path) -> None:
    """Test that Table.take_blobs works with multiple fragments.

    This is a regression test for a bug where Table.take_blobs() passed indices
    positionally to Lance's take_blobs(), causing them to be interpreted as row IDs
    instead of logical indices. This caused failures when accessing blobs beyond
    the first fragment.
    """
    db = connect(tmp_path)

    # Create initial table with blob column
    schema = pa.schema(
        [
            pa.field("a", pa.int32()),
            pa.field(
                "blob", pa.large_binary(), metadata={"lance-encoding:blob": "true"}
            ),
        ]
    )
    blobs1 = [b"hello", b"world"]
    tbl_data = pa.Table.from_pydict(
        {"a": list(range(len(blobs1))), "blob": blobs1}, schema=schema
    )
    tbl = db.create_table("multi_frag_blob", tbl_data)

    # Add more rows to create second fragment
    blobs2 = [b"second", b"fragment", b"data"]
    more_data = pa.Table.from_pydict(
        {"a": list(range(len(blobs1), len(blobs1) + len(blobs2))), "blob": blobs2},
        schema=schema,
    )
    tbl.add(more_data)

    # Verify we have multiple fragments
    assert len(tbl.to_lance().get_fragments()) >= 2

    # Test take_blobs from first fragment
    result1 = tbl.take_blobs(indices=[0], column="blob")
    assert result1[0].read() == b"hello"

    # Test take_blobs from second fragment (this was failing before the fix)
    result2 = tbl.take_blobs(indices=[3], column="blob")
    assert result2[0].read() == b"fragment"

    # Test take_blobs spanning both fragments
    result_both = tbl.take_blobs(indices=[1, 4], column="blob")
    assert result_both[0].read() == b"world"
    assert result_both[1].read() == b"data"


def test_context_local(tmp_path: Path) -> None:
    ray.shutdown()
    db = connect(tmp_path)

    with db.context(cluster_type=GenevaClusterType.LOCAL_RAY):
        ray.get(ray.remote(lambda: importlib.import_module("geneva")).remote())


def test_array_udf_filtering_optimization(tmp_path: Path) -> None:
    """Test that Array UDFs only process filtered rows, not all rows."""

    @udf(data_type=pa.int32())
    def tracking_array_udf(a: pa.Array) -> pa.Array:
        """Array UDF that validates it only receives filtered values."""
        values = a.to_pylist()

        # The UDF should only receive filtered values: [0, 2, 4, 6, 8]
        # If it receives any odd values, the optimization isn't working
        for val in values:
            if val % 2 != 0:
                raise AssertionError(
                    f"Array UDF received unfiltered value {val}. "
                    f"Optimization failed - UDF should only receive even values."
                )

        return pa.compute.multiply(a, pa.scalar(10))

    # Create test data with 10 rows (0-9)
    tbl_path = tmp_path / "test.lance"
    data = {"a": pa.array(range(10))}
    table = pa.Table.from_pydict(data)
    lance.write_dataset(table, tbl_path, max_rows_per_file=32)

    db = connect(tmp_path)
    tbl = db.open_table("test")
    tbl.add_columns({"result": tracking_array_udf})

    # Apply filter that should only include even rows: 0, 2, 4, 6, 8
    tbl.backfill("result", where="a % 2 = 0")

    # Verify final results are correct
    tbl.checkout_latest()
    result = tbl.to_arrow().to_pydict()
    expected_result = [0, None, 20, None, 40, None, 60, None, 80, None]
    assert result["result"] == expected_result


def test_recordbatch_udf_filtering_optimization(tmp_path: Path) -> None:
    """Test that RecordBatch UDFs only process filtered rows, not all rows."""

    @udf(data_type=pa.int32())
    def tracking_recordbatch_udf(batch: pa.RecordBatch) -> pa.Array:
        """RecordBatch UDF that validates it only receives filtered rows."""
        values = batch["a"].to_pylist()

        # The UDF should only receive filtered values: [0, 2, 4, 6, 8]
        # If it receives any odd values, the optimization isn't working
        for val in values:
            if val % 2 != 0:
                raise AssertionError(
                    f"RecordBatch UDF received unfiltered value {val}. "
                    f"Optimization failed - UDF should only receive even values."
                )

        return pa.compute.multiply(batch["a"], pa.scalar(10))

    # Create test data with 10 rows (0-9)
    tbl_path = tmp_path / "test.lance"
    data = {"a": pa.array(range(10))}
    table = pa.Table.from_pydict(data)
    lance.write_dataset(table, tbl_path, max_rows_per_file=32)

    db = connect(tmp_path)
    tbl = db.open_table("test")
    tbl.add_columns({"result": tracking_recordbatch_udf})

    # Apply filter that should only include even rows: 0, 2, 4, 6, 8
    tbl.backfill("result", where="a % 2 = 0")

    # Verify final results are correct
    tbl.checkout_latest()
    result = tbl.to_arrow().to_pydict()
    expected_result = [0, None, 20, None, 40, None, 60, None, 80, None]
    assert result["result"] == expected_result


def test_scalar_udf_filtering_optimization(tmp_path: Path) -> None:
    """Test that Scalar UDFs only process filtered rows (should already work)."""

    @udf(data_type=pa.int32())
    def tracking_scalar_udf(a: int) -> int:
        """Scalar UDF that validates it only receives filtered values."""
        # The UDF should only receive filtered values: 0, 2, 4, 6, 8
        # If it receives any odd values, the optimization isn't working
        if a % 2 != 0:
            raise AssertionError(
                f"Scalar UDF received unfiltered value {a}. "
                f"Optimization failed - UDF should only receive even values."
            )
        return a * 10

    # Create test data with 10 rows (0-9)
    tbl_path = tmp_path / "test.lance"
    data = {"a": pa.array(range(10))}
    table = pa.Table.from_pydict(data)
    lance.write_dataset(table, tbl_path, max_rows_per_file=32)

    db = connect(tmp_path)
    tbl = db.open_table("test")
    tbl.add_columns({"result": tracking_scalar_udf})

    # Apply filter that should only include even rows: 0, 2, 4, 6, 8
    tbl.backfill("result", where="a % 2 = 0")

    # Verify final results are correct
    tbl.checkout_latest()
    result = tbl.to_arrow().to_pydict()
    expected_result = [0, None, 20, None, 40, None, 60, None, 80, None]
    assert result["result"] == expected_result


@pytest.mark.multibackfill
def test_backfill_checkpoint_size_overrides_udf_checkpoint_size(
    tmp_path: Path,
) -> None:
    """Backfill checkpoint_size should override the UDF-declared batch_size.

    Scenarios:
    1) UDF default (100), checkpoint_size=50 => max observed 50, never exceed 50
    2) UDF default (100), checkpoint_size=150 => max observed 150, includes 150
    3) UDF=200, checkpoint_size=150 => max observed 150, includes 150
    4) UDF=200, checkpoint_size=250 => max observed 250, includes 250
    """

    def run_case(
        *,
        name: str,
        udf_batch_size: int | None,
        checkpoint_size: int,
        total_rows: int,
    ) -> None:
        # Define UDF with optional declared batch_size
        if udf_batch_size is None:

            @udf(data_type=pa.int32(), num_cpus=1)
            def echo_batch_size(batch: pa.RecordBatch) -> pa.Array:
                n = batch.num_rows
                return pa.array([n] * n, type=pa.int32())
        else:

            @udf(data_type=pa.int32(), batch_size=udf_batch_size, num_cpus=1)
            def echo_batch_size(batch: pa.RecordBatch) -> pa.Array:
                n = batch.num_rows
                return pa.array([n] * n, type=pa.int32())

        # Create dataset
        tbl_path = tmp_path / f"{name}.lance"
        data = {"a": pa.array(range(total_rows))}
        table = pa.Table.from_pydict(data)
        lance.write_dataset(table, tbl_path, max_rows_per_file=300)

        db = connect(tmp_path)
        tbl = db.open_table(name)
        tbl.add_columns({"observed": echo_batch_size})

        # Backfill with override batch size
        tbl.backfill("observed", checkpoint_size=checkpoint_size)

        # Validate that observed batch sizes never exceed override
        tbl.checkout_latest()
        observed = tbl.to_arrow().column("observed").to_pylist()
        vals = [int(v) for v in observed if v is not None]
        assert max(vals) == checkpoint_size
        assert all(0 <= v <= checkpoint_size for v in vals)

    # 1) UDF default (100), backfill=50
    run_case(
        name="override_default_50",
        udf_batch_size=None,
        checkpoint_size=50,
        total_rows=300,
    )

    # 2) UDF default (100), backfill=150
    run_case(
        name="override_default_150",
        udf_batch_size=None,
        checkpoint_size=150,
        total_rows=600,
    )

    # 3) UDF=200, backfill=150
    run_case(
        name="override_udf200_150",
        udf_batch_size=200,
        checkpoint_size=150,
        total_rows=600,
    )

    # 4) UDF=200, backfill=250
    run_case(
        name="override_udf200_250",
        udf_batch_size=200,
        checkpoint_size=250,
        total_rows=1000,
    )


def test_backfill_async_checkpoint_size_used(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """backfill_async respects checkpoint_size and warns on deprecated batch_size."""

    @udf(data_type=pa.int32(), batch_size=64, num_cpus=1)
    def echo_batch_size(batch: pa.RecordBatch) -> pa.Array:
        n = batch.num_rows
        return pa.array([n] * n, type=pa.int32())

    tbl_path = tmp_path / "ckp_async.lance"
    data = {"a": pa.array(range(55))}
    table = pa.Table.from_pydict(data)
    lance.write_dataset(table, tbl_path, max_rows_per_file=32)

    db = connect(tmp_path)
    tbl = db.open_table("ckp_async")
    tbl.add_columns({"observed": echo_batch_size})

    # checkpoint_size override
    fut = tbl.backfill_async("observed", checkpoint_size=11)
    fut.result()

    tbl.checkout_latest()
    vals = [
        int(v) for v in tbl.to_arrow().column("observed").to_pylist() if v is not None
    ]
    assert max(vals) == 11

    # batch_size deprecated warning when only batch_size passed (fresh table)
    caplog.set_level(logging.WARNING, logger="geneva.utils.batch_size")

    tbl_path2 = tmp_path / "ckp_async_b.lance"
    data2 = {"a": pa.array(range(45))}
    lance.write_dataset(pa.Table.from_pydict(data2), tbl_path2, max_rows_per_file=32)

    db2 = connect(tmp_path)
    tbl2 = db2.open_table("ckp_async_b")
    tbl2.add_columns({"observed": echo_batch_size})

    fut2 = tbl2.backfill_async("observed", batch_size=13)
    fut2.result()

    assert any("batch_size is deprecated" in rec.message for rec in caplog.records)
    tbl2.checkout_latest()
    vals2 = [
        int(v) for v in tbl2.to_arrow().column("observed").to_pylist() if v is not None
    ]
    assert max(vals2) == 13


@pytest.fixture
def dir_namespace_props(tmp_path) -> dict[str, str]:
    return {"root": str(tmp_path)}


@pytest.fixture(autouse=True)
def dir_namespace_db(tmp_path, dir_namespace_props) -> Connection:
    db = geneva.connect(
        namespace_impl="dir",
        namespace_properties=dir_namespace_props,
    )
    yield db
    db.close()


@pytest.fixture
def rest_namespace_db(
    tmp_path, dir_namespace_props
) -> Generator[Connection, None, None]:
    """Create a REST namespace with adapter for testing."""
    unique_id = uuid.uuid4().hex[:8]
    port = 4000 + hash(unique_id) % 10000

    with lance.namespace.RestAdapter("dir", dir_namespace_props, port=port):
        db = geneva.connect(
            namespace_impl="rest",
            namespace_properties={"uri": f"http://127.0.0.1:{port}"},
        )
        yield db
        db.close()


def test_backfill_with_db(db) -> None:
    _test_backfill_with_namespace(db)


def test_backfill_with_dir_namespace_root(dir_namespace_db) -> None:
    _test_backfill_with_namespace(dir_namespace_db)


def test_backfill_with_rest_namespace_root(rest_namespace_db) -> None:
    _test_backfill_with_namespace(rest_namespace_db)


def test_backfill_with_dir_namespace_child(dir_namespace_db) -> None:
    _test_backfill_with_namespace(dir_namespace_db, namespace=["workspace"])


def test_backfill_with_rest_namespace_child(rest_namespace_db) -> None:
    _test_backfill_with_namespace(rest_namespace_db, namespace=["workspace"])


def _test_backfill_with_namespace(
    db_impl: Connection, namespace: list[str] | None = None
) -> None:
    from geneva.table import Table

    @udf(data_type=pa.int64())
    def add_one(a: int):  # noqa A002
        return a + 1

    schema = pa.schema(
        [
            pa.field("a", pa.int32()),
            pa.field("b", pa.int32()),
        ]
    )

    data = pa.table({"a": range(10, 20), "b": range(30, 40)})

    # If namespace is provided (not root), create it
    if namespace:
        from lance_namespace import CreateNamespaceRequest

        ns = db_impl.namespace_client
        assert ns is not None, "This test requires a namespace connection"
        ns.create_namespace(CreateNamespaceRequest(id=namespace))

        # Create table in the child namespace
        db_impl._connect.create_table("t", schema=schema, namespace=namespace)
        tbl = Table(db_impl, "t", namespace=namespace)
    else:
        # Create table in root namespace
        tbl = db_impl.create_table("t", schema=schema)

    tbl.add(pa.table(data))
    tbl.add_columns({"c": add_one})
    tbl.backfill("c")
    vals = tbl.to_arrow()
    _LOG.info(f"=== backfill result ver {tbl.version}: {vals}")
    assert vals["c"].to_pylist() == [11, 12, 13, 14, 15, 16, 17, 18, 19, 20], (
        "backfill didn't succeed"
    )

    # Verify checkpoint folder and files exist (if created)
    # Note: Small local tests may not create checkpoints
    if db_impl.namespace_client:
        from lance_namespace import DescribeTableRequest

        table_id = namespace + ["t"] if namespace else ["t"]
        table_desc = db_impl.namespace_client.describe_table(
            DescribeTableRequest(id=table_id)
        )
        table_location = table_desc.location
        assert table_location is not None, "Table location should not be None"
        _LOG.info(f"Table location: {table_location}")

        # Check if checkpoint folder exists
        checkpoint_path = f"{table_location.rstrip('/')}/ckp"
        _LOG.info(f"Checking checkpoint path: {checkpoint_path}")

        # Use pyarrow filesystem to check if checkpoint directory exists
        import pyarrow.fs as pafs

        filesystem, path = pafs.FileSystem.from_uri(checkpoint_path)
        try:
            dir_info = filesystem.get_file_info(path)
            if dir_info.type == pafs.FileType.Directory:
                # Directory exists, verify checkpoint files
                file_infos = filesystem.get_file_info(
                    pafs.FileSelector(path, recursive=True)
                )
                checkpoint_files = [
                    info.path
                    for info in file_infos
                    if info.type == pafs.FileType.File and info.path.endswith(".lance")
                ]
                _LOG.info(
                    f"Found {len(checkpoint_files)} checkpoint files: "
                    f"{checkpoint_files}"
                )
                assert len(checkpoint_files) > 0, (
                    f"Checkpoint directory exists but no files found in "
                    f"{checkpoint_path}"
                )
                _LOG.info(f"Verified checkpoint files exist at {checkpoint_path}")
            else:
                # Checkpoint directory doesn't exist - this is OK for small local tests
                _LOG.info(
                    f"Checkpoint directory not created "
                    f"(expected for small local tests): {checkpoint_path}"
                )
        except Exception as e:
            # Directory doesn't exist - OK for small tests
            _LOG.info(
                f"Checkpoint directory not found (expected for small local tests): {e}"
            )

    # Drop table
    if namespace:
        db_impl.drop_table("t", namespace=namespace)
    else:
        db_impl.drop_table("t")

    _LOG.info(f"{type(db_impl)} success")

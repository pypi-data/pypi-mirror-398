# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors
import tempfile
import uuid
from datetime import timezone
from pathlib import Path
from typing import Any

import pytest
import ray
from lancedb import connect_async

from geneva.db import connect
from geneva.jobs.jobs import (
    GENEVA_JOBS_TABLE_NAME,
    JobMetric,
    JobRecord,
    JobStateManager,
)
from geneva.runners.ray.jobtracker import JobTracker
from geneva.table import TableReference

pytestmark = pytest.mark.ray


@pytest.fixture(autouse=True)
def ray_cluster() -> None:
    ray.shutdown()
    ray.init(
        log_to_driver=True,
        logging_config=ray.LoggingConfig(
            encoding="TEXT", log_level="DEBUG", additional_log_standard_attrs=["name"]
        ),
    )
    yield
    ray.shutdown()


@pytest.fixture
async def temp_db_path() -> Any:
    """Create a temporary database directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
async def db_connection(temp_db_path) -> Any:
    """Create a Geneva database connection."""
    db = connect(temp_db_path)
    yield db
    db.close()


@pytest.fixture
async def jobs_table(db_connection) -> Any:
    """Create the geneva_jobs table with proper schema."""
    # Create the jobs table using JobStateManager to ensure proper schema
    job_manager = JobStateManager(db_connection)
    return job_manager.get_table()


@pytest.fixture
async def table_reference(temp_db_path) -> TableReference:
    """Create a TableReference for testing."""
    return TableReference(
        table_id=["test_table"],
        version=None,
        db_uri=str(temp_db_path),
        namespace_impl=None,
        namespace_properties=None,
    )


@pytest.fixture
async def async_db_connection(temp_db_path) -> Any:
    """Create an async LanceDB connection."""
    async_conn = await connect_async(str(temp_db_path))
    yield async_conn
    if hasattr(async_conn, "close"):
        close_result = async_conn.close()
        if hasattr(close_result, "__await__"):
            await close_result


def test_jobtracker_creation(table_reference) -> None:
    """Test JobTracker can be created with required fields."""
    job_id = str(uuid.uuid4())

    # Create JobTracker instance (without Ray remote for testing)
    tracker = JobTracker.remote(job_id, table_reference)

    tracker.get_all.remote()


@pytest.mark.asyncio
async def test_save_metrics_with_mock_db(
    temp_db_path, async_db_connection, db_connection
) -> None:
    """Test _save_metrics with a real async database connection."""
    job_id = str(uuid.uuid4())

    # Create the jobs table
    jsm = JobStateManager(db_connection, GENEVA_JOBS_TABLE_NAME)

    # Add a test job record
    from datetime import datetime

    jobs_table = await async_db_connection.open_table(GENEVA_JOBS_TABLE_NAME)
    time = datetime(2025, 11, 7, 9, 46, 9, 599847, tzinfo=timezone.utc)
    await jobs_table.add(
        [
            {
                "job_id": job_id,
                "table_name": "test_table",
                "column_name": "test_column",
                "status": "RUNNING",
                "metrics": [],
                "launched_at": time,
                "updated_at": time,
                "completed_at": None,
                "config": "{}",
                "launched_by": "test",
                "manifest_id": None,
                "manifest_checksum": None,
                "events": [],
                "object_ref": None,
                "job_type": "BACKFILL",
            }
        ]
    )

    # Create JobTracker and manually set up the connection
    table_ref = TableReference(
        table_id=["test_table"], version=None, db_uri=str(temp_db_path)
    )

    tracker = JobTracker.remote(job_id, table_ref)

    # Manually set the database connection for testing
    tracker._db = async_db_connection
    tracker._jobs_table = jobs_table

    # Test _save_metrics
    test_metrics = {
        "task1": {"n": 50, "total": 100, "done": False, "desc": "Test task"}
    }

    await tracker._save_metrics.remote(test_metrics)

    jobs = jsm.list_jobs(table_name="test_table")
    jobs[0].updated_at = None
    assert jobs == [
        JobRecord(
            table_name="test_table",
            column_name="test_column",
            job_id=job_id,
            job_type="BACKFILL",
            object_ref=None,
            status="RUNNING",
            launched_at=time,
            updated_at=None,
            completed_at=None,
            config="{}",
            launched_by="test",
            manifest_id=None,
            manifest_checksum=None,
            metrics=[
                JobMetric(name="task1", n=50, total=100, done=False, desc="Test task")
            ],
            events=[],
        )
    ]


@pytest.mark.asyncio
async def test_full_workflow_with_db(temp_db_path, db_connection) -> None:
    """Test a complete workflow with real database operations."""
    job_id = str(uuid.uuid4())

    # Set up the database with jobs table
    job_manager = JobStateManager(db_connection)
    job_record = job_manager.launch("test_table", "test_column")

    # Override with our test job_id
    job_manager.get_table().update(
        where=f"job_id = '{job_record.job_id}'", values={"job_id": job_id}
    )

    # Create async connection for JobTracker
    async_conn = await connect_async(str(temp_db_path))
    jobs_table = await async_conn.open_table(GENEVA_JOBS_TABLE_NAME)

    # Create JobTracker and set up connection
    table_ref = TableReference(
        table_id=["test_table"], version=None, db_uri=str(temp_db_path)
    )

    tracker = JobTracker.remote(job_id, table_ref)
    tracker._db = async_conn
    tracker._jobs_table = jobs_table

    # Test complete workflow
    await tracker.set_total.remote("download", 1000)
    await tracker.set_desc.remote("download", "foo")

    # Simulate progress
    for i in range(0, 1001, 100):
        await tracker.set.remote("download", i)
        if i == 1000:
            break

    # mark done to flush to db
    tracker.mark_done.remote("done")

    # Verify final state
    progress = await tracker.get_progress.remote("download")
    assert progress["n"] == 1000
    assert progress["total"] == 1000
    assert progress["done"] is True
    assert progress["desc"] == "foo"

    # Verify metrics updated in database
    jobs = job_manager.get(job_id)
    assert len(jobs) == 1
    stored_metrics = jobs[0].metrics
    assert len(stored_metrics) == 1

    metric_data = stored_metrics[0]
    assert metric_data.name == "download"
    assert metric_data.n == 1000
    assert metric_data.total == 1000
    assert metric_data.done is True


def test_save_with_throttle_logic() -> None:
    """Test the throttling logic directly."""
    current_time = 0.0
    save_calls = []

    def mock_get_time() -> float:
        return current_time

    def mock_save(metrics) -> None:  # noqa: ARG001
        save_calls.append(current_time)

    # Simulate the throttle logic
    min_time_between_updates = 5.0
    last_updated = -float("inf")  # Initialize to allow first save

    def save_with_throttle(force: bool = False) -> None:
        nonlocal last_updated
        if not force and last_updated + min_time_between_updates > current_time:
            return
        last_updated = current_time
        mock_save({})

    # Test: First save at time 0
    current_time = 0.0
    save_with_throttle()
    assert len(save_calls) == 1

    # Test: Save at time 2 (within throttle) - should be blocked
    current_time = 2.0
    save_with_throttle()
    assert len(save_calls) == 1  # Still 1

    # Test: Save at time 6 (beyond throttle) - should save
    current_time = 6.0
    save_with_throttle()
    assert len(save_calls) == 2

    # Test: Force save at time 7 (within throttle) - should save anyway
    current_time = 7.0
    save_with_throttle(force=True)
    assert len(save_calls) == 3


def test_completion_forces_save_logic() -> None:
    """Test that completion forces save."""
    save_calls = []
    current_time = 0.0

    def mock_save(metrics) -> None:  # noqa: ARG001
        save_calls.append(current_time)

    min_time_between_updates = 100.0  # Very long throttle
    last_updated = -float("inf")

    def save_with_throttle(force: bool = False) -> None:
        nonlocal last_updated
        if not force and last_updated + min_time_between_updates > current_time:
            return
        last_updated = current_time
        mock_save({})

    # First save
    current_time = 0.0
    save_with_throttle()
    assert len(save_calls) == 1

    # Try to save within throttle window - should be blocked
    current_time = 1.0
    save_with_throttle(force=False)
    assert len(save_calls) == 1

    # Force save (like when completing) - should save
    save_with_throttle(force=True)
    assert len(save_calls) == 2


def test_set_and_increment_logic() -> None:
    """Test the set/increment logic for determining when to force save."""

    # Test increment that completes
    total = 100
    n = 90
    done = False
    if total and n >= total:
        done = True
    assert done is False

    # After increment
    n += 10
    if total and n >= total:
        done = True
    assert done is True

    # Test set that completes
    total = 100
    n = 0
    done = False
    n = 100
    if total and n >= total:
        done = True
    assert done is True

    # Test increment past total
    total = 100
    n = 0
    n += 150
    done = False
    if total and n >= total:
        done = True
    assert done is True


def test_zero_throttle() -> None:
    """Test that zero throttle allows all saves."""
    save_calls = []
    current_time = 0.0

    def mock_save(metrics) -> None:  # noqa: ARG001
        save_calls.append(current_time)

    min_time_between_updates = 0.0  # No throttling
    last_updated = -float("inf")

    def save_with_throttle(force: bool = False) -> None:
        nonlocal last_updated
        if not force and last_updated + min_time_between_updates > current_time:
            return
        last_updated = current_time
        mock_save({})

    # Multiple rapid saves - all should go through
    for i in range(5):
        current_time = i * 0.01
        save_with_throttle()

    assert len(save_calls) == 5


def test_mark_done_always_forces() -> None:
    """Test that mark_done behavior always forces save."""
    # mark_done calls save_with_throttle(force=True)
    # So it should always save regardless of throttle

    save_calls = []
    current_time = 0.0

    def mock_save(metrics) -> None:  # noqa: ARG001
        save_calls.append(current_time)

    min_time_between_updates = 100.0
    last_updated = -float("inf")

    def save_with_throttle(force: bool = False) -> None:
        nonlocal last_updated
        if not force and last_updated + min_time_between_updates > current_time:
            return
        last_updated = current_time
        mock_save({})

    # Initial save
    current_time = 0.0
    save_with_throttle()
    assert len(save_calls) == 1

    # mark_done would call with force=True even within throttle window
    current_time = 1.0
    save_with_throttle(force=True)
    assert len(save_calls) == 2

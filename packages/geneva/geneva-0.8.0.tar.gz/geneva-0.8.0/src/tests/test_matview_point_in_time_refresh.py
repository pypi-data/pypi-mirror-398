# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""Tests for materialized view point-in-time refresh (rollback to older versions)."""

from unittest.mock import patch

import pyarrow as pa
import pytest

from geneva import connect
from geneva.jobs.config import JobConfig
from geneva.packager import DockerUDFPackager

pytestmark = pytest.mark.ray


def make_batch(start: int, count: int) -> pa.Table:
    """Create test data with alternating dog/cat categories."""
    return pa.table(
        {
            "id": list(range(start, start + count)),
            "category": [
                "dog" if (i % 2 == 0) else "cat" for i in range(start, start + count)
            ],
            "value": [i * 10 for i in range(start, start + count)],
        }
    )


def test_point_in_time_refresh_requires_stable_row_ids(tmp_path) -> None:
    """Test that point-in-time refresh fails without stable row IDs."""
    packager = DockerUDFPackager(prebuilt_docker_img="test-image:latest")
    db = connect(tmp_path, packager=packager)

    # Create table WITHOUT stable row IDs
    animals = db.create_table("animals", make_batch(0, 100))
    v1 = animals.version

    # Create MV and refresh
    dogs = (
        animals.search(None)
        .where("category == 'dog'")
        .create_materialized_view(conn=db, view_name="dogs")
    )
    dogs.refresh()
    assert dogs.count_rows() == 50

    # Add more data
    animals.add(make_batch(100, 50))
    v2 = animals.version
    assert v2 > v1

    # Refresh to v2 should fail (different version without stable row IDs)
    with pytest.raises(RuntimeError, match="stable row IDs"):
        dogs.refresh()


def test_point_in_time_refresh_rollback(tmp_path) -> None:
    """Test that we can roll back to an older source version with stable row IDs."""
    packager = DockerUDFPackager(prebuilt_docker_img="test-image:latest")
    db = connect(tmp_path, packager=packager)

    # Create table WITH stable row IDs
    animals = db.create_table(
        "animals",
        make_batch(0, 100),
        storage_options={"new_table_enable_stable_row_ids": True},
    )
    v1 = animals.version

    # Create MV and refresh
    dogs = (
        animals.search(None)
        .where("category == 'dog'")
        .create_materialized_view(conn=db, view_name="dogs")
    )
    dogs.refresh()
    assert dogs.count_rows() == 50  # 50 dogs out of 100 (every other row)

    # Add more data
    animals.add(make_batch(100, 50))

    # Refresh to latest
    dogs.refresh()
    assert dogs.count_rows() == 75  # 75 dogs out of 150

    # Rollback to v1 (point-in-time refresh)
    dogs.refresh(src_version=v1)
    assert dogs.count_rows() == 50  # Back to 50 dogs

    # Can refresh forward again
    dogs.refresh()
    assert dogs.count_rows() == 75  # Back to 75 dogs


def test_point_in_time_refresh_multiple_rollbacks(tmp_path) -> None:
    """Test multiple rollback and forward refreshes."""
    packager = DockerUDFPackager(prebuilt_docker_img="test-image:latest")
    db = connect(tmp_path, packager=packager)

    # Create table WITH stable row IDs
    animals = db.create_table(
        "animals",
        make_batch(0, 100),
        storage_options={"new_table_enable_stable_row_ids": True},
    )
    v1 = animals.version

    # Create MV and refresh
    dogs = (
        animals.search(None)
        .where("category == 'dog'")
        .create_materialized_view(conn=db, view_name="dogs")
    )
    dogs.refresh()
    count_v1 = dogs.count_rows()
    assert count_v1 == 50

    # Add batch 2
    animals.add(make_batch(100, 50))
    v2 = animals.version
    dogs.refresh()
    count_v2 = dogs.count_rows()
    assert count_v2 == 75

    # Add batch 3
    animals.add(make_batch(150, 50))
    v3 = animals.version
    dogs.refresh()
    count_v3 = dogs.count_rows()
    assert count_v3 == 100

    # Rollback to v1
    dogs.refresh(src_version=v1)
    assert dogs.count_rows() == count_v1

    # Rollback to v2
    dogs.refresh(src_version=v2)
    assert dogs.count_rows() == count_v2

    # Forward to v3
    dogs.refresh(src_version=v3)
    assert dogs.count_rows() == count_v3

    # Rollback to v1 again
    dogs.refresh(src_version=v1)
    assert dogs.count_rows() == count_v1


def test_point_in_time_refresh_without_filter(tmp_path) -> None:
    """Test point-in-time refresh on MV without WHERE filter."""
    packager = DockerUDFPackager(prebuilt_docker_img="test-image:latest")
    db = connect(tmp_path, packager=packager)

    # Create table WITH stable row IDs
    animals = db.create_table(
        "animals",
        make_batch(0, 100),
        storage_options={"new_table_enable_stable_row_ids": True},
    )
    v1 = animals.version

    # Create MV without filter (copies all rows)
    all_animals = animals.search(None).create_materialized_view(
        conn=db, view_name="all_animals"
    )
    all_animals.refresh()
    assert all_animals.count_rows() == 100

    # Add more data
    animals.add(make_batch(100, 50))

    # Refresh to latest
    all_animals.refresh()
    assert all_animals.count_rows() == 150

    # Rollback to v1
    all_animals.refresh(src_version=v1)
    assert all_animals.count_rows() == 100

    # Forward again
    all_animals.refresh()
    assert all_animals.count_rows() == 150


def test_point_in_time_refresh_batched_deletion(tmp_path) -> None:
    """Test that rollback deletes rows in batches when delete_batch_size is small."""
    packager = DockerUDFPackager(prebuilt_docker_img="test-image:latest")
    db = connect(tmp_path, packager=packager)

    # Create table WITH stable row IDs
    animals = db.create_table(
        "animals",
        make_batch(0, 100),
        storage_options={"new_table_enable_stable_row_ids": True},
    )
    v1 = animals.version

    # Create MV without filter (copies all rows)
    all_animals = animals.search(None).create_materialized_view(
        conn=db, view_name="all_animals"
    )
    all_animals.refresh()
    assert all_animals.count_rows() == 100

    # Add more data - 50 additional rows
    animals.add(make_batch(100, 50))

    # Refresh to latest
    all_animals.refresh()
    assert all_animals.count_rows() == 150

    # Rollback to v1 with small batch size (10) to force multiple batches
    # This will delete 50 rows in 5 batches of 10
    config_with_small_batch = JobConfig(delete_batch_size=10)

    with patch.object(JobConfig, "get", return_value=config_with_small_batch):
        all_animals.refresh(src_version=v1)

    # Verify rollback worked correctly
    assert all_animals.count_rows() == 100


def test_forward_refresh_with_source_deletions(tmp_path) -> None:
    """Test that forward refresh deletes MV rows when source rows are deleted."""
    packager = DockerUDFPackager(prebuilt_docker_img="test-image:latest")
    db = connect(tmp_path, packager=packager)

    # Create table WITH stable row IDs
    animals = db.create_table(
        "animals",
        make_batch(0, 100),
        storage_options={"new_table_enable_stable_row_ids": True},
    )

    # Create MV for dogs only and refresh
    dogs = (
        animals.search(None)
        .where("category == 'dog'")
        .create_materialized_view(conn=db, view_name="dogs")
    )
    dogs.refresh()
    assert dogs.count_rows() == 50  # 50 dogs (IDs 0, 2, 4, ..., 98)

    # Delete some dogs from source (IDs 0, 2, 4 are dogs)
    animals.delete("id IN (0, 2, 4)")

    # Forward refresh should detect and delete corresponding MV rows
    dogs.refresh()
    assert dogs.count_rows() == 47  # 50 - 3 deleted dogs


def test_forward_refresh_with_mixed_adds_and_deletes(tmp_path) -> None:
    """Test forward refresh handles both additions and deletions."""
    packager = DockerUDFPackager(prebuilt_docker_img="test-image:latest")
    db = connect(tmp_path, packager=packager)

    # Create table WITH stable row IDs
    animals = db.create_table(
        "animals",
        make_batch(0, 100),
        storage_options={"new_table_enable_stable_row_ids": True},
    )

    # Create MV for dogs only and refresh
    dogs = (
        animals.search(None)
        .where("category == 'dog'")
        .create_materialized_view(conn=db, view_name="dogs")
    )
    dogs.refresh()
    assert dogs.count_rows() == 50  # 50 dogs

    # Delete some dogs (IDs 0, 2 are dogs)
    animals.delete("id IN (0, 2)")

    # Add new rows (IDs 100-149, 25 will be dogs)
    animals.add(make_batch(100, 50))

    # Forward refresh should handle both deletions and additions
    dogs.refresh()
    # 50 original - 2 deleted + 25 new dogs = 73
    assert dogs.count_rows() == 73


def test_forward_refresh_filter_affects_deletions(tmp_path) -> None:
    """Test that MV filter is applied when checking deletions."""
    packager = DockerUDFPackager(prebuilt_docker_img="test-image:latest")
    db = connect(tmp_path, packager=packager)

    # Create table WITH stable row IDs
    animals = db.create_table(
        "animals",
        make_batch(0, 100),
        storage_options={"new_table_enable_stable_row_ids": True},
    )

    # Create MV for dogs only and refresh
    dogs = (
        animals.search(None)
        .where("category == 'dog'")
        .create_materialized_view(conn=db, view_name="dogs")
    )
    dogs.refresh()
    initial_count = dogs.count_rows()
    assert initial_count == 50

    # Delete cats (IDs 1, 3, 5 are cats, not dogs)
    animals.delete("id IN (1, 3, 5)")

    # Forward refresh should not affect MV (cats weren't in it)
    dogs.refresh()
    assert dogs.count_rows() == initial_count  # Still 50 dogs

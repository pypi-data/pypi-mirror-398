# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Test file existence checking UDF for OpenVid videos.
"""

import logging

import pytest

_LOG = logging.getLogger(__name__)


def test_has_file_column_added(openvid_table):
    """Test that has_file column was added to the table."""
    conn, tbl, table_name = openvid_table

    # Verify has_file column exists
    assert "has_file" in tbl.schema.names, (
        f"Expected 'has_file' column in schema, got: {tbl.schema.names}"
    )

    _LOG.info(f"✓ has_file column exists in table schema")


def test_has_file_backfill(
    openvid_table,
    standard_cluster,
    num_videos,
    batch_size,
):
    """Test backfilling has_file column to check video existence."""
    conn, tbl, table_name = openvid_table
    cluster_name = standard_cluster

    _LOG.info(f"Starting has_file backfill for {num_videos} videos (batch_size={batch_size})")

    # Run backfill with manifest
    with conn.context(cluster=cluster_name, manifest="openvid-simple-udfs-v1"):
        result = tbl.backfill(
            "has_file",
            batch_size=batch_size,
        )

    _LOG.info(f"Backfill completed: {result}")

    # Verify results
    df = tbl.to_pandas()
    assert len(df) > 0, "Table should have data"
    assert "has_file" in df.columns, "has_file column should exist"

    # Check that we got some results (at least some files should exist)
    has_file_count = df["has_file"].sum() if "has_file" in df.columns else 0
    _LOG.info(f"Files found: {has_file_count}/{len(df)}")

    # Log some sample results
    _LOG.info("\nSample results:")
    sample_cols = ["video", "has_file"] if "video" in df.columns else ["has_file"]
    _LOG.info(f"\n{df[sample_cols].head(10)}")

    _LOG.info(f"✓ has_file backfill completed successfully")


def test_has_file_filter_existing(
    openvid_table,
    standard_cluster,
):
    """Test filtering to only videos that exist in GCS."""
    conn, tbl, table_name = openvid_table
    cluster_name = standard_cluster

    # Ensure has_file is populated (this may have been done by previous test)
    df_all = tbl.to_pandas()
    if "has_file" not in df_all.columns or df_all["has_file"].isna().all():
        pytest.skip("has_file column not populated - run test_has_file_backfill first")

    # Filter to only existing files
    existing_videos = tbl.search().where("has_file = true").to_pandas()

    _LOG.info(f"Total videos: {len(df_all)}")
    _LOG.info(f"Existing videos: {len(existing_videos)}")

    if len(existing_videos) > 0:
        _LOG.info("\nSample existing videos:")
        sample_cols = ["video", "has_file"]
        _LOG.info(f"\n{existing_videos[sample_cols].head(5)}")

    _LOG.info(f"✓ Successfully filtered to {len(existing_videos)} existing videos")

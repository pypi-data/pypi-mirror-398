# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Test basic table creation and video loading for OpenVid pipeline.

This is a minimal test to verify the e2e scaffolding works.
"""

import logging

_LOG = logging.getLogger(__name__)


def test_openvid_table_creation(
    openvid_table: tuple,
    num_videos: int,
) -> None:
    """
    Test that the OpenVid table is created correctly.

    This test:
    1. Uses shared OpenVid table fixture
    2. Validates table schema and row count
    3. Checks that required CSV columns exist (video, caption, frame, fps, seconds)
    """
    conn, tbl, table_name = openvid_table

    _LOG.info(f"Testing table: {table_name}")
    _LOG.info(f"Table schema: {tbl.schema}")
    _LOG.info(f"Table row count: {len(tbl)}")

    # Validate schema - check for expected CSV columns
    schema = tbl.schema
    expected_columns = ['video', 'caption', 'frame', 'fps', 'seconds']

    for col in expected_columns:
        assert col in schema.names, f"{col} column not found in schema"

    # Check if video_path was added
    if "video_path" in schema.names:
        _LOG.info("video_path column found (GCS paths added)")

    # Validate row count
    assert len(tbl) > 0, "Table should have at least one row"
    assert len(tbl) <= num_videos, f"Table should have at most {num_videos} rows"

    # Validate data
    df = tbl.to_pandas()
    _LOG.info(f"Sample data:\n{df.head()}")

    # Check required columns have data
    assert df["video"].notna().all(), "video column has null values"
    assert df["caption"].notna().all(), "caption column has null values"

    # Check numeric columns
    assert df["frame"].notna().all(), "frame column has null values"
    assert df["fps"].notna().all(), "fps column has null values"
    assert df["seconds"].notna().all(), "seconds column has null values"

    # If video_path exists, validate it
    if "video_path" in df.columns:
        assert df["video_path"].notna().all(), "video_path has null values"
        assert all(df["video_path"].str.startswith("gs://")), "video_path should start with gs://"

    _LOG.info("Table creation test passed!")

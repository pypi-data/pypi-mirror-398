#!/usr/bin/env python3
# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors
"""
Setup script to create the demo OpenVid table.

This script creates the initial demo table at GENEVA_DB_PATH that will be
used by e2e tests. Tests copy from this pre-existing table rather than
creating from scratch each time.

Usage:
    # Create demo table with 1000 videos (default)
    python setup_demo_table.py

    # Create demo table with custom number of videos
    python setup_demo_table.py --num-videos 500

    # Include video paths from source bucket
    python setup_demo_table.py --source-bucket gs://my-bucket/videos
"""

import argparse
import logging

from conftest import (
    DEMO_TABLE_NAME,
    GENEVA_DB_PATH,
    SOURCE_TABLE_NAME,
    VID_DATA_PATH,
    create_openvid_demo_table,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)
_LOG = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create demo OpenVid table for e2e tests"
    )
    parser.add_argument(
        "--num-videos",
        type=int,
        default=100,
        help="Number of videos to include in demo table (default: 100)",
    )
    parser.add_argument(
        "--source-bucket",
        type=str,
        default=None,
        help="GCS bucket path containing videos (e.g., gs://bucket/videos)",
    )
    args = parser.parse_args()

    _LOG.info("=" * 70)
    _LOG.info("Creating Demo OpenVid Table")
    _LOG.info("=" * 70)
    _LOG.info(f"Destination: {GENEVA_DB_PATH}")
    _LOG.info(f"Source table: {SOURCE_TABLE_NAME} (full dataset)")
    _LOG.info(f"Demo table: {DEMO_TABLE_NAME} (sample)")
    _LOG.info(f"Number of videos: {args.num_videos}")
    _LOG.info(f"Source bucket: {args.source_bucket or 'None (metadata only)'}")
    _LOG.info(f"Video data path: {VID_DATA_PATH}")
    _LOG.info("=" * 70)

    try:
        create_openvid_demo_table(
            num_videos=args.num_videos, source_bucket=args.source_bucket
        )
        _LOG.info("=" * 70)
        _LOG.info("✓ Demo tables created successfully!")
        _LOG.info(f"  Source table: {GENEVA_DB_PATH}/{SOURCE_TABLE_NAME}")
        _LOG.info(f"  Demo table: {GENEVA_DB_PATH}/{DEMO_TABLE_NAME}")
        _LOG.info(
            "  Tests will copy from demo table using openvid_table fixture"
        )
        _LOG.info("=" * 70)
    except Exception as e:
        _LOG.error("=" * 70)
        _LOG.error(f"✗ Failed to create demo table: {e}")
        _LOG.error("=" * 70)
        raise


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Upload manifest and add columns for video embeddings UDF to Geneva.

This script runs in the UDF's dependency environment (via uv run)
and uploads the manifest to the Geneva connection, then adds columns
to the specified table.

Usage:
    export GENEVA_TABLE_NAME=openvid_shared_abc123
    cd e2e/openvid/udfs/video-embeddings
    uv run python upload_manifest.py --bucket gs://bucket/path

Environment Variables:
    GENEVA_TABLE_NAME: Table name to add columns to (required)
    VIDEO_EMBEDDING_COL: Custom column name for video_embedding (default: "video_embedding")
"""

import logging
import os

from geneva.manifest.uploader_cli import main_upload_workflow
from manifest import create_manifest
from video_embedding_udf import VideoEmbedding

logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger(__name__)


def get_columns() -> dict[str, callable]:
    """
    Get column definitions for this UDF package.

    Column names can be customized via environment variables:
    - VIDEO_EMBEDDING_COL: Custom name for video_embedding column (default: "video_embedding_vjpea2")

    Returns:
        Dictionary mapping column names to UDF functions
    """
    return {
        os.getenv("VIDEO_EMBEDDING_COL", "video_embedding_vjepa2"): VideoEmbedding(),
    }


if __name__ == "__main__":
    main_upload_workflow(
        get_columns_fn=get_columns,
        create_manifest_fn=create_manifest,
        description="Upload video embeddings UDF manifest and add columns to table",
        default_manifest_name="video-embeddings-v1",
        logger=_LOG,
    )

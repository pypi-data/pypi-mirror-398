#!/usr/bin/env python
# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Upload manifest and add columns for BLIP caption UDF to Geneva.

This script runs in the UDF's dependency environment (via uv run)
and uploads the manifest to the Geneva connection, then adds columns
to the specified table.

Usage:
    export GENEVA_TABLE_NAME=oxford_pets_shared_abc123
    cd e2e/oxford-pets/udfs/blip
    uv run python upload_manifest.py --bucket gs://bucket/path

Environment Variables:
    GENEVA_TABLE_NAME: Table name to add columns to (required)
    CAPTION_COL: Custom column name for caption (default: "caption")
"""

import logging
import os

from geneva.manifest.uploader_cli import main_upload_workflow
from blip_caption_udf import GenCaption
from manifest import create_manifest

logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger(__name__)


def get_columns() -> dict[str, callable]:
    """
    Get column definitions for this UDF package.

    Column names can be customized via environment variables:
    - CAPTION_COL: Custom name for caption column (default: "caption")

    Returns:
        Dictionary mapping column names to UDF functions
    """
    return {
        os.getenv("CAPTION_COL", "caption"): GenCaption(),
    }


if __name__ == "__main__":
    main_upload_workflow(
        get_columns_fn=get_columns,
        create_manifest_fn=create_manifest,
        description="Upload BLIP caption UDF manifest and add columns to table",
        default_manifest_name="blip-udfs-v1",
        logger=_LOG,
    )

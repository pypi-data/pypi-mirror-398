#!/usr/bin/env python
# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Upload manifest and add columns for simple OpenVid UDFs to Geneva.

This script runs in the UDF's dependency environment (via uv run)
and uploads the manifest to the Geneva connection, then adds columns
to the specified table.

Usage:
    export GENEVA_TABLE_NAME=openvid_shared_abc123
    cd e2e/openvid/udfs/simple
    uv run python upload_manifest.py --bucket gs://bucket/path

Environment Variables:
    GENEVA_TABLE_NAME: Table name to add columns to (required)
    HAS_FILE_COL: Custom column name for has_file (default: "has_file")
"""

import logging
import os

from geneva.manifest.uploader_cli import main_upload_workflow
from manifest import create_manifest
from simple_udfs import HasFile

logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger(__name__)


def get_columns() -> dict[str, callable]:
    """
    Get column definitions for this UDF package.

    Column names can be customized via environment variables:
    - HAS_FILE_COL: Custom name for has_file column (default: "has_file")

    Returns:
        Dictionary mapping column names to UDF functions
    """
    return {
        os.getenv("HAS_FILE_COL", "has_file"): HasFile(),
    }


if __name__ == "__main__":
    main_upload_workflow(
        get_columns_fn=get_columns,
        create_manifest_fn=create_manifest,
        description="Upload simple OpenVid UDFs manifest and add columns to table",
        default_manifest_name="openvid-simple-udfs-v1",
        logger=_LOG,
    )

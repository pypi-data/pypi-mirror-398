#!/usr/bin/env python
# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Upload manifest for frame extractor UDF to Geneva.

This script runs in the UDF's dependency environment (via uv run)
and uploads the manifest to the Geneva connection. It does NOT add
columns to the source table because blob columns break regular queries.

The blob column (first_frame) is added when creating MVs that use this UDF.

Usage:
    cd e2e/openvid/udfs/frame_extractor
    uv run python upload_manifest.py --bucket gs://bucket/path
"""

import argparse
import logging

import geneva
from manifest import create_manifest

logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload frame extractor UDF manifest (manifest only, no columns)"
    )
    parser.add_argument("--bucket", required=True, help="Geneva bucket path")
    parser.add_argument(
        "--manifest-name",
        default="frame-extractor-v1",
        help="Name for the manifest",
    )
    args = parser.parse_args()

    # Create manifest
    _LOG.info("Creating manifest '%s'", args.manifest_name)
    manifest = create_manifest(args.manifest_name)

    _LOG.info("Manifest summary:")
    _LOG.info("  Name: %s", manifest.name)
    _LOG.info("  pip dependencies: %s", manifest.pip)

    # Upload manifest only (no column addition)
    # Blob columns should not be added to the source table as they break
    # regular queries. The blob column is created when making MVs.
    _LOG.info("Connecting to %s", args.bucket)
    conn = geneva.connect(args.bucket)

    _LOG.info("Uploading manifest '%s'", args.manifest_name)
    conn.define_manifest(args.manifest_name, manifest)

    _LOG.info("✓ Successfully uploaded manifest '%s' to %s", args.manifest_name, args.bucket)
    _LOG.info("Note: No columns added to source table (blob columns added via MV creation)")

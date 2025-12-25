#!/usr/bin/env python
# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Upload manifest and add columns for sentence transformer UDF to Geneva.

This script runs in the UDF's dependency environment (via uv run)
and uploads the manifest to the Geneva connection, then adds columns
to the specified table.

Usage:
    export GENEVA_TABLE_NAME=oxford_pets_shared_abc123
    cd e2e/oxford-pets/udfs/sentence-transformers
    uv run python upload_manifest.py --bucket gs://bucket/path

Environment Variables:
    GENEVA_TABLE_NAME: Table name to add columns to (required)
    IMAGE_ID_EMBEDDING_COL: Custom column name for image_id embeddings (default: "image_id_embedding")
"""

import logging
import os

from geneva.manifest.uploader_cli import main_upload_workflow
from manifest import create_manifest

logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger(__name__)

from geneva.udfs.embeddings import sentence_transformer_udf

# Create the UDF that embeds text from image_id field
# Using dimension=384 for lazy loading (all-MiniLM-L6-v2 model)
text_embedding = sentence_transformer_udf(
    model="sentence-transformers/all-MiniLM-L6-v2",
    column="image_id",  # Use image_id as input text
    normalize=True,
    trust_remote_code=True,
    dimension=384,  # Specify dimension to enable lazy loading
)


def get_columns() -> dict[str, callable]:
    """
    Get column definitions for this UDF package.

    Column names can be customized via environment variables:
    - IMAGE_ID_EMBEDDING_COL: Custom name for text embedding column
      (default: "image_id_embedding")

    Returns:
        Dictionary mapping column names to UDF functions
    """
    return {
        os.getenv("IMAGE_ID_EMBEDDING_COL", "image_id_embedding"): text_embedding,
    }


if __name__ == "__main__":
    main_upload_workflow(
        get_columns_fn=get_columns,
        create_manifest_fn=create_manifest,
        description="Upload sentence transformer UDF manifest and add columns to table",
        default_manifest_name="sentence-transformers-udfs-v1",
        logger=_LOG,
    )

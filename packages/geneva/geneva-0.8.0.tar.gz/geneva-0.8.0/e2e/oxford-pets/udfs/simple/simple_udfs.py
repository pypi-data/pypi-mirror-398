# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Simple CPU-only UDFs for image processing.

These UDFs have minimal dependencies and can run on any worker.
"""

import io

import pyarrow as pa

import geneva


@geneva.udf(version="0.1")
def file_size(image: bytes) -> int:
    """Compute the byte size of an image."""
    return len(image)


@geneva.udf(
    version="0.1",
    data_type=pa.struct(
        [pa.field("width", pa.int32()), pa.field("height", pa.int32())]
    ),
)
def dimensions(image: bytes) -> tuple[int, int]:
    """Extract image dimensions (width, height)."""
    from PIL import Image

    image_stream = io.BytesIO(image)
    img = Image.open(image_stream)
    return img.size

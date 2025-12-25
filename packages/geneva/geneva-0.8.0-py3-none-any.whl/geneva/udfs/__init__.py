# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""Collection of built-in User Defined Functions provided by Geneva."""

from geneva.udfs.embeddings import sentence_transformer_udf

__all__ = [
    "sentence_transformer_udf",
]

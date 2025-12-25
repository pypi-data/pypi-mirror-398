# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""Frame extraction UDF for blob column testing in materialized views."""

from .frame_extractor_udf import ExtractFirstFrame

__all__ = ["ExtractFirstFrame"]

# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""Helpers for normalizing batch size parameters.

These helpers intentionally enforce that read- and map-task batch sizes remain
identical today. Callers may pass either the legacy ``batch_size`` parameter or
the new ``checkpoint_size`` alias (which will eventually be used to override
map-task batch size specifically). The helper prefers ``checkpoint_size`` when
both are provided, logs a warning if the two values differ, and warns that
``batch_size`` is deprecated when used without ``checkpoint_size``.
"""

from __future__ import annotations

import logging

_LOG = logging.getLogger(__name__)


def resolve_batch_size(
    *, batch_size: int | None = None, checkpoint_size: int | None = None
) -> int | None:
    """Return the effective batch size, preferring ``checkpoint_size``.

    If both values are provided and differ, ``checkpoint_size`` wins and a warning
    is logged. When only ``batch_size`` is provided, a deprecation warning is emitted.
    """
    if (
        batch_size is not None
        and checkpoint_size is not None
        and batch_size != checkpoint_size
    ):
        _LOG.warning(
            "checkpoint_size (%s) overrides batch_size (%s); values should match,"
            " batch_size is deprecated.",
            checkpoint_size,
            batch_size,
        )
        return checkpoint_size
    elif batch_size is not None and checkpoint_size is None:
        _LOG.warning(
            "batch_size is deprecated; please use checkpoint_size instead (value=%s).",
            batch_size,
        )
        return batch_size

    if checkpoint_size is not None:
        return checkpoint_size
    return batch_size

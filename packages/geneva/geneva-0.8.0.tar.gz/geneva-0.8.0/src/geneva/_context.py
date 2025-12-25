# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

_LOG = logging.getLogger(__name__)

if TYPE_CHECKING:
    # Only for type checkers; no runtime import of raycluster or ray.
    from geneva.runners.ray.raycluster import RayCluster  # pragma: no cover

CURRENT_GENEVA_CONTEXT: Optional[RayCluster] = None


def get_current_context() -> Optional[RayCluster]:
    global CURRENT_GENEVA_CONTEXT
    return CURRENT_GENEVA_CONTEXT


def set_current_context(rc: Optional[RayCluster]) -> None:
    from geneva.runners.ray.raycluster import RayCluster

    global CURRENT_GENEVA_CONTEXT
    if rc is not None and not isinstance(rc, RayCluster):
        raise ValueError("rc must be a RayCluster or None")

    if (
        rc is not None
        and CURRENT_GENEVA_CONTEXT is not None
        and rc != CURRENT_GENEVA_CONTEXT
    ):
        _LOG.warning(
            "Overwriting existing Geneva context %s with new context %s",
            CURRENT_GENEVA_CONTEXT,
            rc,
        )

    CURRENT_GENEVA_CONTEXT = rc

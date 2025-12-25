# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import logging
from typing import Any

import ray
import ray.exceptions
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

_LOG = logging.getLogger(__name__)

# Default timeout for ray.get() calls in integration tests (seconds)
RAY_GET_TIMEOUT = 90
RAY_GET_RETRIES = 4


def ray_get_with_retry(
    obj_ref: ray.ObjectRef,
    timeout: float = RAY_GET_TIMEOUT,
    retries: int = RAY_GET_RETRIES,
) -> Any:
    """Call ray.get() with timeout and retries.

    Args:
        obj_ref: The Ray object reference to get.
        timeout: Timeout in seconds for each attempt.
        retries: Number of retry attempts after the first failure.

    Returns:
        The result of ray.get().

    Raises:
        ray.exceptions.GetTimeoutError: If all attempts timeout.
    """

    @retry(
        retry=retry_if_exception_type(ray.exceptions.GetTimeoutError),
        stop=stop_after_attempt(1 + retries),
        wait=wait_fixed(1),
        before_sleep=before_sleep_log(_LOG, logging.WARNING),
        reraise=True,
    )
    def _get_with_retry() -> Any:
        return ray.get(obj_ref, timeout=timeout)

    return _get_with_retry()

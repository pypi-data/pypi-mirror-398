# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import logging

import pytest

from geneva.table import Table
from geneva.utils.batch_size import resolve_batch_size


def test_resolve_batch_size_prefers_checkpoint_alias(
    caplog: pytest.LogCaptureFixture,
) -> None:
    assert resolve_batch_size(checkpoint_size=5) == 5
    assert resolve_batch_size(batch_size=7, checkpoint_size=7) == 7
    with caplog.at_level(logging.WARNING):
        assert resolve_batch_size(batch_size=4, checkpoint_size=9) == 9
    assert any("overrides batch_size" in rec.message for rec in caplog.records)
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        assert resolve_batch_size(batch_size=6) == 6
    assert any("batch_size is deprecated" in rec.message for rec in caplog.records)
    assert resolve_batch_size() is None


def test_table_normalize_backfill_checkpoint_size() -> None:
    kwargs = {"checkpoint_size": 12}
    Table._normalize_backfill_batch_kwargs(kwargs)
    assert kwargs == {"checkpoint_size": 12}


def test_table_normalize_backfill_conflict_raises(
    caplog: pytest.LogCaptureFixture,
) -> None:
    kwargs = {"batch_size": 8, "checkpoint_size": 4}
    with caplog.at_level(logging.WARNING):
        Table._normalize_backfill_batch_kwargs(kwargs)
    assert any("overrides batch_size" in rec.message for rec in caplog.records)
    assert kwargs == {"checkpoint_size": 4}


def test_table_normalize_backfill_task_size_rejected(
    caplog: pytest.LogCaptureFixture,
) -> None:
    kwargs = {"task_size": 5}
    with caplog.at_level(logging.WARNING):
        Table._normalize_backfill_batch_kwargs(kwargs)
    assert any("task_size is not supported" in rec.message for rec in caplog.records)

# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

from collections.abc import Iterator

import pyarrow as pa

from geneva.apply import CheckpointingApplier, _count_udf_rows
from geneva.apply.task import (
    DEFAULT_CHECKPOINT_ROWS,
    BackfillUDFTask,
    ReadTask,
)
from geneva.transformer import BACKFILL_SELECTED, udf


def test_count_udf_rows_recordbatch_with_and_without_mask() -> None:
    batch_with_mask = pa.record_batch(
        [
            pa.array([1, 2, 3]),
            pa.array([True, False, True]),
        ],
        names=["a", BACKFILL_SELECTED],
    )
    assert _count_udf_rows(batch_with_mask) == 2

    batch_no_mask = pa.record_batch([pa.array([10, 20])], names=["a"])
    assert _count_udf_rows(batch_no_mask) == 2


def test_count_udf_rows_list_of_dicts() -> None:
    rows = [
        {"a": 1, BACKFILL_SELECTED: True},
        {"a": 2, BACKFILL_SELECTED: False},
        {"a": 3},  # defaults to selected
    ]
    assert _count_udf_rows(rows) == 2


class _DummyReadTask(ReadTask):
    def __init__(self, batches: list[pa.RecordBatch]) -> None:
        self._batches = batches

    def to_batches(
        self,
        *,
        batch_size: int = DEFAULT_CHECKPOINT_ROWS,
    ) -> Iterator[pa.RecordBatch]:
        yield from self._batches

    def checkpoint_key(self) -> str:
        return "dummy"

    def dest_frag_id(self) -> int:
        return 0

    def dest_offset(self) -> int:
        return 0

    def num_rows(self) -> int:
        return sum(batch.num_rows for batch in self._batches)

    def table_uri(self) -> str:
        return "memory://dummy"


@udf(data_type=pa.int32())
def _double(a: int) -> int:
    return a * 2


def test_checkpointing_applier_reports_cnt_udf_computed() -> None:
    map_task = BackfillUDFTask(udfs={"b": _double})

    batches = [
        pa.record_batch(
            [
                pa.array([1, 2]),
                pa.array([True, True]),
                pa.array([0, 1], type=pa.uint64()),
            ],
            names=["a", BACKFILL_SELECTED, "_rowaddr"],
        ),
        pa.record_batch(
            [
                pa.array([3, 4]),
                pa.array([True, False]),
                pa.array([2, 3], type=pa.uint64()),
            ],
            names=["a", BACKFILL_SELECTED, "_rowaddr"],
        ),
    ]
    read_task = _DummyReadTask(batches)

    applier = CheckpointingApplier(checkpoint_uri="memory", map_task=map_task)
    checkpoint_key, cnt_udf_computed = applier.run(read_task)

    assert cnt_udf_computed == 3
    stored_batch = applier.checkpoint_store[checkpoint_key]
    assert stored_batch.num_rows == 4

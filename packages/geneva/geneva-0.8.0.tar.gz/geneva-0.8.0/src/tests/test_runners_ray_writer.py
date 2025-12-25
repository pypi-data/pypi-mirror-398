from pathlib import Path

import pyarrow as pa
import pytest
import ray
import ray.util.queue

from geneva.checkpoint import CheckpointStore
from geneva.runners.ray.writer import (
    _align_batches_to_physical_layout,
    _buffer_and_sort_batches,
)

pytestmark = pytest.mark.ray


def test_buffer_sort_and_align_batches_no_alignment_needed(
    tmp_path: Path,
) -> None:
    batch1 = pa.RecordBatch.from_arrays(
        [pa.array(range(16), type=pa.uint64()), pa.array(range(16), type=pa.uint64())],
        names=["data", "_rowaddr"],
    )

    batch2 = pa.RecordBatch.from_arrays(
        [
            pa.array(range(16, 32), type=pa.uint64()),
            pa.array(range(16, 32), type=pa.uint64()),
        ],
        names=["data", "_rowaddr"],
    )

    store = CheckpointStore.from_uri(tmp_path.as_posix())

    store["batch1"] = batch1
    store["batch2"] = batch2

    queue = ray.util.queue.Queue()
    queue.put(
        (
            16,
            "batch2",
        )
    )
    queue.put(
        (
            0,
            "batch1",
        )
    )

    assert list(
        _align_batches_to_physical_layout(
            32,
            32,
            0,
            _buffer_and_sort_batches(
                32,
                store,
                queue,
            ),
        )
    ) == [
        pa.RecordBatch.from_arrays(
            [
                pa.array(range(16), type=pa.uint64()),
                pa.array(range(16), type=pa.uint64()),
            ],
            names=["data", "_rowaddr"],
        ),
        pa.RecordBatch.from_arrays(
            [
                pa.array(range(16, 32), type=pa.uint64()),
                pa.array(range(16, 32), type=pa.uint64()),
            ],
            names=["data", "_rowaddr"],
        ),
    ]


def test_buffer_sort_and_align_batches_alignment_needed(
    tmp_path: Path,
) -> None:
    batch1 = pa.RecordBatch.from_arrays(
        [
            pa.array(range(0, 16, 2), type=pa.uint64()),
            pa.array(range(0, 16, 2), type=pa.uint64()),
        ],
        names=["data", "_rowaddr"],
    )

    batch2 = pa.RecordBatch.from_arrays(
        [
            pa.array(range(16, 32, 2), type=pa.uint64()),
            pa.array(range(16, 32, 2), type=pa.uint64()),
        ],
        names=["data", "_rowaddr"],
    )

    store = CheckpointStore.from_uri(tmp_path.as_posix())

    store["batch1"] = batch1
    store["batch2"] = batch2

    queue = ray.util.queue.Queue()
    queue.put(
        (
            8,
            "batch2",
        )
    )
    queue.put(
        (
            0,
            "batch1",
        )
    )

    batches = list(
        _align_batches_to_physical_layout(
            64,
            16,
            0,
            _buffer_and_sort_batches(
                16,
                store,
                queue,
            ),
        )
    )

    assert pa.Table.from_batches(batches).combine_chunks().to_batches() == [
        pa.RecordBatch.from_arrays(
            [
                pa.array(
                    [i if i % 2 == 0 else None for i in range(32)] + [None] * 32,
                    type=pa.uint64(),
                ),
                pa.array(range(64), type=pa.uint64()),
            ],
            names=["data", "_rowaddr"],
        )
    ]

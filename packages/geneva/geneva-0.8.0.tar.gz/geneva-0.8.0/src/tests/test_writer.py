# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import logging

import pyarrow as pa
import pytest

from geneva.runners.ray.writer import (
    _align_batches_to_physical_layout,
    _fill_rowaddr_gaps,
)

_LOG = logging.getLogger(__name__)


# --- Fixtures and helpers ---
def make_batch(rowaddrs, values) -> pa.RecordBatch:
    schema = pa.schema(
        [
            ("_rowaddr", pa.uint64()),
            ("v", pa.int64()),
        ]
    )
    return pa.RecordBatch.from_arrays(
        [pa.array(rowaddrs, type=pa.uint64()), pa.array(values, type=pa.int64())],
        schema=schema,
    )


# --- Lower-level tests for _align_batch_to_row_address ---
def test_fill_rowaddr_gaps_no_holes() -> None:
    batch = make_batch([0, 1, 2], [1, 2, 3])
    out = _fill_rowaddr_gaps(batch)
    assert out.num_rows == 3
    assert out.column("_rowaddr").to_pylist() == [0, 1, 2]
    assert out.column("v").to_pylist() == [1, 2, 3]


def test_fill_rowaddr_gaps_with_holes() -> None:
    batch = make_batch([1, 3, 4, 7], [10, 30, 40, 70])
    out = _fill_rowaddr_gaps(batch)
    assert out.num_rows == 7
    assert out.column("_rowaddr").to_pylist() == [1, 2, 3, 4, 5, 6, 7]
    assert out.column("v").to_pylist() == [10, None, 30, 40, None, None, 70]


# --- Lower-level tests for _align_batches_to_physical_layout ---


def test_align_no_gaps() -> None:
    # Continuous coverage, no filler needed
    batch = make_batch([0, 1, 2], [1, 2, 3])
    out = list(
        _align_batches_to_physical_layout(
            num_physical_rows=3, num_logical_rows=3, frag_id=0, batches=iter([batch])
        )
    )
    assert len(out) == 1
    assert out[0].column("_rowaddr").to_pylist() == [0, 1, 2]
    assert out[0].column("v").to_pylist() == [1, 2, 3]


def test_align_gap_between() -> None:
    # Two batches with a gap in local row addrs
    batch1 = make_batch([0, 1], [10, 20])
    batch2 = make_batch([3, 4], [30, 40])
    out = list(
        _align_batches_to_physical_layout(
            num_physical_rows=5,
            num_logical_rows=4,
            frag_id=1,
            batches=iter([batch1, batch2]),
        )
    )
    # Expect: batch1, filler for local row 2, then batch2
    assert len(out) == 3

    # strips the fragment id from the _rowaddr
    def local_rowaddr(arr) -> list[int]:
        return [v & 0xFFFFFFFF for v in arr]

    # Filler should appear as second element
    _LOG.info(f"Output batches: {out}")
    filler = out[1]
    _LOG.info(f"Filler: {filler}")
    assert filler.num_rows == 1
    assert local_rowaddr(filler.column("_rowaddr").to_pylist()) == [2]


def test_align_gap_between_and_inside() -> None:
    # Two batches with a gap in local row addrs
    batch1 = make_batch([0, 1], [10, 20])
    batch2 = make_batch([3, 5], [30, 50])  # 4 is missing
    out = list(
        _align_batches_to_physical_layout(
            num_physical_rows=6,
            num_logical_rows=4,
            frag_id=1,
            batches=iter([batch1, batch2]),
        )
    )
    # Expect: batch1, filler for local row 2, then batch2
    assert len(out) == 3

    # strips the fragment id from the _rowaddr
    def local_rowaddr(arr) -> list[int]:
        return [v & 0xFFFFFFFF for v in arr]

    # Filler should appear as second element
    _LOG.info(f"Output batches: {out}")
    filler = out[1]
    _LOG.info(f"Filler: {filler}")
    assert filler.num_rows == 1
    assert local_rowaddr(filler.column("_rowaddr").to_pylist()) == [2]

    fill_gap = out[2]
    assert fill_gap.num_rows == 3
    assert local_rowaddr(fill_gap.column("_rowaddr").to_pylist()) == [3, 4, 5]


def test_align_start_gap() -> None:
    # First batch starts at 2, should get filler for [0,1]
    batch = make_batch([2, 3], [5, 6])
    out = list(
        _align_batches_to_physical_layout(
            num_physical_rows=4, num_logical_rows=2, frag_id=2, batches=iter([batch])
        )
    )
    # First is filler of size 2, then batch
    assert len(out) == 2
    assert out[0].num_rows == 2
    # local rowaddrs of filler
    start_filler = [v & 0xFFFFFFFF for v in out[0].column("_rowaddr").to_pylist()]
    assert start_filler == [0, 1]


def test_align_end_filler() -> None:
    # Batch covers only first row, tail filler for [1,2]
    batch = make_batch([0], [7])
    out = list(
        _align_batches_to_physical_layout(
            num_physical_rows=3, num_logical_rows=1, frag_id=0, batches=iter([batch])
        )
    )
    # Expect batch then filler of 2 rows
    assert len(out) == 2
    assert out[1].num_rows == 2
    local_rows = [v & 0xFFFFFFFF for v in out[1].column("_rowaddr").to_pylist()]
    assert local_rows == [1, 2]


def test_align_empty_raises() -> None:
    # No input batches should error
    with pytest.raises(ValueError, match="No batches found"):
        list(
            _align_batches_to_physical_layout(
                num_physical_rows=3, num_logical_rows=0, frag_id=0, batches=iter([])
            )
        )


def test_align_invalid_counts() -> None:
    # logical > physical rows should error
    batch = make_batch([0, 1, 2], [1, 2, 3])
    with pytest.raises(
        ValueError,
        match="Logical rows should be greater than or equal to physical rows",
    ):
        list(
            _align_batches_to_physical_layout(
                num_physical_rows=2,
                num_logical_rows=3,
                frag_id=0,
                batches=iter([batch]),
            )
        )

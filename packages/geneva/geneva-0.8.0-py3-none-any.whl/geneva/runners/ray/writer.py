# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import logging
import os
import urllib
import urllib.parse
import uuid
from collections.abc import Iterator
from typing import Optional, cast

import attrs
import lance
import lance.file
import pyarrow as pa
import ray
import ray.actor
import ray.util.queue
from yarl import URL

from geneva.checkpoint import CheckpointStore
from geneva.namespace import get_storage_options_provider
from geneva.utils.parse_rust_debug import extract_field_ids
from geneva.utils.sequence_queue import SequenceQueue

_LOG = logging.getLogger(__name__)


def _fill_rowaddr_gaps(batch: pa.RecordBatch) -> pa.RecordBatch:
    """
    This fills the gaps in the _rowaddr column of the batch.
    It assumes that the _rowaddr column is present and sorted.
    It will fill in the gaps with None values for other columns.

    example: start with rowaddr [1, 3], values [10, 30]
    returns rowaddr [1, 2, 3], values [10, None, 30]
    """
    if "_rowaddr" not in batch.schema.names:
        raise ValueError(
            "No _rowaddr column found in the batch,"
            " please make sure the scanner is configured with with_row_address=True"
        )

    rowaddr: pa.Array = batch["_rowaddr"]

    rowaddr_start = rowaddr[0].as_py()
    rowaddr_end = rowaddr[-1].as_py()

    num_physical_rows_in_range = rowaddr_end - rowaddr_start + 1

    if num_physical_rows_in_range == batch.num_rows:
        return batch

    # TODO: this is inefficient in python, do it in rust
    data_dict = {
        "_rowaddr": pa.array(range(rowaddr_start, rowaddr_end + 1), type=pa.uint64()),
    }
    for name in batch.schema.names:
        if name == "_rowaddr":
            continue

        arr = batch[name]

        # Build list with gaps filled as None.
        #
        # IMPORTANT: We use explicit list collection rather than a
        # generator/iterator approach for creating PyArrow arrays. This ensures
        # PyArrow constructs arrays with proper buffer structure for
        # variable-width types (strings, binary, lists).
        #
        # Variable-width types require multiple buffers:
        # - Strings: validity bitmap + offsets buffer + data buffer
        # - Lists: validity bitmap + offsets buffer + child array buffers
        #
        # When creating arrays from iterators, PyArrow may apply optimizations
        # that create malformed arrays incompatible with LanceDB's buffer
        # validation. LanceDB/Rust requires proper buffer structure even for
        # null-heavy arrays.
        #
        # Using explicit list collection ensures consistent, predictable array
        # construction that passes LanceDB validation when written to Lance
        # format.
        result_list = []
        next_idx = rowaddr_start
        for val, row_addr in zip(
            batch[name].to_pylist(), rowaddr.to_pylist(), strict=False
        ):
            while next_idx < row_addr:
                result_list.append(None)
                next_idx += 1
            result_list.append(val)
            next_idx += 1

        # Create array using pa.table() to ensure proper buffer structure
        # for variable-width types (strings, binary, lists).
        # See task.py for similar fix and explanation.
        temp_table = pa.table(
            {"_temp": result_list},
            schema=pa.schema([("_temp", arr.type)]),
        )
        data_dict[name] = temp_table.column("_temp").combine_chunks()  # type: ignore[assignment]

    return batch.from_pydict(data_dict, schema=batch.schema)


def _buffer_and_sort_batches(
    num_logical_rows: int,
    store: CheckpointStore,
    queue: ray.util.queue.Queue,
) -> Iterator[pa.RecordBatch]:
    """
    buffer batches from the queue, which is yields a tuple of
    * serial number of the batch -- currently the offset of the batch
    * the data key dict of the batch

    serial number can arrive out of order, so we need to buffer them
    until we have the next expected serial number. In most cases, the
    serial number is the offset of the batch, and we keep track of the
    expected serial number in the variable `written_rows`
    """
    accumulation_queue = SequenceQueue()
    rows_returned = 0
    while rows_returned < num_logical_rows:
        # Pump the input until we have the next batch
        while (
            accumulation_queue.next_position() < num_logical_rows
            and accumulation_queue.is_empty()
        ):
            try:
                batch: tuple[int, str] = queue.get()
            except (
                ray.exceptions.ActorDiedError,  # type: ignore[attr-defined]
                ray.exceptions.ActorUnavailableError,  # type: ignore[attr-defined]
            ):
                _LOG.exception("Writer failed to read from checkpoint queue, exiting")
                ray.actor.exit_actor()
                return  # Unreachable, but makes pyright happy

            checkpoint_key = batch[1]

            _LOG.info("checkpoints")
            _LOG.info(f"{store=}")

            stored = store[checkpoint_key]
            accumulation_queue.put(batch[0], stored.num_rows, stored)

        # Return the next batch (and any other freed batches)
        while not accumulation_queue.is_empty():
            batch = accumulation_queue.pop()  # type: ignore[assignment]
            if batch is not None:
                yield batch  # type: ignore[misc]
                rows_returned += batch.num_rows  # type: ignore[attr-defined]


def _make_filler_batch(
    fill_start: int,
    fill_end: int,
    schema: pa.Schema,
) -> pa.RecordBatch:
    """
    make a batch that fills the range [fill_start, fill_end) with None values
    for all columns except _rowaddr, which will be filled with the range.
    Note: fill_end is exclusive, so the batch will have (fill_end - fill_start) rows.
    """
    _LOG.info(f"Filling range: {fill_start} -- {fill_end}")
    rowaddr_arr = pa.array(range(fill_start, fill_end), type=pa.uint64())
    # IMPORTANT: Use pa.nulls() instead of pa.array([None] * n, type=...)
    #
    # pa.nulls() creates arrays with proper buffer structure for all types,
    # especially variable-width types (strings, binary, lists) which require:
    # - Validity bitmap (which values are null)
    # - Offsets buffer (for variable-width types)
    # - Data buffer (must be allocated even if all nulls)
    #
    # Using pa.array([None] * n) can create string/binary arrays with missing
    # data buffers (PyArrow optimization), which causes LanceDB/Rust to panic
    # due to buffer count mismatches in variable-width arrays.
    #
    # pa.nulls() guarantees proper buffer allocation that passes LanceDB
    # validation.
    data_dict = {
        name: pa.nulls(fill_end - fill_start, type=schema.field(name).type)
        for name in schema.names
        if name != "_rowaddr"
    }
    data_dict["_rowaddr"] = rowaddr_arr
    return pa.RecordBatch.from_pydict(data_dict, schema=schema)


def _filter_columns_to_schema(
    batches: Iterator[pa.RecordBatch],
    target_column_names: list[str],
) -> Iterator[pa.RecordBatch]:
    """
    Filter batches to only include columns that are in the target schema.

    This is necessary because the input batches may contain columns from the
    source table that are not part of the materialized view's selected columns.
    For example, if the source table has [id, title, width, height] but the
    materialized view only selects [title], the batches from the UDF application
    will still contain all source columns. We must filter to only the target
    columns before writing to Lance.

    IMPORTANT: This must be done AFTER all UDF processing and gap filling, but
    BEFORE writing to Lance, to ensure the written data matches the target schema.

    Parameters
    ----------
    batches : Iterator[pa.RecordBatch]
        Input batches that may contain extra columns
    target_column_names : list[str]
        Names of columns that should be in the output (including _rowaddr)

    Yields
    ------
    pa.RecordBatch
        Batches filtered to only contain target columns, in the order specified
        by target_column_names
    """
    for batch in batches:
        # Filter to only columns in target schema, preserving order
        # Always include _rowaddr if present
        columns_to_keep = [
            col for col in target_column_names if col in batch.schema.names
        ]
        if "_rowaddr" in batch.schema.names and "_rowaddr" not in columns_to_keep:
            columns_to_keep.append("_rowaddr")

        # Select only the columns we want, which creates a new batch
        filtered_batch = batch.select(columns_to_keep)
        yield filtered_batch


def _align_batches_to_physical_layout(
    num_physical_rows: int,
    num_logical_rows: int,
    frag_id: int,
    batches: Iterator[pa.RecordBatch],
) -> Iterator[pa.RecordBatch]:
    """
    This aligns the batches to the physical rows layout.

    It will fill in the _rowaddr gaps within a batch with new rows with the _rowaddr
    index values and None values for the other columns.  It will also fill the _rowaddr
    gaps between batches with the _rowaddr index values and None values for the other
    cols.
    """

    if num_logical_rows > num_physical_rows:
        raise ValueError(
            "Logical rows should be greater than or equal to physical rows"
        )

    next_batch_rowaddr = 0

    schema = None

    for batch in map(
        _fill_rowaddr_gaps,
        batches,
    ):
        # skim the schema from the stream
        # we expect at least one batch, otherwise the whole fragment has been
        # deleted and the metadata would have been deleted by lance so we wouldn't
        # be here because no writer would be created
        if schema is None:
            schema = batch.schema

        incoming_local_rowaddr = batch["_rowaddr"][0].as_py() & 0xFFFFFFFF
        if incoming_local_rowaddr != next_batch_rowaddr:
            # global row id has frag_id in high bits
            fill_start = frag_id << 32 | next_batch_rowaddr
            fill_end = frag_id << 32 | incoming_local_rowaddr
            yield _make_filler_batch(fill_start, fill_end, schema)
            next_batch_rowaddr = incoming_local_rowaddr

        yield batch
        next_batch_rowaddr += batch.num_rows

    if schema is None:
        raise ValueError("No batches found")

    # fill the rest of the rows at the end
    if next_batch_rowaddr < num_physical_rows:
        fill_start = frag_id << 32 | next_batch_rowaddr
        fill_end = frag_id << 32 | num_physical_rows
        yield _make_filler_batch(fill_start, fill_end, schema)


@ray.remote(num_cpus=1)  # type: ignore[misc]
@attrs.define
class FragmentWriter:  # pyright: ignore[reportRedeclaration]
    uri: str
    column_names: list[str]
    checkpoint_uri: str
    fragment_id: int

    checkpoint_keys: ray.util.queue.Queue

    where: str | None = None
    namespace_impl: Optional[str] = None
    namespace_properties: Optional[dict[str, str]] = None
    table_id: Optional[list[str]] = None

    _store: CheckpointStore = attrs.field(init=False)

    def __attrs_post_init__(self) -> None:
        self._store = CheckpointStore.from_uri(self.checkpoint_uri)

    # frag id, new_file, rows_written
    def write(self) -> tuple[int, lance.fragment.DataFile, int]:
        _LOG.debug(
            f"Writing fragment {self.fragment_id} to {self.uri} with columns"
            f" {self.column_names} where '{self.where}'"
        )
        # Open dataset
        dataset = lance.dataset(self.uri)

        frag = dataset.get_fragment(self.fragment_id)
        if frag is None:
            _LOG.warning(f"Fragment {self.fragment_id} not found in dataset {self.uri}")
            raise ValueError(f"Fragment {self.fragment_id} not found")
        num_physical_rows = frag.physical_rows  # num rows before deletions
        num_logical_rows = frag.count_rows()  # num rows including filters/deletions

        import more_itertools

        # we always write files that physically align with the fragment
        it = _buffer_and_sort_batches(
            num_logical_rows,
            self._store,
            self.checkpoint_keys,
        )

        it = _align_batches_to_physical_layout(
            num_physical_rows,
            num_logical_rows,
            self.fragment_id,
            it,
        )

        # Filter batches to only include columns in the target schema.
        # This removes any source table columns that weren't selected in the
        # materialized view (e.g., if source has [id, title, width] but view
        # only selects [title], this removes id and width).
        it = _filter_columns_to_schema(it, self.column_names)

        it = more_itertools.peekable(it)

        file_id = str(uuid.uuid4())
        path = str(URL(self.uri) / "data" / f"{file_id}.lance")
        if not urllib.parse.urlparse(self.uri).scheme:
            path = f"file://{os.path.abspath(path)}"

        written = 0
        schema = it.peek().schema

        # Reconstruct storage_options_provider if we have namespace config
        # and the namespace provides storage_options (e.g., cloud credentials)
        storage_options_provider, storage_options = get_storage_options_provider(
            self.namespace_impl, self.namespace_properties, self.table_id
        )

        with lance.file.LanceFileWriter(
            path,
            schema,
            storage_options=storage_options,
            storage_options_provider=storage_options_provider,
        ) as writer:
            for batch in it:
                writer.write_batch(batch)
                written += batch.num_rows

        field_ids = []
        for column_name in self.column_names:
            field_ids.extend(extract_field_ids(dataset.lance_schema, column_name))

        _LOG.debug(
            f"writing fragment file {file_id}.lance with cols:{self.column_names} "
        )
        new_datafile = lance.fragment.DataFile(
            f"{file_id}.lance",
            field_ids,
            list(range(len(field_ids))),
            2,  # major version
            0,  # minor version
        )

        return self.fragment_id, new_datafile, written


FragmentWriter: ray.actor.ActorClass = cast("ray.actor.ActorClass", FragmentWriter)

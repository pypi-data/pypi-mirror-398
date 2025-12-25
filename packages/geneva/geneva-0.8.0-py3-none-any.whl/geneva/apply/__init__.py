# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import hashlib
import itertools
import logging
import random
from collections.abc import Callable, Iterator, Mapping
from typing import TYPE_CHECKING, Any, Optional, TypeVar

import attrs
import lance
import more_itertools
import pyarrow as pa
import pyarrow.compute as pc
from yarl import URL

from geneva.apply.applier import BatchApplier
from geneva.apply.simple import SimpleApplier
from geneva.apply.task import (
    DEFAULT_CHECKPOINT_ROWS,
    CopyTask,
    MapTask,
    ReadTask,
    ScanTask,
)
from geneva.checkpoint import CheckpointStore
from geneva.debug.logger import ErrorLogger, NoOpErrorLogger
from geneva.table import TableReference
from geneva.transformer import BACKFILL_SELECTED

if TYPE_CHECKING:
    from lance_namespace import LanceNamespace

_LOG = logging.getLogger(__name__)


def _legacy_map_task_key(map_task: MapTask) -> str:
    """Best-effort reconstruction of pre-range map task key."""
    try:
        return map_task.legacy_map_task_key(where=getattr(map_task, "where", None))
    except Exception:
        return "unknown"


def _legacy_fragment_dedupe_key(uri: str, frag_id: int, map_task: MapTask) -> str:
    key = f"{uri}:{frag_id}:{_legacy_map_task_key(map_task)}"
    return hashlib.sha256(key.encode()).hexdigest()


def _count_udf_rows(batch: pa.RecordBatch | list[dict[str, Any]]) -> int:
    """
    Count the number of rows that will execute a UDF within the provided batch.

    The BACKFILL_SELECTED column (when present) identifies the subset of rows
    whose UDF should be evaluated. When the column is absent we assume all rows
    execute the UDF.
    """
    if isinstance(batch, pa.RecordBatch):
        if BACKFILL_SELECTED in batch.schema.names:
            mask = batch[BACKFILL_SELECTED]
            # pyarrow.compute.sum skips nulls by default, treating them as zero.
            summed = pc.sum(mask)
            value = summed.as_py() if hasattr(summed, "as_py") else summed
            return int(value or 0)
        return int(batch.num_rows)

    if not batch:
        return 0

    # this is the blob case where the batch is a list of dicts
    count = 0
    for row in batch:
        if not isinstance(row, dict):
            count += 1
            continue
        selected = row.get(BACKFILL_SELECTED, True)
        if selected:
            count += 1
    return count


def _check_fragment_data_file_exists(
    uri: str,
    frag_id: int,
    map_task: MapTask,
    checkpoint_store: CheckpointStore,
    dataset_version: int | str | None = None,
    namespace: Optional["LanceNamespace"] = None,
    table_id: Optional[list[str]] = None,
    storage_options: Optional[dict[str, str]] = None,
) -> bool:
    """
    Check if a fragment data file already exists in staging or target locations.

    Returns True if the fragment can be skipped because its data file already exists.
    """
    # Import here to avoid circular imports
    from geneva.runners.ray.pipeline import _get_fragment_dedupe_key

    # Get the fragment's checkpoint key
    dedupe_key = _get_fragment_dedupe_key(
        uri, frag_id, map_task, dataset_version=dataset_version
    )
    if dedupe_key not in checkpoint_store and dataset_version is not None:
        # Try versionless (pre-dataset-version) new-format key
        alt_key = _get_fragment_dedupe_key(uri, frag_id, map_task, dataset_version=None)
        if alt_key in checkpoint_store:
            dedupe_key = alt_key
    if dedupe_key not in checkpoint_store:
        # Backward compatibility for pre-change checkpoint keys
        legacy_key = _legacy_fragment_dedupe_key(uri, frag_id, map_task)
        if legacy_key in checkpoint_store:
            dedupe_key = legacy_key
        else:
            return False

    # Check if fragment is already checkpointed
    if dedupe_key not in checkpoint_store:
        return False

    try:
        # Get the stored file path from checkpoint
        checkpointed_data = checkpoint_store[dedupe_key]
        if "file" not in checkpointed_data.schema.names:
            return False

        file_list = checkpointed_data["file"].to_pylist()
        file_path = "".join(str(f) for f in file_list if f is not None)
        if not file_path:
            return False

        # Check staging location first (dataset/data/{file}.lance)
        base_url = URL(uri)
        if base_url.scheme == "":
            base_url = URL(f"file://{uri}")

        # For Lance datasets, the URI ends with .lance, get the parent directory
        if str(base_url).endswith(".lance"):
            base_url = base_url.parent

        staging_url = base_url / "data" / file_path

        try:
            # Check if the staging file exists using lance's file system abstraction
            from pyarrow.fs import FileSystem

            fs, path = FileSystem.from_uri(str(staging_url))
            file_info = fs.get_file_info(path)
            from pyarrow.fs import FileType

            if file_info.type != FileType.NotFound:
                _LOG.info(
                    f"Fragment {frag_id} data file exists in staging: {staging_url}"
                )
                return True
        except Exception as e:
            _LOG.debug(f"Failed to check staging location {staging_url}: {e}")

        # Check target table location as fallback
        # The file might have been moved/committed to the main dataset
        if namespace and table_id:
            dataset = lance.dataset(
                namespace=namespace,
                table_id=table_id,
                storage_options=storage_options,
            )
        else:
            dataset = lance.dataset(uri, storage_options=storage_options)

        try:
            fragment = dataset.get_fragment(frag_id)
            if fragment is not None:
                # Check if any data files in the fragment match our expected file
                for data_file in fragment.data_files():
                    if data_file.path == file_path:
                        _LOG.info(
                            f"Fragment {frag_id} data file exists in target: "
                            f"{data_file.path}"
                        )
                        return True
        except Exception as e:
            _LOG.debug(f"Failed to check target location for fragment {frag_id}: {e}")

    except Exception as e:
        _LOG.debug(f"Failed to check fragment data file for {frag_id}: {e}")

    return False


class _CountingReadTask(ReadTask):
    """Proxy ReadTask that counts rows selected for UDF execution."""

    def __init__(self, inner: ReadTask) -> None:
        self._inner = inner
        self.cnt_udf_computed: int = 0

    def to_batches(
        self,
        *,
        batch_size: int = DEFAULT_CHECKPOINT_ROWS,
    ) -> Iterator[pa.RecordBatch | list[dict]]:
        for batch in self._inner.to_batches(batch_size=batch_size):
            yield batch
            self.cnt_udf_computed += _count_udf_rows(batch)

    def checkpoint_key(self) -> str:
        return self._inner.checkpoint_key()

    def dest_frag_id(self) -> int:
        return self._inner.dest_frag_id()

    def dest_offset(self) -> int:
        return self._inner.dest_offset()

    def num_rows(self) -> int:
        return self._inner.num_rows()

    def table_uri(self) -> str:
        return self._inner.table_uri()

    def __getattr__(self, item: str) -> Any:
        return getattr(self._inner, item)


@attrs.define
class CheckpointingApplier:
    """
    Reads a read task and applies a map task to the data
    using a batch applier.

    The applier will checkpoint the output of the map task so that it can be
    resumed from the same point if the job is interrupted.
    """

    checkpoint_uri: str = attrs.field()
    map_task: MapTask = attrs.field()

    error_logger: ErrorLogger = attrs.field(default=NoOpErrorLogger())
    batch_applier: BatchApplier = attrs.field(
        factory=SimpleApplier,
        converter=attrs.converters.default_if_none(factory=SimpleApplier),
    )

    checkpoint_store: CheckpointStore = attrs.field(init=False)

    def __attrs_post_init__(self) -> None:
        self.checkpoint_store = CheckpointStore.from_uri(self.checkpoint_uri)

    @property
    def output_schema(self) -> pa.Schema:
        return self.map_task.output_schema()

    def _checkpoint_key_for_task(self, task: ReadTask) -> str:
        start = task.dest_offset()
        end = start + task.num_rows()

        try:
            dataset_uri = task.table_uri()
        except Exception:
            dataset_uri = "unknown"

        dataset_version = getattr(task, "version", None)
        where = getattr(task, "where", None)

        return self.map_task.checkpoint_key(
            dataset_uri=dataset_uri or "",
            dataset_version=dataset_version,
            frag_id=task.dest_frag_id(),
            start=start,
            end=end,
            where=where,
        )

    def _run(self, task: ReadTask) -> tuple[str, int]:
        proxy_task = _CountingReadTask(task)
        _LOG.info("Running task %s", task)
        # track the batch sequence number so we can checkpoint any errors
        # when reproducing locally we can seek to the erroring batch quickly

        checkpoint_key = self._checkpoint_key_for_task(task)
        if checkpoint_key in self.checkpoint_store:
            _LOG.info("Using cached result for %s", checkpoint_key)
            return checkpoint_key, 0

        batch = self.batch_applier.run(
            proxy_task,
            self.map_task,
            error_logger=self.error_logger,
        )

        self.checkpoint_store[checkpoint_key] = batch
        _LOG.info(f"checkpointed key={checkpoint_key}")
        return checkpoint_key, proxy_task.cnt_udf_computed

    def run(self, task: ReadTask) -> tuple[str, int]:
        try:
            return self._run(task)
        except Exception as e:
            logging.exception("Error running task %s: %s", task, e)
            raise RuntimeError(f"Error running task {task}") from e

    def status(self, task: ReadTask) -> bool:
        checkpoint_key = self._checkpoint_key_for_task(task)
        return checkpoint_key in self.checkpoint_store


def _plan_read(
    uri: str,
    table_ref: TableReference,
    columns: list[str],
    *,
    read_version: int | None = None,
    batch_size: int = DEFAULT_CHECKPOINT_ROWS,
    where: str | None = None,
    num_frags: int | None = None,
    map_task: MapTask | None = None,
    checkpoint_store: CheckpointStore | None = None,
) -> tuple[Iterator[ReadTask], dict, dict]:
    """Make Plan for Reading Data from a Dataset
    We want a ScanTask for each fragment in the dataset even if they are filtered
    out. This should make the checkpointing recovery easier to manage.

    Returns a tuple of (ReadTask iterator, skipped_fragments dict, skipped_stats dict).
    skipped_stats contains {'fragments': count, 'rows': count} for progress tracking.
    """
    # Open dataset with namespace if available
    if namespace := table_ref.connect_namespace():
        dataset = lance.dataset(namespace=namespace, table_id=table_ref.table_id)
    else:
        dataset = lance.dataset(uri)

    if read_version is not None:
        dataset = dataset.checkout_version(read_version)

    skipped_fragments = {}
    skipped_stats = {"fragments": 0, "rows": 0}
    tasks = []

    # get_fragments has an unsupported filter method, so we do filtering deeper in.
    for idx, frag in enumerate(dataset.get_fragments()):
        _LOG.info(
            f"Processing fragment {idx} (fragment_id={frag.fragment_id}), "
            f"num_frags={num_frags}"
        )
        if num_frags is not None and idx >= num_frags:
            _LOG.info(f"Breaking loop: idx {idx} >= num_frags {num_frags}")
            break

        # Check if fragment data file already exists (fragment-level checkpoint)
        checkpoint_exists = (
            map_task is not None
            and checkpoint_store is not None
            and _check_fragment_data_file_exists(
                uri,
                frag.fragment_id,
                map_task,
                checkpoint_store,
                dataset_version=dataset.version,
                namespace=namespace,
                table_id=table_ref.table_id,
            )
        )
        _LOG.info(
            f"Fragment {idx} (fragment_id={frag.fragment_id}): "
            f"checkpoint_exists={checkpoint_exists}"
        )

        if checkpoint_exists:
            _LOG.info(
                f"Skipping fragment {frag.fragment_id} - data file already exists"
            )

            # Count rows in skipped fragment for progress tracking
            frag_rows = frag.count_rows()
            filtered_frag_rows = frag.count_rows(filter=where)
            skipped_rows = filtered_frag_rows if where else frag_rows

            skipped_stats["fragments"] += 1
            skipped_stats["rows"] += skipped_rows

            # Collect skipped fragment information for commit inclusion
            from geneva.runners.ray.pipeline import _get_fragment_dedupe_key
            from geneva.utils.parse_rust_debug import extract_field_ids

            # These should not be None here due to the checkpoint_exists check above
            assert map_task is not None
            assert checkpoint_store is not None

            dedupe_key = _get_fragment_dedupe_key(
                uri, frag.fragment_id, map_task, dataset_version=dataset.version
            )
            if dedupe_key not in checkpoint_store and dataset.version is not None:
                alt_key = _get_fragment_dedupe_key(
                    uri, frag.fragment_id, map_task, dataset_version=None
                )
                if alt_key in checkpoint_store:
                    dedupe_key = alt_key
            if dedupe_key not in checkpoint_store:
                legacy_key = _legacy_fragment_dedupe_key(
                    uri, frag.fragment_id, map_task
                )
                if legacy_key in checkpoint_store:
                    dedupe_key = legacy_key
            checkpointed_data = checkpoint_store[dedupe_key]
            file_list = checkpointed_data["file"].to_pylist()
            file_path = "".join(str(f) for f in file_list if f is not None)

            # The checkpointed files should only contain the columns being transformed
            # For UDF tasks, determine the field_ids for the output columns
            # Use the same logic as the writer to ensure consistency
            field_ids = []
            if hasattr(map_task, "udfs") and map_task.udfs:  # type: ignore[attr-defined]
                # Use extract_field_ids for consistency with writer.py
                # Pre-check schema to avoid try-except in loop (PERF203)
                schema_fields = {
                    field.name() for field in dataset.lance_schema.fields()
                }

                for column_name in map_task.udfs:  # type: ignore[attr-defined]
                    if column_name not in schema_fields:
                        # Column doesn't exist in current schema, this shouldn't happen
                        # for checkpointed fragments, but if it does, skip this fragment
                        _LOG.warning(
                            f"Column {column_name} not found in schema for "
                            f"checkpointed fragment {frag.fragment_id}, skipping"
                        )
                        continue

                    field_ids.extend(
                        extract_field_ids(dataset.lance_schema, column_name)
                    )
            else:
                # Fallback: use all columns (this shouldn't happen for UDF tasks)
                for column_name in columns:
                    field_ids.extend(
                        extract_field_ids(dataset.lance_schema, column_name)
                    )

            # Create a DataFile object for this existing file
            existing_data_file = lance.fragment.DataFile(
                file_path,
                field_ids,
                list(range(len(field_ids))),
                2,  # major_version
                0,  # minor_version
            )
            skipped_fragments[frag.fragment_id] = existing_data_file
            continue

        frag_rows = frag.count_rows()
        filtered_frag_rows = frag.count_rows(filter=where)
        if filtered_frag_rows == 0:
            _LOG.debug(
                f"frag {frag.fragment_id} filtered by '{where}' has no rows, skipping."
            )
            continue

        _LOG.debug(
            f"plan_read fragment: {frag} has {frag_rows} rows, filtered to"
            f" {filtered_frag_rows} rows"
        )
        for offset in range(0, frag_rows, batch_size if batch_size > 0 else frag_rows):
            limit = min(batch_size, frag_rows - offset)
            _LOG.debug(
                f"scan task: idx={idx} fragid={frag.fragment_id} offset={offset} "
                f"limit={limit} where={where}"
            )

            tasks.append(
                ScanTask(
                    uri=uri,
                    table_ref=table_ref,
                    version=read_version
                    if read_version is not None
                    else dataset.version,
                    columns=columns,
                    frag_id=frag.fragment_id,
                    offset=offset,
                    limit=limit,
                    where=where,
                    with_row_address=True,
                )
            )

    return iter(tasks), skipped_fragments, skipped_stats


T = TypeVar("T")  # Define type variable "T"


@attrs.define
class _LanceReadPlanIterator(Iterator[T]):
    it: Iterator[T]
    total: int

    def __iter__(self) -> Iterator[T]:
        return self

    def __next__(self) -> T:
        return next(self.it)

    def __len__(self) -> int:
        return self.total


def _num_tasks(
    *,
    uri: str,
    read_version: int | None = None,
    batch_size: int = DEFAULT_CHECKPOINT_ROWS,
    namespace_client: Optional["LanceNamespace"] = None,
    table_id: Optional[list[str]] = None,
) -> int:
    if batch_size <= 0:
        return 1

    # Open dataset with namespace if available
    if namespace_client and table_id:
        dataset = lance.dataset(
            namespace=namespace_client,
            table_id=table_id,
            version=read_version,
        )
    else:
        dataset = lance.dataset(uri, version=read_version)

    return sum(-(-frag.count_rows() // batch_size) for frag in dataset.get_fragments())


T = TypeVar("T")


def _buffered_shuffle(it: Iterator[T], buffer_size: int) -> Iterator[T]:
    """Shuffle an iterator using a buffer of size buffer_size
    not perfectly random, but good enough for spreading out IO
    """
    # Initialize the buffer with the first buffer_size items from the iterator
    buffer = []
    # Fill the buffer with up to buffer_size items initially
    try:
        for _ in range(buffer_size):
            item = next(it)
            buffer.append(item)
    except StopIteration:
        pass

    while True:
        # Select a random item from the buffer
        index = random.randint(0, len(buffer) - 1)
        item = buffer[index]

        # Try to replace the selected item with a new one from the iterator
        try:
            next_item = next(it)
            buffer[index] = next_item
            # Yield the item AFTER replacing it in the buffer
            # this way the buffer is always contiguous so we can
            # simply yield the buffer at the end
            yield item
        except StopIteration:
            yield from buffer
            break


R = TypeVar("R")


def diversity_aware_shuffle(
    it: Iterator[T],
    key: Callable[[T], R],
    *,
    diversity_goal: int = 4,
    buffer_size: int = 1024,
) -> Iterator[T]:
    """A shuffle iterator that is aware of the diversity of the data
    being shuffled. The key function should return a value that is
    is used to determine the diversity of the data. The diversity_goal
    is the number of unique values that should be in the buffer at any
    given time. if the buffer is full, the items is yielded in a round-robin
    fashion. This is useful for shuffling tasks that are diverse, but

    This algorithm is bounded in memory by the buffer_size, so it is reasonably
    efficient for large datasets.
    """

    # NOTE: this is similar to itertools.groupby, but with a buffering limit

    buffer: dict[R, list[T]] = {}
    buffer_total_size = 0

    peekable_it = more_itertools.peekable(it)

    def _maybe_consume_from_iter() -> bool:
        nonlocal buffer_total_size
        item = peekable_it.peek(default=None)
        if item is None:
            return False
        key_val = key(item)
        if key_val not in buffer and len(buffer) < diversity_goal:
            buffer[key_val] = []
        else:
            return False

        # if the buffer still has room, add the item
        if buffer_total_size < buffer_size:
            buffer[key_val].append(item)
            buffer_total_size += 1
        else:
            return False

        next(peekable_it)
        return True

    while _maybe_consume_from_iter():
        ...

    production_counter = 0

    def _next_key() -> T | None:
        nonlocal buffer_total_size, production_counter
        if not buffer_total_size:
            return None

        # TODO: add warning about buffer size not big enough for diversity_goal
        buffer_slot = production_counter % len(buffer)
        key = next(itertools.islice(buffer.keys(), buffer_slot, buffer_slot + 1))
        assert key in buffer
        key_buffer = buffer[key]

        buffer_total_size -= 1
        item = key_buffer.pop(0)
        if not key_buffer:
            del buffer[key]

        # try to fill the removed buffer slot
        _maybe_consume_from_iter()
        production_counter += 1
        return item

    while (item := _next_key()) is not None:
        yield item


def plan_read(
    uri: str,
    table_ref: TableReference,
    columns: list[str],
    *,
    read_version: int | None = None,
    batch_size: int = DEFAULT_CHECKPOINT_ROWS,
    where: str | None = None,
    shuffle_buffer_size: int = 0,
    task_shuffle_diversity: int | None = None,
    num_frags: int | None = None,
    map_task: MapTask | None = None,
    checkpoint_store: CheckpointStore | None = None,
    **unused_kwargs,
) -> tuple[Iterator[ReadTask], Mapping]:
    """
    Make Plan for Reading Data from a Dataset

    Parameters
    ----------
    num_frags:
        max number of fragments to scan for sampling use cases.
    """
    it, skipped_fragments, skipped_stats = _plan_read(
        uri,
        table_ref,
        columns=columns,
        read_version=read_version,
        batch_size=batch_size,
        where=where,
        num_frags=num_frags,
        map_task=map_task,
        checkpoint_store=checkpoint_store,
    )
    # same as no shuffle
    if shuffle_buffer_size > 1 and task_shuffle_diversity is None:
        it = _buffered_shuffle(it, buffer_size=shuffle_buffer_size)
    elif task_shuffle_diversity is not None:
        buffer_size = max(4 * task_shuffle_diversity, shuffle_buffer_size)
        it = diversity_aware_shuffle(
            it,
            key=lambda task: task.checkpoint_key(),
            diversity_goal=task_shuffle_diversity,
            buffer_size=buffer_size,
        )

    unused_kwargs["skipped_fragments"] = skipped_fragments
    unused_kwargs["skipped_stats"] = skipped_stats

    # Get namespace from table_ref for _num_tasks
    namespace_client = table_ref.connect_namespace()

    return _LanceReadPlanIterator(
        it,
        _num_tasks(
            uri=uri,
            read_version=read_version,
            batch_size=batch_size,
            namespace_client=namespace_client,
            table_id=table_ref.table_id,
        ),
    ), unused_kwargs


def _plan_copy(
    src: TableReference,
    dst: TableReference,
    columns: list[str],
    *,
    batch_size: int = DEFAULT_CHECKPOINT_ROWS,
    only_fragment_ids: set[int] | None = None,
) -> tuple[Iterator[CopyTask], int]:
    """Make Plan for Reading Data from a Dataset

    For materialized views, this iterates over DESTINATION fragments and creates
    CopyTasks for all of them. This destination-driven approach correctly handles
    cases where source fragments are consolidated into fewer destination fragments
    (e.g., due to filters or shuffle operations).

    Args:
        only_fragment_ids: If provided, only create tasks for the specified
            destination fragment IDs. Used for incremental refresh to process
            only specific fragments.
    """
    # Read from DESTINATION dataset (destination-driven approach for materialized views)
    dst_dataset = dst.open().to_lance()

    num_tasks = 0
    for frag in dst_dataset.get_fragments():
        # Skip fragments that don't match the filter
        if only_fragment_ids is not None and frag.fragment_id not in only_fragment_ids:
            continue
        frag_rows = frag.count_rows()
        # ceil_div
        num_tasks += -(frag_rows // -batch_size)

    def task_gen() -> Iterator[CopyTask]:
        for frag in dst_dataset.get_fragments():
            # Skip fragments that don't match the filter
            if (
                only_fragment_ids is not None
                and frag.fragment_id not in only_fragment_ids
            ):
                continue
            frag_rows = frag.count_rows()
            for offset in range(0, frag_rows, batch_size):
                limit = min(batch_size, frag_rows - offset)
                yield CopyTask(
                    src=src,
                    dst=dst,
                    columns=columns,
                    frag_id=frag.fragment_id,
                    offset=offset,
                    limit=limit,
                )

    return (task_gen(), num_tasks)


def plan_copy(
    src: TableReference,
    dst: TableReference,
    columns: list[str],
    *,
    batch_size: int = DEFAULT_CHECKPOINT_ROWS,
    shuffle_buffer_size: int = 0,
    task_shuffle_diversity: int | None = None,
    only_fragment_ids: set[int] | None = None,
    **unused_kwargs,
) -> Iterator[CopyTask]:
    (it, num_tasks) = _plan_copy(
        src,
        dst,
        columns,
        batch_size=batch_size,
        only_fragment_ids=only_fragment_ids,
    )
    # same as no shuffle
    if shuffle_buffer_size > 1 and task_shuffle_diversity is None:
        it = _buffered_shuffle(it, buffer_size=shuffle_buffer_size)
    elif task_shuffle_diversity is not None:
        buffer_size = max(4 * task_shuffle_diversity, shuffle_buffer_size)
        it = diversity_aware_shuffle(
            it,
            key=lambda task: task.checkpoint_key(),
            diversity_goal=task_shuffle_diversity,
            buffer_size=buffer_size,
        )

    return _LanceReadPlanIterator(it, num_tasks)

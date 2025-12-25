# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import contextlib
import copy
import functools
import json
import logging
import random
import time
import uuid
from collections import Counter
from collections.abc import Generator, Iterator
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, cast

import attrs
import cloudpickle
import lance
import pyarrow as pa
import ray.actor
import ray.exceptions
import ray.util.queue
from pyarrow.fs import FileSystem
from ray.actor import ActorHandle
from tqdm.std import tqdm as TqdmType  # noqa: N812

from geneva.apply import (
    CheckpointingApplier,
    plan_copy,
    plan_read,
)
from geneva.apply.applier import BatchApplier
from geneva.apply.multiprocess import MultiProcessBatchApplier
from geneva.apply.simple import SimpleApplier
from geneva.apply.task import BackfillUDFTask, CopyTableTask, MapTask, ReadTask
from geneva.checkpoint import CheckpointStore
from geneva.db import Connection
from geneva.debug.error_store import GENEVA_ERRORS_TABLE_NAME, ErrorStore
from geneva.debug.logger import TableErrorLogger
from geneva.jobs.config import JobConfig
from geneva.namespace import get_storage_options_provider
from geneva.packager import UDFPackager, UDFSpec
from geneva.query import (
    MATVIEW_META_BASE_DBURI,
    MATVIEW_META_BASE_TABLE,
    MATVIEW_META_QUERY,
    MATVIEW_META_VERSION,
    GenevaQuery,
    GenevaQueryBuilder,
)

if TYPE_CHECKING:
    from lance_namespace import LanceNamespace

# Namespace imports for storage_options_provider

from geneva.runners.ray.actor_pool import ActorPool
from geneva.runners.ray.jobtracker import JobTracker
from geneva.runners.ray.kuberay import _ray_status
from geneva.runners.ray.raycluster import (
    ray_tqdm,
)
from geneva.runners.ray.writer import FragmentWriter
from geneva.table import JobFuture, Table, TableReference
from geneva.tqdm import (
    Colors,
    fmt,
    fmt_numeric,
    fmt_pending,
    tqdm,
)
from geneva.transformer import UDF
from geneva.utils.batch_size import resolve_batch_size
from geneva.utils.parse_rust_debug import extract_field_ids
from geneva.utils.ray import CPU_ONLY_NODE

_LOG = logging.getLogger(__name__)


REFRESH_EVERY_SECONDS = 5.0

CNT_WORKERS_PENDING = "cnt_geneva_workers_pending"
CNT_WORKERS_ACTIVE = "cnt_geneva_workers_active"
CNT_RAY_NODES = "cnt_ray_nodes"
CNT_K8S_NODES = "k8s_nodes_provisioned"
CNT_K8S_PHASE = "k8s_cluster_phase"
METRIC_UDF_VALUES = "udf_values_computed"


@ray.remote  # type: ignore[misc]
@attrs.define
class ApplierActor:  # pyright: ignore[reportRedeclaration]
    applier: CheckpointingApplier

    def __ray_ready__(self) -> None:
        pass

    def __repr__(self) -> str:
        """Custom repr that safely handles missing attributes during unpickling.

        This is necessary because attrs-generated __repr__ can fail when called
        during exception handling in Ray if the object hasn't been fully unpickled yet.
        """
        try:
            # Try to get all attrs fields safely
            field_strs = []
            for field in attrs.fields(self.__class__):
                # Check if attribute exists first before accessing it
                if hasattr(self, field.name):
                    value = getattr(self, field.name)
                    field_strs.append(f"{field.name}={value!r}")
                else:
                    field_strs.append(f"{field.name}=<not set>")

            return f"{self.__class__.__qualname__}({', '.join(field_strs)})"
        except Exception:
            # Fallback if even that fails
            return f"<{self.__class__.__name__} (repr failed)>"

    def run(self, task) -> tuple[ReadTask, str, int]:
        checkpoint_key, cnt_udf_computed = self.applier.run(task)
        return task, checkpoint_key, cnt_udf_computed


ApplierActor: ray.actor.ActorClass = cast("ray.actor.ActorClass", ApplierActor)  # type: ignore[no-redef]


def _get_fragment_dedupe_key(
    uri: str,
    frag_id: int,
    map_task: MapTask,
    dataset_version: int | str | None = None,
) -> str:
    prefix = map_task.checkpoint_prefix(
        dataset_uri=uri,
        dataset_version=None,
        where=getattr(map_task, "where", None),
        column=None,
    )
    return f"{prefix}_frag-{frag_id}"


def get_source_data_files(
    src_frag,
    relevant_field_ids: frozenset[int] | None = None,
) -> frozenset[str]:
    """Get set of data file paths in this fragment for relevant fields.

    This is used to detect when source data has been modified via backfill.
    When a backfill runs (even on the same field), new data files are created
    with new UUIDs. Tracking file paths detects ALL data changes, including:
    - New fields being backfilled
    - Existing fields being re-backfilled with different UDF

    Args:
        src_frag: A Lance fragment object
        relevant_field_ids: If provided, only include files containing these
            field IDs. If None, include all files (backward compatible).

    Returns:
        frozenset of data file paths in this fragment
    """
    if relevant_field_ids is None:
        return frozenset(df.path for df in src_frag.data_files())

    # Filter to files containing at least one relevant field
    return frozenset(
        df.path for df in src_frag.data_files() if set(df.fields) & relevant_field_ids
    )


def get_combined_source_data_files(
    src_dataset: lance.LanceDataset,
    src_frag_ids: set[int],
    relevant_field_ids: frozenset[int] | None = None,
) -> frozenset[str]:
    """Get union of data file paths across multiple source fragments.

    Why union? We want to detect if ANY data file changes in ANY source fragment
    that contributes to a destination fragment. When any backfill runs on any
    source fragment, new data files are created, and the union changes.

    This is more robust than field coverage tracking because it detects:
    - New fields being backfilled (new files for new field IDs)
    - Existing fields being re-backfilled (new files replace old files)

    Note: Compaction is handled separately via stable_row_id mapping.

    Args:
        src_dataset: The source Lance dataset
        src_frag_ids: Set of source fragment IDs that contribute to a destination
        relevant_field_ids: If provided, only include files containing these
            field IDs. If None, include all files.

    Returns:
        frozenset of all data file paths from all source fragments (union)
    """
    all_files: set[str] = set()
    for frag_id in src_frag_ids:
        frag = src_dataset.get_fragment(frag_id)
        if frag is not None:
            all_files.update(get_source_data_files(frag, relevant_field_ids))
    return frozenset(all_files)


def _get_relevant_field_ids(
    src_dataset: lance.LanceDataset,
    input_cols: list[str],
) -> frozenset[int]:
    """Get field IDs for columns the MV reads from the source.

    This is used to filter data file tracking to only files containing
    columns that the MV actually uses. If a new column is added to the
    source that isn't in the MV, changes to that column won't trigger
    MV refresh.

    Args:
        src_dataset: The source Lance dataset
        input_cols: List of column names the MV reads

    Returns:
        frozenset of field IDs for the relevant columns
    """
    from geneva.utils.parse_rust_debug import extract_field_ids

    field_ids: set[int] = set()
    for col_name in input_cols:
        try:
            ids = extract_field_ids(src_dataset.lance_schema, col_name)
            field_ids.update(ids)
        except Exception:  # noqa: PERF203
            # Column may not exist in source (e.g., computed column)
            _LOG.debug(f"Column {col_name} not found in source schema, skipping")
    return frozenset(field_ids)


def _run_column_adding_pipeline(
    map_task: MapTask,
    checkpoint_store: CheckpointStore,
    error_store: ErrorStore,
    config: JobConfig,
    dst: TableReference,
    input_plan: Iterator[ReadTask],
    job_id: str | None,
    applier_concurrency: int = 8,
    *,
    intra_applier_concurrency: int = 1,
    use_cpu_only_pool: bool = False,
    job_tracker=None,
    where=None,
    skipped_fragments: dict | None = None,
    skipped_stats: dict | None = None,
    enable_job_tracker_saves: bool = True,
    src_data_files_by_dst: dict[int, frozenset[str]] | None = None,
) -> None:
    """
    Run the column adding pipeline.

    Args:
    * use_cpu_only_pool: If True will force schedule cpu-only actors on cpu-only nodes.

    """
    job_id = job_id or uuid.uuid4().hex

    job_tracker = job_tracker or JobTracker.options(
        name=f"jobtracker-{job_id}",
        num_cpus=0.1,
        memory=128 * 1024 * 1024,
        max_restarts=-1,
    ).remote(job_id, dst, enable_saves=enable_job_tracker_saves)  # type: ignore[call-arg]

    job = ColumnAddPipelineJob(
        map_task=map_task,
        checkpoint_store=checkpoint_store,
        error_store=error_store,
        config=config,
        dst=dst,
        input_plan=input_plan,
        job_id=job_id,
        applier_concurrency=applier_concurrency,
        intra_applier_concurrency=intra_applier_concurrency,
        use_cpu_only_pool=use_cpu_only_pool,
        job_tracker=job_tracker,  # type: ignore[arg-type]
        where=where,
        skipped_fragments=skipped_fragments or {},
        skipped_stats=skipped_stats or {},
        src_data_files_by_dst=src_data_files_by_dst or {},
    )
    job.run()


@attrs.define
class ColumnAddPipelineJob:
    """ColumnAddPipeline drives batches of rows to commits in the dataset.

    ReadTasks are defined wrapped for tracking, and then dispatched for udf exeuction
    in the ActorPool.  The results are sent to the FragmentWriterManager which
    manages fragment checkpoints and incremental commits.
    """

    map_task: MapTask
    checkpoint_store: CheckpointStore
    error_store: ErrorStore
    config: JobConfig
    dst: TableReference
    input_plan: Iterator[ReadTask]
    job_id: str
    applier_concurrency: int = 8
    intra_applier_concurrency: int = 1
    use_cpu_only_pool: bool = False
    job_tracker: ActorHandle | None = None
    where: str | None = None
    skipped_fragments: dict = attrs.field(factory=dict)
    skipped_stats: dict = attrs.field(factory=dict)
    src_data_files_by_dst: dict[int, frozenset[str]] = attrs.field(factory=dict)
    _total_rows: int = attrs.field(default=0, init=False)
    _last_status_refresh: float = attrs.field(factory=lambda: 0.0, init=False)

    def setup_inputplans(self) -> tuple[Iterator[ReadTask], Counter[int], int]:
        all_tasks = list(self.input_plan)
        self.job_tracker = (
            self.job_tracker
            or JobTracker.options(  # type: ignore[assignment]
                name=f"jobtracker-{self.job_id}",
                num_cpus=0.1,
                memory=128 * 1024 * 1024,
                max_restarts=-1,
            ).remote(self.job_id, self.dst)  # type: ignore[call-arg]
        )

        self._total_rows = sum(t.num_rows() for t in all_tasks)
        plan_len = len(all_tasks)

        # fragments
        if self.job_tracker is not None:
            self.job_tracker.set_total.remote("fragments", plan_len)
            self.job_tracker.set_desc.remote(
                "fragments",
                f"[{self.dst.table_name} - {self.map_task.name()}] Batches scheduled",
            )

        # this reports # of batches started, not completed.
        tasks_by_frag = Counter(t.dest_frag_id() for t in all_tasks)
        return (
            ray_tqdm(all_tasks, self.job_tracker, metric="fragments"),
            tasks_by_frag,
            plan_len,
        )

    def setup_actor(self) -> ray.actor.ActorHandle:
        actor = ApplierActor

        # actor.options can only be called once, we must pass all override args
        # in one shot
        num_cpus = self.map_task.num_cpus()
        args = {
            "num_cpus": (num_cpus or 1) * self.intra_applier_concurrency,
        }
        num_gpus = self.map_task.num_gpus()
        if num_gpus and num_gpus > 0:
            args["num_gpus"] = num_gpus
        elif self.use_cpu_only_pool:
            _LOG.info("Using CPU only pool for applier, setting %s to 1", CPU_ONLY_NODE)
            args["resources"] = {CPU_ONLY_NODE: 1}  # type: ignore[assignment]
        memory = self.map_task.memory()
        if memory:
            args["memory"] = memory * self.intra_applier_concurrency
        actor = actor.options(**args)  # type: ignore[attr-defined]
        return actor  # type: ignore[return-value]

    def setup_batchapplier(self) -> BatchApplier:
        if self.intra_applier_concurrency > 1:
            return MultiProcessBatchApplier(
                num_processes=self.intra_applier_concurrency, job_id=self.job_id
            )
        else:
            return SimpleApplier(job_id=self.job_id)

    def setup_actorpool(self) -> ActorPool:
        batch_applier = self.setup_batchapplier()

        errors_tbl = copy.deepcopy(self.dst)
        errors_tbl.table_id = [GENEVA_ERRORS_TABLE_NAME]

        applier = CheckpointingApplier(
            map_task=self.map_task,
            batch_applier=batch_applier,
            checkpoint_uri=self.checkpoint_store.uri(),
            error_logger=TableErrorLogger(table_ref=errors_tbl),
        )

        actor = self.setup_actor()
        if self.job_tracker is not None:
            self.job_tracker.set_total.remote("workers", self.applier_concurrency)
            self.job_tracker.set_desc.remote("workers", "Workers started")

        pool = ActorPool(
            functools.partial(actor.remote, applier=applier),
            self.applier_concurrency,
            job_tracker=self.job_tracker,
            worker_metric="workers",
        )
        return pool

    def setup_writertracker(self) -> tuple[lance.LanceDataset, int]:
        ds = self.dst.open().to_lance()
        fragments = ds.get_fragments()
        len_frags = len(fragments)

        if self.job_tracker is not None:
            self.job_tracker.set_total.remote("writer_fragments", len_frags)
            self.job_tracker.set_desc.remote("writer_fragments", "Fragments written")
        ray_tqdm(fragments, self.job_tracker, metric="writer_fragments")

        return ds, len_frags

    def _refresh_cluster_status(self) -> None:
        # cluster metrics
        try:
            ray_status = _ray_status()

            # TODO batch this.
            if self.job_tracker is not None:
                m_rn = CNT_RAY_NODES
                cnt_workers = ray_status.get(m_rn, 0)
                self.job_tracker.set_desc.remote(m_rn, "ray nodes provisioned")
                self.job_tracker.set.remote(m_rn, cnt_workers)

                # TODO separate metrics for gpu and cpu workers?
                m_caa = CNT_WORKERS_ACTIVE
                cnt_active = ray_status.get(m_caa, 0)
                self.job_tracker.set_desc.remote(m_caa, "active workers")
                self.job_tracker.set_total.remote(m_caa, self.applier_concurrency)
                self.job_tracker.set.remote(m_caa, cnt_active)

                m_cpa = CNT_WORKERS_PENDING
                cnt_pending = ray_status.get(m_cpa, 0)
                self.job_tracker.set_desc.remote(m_cpa, "pending workers")
                self.job_tracker.set_total.remote(m_cpa, self.applier_concurrency)
                self.job_tracker.set.remote(m_cpa, cnt_pending)

        except Exception:
            _LOG.debug("refresh: failed to get ray status", exc_info=True)
            # do nothing

    def _try_refresh_cluster_status(self) -> None:
        now = time.monotonic()
        if now - self._last_status_refresh >= REFRESH_EVERY_SECONDS:
            self._refresh_cluster_status()
            self._last_status_refresh = now

    def run(self) -> None:
        plans, tasks_by_frag, cnt_batches = self.setup_inputplans()
        pool = self.setup_actorpool()
        ds, cnt_fragments = self.setup_writertracker()

        prefix = (
            f"[{self.dst.table_name} - {self.map_task.name()} "
            f"({cnt_fragments} fragments)]"
        )

        try:
            self._refresh_cluster_status()
        except Exception:
            _LOG.debug("initial cluster status refresh failed", exc_info=True)
            # do nothing

        # formatting to show fragments
        try:
            cg = (
                int(self.config.commit_granularity)
                if self.config.commit_granularity is not None
                else 0
            )
        except Exception:
            cg = 0
        cg = max(cg, 0)
        cgstr = (
            "(commit at completion)"
            if cg == 0
            else f"(every {cg} fragment{'s' if cg != 1 else ''})"
        )
        # rows metrics (all cumulative)
        if self.job_tracker is not None:
            # Get the full dataset total (including skipped fragments)
            dataset_total_rows = self._total_rows
            # skipped_stats is {'fragments': count, 'rows': count} for
            # progress tracking.
            if self.skipped_stats:
                dataset_total_rows += self.skipped_stats.get("rows", 0)

            skipped_rows = self.skipped_stats.get("rows", 0)

            previously_completed = (
                f" ({skipped_rows} previously completed)" if skipped_rows > 0 else ""
            )
            for m, desc in [
                (
                    "rows_checkpointed",
                    f"{prefix} Rows checkpointed{previously_completed}",
                ),
                (
                    "rows_ready_for_commit",
                    f"{prefix} Rows ready for commit",
                ),
                (
                    "rows_committed",
                    f"{prefix} Rows committed {cgstr}",
                ),
            ]:
                self.job_tracker.set_total.remote(m, dataset_total_rows)
                self.job_tracker.set_desc.remote(m, desc)
                # Initialize with skipped rows as already completed
                if skipped_rows > 0:
                    self.job_tracker.set.remote(m, skipped_rows)
            # Track the number of rows processed by UDF excluding skipped rows.
            self.job_tracker.set_desc.remote(
                METRIC_UDF_VALUES,
                f"{prefix} Rows processed by UDF",
            )

        _LOG.info(
            f"Pipeline executing on {cnt_batches} batches over "
            f"{cnt_fragments} table fragments"
        )

        # kick off the applier actors
        applier_iter = pool.map_unordered(
            lambda actor, value: actor.run.remote(value),
            # the API says list, but iterables are fine
            plans,
        )

        fwm = FragmentWriterManager(
            ds.version,
            ds_uri=ds.uri,
            map_task=self.map_task,
            checkpoint_store=self.checkpoint_store,
            where=self.where,
            job_tracker=self.job_tracker,
            commit_granularity=self.config.commit_granularity,
            expected_tasks=dict(tasks_by_frag),
            skipped_fragments=self.skipped_fragments or {},
            namespace_impl=self.dst.namespace_impl,
            namespace_properties=self.dst.namespace_properties,
            table_id=self.dst.table_id,
            storage_options=None,
            src_data_files_by_dst=self.src_data_files_by_dst,
        )

        for task, checkpoint_key, cnt_udf_computed in applier_iter:
            fwm.ingest(checkpoint_key, task, cnt_udf_computed)
            # ensure we discover any frgments that finished writing even if the
            # current task belongs to another fragment.
            fwm.poll_all()
            self._try_refresh_cluster_status()

        pool.shutdown()
        fwm.cleanup()
        # Ensure final metrics reflect all processed rows even if some tracker
        # updates were dropped or delayed.
        fwm.finalize_metrics()
        with contextlib.suppress(Exception):
            self._refresh_cluster_status()


@attrs.define
class FragmentWriterSession:
    """This tracks all the batch tasks for a single fragment.

    It is responsible for managing the fragment writer's life cycle and does the
    bookkeeping of inflight tasks, completed tasks, and the queue of tasks to write.
    These are locally tracked and accounted for before the fragment is considered
    complete and ready to be commited to the dataset.

    It expects to be initialized and then fed with `ingest_task` calls. After all tasks
    have been added, it is `seal`ed meaning no more input tasks are expected.  Then it
    can be `drain`ed to yield all completed tasks.
    """

    frag_id: int
    ds_uri: str
    output_columns: list[str]
    checkpoint_store: CheckpointStore
    where: str | None
    namespace_impl: Optional[str] = None
    namespace_properties: Optional[dict[str, str]] = None
    table_id: Optional[list[str]] = None

    # runtime state.  This is single-threaded and is not thread-safe.
    queue: ray.util.queue.Queue = attrs.field(factory=ray.util.queue.Queue, init=False)
    actor: ActorHandle = attrs.field(init=False)
    cached_tasks: list[tuple[int, Any]] = attrs.field(factory=list, init=False)
    inflight: dict[ray.ObjectRef, int] = attrs.field(factory=dict, init=False)
    _shutdown: bool = attrs.field(default=False, init=False)

    sealed: bool = attrs.field(default=False, init=False)  # no more tasks will be added
    enqueued: int = attrs.field(default=0, init=False)  # total expected tasks
    completed: int = attrs.field(default=0, init=False)  # total compelted tasks

    def __attrs_post_init__(self) -> None:
        self._start_writer()

    def _start_writer(self) -> None:
        self.actor = FragmentWriter.options(  # type: ignore[assignment]
            num_cpus=0.1,  # make it cheap to schedule (not require full cpu)
            memory=1024 * 1024 * 1024,  # 1gb ram
        ).remote(
            self.ds_uri,
            self.output_columns,
            self.checkpoint_store.uri(),
            self.frag_id,
            self.queue,
            where=self.where,
            namespace_impl=self.namespace_impl,
            namespace_properties=self.namespace_properties,
            table_id=self.table_id,
        )
        # prime one future so we can detect when it finishes
        fut = self.actor.write.remote()  # type: ignore[call-arg]
        self.inflight[fut] = self.frag_id  # type: ignore[assignment]

    def shutdown(self) -> None:
        len_inflight = len(self.inflight)
        if len_inflight > 0:
            try:
                is_empty = self.queue.empty()
            except (ray.exceptions.RayError, Exception):
                # queue actor died or unavailble.  assume empty
                is_empty = True
                # queue should be empty and inflight should be 0.
                _LOG.warning(
                    "Shutting down frag %s - queue empty %s, inflight: %d",
                    self.frag_id,
                    is_empty,
                    len_inflight,
                )

        if self._shutdown:
            return  # idempotent
        self.queue.shutdown()
        ray.kill(self.actor)
        self._shutdown = True

    def _restart(self) -> None:
        self.shutdown()

        # make it cheap to schedule (not require full cpu, reserve 256MiB ram)
        self.queue = ray.util.queue.Queue(
            actor_options={"num_cpus": 0.1, "memory": 256 * 1024 * 1024}
        )
        self.inflight.clear()
        self.cached_tasks, old_tasks = [], self.cached_tasks
        self.__attrs_post_init__()  # recreates writer & first future

        # replay tasks
        for off, res in old_tasks:
            self.queue.put((off, res))

    def ingest_task(self, offset: int, result: Any) -> None:
        """Called by manager when a new (offset, result) arrives."""
        self.cached_tasks.append((offset, result))
        self.enqueued += 1
        try:
            self.queue.put((offset, result))
        except (ray.exceptions.ActorDiedError, ray.exceptions.ActorUnavailableError):
            _LOG.warning("Writer actor for frag %s died – restarting", self.frag_id)
            self._restart()

    def poll_ready(self) -> list[tuple[int, Any, int]]:
        """Non‑blocking check for any finished futures.
        Returns list of (frag_id, new_file, rows_written) that completed."""
        ready, _ = ray.wait(list(self.inflight.keys()), timeout=0.0)
        completed: list[tuple[int, Any, int]] = []

        for fut in ready:
            try:
                res = ray.get(fut)
                assert isinstance(res, tuple) and len(res) == 3, (  # noqa: PT018
                    "FragmentWriter.write() should return (frag_id, new_file,"
                    " rows_written), "
                )
                fid, new_file, rows_written = res
                completed.append((fid, new_file, rows_written))
            except (
                ray.exceptions.ActorDiedError,
                ray.exceptions.ActorUnavailableError,
            ):
                _LOG.warning(
                    "Writer actor for frag %s unavailable – restarting", self.frag_id
                )
                self._restart()
                return []  # will show up next poll
            assert fid == self.frag_id
            self.completed += 1
            self.inflight.pop(fut)

        return completed

    def seal(self) -> None:
        self.sealed = True

    def drain(self) -> Generator[tuple[int, Any, int], None, None]:
        """Yield all (frag_id,new_file, rows_written) as futures complete."""
        while self.inflight:
            ready, _ = ray.wait(list(self.inflight.keys()), timeout=5.0)
            if not ready:
                continue

            for fut in ready:
                try:
                    res = ray.get(fut)
                    assert isinstance(res, tuple) and len(res) == 3, (  # noqa: PT018
                        "FragmentWriter.write() should return (frag_id, new_file,"
                        " rows_written), "
                    )
                    fid, new_file, rows_written = res
                    yield fid, new_file, rows_written
                    self.completed += 1
                except (
                    ray.exceptions.ActorDiedError,
                    ray.exceptions.ActorUnavailableError,
                ):
                    _LOG.warning(
                        "Writer actor for frag %s died during drain—restarting",
                        self.frag_id,
                    )
                    # clear out any old futures, spin up a fresh actor & queue
                    self._restart()
                    # break out to re-enter the while loop with a clean slate
                    break
                # sucessful write
                self.inflight.pop(fut)


@attrs.define
class FragmentWriterManager:
    """FragmentWriterManager is responsible for writing out fragments
    from the ReadTasks to the destination dataset.

    There is one instance so that we can track pending completed fragments and do
    partial commits.
    """

    dst_read_version: int
    ds_uri: str
    map_task: MapTask
    checkpoint_store: CheckpointStore
    where: str | None
    job_tracker: ActorHandle | None
    commit_granularity: int
    expected_tasks: dict[int, int]  # frag_id, # batches
    # int key is frag_id
    skipped_fragments: dict[int, lance.fragment.DataFile] = attrs.field(factory=dict)
    namespace_impl: Optional[str] = None
    namespace_properties: Optional[dict[str, str]] = None
    table_id: Optional[list[str]] = None
    storage_options: Optional[dict[str, str]] = None
    # Source data files per destination fragment (for MV checkpoint validation)
    src_data_files_by_dst: dict[int, frozenset[str]] = attrs.field(factory=dict)

    # internal state
    sessions: dict[int, FragmentWriterSession] = attrs.field(factory=dict, init=False)
    remaining_tasks: dict[int, int] = attrs.field(init=False)
    output_columns: list[str] = attrs.field(init=False)
    # Track fragment IDs that are skipped to avoid double-counting in progress
    _skipped_fragment_ids: set[int] = attrs.field(factory=set, init=False)
    # (frag_id, lance.fragment.DataFile, # rows)
    rows_input_by_frag: dict[int, int] = attrs.field(factory=dict, init=False)
    # Local reconciled totals (authoritative at teardown even if tracker updates drop)
    _reconciled_rows_checkpointed_total: int = attrs.field(default=0, init=False)
    _reconciled_rows_ready_total: int = attrs.field(default=0, init=False)
    _reconciled_rows_committed_total: int = attrs.field(default=0, init=False)
    to_commit: list[tuple[int, lance.fragment.DataFile, int]] = attrs.field(
        factory=list, init=False
    )

    @property
    def namespace_client(self) -> "LanceNamespace | None":
        """Create namespace client from impl and properties if available."""
        if self.namespace_impl is not None and self.namespace_properties is not None:
            from lance_namespace import connect as namespace_connect

            return namespace_connect(self.namespace_impl, self.namespace_properties)
        return None

    def __attrs_post_init__(self) -> None:
        # all output cols except for _rowaddr because it is implicit since the
        # lancedatafile is writing out in sequential order
        self.output_columns = [
            f.name for f in self.map_task.output_schema() if f.name != "_rowaddr"
        ]
        self.remaining_tasks = dict(self.expected_tasks)

        # Immediately add skipped fragments to commit list and update progress tracking
        total_skipped_rows = 0
        for frag_id, data_file in self.skipped_fragments.items():
            # Estimate row count from original fragment if available
            try:
                # Open dataset with namespace if available
                if self.namespace_client and self.table_id:
                    dataset = lance.dataset(
                        namespace=self.namespace_client,
                        table_id=self.table_id,
                        storage_options=self.storage_options,
                    )
                else:
                    dataset = lance.dataset(
                        self.ds_uri, storage_options=self.storage_options
                    )

                original_fragment = dataset.get_fragment(frag_id)
                if original_fragment is None:
                    row_count = 0
                else:
                    row_count = original_fragment.count_rows()
                    # Note: we ignore where filters since we care about rows in the
                    # fragment
            except Exception:
                row_count = 0  # Default if we can't get the count

            self.to_commit.append((frag_id, data_file, row_count))
            self._skipped_fragment_ids.add(
                frag_id
            )  # Track that this fragment is skipped
            total_skipped_rows += row_count
            _LOG.info(
                f"Added skipped fragment {frag_id} to commit list with {row_count} rows"
            )
        # Skipped rows are effectively "already ready/committed"
        self._reconciled_rows_checkpointed_total += total_skipped_rows
        self._reconciled_rows_ready_total += total_skipped_rows
        self._reconciled_rows_committed_total += total_skipped_rows

    def poll_all(self) -> None:
        for sess in list(self.sessions.values()):
            for fid, new_file, rows_written in sess.poll_ready():
                self._record_fragment(
                    fid, new_file, self.commit_granularity, rows_written
                )

    def ingest(self, checkpoint_key, task, cnt_udf_computed: int) -> None:
        frag_id = task.dest_frag_id()

        sess = self.sessions.get(frag_id)
        if sess is None:
            _LOG.debug("Creating writer for fragment %d", frag_id)
            sess = FragmentWriterSession(
                frag_id=frag_id,
                ds_uri=self.ds_uri,
                output_columns=self.output_columns,
                checkpoint_store=self.checkpoint_store,
                where=self.where,
                namespace_impl=self.namespace_impl,
                namespace_properties=self.namespace_properties,
                table_id=self.table_id,
            )
            self.sessions[frag_id] = sess

        sess.ingest_task(task.dest_offset(), checkpoint_key)
        try:
            num_rows = getattr(task, "num_rows", None)
            if callable(num_rows):
                num_rows = num_rows()
            if isinstance(num_rows, int) and num_rows > 0 and self.job_tracker:
                self.job_tracker.increment.remote("rows_checkpointed", num_rows)
                self._reconciled_rows_checkpointed_total += int(num_rows)
                self.rows_input_by_frag[frag_id] = self.rows_input_by_frag.get(
                    frag_id, 0
                ) + int(num_rows)
            if (
                self.job_tracker
                and isinstance(cnt_udf_computed, int)
                and cnt_udf_computed > 0
            ):
                self.job_tracker.increment.remote(METRIC_UDF_VALUES, cnt_udf_computed)
        except Exception:
            _LOG.exception("Failed to get number of rows from result for task %s", task)
        self.remaining_tasks[frag_id] -= 1
        if self.remaining_tasks[frag_id] <= 0:
            sess.seal()

        # TODO check if previously checkpointed fragment exists

    def _record_fragment(
        self,
        frag_id: int,
        new_file,
        commit_granularity: int,
        rows_written: int,
    ) -> None:
        dedupe_key = _get_fragment_dedupe_key(
            self.ds_uri, frag_id, self.map_task, dataset_version=self.dst_read_version
        )
        # Store file name and source data file paths in checkpoint.
        # The source data files are the UNION of file paths across all source
        # fragments that contributed rows to this destination fragment.
        # When any backfill runs (even re-running UDF on same field), new data
        # files with new UUIDs are created, changing the union and triggering
        # checkpoint invalidation.
        checkpoint_data: dict[str, list] = {"file": [new_file.path]}

        # Include source data file paths if available (for MV refresh)
        src_files = self.src_data_files_by_dst.get(frag_id)
        if src_files is not None:
            checkpoint_data["src_data_files"] = [json.dumps(sorted(src_files))]
            _LOG.debug(
                f"Storing data files in checkpoint for frag {frag_id}: "
                f"{len(src_files)} files"
            )

        self.checkpoint_store[dedupe_key] = pa.RecordBatch.from_pydict(checkpoint_data)
        if self.job_tracker:
            self.job_tracker.increment.remote("writer_fragments", 1)

        input_rows = int(self.rows_input_by_frag.get(frag_id, 0))

        # Check if this fragment was already committed as a skipped fragment
        # Use _skipped_fragment_ids instead of searching to_commit, since to_commit
        # gets cleared after each commit but _skipped_fragment_ids persists
        if frag_id in self._skipped_fragment_ids:
            _LOG.info(
                f"Fragment {frag_id} was already committed as skipped fragment, "
                f"not re-adding to commit list"
            )
            return  # Don't add it again to avoid double-commit

        # New fragment, add it normally
        _LOG.info(f"Adding new fragment {frag_id} to commit list")
        self.to_commit.append((frag_id, new_file, input_rows))
        if input_rows > 0 and self.job_tracker:
            self.job_tracker.increment.remote("rows_ready_for_commit", input_rows)
        # Track totals locally so we can reconcile metrics even if tracker updates drop
        self._reconciled_rows_ready_total += input_rows

        # Track processed writes and hybrid-shutdown
        sess = self.sessions.get(frag_id)
        if sess and sess.sealed and not sess.inflight:
            # flush any pending commit for this fragment
            sess.shutdown()
            self.sessions.pop(frag_id, None)

        self._commit_if_n_fragments(commit_granularity)

    # aka _try_commit
    def _commit_if_n_fragments(
        self, commit_granularity: int, robust: bool = False
    ) -> None:
        """Commit fragments if we have enough to meet granularity threshold.

        Args:
            commit_granularity: Minimum number of fragments to commit
            robust: If True, retry RuntimeError with 'Too many concurrent writers'
        """
        n = max(1, int(commit_granularity))
        if len(self.to_commit) < n:
            return

        to_commit = self.to_commit
        self.to_commit = []
        version = self.dst_read_version
        operation = lance.LanceOperation.DataReplacement(
            replacements=[
                lance.LanceOperation.DataReplacementGroup(
                    fragment_id=frag_id,
                    new_file=new_file,
                )
                for frag_id, new_file, _rows in to_commit
            ]
        )

        retry_attempt = 0
        max_retries = 7 if robust else 0
        commit_type = "Robust" if robust else "Standard"

        while True:
            try:
                _LOG.info(
                    "%s commit: %d fragments to %s at version %d%s",
                    commit_type,
                    len(to_commit),
                    self.ds_uri,
                    version,
                    f" (attempt {retry_attempt + 1})"
                    if robust and retry_attempt > 0
                    else "",
                )

                # Reconstruct storage_options_provider if we have namespace config
                # and the namespace provides storage_options (e.g., cloud credentials)
                storage_options_provider, storage_options = (
                    get_storage_options_provider(
                        self.namespace_impl, self.namespace_properties, self.table_id
                    )
                )
                lance.LanceDataset.commit(
                    self.ds_uri,
                    operation,
                    read_version=version,
                    storage_options=storage_options,
                    storage_options_provider=storage_options_provider,
                )
                # rows committed == sum(input rows for fragments just committed)
                # Exclude skipped fragments since they were already counted in
                # "ready for commit"
                committed_rows = sum(
                    _rows
                    for _fid, _new_file, _rows in to_commit
                    if _fid not in self._skipped_fragment_ids
                )
                if committed_rows and self.job_tracker:
                    self.job_tracker.increment.remote("rows_committed", committed_rows)
                self._reconciled_rows_committed_total += committed_rows

                if robust and retry_attempt > 0:
                    _LOG.info(
                        "%s commit succeeded after %d attempts",
                        commit_type,
                        retry_attempt + 1,
                    )
                break
            except OSError as e:
                # Conflict error has this message:
                # OSError: Commit conflict for version 6: This DataReplacement \
                # transaction is incompatible with concurrent transaction \
                # DataReplacement at version 6.,
                if "Commit conflict for version" not in str(e):
                    # only handle version conflict
                    raise e

                # WARNING - the versions are sequentially increasing and we assume we'll
                # eventually find a version that will not conflict.  This could be a
                # problem for rare cases where column replacements happen concurrently.

                # TODO: This is a workaround for now, but we should consider adding
                # conflict resolution to lance.

                # this is a version conflict, retry with next version
                _LOG.debug(
                    (
                        "%s commit failed with version conflict: %s. "
                        "Retrying with next version."
                    ),
                    commit_type,
                    e,
                )
                version += 1
            except RuntimeError as e:
                # Handle "Too many concurrent writers" errors from Lance
                # Only retry in robust mode
                if not robust or "Too many concurrent writers" not in str(e):
                    # only handle concurrent writers error in robust mode
                    raise e

                retry_attempt += 1
                if retry_attempt >= max_retries:
                    _LOG.error(
                        (
                            "%s commit failed after %d attempts with concurrent "
                            "writers error: %s"
                        ),
                        commit_type,
                        retry_attempt,
                        e,
                    )
                    raise e

                _LOG.info(
                    (
                        "%s commit failed with concurrent writers (attempt %d/%d): %s. "
                        "Retrying with backoff."
                    ),
                    commit_type,
                    retry_attempt,
                    max_retries,
                    e,
                )
                # Use exponential backoff with jitter for concurrent writers
                backoff = min(30.0, 0.5 * (2 ** min(5, retry_attempt)))
                backoff += random.uniform(0, backoff * 0.1)  # Add 10% jitter
                time.sleep(backoff)

    def cleanup(self) -> None:
        _LOG.debug("draining & shutting down any leftover sessions")

        # 1) Commit any top‑of‑buffer fragments with robust retry logic
        self._commit_if_n_fragments(1, robust=True)

        # 2) Drain & shutdown whatever sessions remain
        for _frag_id, sess in list(self.sessions.items()):
            for fid, new_file, rows_written in sess.drain():
                # this may in turn pop more sessions via _record_fragment
                self._record_fragment(
                    fid, new_file, self.commit_granularity, rows_written
                )
            sess.shutdown()

        # 3) Clear out any sessions that finished in the loop above
        self.sessions.clear()

        # 4) Final safety commit of anything left with robust retry logic
        self._commit_if_n_fragments(1, robust=True)

    def finalize_metrics(self) -> None:
        """Ensure row progress metrics are fully populated at job end.

        Ray actor messages can be dropped or delayed under heavy load; by the time the
        job finishes the tracker may not have seen every incremental update.  We keep
        local running totals and overwrite the tracker metrics with the reconciled
        values so finished jobs always report the correct counts.
        """
        if self.job_tracker is None:
            return

        try:
            total_checkpointed = self._reconciled_rows_checkpointed_total
            total_ready = self._reconciled_rows_ready_total
            total_committed = self._reconciled_rows_committed_total

            refs = []
            for name, value in (
                ("rows_checkpointed", total_checkpointed),
                ("rows_ready_for_commit", total_ready),
                ("rows_committed", total_committed),
            ):
                # set() will also mark done when n >= total
                refs.append(self.job_tracker.set.remote(name, value))
                # Explicitly mark done to force a final save even if totals are zero
                refs.append(self.job_tracker.mark_done.remote(name))

            if refs:
                # Best‑effort wait so we don't hang shutdown indefinitely
                try:
                    ray.get(refs, timeout=5.0)
                except ray.exceptions.GetTimeoutError:
                    _LOG.warning(
                        "Final metric reconciliation timed out; metrics will still be "
                        "correct on the next tracker flush if the actor stays alive"
                    )
        except Exception:
            _LOG.exception("Failed to finalize row metrics")


def fetch_udf(table: Table, column_name: str) -> UDFSpec:
    schema = table._ltbl.schema
    field = schema.field(column_name)
    if field is None:
        raise ValueError(f"Column {column_name} not found in table {table}")

    udf_path = metadata_value("virtual_column.udf", field.metadata)
    fs, root_uri = FileSystem.from_uri(table.to_lance().uri)
    udf_payload = fs.open_input_file(f"{root_uri}/{udf_path}").read()

    udf_name = metadata_value("virtual_column.udf_name", field.metadata)
    udf_backend = metadata_value("virtual_column.udf_backend", field.metadata)

    return UDFSpec(
        name=udf_name,
        backend=udf_backend,
        udf_payload=udf_payload,
    )


def metadata_value(key: str, metadata: dict[bytes, bytes] | None) -> str:
    if metadata is None:
        raise ValueError(f"Metadata is None, cannot find key {key}")
    value = metadata.get(key.encode("utf-8"))
    if value is None:
        raise ValueError(f"Metadata key {key} not found in metadata {metadata}")
    return value.decode("utf-8")


def _get_matview_version(schema: pa.Schema) -> int:
    """Get materialized view version from schema metadata.

    Args:
        schema: PyArrow schema from materialized view table

    Returns:
        int: Version number (1 for legacy fragment+offset, 2 for direct row IDs)
             Defaults to 1 for backwards compatibility with v0.7.x MVs
    """
    metadata = schema.metadata or {}
    version_bytes = metadata.get(MATVIEW_META_VERSION.encode(), b"1")
    return int(version_bytes.decode())


# Maximum number of row IDs to include in a single DELETE statement
# to avoid SQL statement size limits
MAX_DELETE_BATCH_SIZE = 10000


def _get_valid_source_row_ids_at_version(
    src_db_uri: str,
    src_table_name: str,
    target_version: int,
    query: GenevaQuery,
    namespace_impl: str | None = None,
    namespace_properties: dict[str, str] | None = None,
) -> set[int]:
    """Get all row IDs that exist in source table at target version.

    Applies the MV's WHERE filter to only return matching rows.

    Args:
        src_db_uri: URI of the source database
        src_table_name: Name of the source table
        target_version: Version of the source table to query
        query: The GenevaQuery containing the WHERE filter
        namespace_impl: Optional namespace implementation
        namespace_properties: Optional namespace properties

    Returns:
        set: Row IDs that exist in the source table at target_version and match filter
    """
    from geneva.db import connect

    # Connect to source database (use context manager to ensure connection is closed)
    with connect(
        src_db_uri,
        namespace_impl=namespace_impl,
        namespace_properties=namespace_properties,
    ) as src_db:
        src_table = src_db.open_table(src_table_name)
        src_dataset = src_table.to_lance().checkout_version(target_version)

        # Build scanner with the MV's WHERE filter
        filter_expr = query.base.filter if query.base and query.base.filter else None

        scanner = src_dataset.scanner(
            columns=[],  # Only need row IDs, not data columns
            filter=filter_expr,
            with_row_id=True,
        )

        # Collect all valid row IDs
        valid_row_ids: set[int] = set()
        for batch in scanner.to_batches():
            if "_rowid" in batch.schema.names:
                valid_row_ids.update(
                    rid for rid in batch["_rowid"].to_pylist() if rid is not None
                )

        _LOG.info(
            f"Found {len(valid_row_ids)} valid row IDs in source table "
            f"at version {target_version}"
        )
        return valid_row_ids


def _delete_rows_not_in_source_version(
    dst_table: Table,
    valid_source_row_ids: set[int],
    batch_size: int = MAX_DELETE_BATCH_SIZE,
) -> int:
    """Delete destination rows whose __source_row_id is not in the valid set.

    Args:
        dst_table: The destination (MV) table
        valid_source_row_ids: Set of row IDs that are valid in the target source version
        batch_size: Number of rows to delete per batch (default: MAX_DELETE_BATCH_SIZE)

    Returns:
        int: Count of deleted rows
    """
    # Get current destination row IDs
    dst_data = dst_table.to_lance().scanner(columns=["__source_row_id"]).to_table()

    current_row_ids = {
        rid for rid in dst_data["__source_row_id"].to_pylist() if rid is not None
    }

    # Find rows to delete (in destination but NOT in source)
    rows_to_delete = current_row_ids - valid_source_row_ids

    if not rows_to_delete:
        _LOG.info("No rows to delete - all destination rows exist in target version")
        return 0

    _LOG.info(f"Deleting {len(rows_to_delete)} rows not present in target version")

    # Batch deletions for large sets to avoid SQL statement size limits
    rows_list = list(rows_to_delete)
    total_deleted = 0

    for i in range(0, len(rows_list), batch_size):
        batch = rows_list[i : i + batch_size]
        row_ids_str = ",".join(str(rid) for rid in batch)
        dst_table.delete(where=f"__source_row_id IN ({row_ids_str})")
        total_deleted += len(batch)
        _LOG.info(f"Deleted batch of {len(batch)} rows (total: {total_deleted})")

    return total_deleted


def _delete_stale_mv_rows(
    dst: TableReference,
    dst_table: Table,
    src_dburi: str,
    src_name: str,
    src_version: int,
    query: GenevaQuery,
    delete_batch_size: int,
    reason: str,
    existing_source_row_ids: set[int] | None = None,
) -> tuple[Table, lance.LanceDataset, int, set[int]]:
    """Delete MV rows whose source rows don't exist at src_version.

    This is used by both backward refresh (rollback) and forward refresh
    (delete sync) to remove stale rows from the materialized view.

    Args:
        dst: The destination table reference
        dst_table: The destination (MV) table
        src_dburi: URI of the source database
        src_name: Name of the source table
        src_version: Version of the source table to query
        query: The GenevaQuery containing the WHERE filter
        delete_batch_size: Number of rows to delete per batch
        reason: Description for logging (e.g., "Backward refresh", "Forward refresh")
        existing_source_row_ids: If provided, first checks if any deletions needed
                                 before querying source. Returns early if none.

    Returns:
        Tuple of (dst_table, dst_dataset, deleted_count, valid_row_ids)
    """
    # Get valid row IDs at target version (with MV filter applied)
    valid_row_ids = _get_valid_source_row_ids_at_version(
        src_dburi, src_name, src_version, query
    )

    # Early exit if caller knows there are no deletions
    if existing_source_row_ids is not None:
        rows_to_delete = existing_source_row_ids - valid_row_ids
        if not rows_to_delete:
            _LOG.info(f"{reason}: no rows to delete")
            return dst_table, dst_table.to_lance(), 0, valid_row_ids

    # Delete destination rows not in target version
    deleted_count = _delete_rows_not_in_source_version(
        dst_table, valid_row_ids, batch_size=delete_batch_size
    )
    _LOG.info(f"{reason}: deleted {deleted_count} rows from MV")

    # Re-open destination table after deletion to get fresh state
    dst_table = dst.open()
    dst_dataset = dst_table.to_lance()

    return dst_table, dst_dataset, deleted_count, valid_row_ids


def _extract_fragment_ids_from_row_ids(row_ids: list[int], mv_version: int) -> set[int]:
    """Extract source fragment IDs from __source_row_id values.

    Args:
        row_ids: List of __source_row_id values from materialized view
        mv_version: Materialized view version (1 or 2)

    Returns:
        set: Source fragment IDs referenced by these row IDs

    Note:
        Version 1: Fragment+offset encoding (fragment << 32 | offset)
          - Used for v0.7.x and earlier (always)
          - Used for v0.8.x+ without stable row IDs (Lance's _rowid encoding)
        Version 2: Stable row IDs (v0.8.x+ with stable row IDs enabled)
          - Row IDs are stable logical IDs that persist across compaction
          - Fragment IDs cannot be reliably extracted from row IDs (may change)
          - For now, conservatively return empty set to force full processing
          - TODO: Query Lance to map stable row IDs to current fragment IDs
    """
    if mv_version == 1:
        # Fragment+offset encoding: extract fragment ID from upper 32 bits
        return {row_id >> 32 for row_id in row_ids if row_id is not None}
    else:  # version 2 (stable row IDs)
        # Stable row IDs: Cannot extract fragment IDs from row IDs.
        # Return empty set to indicate we can't determine source fragments
        # from row IDs alone. This will cause the refresh logic to process
        # all source fragments (conservative but correct).
        return set()


def _validate_checkpoint_data_files(
    checkpoint_store: CheckpointStore,
    dedupe_key: str,
    current_data_files: frozenset[str],
) -> bool:
    """Validate that stored data files match current source data files.

    This detects when source data has been modified via backfill. When any
    backfill runs (including re-running a UDF on the same column), new data
    files with new UUIDs are created. Comparing file paths detects ALL changes.

    Args:
        checkpoint_store: The checkpoint store
        dedupe_key: The checkpoint key for this fragment
        current_data_files: Current data file paths from source fragments

    Returns:
        True if checkpoint is valid (data files match or not stored),
        False if checkpoint is invalid (data files changed)
    """
    _LOG.debug(
        f"_validate_checkpoint_data_files: key={dedupe_key}, "
        f"current={sorted(current_data_files)}"
    )
    if dedupe_key not in checkpoint_store:
        _LOG.info(
            f"_validate_checkpoint_data_files: checkpoint key not found {dedupe_key}, "
            "invalidating to force reprocess"
        )
        return False  # Key not found - force reprocess to ensure correct checkpoint

    try:
        checkpointed_data = checkpoint_store[dedupe_key]
        _LOG.debug(
            f"_validate_checkpoint_data_files: checkpoint schema="
            f"{checkpointed_data.schema.names}"
        )

        # If no src_data_files stored, invalidate checkpoint to ensure refresh.
        # This handles legacy checkpoints created before data file tracking.
        if "src_data_files" not in checkpointed_data.schema.names:
            _LOG.info(
                "_validate_checkpoint_data_files: no src_data_files in "
                "checkpoint, invalidating to ensure refresh"
            )
            return False

        stored_files_json = checkpointed_data["src_data_files"][0].as_py()
        _LOG.debug(
            f"_validate_checkpoint_data_files: stored_files_json={stored_files_json}"
        )
        if stored_files_json is None:
            _LOG.info(
                "_validate_checkpoint_data_files: src_data_files is null, "
                "invalidating to ensure refresh"
            )
            return False

        stored_files = frozenset(json.loads(stored_files_json))
        if stored_files != current_data_files:
            _LOG.info(
                f"Checkpoint data files mismatch for {dedupe_key}: "
                f"stored={sorted(stored_files)}, "
                f"current={sorted(current_data_files)}"
            )
            return False

        _LOG.debug(
            "_validate_checkpoint_data_files: data files match, checkpoint valid"
        )
        return True
    except Exception as e:
        _LOG.debug(f"Failed to validate data files for {dedupe_key}: {e}")
        return True  # On error, assume valid (conservative)


class DstToSrcMappingResult(NamedTuple):
    """Result of mapping destination fragments to source fragments.

    Attributes:
        dst_to_src_map: Mapping from dst fragment ID to set of src fragment IDs
        dst_frags_with_checkpoint: Set of dst fragment IDs with valid checkpoints
        existing_source_row_ids: Set of all source row IDs already in destination
        src_data_files_by_dst: Mapping from dst fragment ID to union of data file
            paths from all contributing source fragments
    """

    dst_to_src_map: dict[int, set[int]]
    dst_frags_with_checkpoint: set[int]
    existing_source_row_ids: set[int]
    src_data_files_by_dst: dict[int, frozenset[str]]


def _build_dst_to_src_mapping(
    dst_dataset: lance.LanceDataset,
    dst_uri: str,
    map_task,
    checkpoint_store: CheckpointStore,
    src_dataset: lance.LanceDataset | None = None,
    relevant_field_ids: frozenset[int] | None = None,
) -> DstToSrcMappingResult:
    """Build mapping from destination to source fragments, track checkpoints.

    This function iterates over destination fragments and:
    1. Extracts which source fragments contributed to each destination fragment
    2. Computes the UNION of source data file paths for checkpoint validation
    3. Validates existing checkpoints against current source data files

    Why track data file paths? When any backfill runs (including re-running a UDF
    on the same column), new data files with new UUIDs are created. By tracking
    the union of all data file paths from source fragments, we detect ANY change.

    Args:
        dst_dataset: The destination Lance dataset
        dst_uri: URI of the destination dataset
        map_task: The map task being applied
        checkpoint_store: The checkpoint store
        src_dataset: The source Lance dataset (optional, for data file validation)
        relevant_field_ids: If provided, only track data files containing these
            field IDs. This filters out unrelated columns from tracking.

    Returns:
        DstToSrcMappingResult with fragment mappings and checkpoint info
    """
    from geneva.apply import _check_fragment_data_file_exists

    # Get MV version for backwards compatibility
    mv_version = _get_matview_version(dst_dataset.schema)
    _LOG.info(f"Materialized view version: {mv_version}")

    dst_to_src_map: dict[int, set[int]] = {}
    dst_frags_with_checkpoint: set[int] = set()
    existing_source_row_ids: set[int] = set()
    src_data_files_by_dst: dict[int, frozenset[str]] = {}

    _LOG.debug(
        f"_build_dst_to_src_mapping: src_dataset={src_dataset is not None}, "
        f"dst frags={[f.fragment_id for f in dst_dataset.get_fragments()]}"
    )
    for dst_frag in dst_dataset.get_fragments():
        dst_frag_id = dst_frag.fragment_id

        # Read __source_row_id to map destination to source fragments FIRST
        # so we can validate data files
        source_frag_ids: set[int] = set()
        try:
            scanner = dst_dataset.scanner(
                columns=["__source_row_id"],
                fragments=[dst_frag],
            )
            dst_frag_data = scanner.to_table()
            if len(dst_frag_data) > 0:
                source_row_ids = cast(
                    "list[int]", dst_frag_data["__source_row_id"].to_pylist()
                )
                # Build fragment ID mapping using version-aware extraction
                source_frag_ids = _extract_fragment_ids_from_row_ids(
                    [rid for rid in source_row_ids if rid is not None],
                    mv_version,
                )
                dst_to_src_map[dst_frag_id] = source_frag_ids
                _LOG.debug(
                    f"_build_dst_to_src_mapping: dst_frag={dst_frag_id} -> "
                    f"src_frags={source_frag_ids}"
                )
                # Collect all source row IDs for deduplication
                existing_source_row_ids.update(
                    row_id for row_id in source_row_ids if row_id is not None
                )
        except Exception as e:
            _LOG.warning(
                f"Failed to read __source_row_id from destination fragment "
                f"{dst_frag_id}: {e}"
            )

        # Compute source data files for this destination fragment.
        # We compute the UNION of data file paths from all source fragments
        # that contributed rows to this destination. Union detects when ANY
        # data file changes in ANY source fragment (new backfill creates new files).
        current_data_files: frozenset[str] = frozenset()
        if src_dataset is not None:
            if source_frag_ids:
                # Have specific source fragment IDs - compute union of data files
                current_data_files = get_combined_source_data_files(
                    src_dataset, source_frag_ids, relevant_field_ids
                )
                _LOG.debug(
                    f"Computed source data files for dst frag {dst_frag_id}: "
                    f"src_frags={source_frag_ids}, "
                    f"file_count={len(current_data_files)}"
                )
            else:
                # Can't determine source fragments (e.g., MV v2 with stable row IDs)
                # Use ALL source fragments' data files (conservative but correct)
                all_src_frag_ids = {f.fragment_id for f in src_dataset.get_fragments()}
                current_data_files = get_combined_source_data_files(
                    src_dataset, all_src_frag_ids, relevant_field_ids
                )
                _LOG.debug(
                    f"Computed source data files for dst frag {dst_frag_id} "
                    f"(all source frags): file_count={len(current_data_files)}"
                )
            src_data_files_by_dst[dst_frag_id] = current_data_files

        # Check if this destination fragment has a valid checkpoint
        checkpoint_exists = _check_fragment_data_file_exists(
            dst_uri,
            dst_frag_id,
            map_task,
            checkpoint_store,
            dataset_version=dst_dataset.version,
        )

        # Validate data files if checkpoint exists and source dataset is provided
        # Note: We validate even if source_frag_ids is empty (MV v2 with stable row IDs)
        # because current_data_files covers all source fragments in that case
        if checkpoint_exists and src_dataset is not None:
            dedupe_key = _get_fragment_dedupe_key(
                dst_uri, dst_frag_id, map_task, dataset_version=dst_dataset.version
            )
            data_files_valid = _validate_checkpoint_data_files(
                checkpoint_store, dedupe_key, current_data_files
            )
            if not data_files_valid:
                _LOG.info(
                    f"Destination fragment {dst_frag_id} checkpoint invalidated: "
                    f"source data files changed"
                )
                checkpoint_exists = False

        if checkpoint_exists:
            dst_frags_with_checkpoint.add(dst_frag_id)
            _LOG.info(f"Destination fragment {dst_frag_id} has valid checkpoint")
        else:
            _LOG.info(f"Destination fragment {dst_frag_id} has no valid checkpoint")

    return DstToSrcMappingResult(
        dst_to_src_map=dst_to_src_map,
        dst_frags_with_checkpoint=dst_frags_with_checkpoint,
        existing_source_row_ids=existing_source_row_ids,
        src_data_files_by_dst=src_data_files_by_dst,
    )


def _identify_new_source_fragments(
    src_dataset: lance.LanceDataset,
    dst_to_src_map: dict[int, set[int]],
) -> list[int]:
    """Identify source fragments that have no representation in destination yet.

    These are truly NEW source fragments that need placeholder rows added.

    Returns:
        list: Source fragment IDs not present in any destination fragment
    """
    # Collect all source fragment IDs that exist in destination
    source_frags_in_destination = set()
    for src_frags in dst_to_src_map.values():
        source_frags_in_destination.update(src_frags)

    # Find source fragments not yet in destination
    new_source_fragments = []
    for frag in src_dataset.get_fragments():
        if frag.fragment_id not in source_frags_in_destination:
            _LOG.info(
                f"Found new source fragment {frag.fragment_id} - needs placeholder rows"
            )
            new_source_fragments.append(frag.fragment_id)

    return new_source_fragments


def _extract_new_row_ids_from_source_fragment(
    src_table,
    query: GenevaQuery,
    frag_id: int,
    existing_source_row_ids: set[int],
) -> list[int]:
    """Extract new row IDs from a source fragment that match the query filter.

    Returns:
        list: New row IDs from this fragment (not already in destination)
    """
    # Build query for this fragment with filters applied
    fragment_query_obj = GenevaQuery(
        fragment_ids=[frag_id],
        base=query.base.model_copy(deep=True),
    )
    fragment_query_obj.base.with_row_id = True
    fragment_query_obj.base.columns = []  # Only get row IDs
    fragment_query_obj.column_udfs = None
    fragment_query_obj.with_row_address = None

    fragment_query_builder = GenevaQueryBuilder.from_query_object(
        src_table, fragment_query_obj
    )

    # Get row IDs from this fragment (with filters applied)
    fragment_data = fragment_query_builder.to_arrow()
    _LOG.info(f"  Fragment {frag_id} query returned {len(fragment_data)} rows")

    if len(fragment_data) == 0:
        return []

    row_ids = cast("list[int]", fragment_data["_rowid"].to_pylist())
    _LOG.info(f"  Row IDs from fragment {frag_id}: {row_ids}")
    # Only add row IDs that don't already exist in destination
    new_row_ids = [
        row_id for row_id in row_ids if row_id not in existing_source_row_ids
    ]

    return new_row_ids


def _append_placeholder_fragments(
    dst_table,
    new_fragment_row_ids: list[int],
    max_rows_per_fragment: int | None = None,
) -> set[int] | None:
    """Append placeholder rows for new source data as new destination fragment(s).

    Args:
        dst_table: The destination table to append to
        new_fragment_row_ids: List of source row IDs to create placeholders for
        max_rows_per_fragment: Optional max rows per fragment. If the number of rows
            exceeds this, multiple fragments will be created by splitting the data
            and calling add() for each chunk. Must be at least 1.

    Returns:
        set[int] | None: The new destination fragment IDs, or None if no rows to add
    """
    if not new_fragment_row_ids:
        _LOG.info(
            "No new placeholder rows needed - all source row IDs already in destination"
        )
        return None

    # Validate max_rows_per_fragment if provided
    if max_rows_per_fragment is not None and max_rows_per_fragment < 1:
        raise ValueError(
            f"max_rows_per_fragment must be at least 1 (got {max_rows_per_fragment})"
        )

    _LOG.info(
        f"Adding {len(new_fragment_row_ids)} placeholder rows for new source data"
        + (
            f" (max_rows_per_fragment={max_rows_per_fragment})"
            if max_rows_per_fragment
            else ""
        )
    )

    # Get the current destination fragment count before adding
    dst_dataset_before = dst_table.to_lance()
    existing_fragment_ids = {
        frag.fragment_id for frag in dst_dataset_before.get_fragments()
    }
    _LOG.info(
        f"Existing destination fragment IDs before append: {existing_fragment_ids}"
    )

    # Split the row IDs into chunks based on max_rows_per_fragment
    # Each chunk will be added separately to create separate fragments
    if max_rows_per_fragment is not None and max_rows_per_fragment > 0:
        chunks = [
            new_fragment_row_ids[i : i + max_rows_per_fragment]
            for i in range(0, len(new_fragment_row_ids), max_rows_per_fragment)
        ]
    else:
        chunks = [new_fragment_row_ids]

    _LOG.info(f"Splitting into {len(chunks)} chunks for separate fragments")

    # Add each chunk as a separate fragment
    for i, chunk in enumerate(chunks):
        placeholder_data = pa.table(
            [
                pa.array(chunk, type=pa.int64()),
                pa.array([False] * len(chunk), type=pa.bool_()),
            ],
            names=["__source_row_id", "__is_set"],
        )
        dst_table.add(placeholder_data)
        _LOG.debug(f"Added chunk {i + 1}/{len(chunks)} with {len(chunk)} rows")

    # Identify the newly created fragment IDs
    dst_dataset_after = dst_table.to_lance()
    new_fragment_ids = {frag.fragment_id for frag in dst_dataset_after.get_fragments()}
    added_fragments = new_fragment_ids - existing_fragment_ids

    if len(added_fragments) >= 1:
        _LOG.info(
            f"Successfully added {len(added_fragments)} placeholder fragment(s) "
            f"{added_fragments} with {len(new_fragment_row_ids)} total rows"
        )
        return added_fragments
    else:
        _LOG.warning(f"Expected at least 1 new fragment but got {len(added_fragments)}")
        return None


def _determine_fragments_to_process(
    dst_to_src_map: dict[int, set[int]],
    dst_frags_with_checkpoint: set[int],
    new_dst_frag_ids: set[int] | None,
) -> set[int] | None:
    """Determine which destination fragments need processing (destination-driven).

    Simply process all destination fragments that don't have checkpoints.

    Returns:
        set[int] | None: Destination fragment IDs to process, or None for all
    """
    # Find all destination fragments without checkpoints
    fragments_to_process = set(dst_to_src_map.keys()) - dst_frags_with_checkpoint

    # Add newly created placeholder fragments (not in dst_to_src_map yet)
    if new_dst_frag_ids:
        fragments_to_process.update(new_dst_frag_ids)
        _LOG.info(
            f"Adding {len(new_dst_frag_ids)} newly created placeholder "
            f"fragment(s) {new_dst_frag_ids} to processing list"
        )

    if not fragments_to_process:
        _LOG.info("All destination fragments have checkpoints - nothing to process")
        return None

    _LOG.info(f"Will process destination fragments: {fragments_to_process}")
    return fragments_to_process


def _safe_extract_field_ids(
    lance_schema, field_name: str, failed_fields: list[str]
) -> list[int]:
    """Extract field IDs, recording failures instead of raising exceptions."""
    try:
        return extract_field_ids(lance_schema, field_name)
    except Exception:
        failed_fields.append(field_name)
        return []


def _collect_skipped_fragments(
    dst_dataset: lance.LanceDataset,
    dst_frags_with_checkpoint: set[int],
    map_task,
    checkpoint_store: CheckpointStore,
) -> tuple[dict[int, lance.fragment.DataFile], dict[str, int]]:
    """Collect checkpointed fragments for commit inclusion.

    Returns:
        tuple: (skipped_fragments, skipped_stats)
            - skipped_fragments: dict mapping frag ID -> DataFile object
            - skipped_stats: dict with 'fragments' and 'rows' counts
    """

    skipped_fragments = {}
    skipped_stats = {"fragments": 0, "rows": 0}

    for frag_id in dst_frags_with_checkpoint:
        try:
            fragment = dst_dataset.get_fragment(frag_id)
            if fragment is None:
                _LOG.warning(f"Fragment {frag_id} not found")
                continue
            frag_rows = fragment.count_rows()
        except Exception as e:
            _LOG.warning(f"Could not get fragment {frag_id}: {e}")
            continue

        skipped_stats["fragments"] += 1
        skipped_stats["rows"] += frag_rows

        # Get checkpoint data
        dedupe_key = _get_fragment_dedupe_key(dst_dataset.uri, frag_id, map_task)
        checkpointed_data = checkpoint_store[dedupe_key]
        file_list = checkpointed_data["file"].to_pylist()
        file_path = "".join(str(f) for f in file_list if f is not None)

        # Extract field_ids for all columns in the output schema
        # For CopyTableTask (materialized views), the checkpoint contains all columns
        # from the view schema, not just the UDF outputs
        field_ids = []
        output_schema = map_task.output_schema()
        failed_fields = []

        for field_name in output_schema.names:
            extracted = _safe_extract_field_ids(
                dst_dataset.lance_schema, field_name, failed_fields
            )
            field_ids.extend(extracted)

        if failed_fields:
            _LOG.warning(
                f"Could not extract field_ids for fields {failed_fields} "
                f"in checkpointed fragment {frag_id}"
            )

        # Create DataFile object for the checkpointed fragment
        existing_data_file = lance.fragment.DataFile(
            file_path,
            field_ids,
            list(range(len(field_ids))),
            2,  # major_version
            0,  # minor_version
        )
        skipped_fragments[frag_id] = existing_data_file

    _LOG.info(
        f"Collected {skipped_stats['fragments']} checkpointed fragments "
        f"with {skipped_stats['rows']} rows"
    )

    return skipped_fragments, skipped_stats


def _validate_mv_source_schema(
    query: GenevaQuery,
    src_table: "Table",
    mv_name: str,
    packager: UDFPackager,
) -> None:
    """
    Validate that source table has all columns required by materialized view query.

    This prevents cryptic errors during refresh when source table schema has evolved
    and dropped columns that the MV depends on.

    Parameters
    ----------
    query : GenevaQuery
        The materialized view query from metadata
    src_table : Table
        The source table to validate against
    mv_name : str
        Name of the materialized view (for error messages)
    packager : UDFPackager
        Packager to unmarshal UDFs to extract input columns

    Raises
    ------
    ValueError
        If source table is missing columns required by the MV query
    """
    required_columns = set()

    # Extract columns from base query SELECT clause
    if query.base.columns:
        if isinstance(query.base.columns, list):
            # Simple column list: ['col1', 'col2']
            required_columns.update(query.base.columns)
        elif isinstance(query.base.columns, dict):
            # Column mapping: {'output': 'source_col'} or {'output': <expression>}
            # Extract string values (column names), skip UDFs (handled separately)
            for value in query.base.columns.values():
                if isinstance(value, str):
                    # Could be a column name or SQL expression
                    # For simplicity, treat as column name
                    # TODO: Parse SQL expressions to extract column references
                    required_columns.add(value)

    # Extract input columns from UDFs
    if query.column_udfs:
        for column_udf in query.column_udfs:
            try:
                # Unmarshal UDF to access input_columns
                udf = packager.unmarshal(column_udf.udf.to_attrs())
                if udf.input_columns is not None:  # type: ignore[reportOptionalMemberAccess]
                    required_columns.update(udf.input_columns)  # type: ignore[reportOptionalMemberAccess]
            except Exception as e:  # noqa: PERF203
                # Note: Performance overhead acceptable for rare schema validation
                _LOG.warning(
                    f"Failed to unmarshal UDF '{column_udf.output_name}' "
                    f"for schema validation: {e}"
                )
                # Continue validation with other columns

    # Compare against source table schema
    source_columns = set(src_table.schema.names)
    missing_columns = required_columns - source_columns

    if missing_columns:
        missing_list = sorted(missing_columns)
        raise ValueError(
            f"Cannot refresh materialized view '{mv_name}': "
            f"Source table is missing required columns: {missing_list}\n\n"
            f"The materialized view query references columns that no longer exist "
            f"in the source table.\n\n"
            f"Options:\n"
            f"  1. Restore the missing columns to the source table\n"
            f"  2. Drop and recreate the materialized view with an updated query\n"
            f"  3. If the column was renamed, update the source table accordingly"
        )


def run_ray_copy_table(
    dst: TableReference,
    packager: UDFPackager,
    checkpoint_store: CheckpointStore | None = None,
    *,
    job_id: str | None = None,
    concurrency: int = 8,
    batch_size: int | None = None,
    task_shuffle_diversity: int | None = None,
    commit_granularity: int | None = None,
    delete_batch_size: int | None = None,
    src_version: int | None = None,
    max_rows_per_fragment: int | None = None,
    **kwargs,
) -> None:
    # prepare job parameters
    config = JobConfig.get().with_overrides(
        batch_size=batch_size,
        task_shuffle_diversity=task_shuffle_diversity,
        commit_granularity=commit_granularity,
        delete_batch_size=delete_batch_size,
    )

    checkpoint_store = checkpoint_store or config.make_checkpoint_store()

    # Create error store from dst connection
    dst_db = dst.open_db()
    error_store = _make_error_store(dst_db)

    # Initialize the JobStateManager to ensure Jobs table is created
    dst_db._history  # noqa: B018

    # Open destination table once and reuse
    dst_table = dst.open()
    dst_schema = dst_table.schema
    if dst_schema.metadata is None:
        raise Exception("Destination dataset must have view metadata.")
    src_dburi = dst_schema.metadata[MATVIEW_META_BASE_DBURI.encode("utf-8")].decode(
        "utf-8"
    )
    src_name = dst_schema.metadata[MATVIEW_META_BASE_TABLE.encode("utf-8")].decode(
        "utf-8"
    )

    # If src_version not specified, fetch the latest version of the source table
    if src_version is None:
        src_db = dst.open_db()
        if src_dburi != dst.db_uri:
            # Source is in a different database, connect to it
            from geneva.db import connect

            src_db = connect(src_dburi, checkpoint=dst.open_checkpoint_store())

        src_table_tmp = src_db.open_table(src_name)
        src_version = src_table_tmp.version
        _LOG.info(
            f"Materialized view refresh: fetched latest source version={src_version} "
            f"for table={src_name} from db={src_dburi}"
        )

    # Create table_id for source table
    src_table_id = [src_name]

    src = TableReference(
        table_id=src_table_id,
        version=src_version,
        db_uri=src_dburi,
        namespace_impl=dst.namespace_impl,
        namespace_properties=dst.namespace_properties,
    )

    query_json = dst_schema.metadata[MATVIEW_META_QUERY.encode("utf-8")]
    query = GenevaQuery.model_validate_json(query_json)

    # Check for point-in-time refresh (rollback to older version)
    from geneva.table import _get_last_refreshed_version

    last_refreshed = _get_last_refreshed_version(dst_table)
    if (
        src_version is not None
        and last_refreshed is not None
        and src_version < last_refreshed
    ):
        # Point-in-time refresh - delete rows not in target version
        _LOG.info(
            f"[EXPERIMENTAL] Point-in-time refresh: rolling back from version "
            f"{last_refreshed} to version {src_version}"
        )
        dst_table, _, _, _ = _delete_stale_mv_rows(
            dst,
            dst_table,
            src_dburi,
            src_name,
            src_version,
            query,
            config.delete_batch_size,
            "Backward refresh",
        )

    src_table = src.open()

    # Validate that source table schema is compatible with MV query
    _validate_mv_source_schema(query, src_table, dst.table_name, packager)

    schema = GenevaQueryBuilder.from_query_object(src_table, query).schema

    job_id = job_id or uuid.uuid4().hex

    column_udfs = query.extract_column_udfs(packager)

    # Use columns from stored query to avoid issues when source table has new columns.
    # The query.base.columns is captured at MV creation time.
    if query.base.columns:
        if isinstance(query.base.columns, list):
            input_cols = list(query.base.columns)
        else:
            # Dict mapping: {'output': 'source_col'} - extract source column names
            input_cols = [v for v in query.base.columns.values() if isinstance(v, str)]
    else:
        # Fallback for older MVs created before columns were captured
        input_cols = [
            n
            for n in src_table.schema.names
            if n not in ["__is_set", "__source_row_id"]
        ]

    # Also include UDF input columns that may not be in the select list
    for udf_transform in column_udfs:
        if udf_transform.udf.input_columns:
            for col in udf_transform.udf.input_columns:
                if col not in input_cols:
                    input_cols.append(col)

    # Create map_task before plan_copy so we can use it for checkpoint checking
    map_task = CopyTableTask(
        column_udfs=column_udfs,
        view_name=dst.table_name,
        schema=schema,
    )

    # === PASS 1: Identify new source fragments and add placeholder rows ===
    # This ensures CopyTask can read __source_row_id from destination during refresh
    _LOG.info("=== PASS 1: Identifying new source fragments ===")

    src_dataset = src_table.to_lance()
    _LOG.info(
        f"Source table has {len(list(src_dataset.get_fragments()))} fragments "
        f"at version={src.version} (Lance version={src_dataset.version})"
    )

    # Compute field IDs for columns the MV reads - used to filter data file tracking
    # so that changes to unrelated columns don't trigger MV refresh
    relevant_field_ids = _get_relevant_field_ids(src_dataset, input_cols)
    _LOG.debug(f"Relevant field IDs for MV columns {input_cols}: {relevant_field_ids}")

    dst_dataset = dst_table.to_lance()

    # Build destination-to-source mapping, identify checkpointed fragments,
    # and collect existing source row IDs (all in one pass for efficiency)
    # Also validates source data files to detect backfill changes
    (
        dst_to_src_map,
        dst_frags_with_checkpoint,
        existing_source_row_ids,
        src_data_files_by_dst,
    ) = _build_dst_to_src_mapping(
        dst_dataset,
        dst_dataset.uri,
        map_task,
        checkpoint_store,
        src_dataset,
        relevant_field_ids,
    )

    # === HANDLE SOURCE DELETIONS (FORWARD REFRESH) ===
    # When doing a forward refresh, check if any source rows have been deleted
    # and remove them from the MV
    if (
        last_refreshed is not None
        and src_version is not None
        and src_version >= last_refreshed  # Forward or same version refresh
        and existing_source_row_ids  # MV has rows
    ):
        dst_table, dst_dataset, deleted_count, valid_row_ids = _delete_stale_mv_rows(
            dst,
            dst_table,
            src_dburi,
            src_name,
            src_version,
            query,
            config.delete_batch_size,
            "Forward refresh",
            existing_source_row_ids,
        )
        if deleted_count > 0:
            existing_source_row_ids = existing_source_row_ids & valid_row_ids

    # Identify truly NEW source fragments (not yet in destination at all)
    new_source_fragments = _identify_new_source_fragments(src_dataset, dst_to_src_map)

    # Extract row IDs from new source fragments and add placeholder rows
    new_fragment_row_ids = []
    for frag_id in new_source_fragments:
        new_row_ids = _extract_new_row_ids_from_source_fragment(
            src_table, query, frag_id, existing_source_row_ids
        )
        new_fragment_row_ids.extend(new_row_ids)
        existing_source_row_ids.update(new_row_ids)

    # Append placeholder rows for new data
    new_dst_frag_ids = _append_placeholder_fragments(
        dst_table, new_fragment_row_ids, max_rows_per_fragment
    )

    # After appending placeholder fragments, update dst reference to use latest version.
    # This is needed because _append_placeholder_fragments creates a new table version.
    if new_dst_frag_ids:
        dst_table.checkout_latest()
        dst = TableReference(
            table_id=dst.table_id,
            version=dst_table.version,
            db_uri=dst.db_uri,
            namespace_impl=dst.namespace_impl,
            namespace_properties=dst.namespace_properties,
        )
        _LOG.info(f"Updated destination reference to version {dst.version}")

        # Compute source data files for newly created destination fragments.
        # This is needed so that checkpoints store data file paths for new fragments,
        # enabling detection of source backfill changes on subsequent refreshes.
        dst_dataset = dst_table.to_lance()
        mv_version = _get_matview_version(dst_dataset.schema)
        for new_dst_frag_id in new_dst_frag_ids:
            new_frag = dst_dataset.get_fragment(new_dst_frag_id)
            if new_frag is None:
                continue
            try:
                scanner = dst_dataset.scanner(
                    columns=["__source_row_id"],
                    fragments=[new_frag],
                )
                frag_data = scanner.to_table()
                if len(frag_data) > 0:
                    source_row_ids = cast(
                        "list[int]", frag_data["__source_row_id"].to_pylist()
                    )
                    src_frag_ids = _extract_fragment_ids_from_row_ids(
                        [rid for rid in source_row_ids if rid is not None],
                        mv_version,
                    )
                    data_files = get_combined_source_data_files(
                        src_dataset, src_frag_ids, relevant_field_ids
                    )
                    src_data_files_by_dst[new_dst_frag_id] = data_files
                    _LOG.info(
                        f"Computed data files for new dst fragment "
                        f"{new_dst_frag_id}: source_frags={src_frag_ids}, "
                        f"file_count={len(data_files)}"
                    )
            except Exception as e:
                _LOG.warning(
                    f"Failed to compute data files for new dst fragment "
                    f"{new_dst_frag_id}: {e}"
                )

    # Collect checkpointed fragments for commit inclusion
    skipped_fragments, skipped_stats = _collect_skipped_fragments(
        dst_dataset, dst_frags_with_checkpoint, map_task, checkpoint_store
    )

    # Determine which destination fragments need processing (destination-driven)
    # Simply process all destination fragments without checkpoints
    fragments_to_process = _determine_fragments_to_process(
        dst_to_src_map, dst_frags_with_checkpoint, new_dst_frag_ids
    )

    # Create plan - process only fragments that need processing
    # (or all if none specified)
    plan = plan_copy(
        src,
        dst,
        input_cols,
        batch_size=config.batch_size,
        task_shuffle_diversity=config.task_shuffle_diversity,
        only_fragment_ids=fragments_to_process,  # None means process all fragments
    )

    if fragments_to_process is not None:
        _LOG.info(f"Planning to process destination fragments: {fragments_to_process}")
    else:
        _LOG.info("Planning to process ALL destination fragments")

    _run_column_adding_pipeline(
        map_task,
        checkpoint_store,
        error_store,
        config,
        dst,
        plan,
        job_id,
        concurrency,
        skipped_fragments=skipped_fragments,
        skipped_stats=skipped_stats,
        src_data_files_by_dst=src_data_files_by_dst,
        **kwargs,
    )

    # Update materialized view metadata to track the source version
    # that was just refreshed
    _LOG.info(
        f"Updating materialized view {dst.table_name} metadata: "
        f"base_table_version={src_version}"
    )
    # Note: Schema metadata updates would require re-creating the table or using
    # Lance operations. For now, we log the version that was refreshed.
    # In future iterations, we could store this in a separate metadata table or
    # use schema evolution to track refresh history.


def dispatch_run_ray_add_column(
    table_ref: TableReference,
    col_name: str,
    *,
    read_version: int | None = None,
    concurrency: int = 8,
    batch_size: int | None = None,
    checkpoint_size: int | None = None,
    task_shuffle_diversity: int | None = None,
    commit_granularity: int | None = None,
    where: str | None = None,
    enable_job_tracker_saves: bool = True,
    **kwargs,
) -> JobFuture:
    """
    Dispatch the Ray add column operation to a remote function.
    This is a convenience function to allow calling the remote function directly.
    """
    if kwargs.get("task_size") is not None:
        _LOG.warning("task_size is not supported for backfill; ignoring value.")
        kwargs.pop("task_size", None)

    checkpoint_size = resolve_batch_size(
        batch_size=batch_size,
        checkpoint_size=checkpoint_size,
    )
    batch_size = None

    from datetime import datetime

    from geneva._context import get_current_context
    from geneva.manifest.mgr import ManifestConfigManager
    from geneva.utils import current_user

    db = table_ref.open_db()
    hist = db._history

    # Extract manifest info from current context
    manifest_id = None
    manifest_checksum = None
    ctx = get_current_context()
    if ctx is not None and ctx.manifest is not None:
        manifest = ctx.manifest
        manifest_checksum = manifest.checksum

        # Auto-register manifest if not already persisted
        if not manifest.name:
            # Generate auto name
            user = current_user()
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            checksum_short = manifest.checksum[:8] if manifest.checksum else "unknown"
            manifest.name = f"auto-{user}-{timestamp}-{checksum_short}"
            _LOG.info(f"Auto-registering manifest as '{manifest.name}'")

        manifest_id = manifest.name

        # Ensure manifest is registered in the database
        manifest_mgr = ManifestConfigManager(db, namespace=db.system_namespace)
        existing = manifest_mgr.load(manifest.name)
        if existing is None:
            _LOG.info(f"Upserting manifest '{manifest.name}' to database")
            manifest_mgr.upsert(manifest)

    job = hist.launch(
        table_ref.table_name,
        col_name,
        where=where,
        manifest_id=manifest_id,
        manifest_checksum=manifest_checksum,
        **kwargs,
    )

    job_tracker = JobTracker.options(
        name=f"jobtracker-{job.job_id}",
        num_cpus=0.1,
        memory=128 * 1024 * 1024,
        max_restarts=-1,
    ).remote(job.job_id, table_ref, enable_saves=enable_job_tracker_saves)  # type: ignore[call-arg]

    # Run on 0.1 cpu so that it's always easy to schedule.
    obj_ref = run_ray_add_column_remote.options(num_cpus=0.1).remote(  # type: ignore[call-arg,misc]
        table_ref,
        col_name,
        read_version=read_version,  # type: ignore[call-arg]
        job_id=job.job_id,  # type: ignore[call-arg]
        job_tracker=job_tracker,  # type: ignore[call-arg]
        concurrency=concurrency,  # type: ignore[call-arg]
        checkpoint_size=checkpoint_size,  # type: ignore[call-arg]
        task_shuffle_diversity=task_shuffle_diversity,  # type: ignore[call-arg]
        commit_granularity=commit_granularity,  # type: ignore[call-arg]
        where=where,  # type: ignore[call-arg]
        **kwargs,
    )
    # object ref is only available here
    hist.set_object_ref(job.job_id, cloudpickle.dumps(obj_ref))
    return RayJobFuture(
        job_id=job.job_id,
        ray_obj_ref=obj_ref,
        job_tracker=job_tracker,  # type: ignore[arg-type]
    )


def _schema_for_validation(tbl: Table, read_version: int | None) -> pa.Schema:
    """
    Get the table schema to validate UDF inputs against.

    If `read_version` is provided, we validate against that historical version of the
    table. Otherwise, we use the current schema.
    """
    if read_version is None:
        return tbl._ltbl.schema

    try:
        dataset = tbl.to_lance().checkout_version(read_version)
        return dataset.schema
    except Exception as exc:  # noqa: BLE001
        raise ValueError(
            f"Failed to load schema for read_version={read_version}. "
            "Ensure the version exists before running backfill."
        ) from exc


def _resolve_read_version(tbl: Table, read_version: int | None) -> int:
    """
    Determine the concrete version a job should read.

    If the caller did not provide read_version, we snapshot the table's current
    version at job launch time. This pins the job to a consistent schema and guards
    against concurrent column drops during execution.
    """
    return read_version if read_version is not None else tbl.version


def validate_backfill_args(
    tbl: Table,
    col_name: str,
    udf: UDF | None = None,
    input_columns: list[str] | None = None,
    *,
    read_version: int | None = None,
) -> None:
    """
    Validate the arguments for the backfill operation.

    This function performs validation before starting a backfill job to catch
    configuration errors early. It validates:

    1. Target column exists in the table
    2. UDF input columns exist in the table schema (for the requested read_version)
    3. Column types are compatible with UDF type annotations (if present)

    All validation is delegated to UDF.validate_against_schema() for consistency.

    Parameters
    ----------
    tbl : Table
        The table to backfill
    col_name : str
        The column name to backfill
    udf : UDF | None
        The UDF to use (if None, will be loaded from column metadata)
    input_columns : list[str] | None
        The input columns for the UDF (if None, will be loaded from column metadata)
    read_version : int | None
        If provided, validate UDF inputs against this historical table version instead
        of the current schema. This catches jobs that try to read from a version that
        lacks required input columns.

    Raises
    ------
    ValueError
        If validation fails (missing columns, type mismatches, etc.)

    Warns
    -----
    UserWarning
        If type validation is skipped due to missing type annotations
    """
    current_schema = tbl._ltbl.schema
    if col_name not in current_schema.names:
        raise ValueError(
            f"Column {col_name} is not defined this table.  "
            "Use add_columns to register it first"
        )

    if udf is None:
        udf_spec = fetch_udf(tbl, col_name)
        udf = tbl._conn._packager.unmarshal(udf_spec)

    # Get input_columns from column metadata if not provided
    if input_columns is None:
        field = tbl._ltbl.schema.field(col_name)
        metadata = field.metadata or {}
        input_columns = json.loads(metadata.get(b"virtual_column.udf_inputs", "null"))

    # Delegate to UDF's consolidated validation method if UDF was successfully
    # unmarshaled. If unmarshal returned None (modules not available), skip validation
    if udf is not None:
        schema = _schema_for_validation(tbl, read_version)
        try:
            udf.validate_against_schema(schema, input_columns)
        except ValueError as exc:
            if read_version is not None:
                raise ValueError(
                    f"{exc} (while validating against read_version {read_version})"
                ) from exc
            raise


@ray.remote
def run_ray_add_column_remote(
    table_ref: TableReference,
    col_name: str,
    *,
    job_id: str | None = None,
    udf: UDF | None = None,
    read_version: int | None = None,
    concurrency: int = 8,
    checkpoint_size: int | None = None,
    task_shuffle_diversity: int | None = None,
    commit_granularity: int | None = None,
    where: str | None = None,
    job_tracker: ActorHandle | None = None,
    **kwargs,
) -> None:
    """
    Remote function to run the Ray add column operation.
    This is a wrapper around `run_ray_add_column` to allow it to be called as a Ray
    task.
    """
    if kwargs.get("task_size") is not None:
        _LOG.warning("task_size is not supported for backfill; ignoring value.")
        kwargs.pop("task_size", None)

    legacy_batch_size = kwargs.pop("batch_size", None)
    checkpoint_size = resolve_batch_size(
        batch_size=legacy_batch_size,
        checkpoint_size=checkpoint_size,
    )

    import geneva  # noqa: F401  Force so that we have the same env in next level down

    tbl = table_ref.open()
    read_version = _resolve_read_version(tbl, read_version)
    hist = tbl._conn._history
    if job_id:
        hist.set_running(job_id)
    try:
        # Get input_columns from column metadata first
        field = tbl._ltbl.schema.field(col_name)
        metadata = field.metadata or {}
        input_columns = json.loads(metadata.get(b"virtual_column.udf_inputs", "null"))

        validate_backfill_args(
            tbl, col_name, udf, input_columns, read_version=read_version
        )
        if udf is None:
            udf_spec = fetch_udf(tbl, col_name)
            udf = tbl._conn._packager.unmarshal(udf_spec)

            # If unmarshal still returns None, we cannot proceed
            if udf is None:
                raise RuntimeError(
                    f"Failed to unmarshal UDF for column '{col_name}'. "
                    "The UDF modules may not be available in the Ray worker "
                    "environment. Ensure the manifest's py_modules includes all "
                    "required dependencies."
                )

        # Apply input_columns override to the UDF if needed
        # This handles the case where add_columns was called with explicit column
        # mapping e.g., table.add_columns({"col": (udf, ["seq"])})
        if input_columns is not None and udf.input_columns != input_columns:
            udf.input_columns = input_columns

        from geneva.runners.ray.pipeline import run_ray_add_column

        # Use table-specific checkpoint store
        checkpoint_store = table_ref.open_checkpoint_store()
        run_ray_add_column(
            table_ref,
            input_columns,
            {col_name: udf},
            checkpoint_store=checkpoint_store,
            read_version=read_version,
            job_id=job_id,
            concurrency=concurrency,
            checkpoint_size=checkpoint_size,
            task_shuffle_diversity=task_shuffle_diversity,
            commit_granularity=commit_granularity,
            where=where,
            job_tracker=job_tracker,
            **kwargs,
        )
        if job_id:
            hist.set_completed(job_id)
    except Exception as e:
        _LOG.exception("Error running Ray add column operation")
        if job_id:
            hist.set_failed(job_id, str(e))
        raise e


def _materialize_read_columns(columns: list[str]) -> list[str]:
    """Return the minimal set of columns to read, preserving dotted paths.

    LanceDB can project struct subfields directly (e.g., "info.left"), so we keep
    dotted paths instead of expanding to the parent struct column. We only de-dupe
    exact column strings while preserving order.
    """

    seen = set()
    physical: list[str] = []
    for col in columns:
        if col in seen:
            continue
        seen.add(col)
        physical.append(col)
    return physical


def run_ray_add_column(
    table_ref: TableReference,
    columns: list[str] | None,
    transforms: dict[str, UDF],
    checkpoint_store: CheckpointStore | None = None,
    *,
    read_version: int | None = None,
    job_id: str | None = None,
    concurrency: int = 8,
    batch_size: int | None = None,
    checkpoint_size: int | None = None,
    task_shuffle_diversity: int | None = None,
    commit_granularity: int | None = None,
    where: str | None = None,
    job_tracker=None,
    **kwargs,
) -> None:
    # prepare job parameters
    checkpoint_size = resolve_batch_size(
        batch_size=batch_size,
        checkpoint_size=checkpoint_size,
    )

    config = JobConfig.get().with_overrides(
        batch_size=checkpoint_size,
        task_shuffle_diversity=task_shuffle_diversity,
        commit_granularity=commit_granularity,
    )

    checkpoint_store = checkpoint_store or config.make_checkpoint_store()

    # Create error store from table connection
    db = table_ref.open_db()
    error_store = _make_error_store(db)

    table = table_ref.open()
    read_version = _resolve_read_version(table, read_version)
    uri = table.to_lance().uri

    # Re‑validate UDF inputs against the schema we will actually read.
    # This narrows the window for concurrent schema changes that could otherwise
    # surface as late, opaque runtime errors.
    schema_for_validation = _schema_for_validation(table, read_version)
    for udf in transforms.values():
        cols_for_udf = columns if columns is not None else udf.input_columns
        udf.validate_against_schema(schema_for_validation, cols_for_udf)

    # add pre-existing col if carrying previous values forward
    carry_forward_cols = list(set(transforms.keys()) & set(table.schema.names))
    _LOG.debug(f"carry_forward_cols {carry_forward_cols}")
    # this copy is necessary because the array extending updates inplace and this
    # columns array is directly referenced by the udf instance earlier
    cols = table.schema.names.copy() if columns is None else columns.copy()
    cols = _materialize_read_columns(cols)
    for cfcol in carry_forward_cols:
        # only append if cf col is not in col list already
        if cfcol not in cols:
            cols.append(cfcol)

    # Respect backfill's batch_size override by passing it into the task.
    map_task = BackfillUDFTask(
        udfs=transforms,
        where=where,
        override_batch_size=config.batch_size,
    )

    plan, pipeline_args = plan_read(
        uri,
        table_ref,
        cols,
        batch_size=config.batch_size,
        read_version=read_version,
        task_shuffle_diversity=config.task_shuffle_diversity,
        where=where,
        map_task=map_task,
        checkpoint_store=checkpoint_store,
        **kwargs,
    )

    _LOG.info(
        f"starting backfill pipeline for {transforms} where='{where}'"
        f" with carry_forward_cols={carry_forward_cols}"
    )
    _run_column_adding_pipeline(
        map_task,
        checkpoint_store,
        error_store,
        config,
        table_ref,
        plan,
        job_id,
        concurrency,
        where=where,
        job_tracker=job_tracker,
        **pipeline_args,
    )


def _make_error_store(db: Connection) -> ErrorStore:
    return ErrorStore(db, namespace=db.system_namespace)


@attrs.define
class RayJobFuture(JobFuture):
    ray_obj_ref: ActorHandle = attrs.field()
    job_tracker: ActorHandle | None = attrs.field(default=None)
    _pbars: dict[str, TqdmType] = attrs.field(factory=dict)
    _RAY_LINE_KEY: str = "_ray_summary_line"

    def _sync_bars(self, snapshot: dict[str, dict]) -> None:
        # single line ray summary
        wa = snapshot.get(CNT_WORKERS_ACTIVE)
        wp = snapshot.get(CNT_WORKERS_PENDING)

        if wa or wp:
            bar = self._pbars.get(self._RAY_LINE_KEY)
            if bar is None:
                # text-only line, like k8s/kr bars
                bar = tqdm(total=0, bar_format="{desc} {bar:0}[{elapsed}]")
                self._pbars[self._RAY_LINE_KEY] = bar

            active_count = wa.get("n", 0) if wa else 0
            pending_count = wp.get("n", 0) if wp else 0
            label = fmt(
                "geneva | workers (active/pending): ", Colors.BRIGHT_MAGENTA, bold=True
            )
            bar.desc = (
                f"{label}({fmt_numeric(active_count)}/{fmt_pending(pending_count)})"
            )
            bar.refresh()

            # close when all are done (harmless if left open)
            if all(m and m.get("done") for m in (wa, wp)):
                bar.close()

        for name, m in snapshot.items():
            if name in {
                CNT_RAY_NODES,
                CNT_WORKERS_PENDING,
                CNT_WORKERS_ACTIVE,
            }:
                continue

            n, total, done, desc = m["n"], m["total"], m["done"], m.get("desc", name)
            bar = self._pbars.get(name)
            if bar is None:
                # Only make bars for the known core metrics (skip "fragments",
                # "writer_fragments", and other randoms)
                if name not in {
                    "rows_checkpointed",
                    "rows_ready_for_commit",
                    "rows_committed",
                }:
                    continue
                bar = tqdm(total=total, desc=fmt(desc, Colors.CYAN, bold=True))
                self._pbars[name] = bar
            bar.total = total
            bar.n = n
            bar.refresh()
            if done:
                bar.close()

    def status(self, timeout: float | None = 0.05) -> None:
        if self.job_tracker is None:
            return
        try:
            snapshot = ray.get(self.job_tracker.get_all.remote(), timeout=timeout)  # type: ignore[call-arg,arg-type]
            self._sync_bars(snapshot)  # type: ignore[arg-type]

        except ray.exceptions.GetTimeoutError:
            _LOG.debug("JobTracker not ready? skip this tick")
            return

    def done(self, timeout: float | None = None) -> bool:
        self.status()
        _LOG.debug("Waiting for Ray job %s to complete", self.ray_obj_ref)
        ready, _ = ray.wait([self.ray_obj_ref], timeout=timeout)
        done = bool(ready)

        _LOG.debug(f"Ray jobs ready to complete: {ready}")

        if done:
            # force final update of progress bars
            self.status(timeout=None)
            _LOG.debug(f"RayJobFuture complete. {done=} {ready=} {self._pbars=}")

        return done

    def result(self, timeout: float | None = None) -> Any:
        # TODO this can throw a ray.exceptions.GetTimeoutError if the task
        # does not complete in time, we should create a new exception type to
        # encapsulate Ray specifics
        self.status()
        return ray.get(self.ray_obj_ref, timeout=timeout)  # type: ignore[call-overload,arg-type]


def get_imported_packages() -> dict:
    import importlib
    import sys

    packages = {}
    for name, module in sys.modules.items():
        if module is None:
            continue
        try:
            mod = importlib.import_module(name.split(".")[0])
            version = getattr(mod, "__version__", None)
            if version:
                packages[mod.__name__] = version
        except Exception as e:
            _LOG.error(e)
            continue
    return packages


@ray.remote
def get_imported() -> dict:
    """A simple utility to return the names and versions of python packages
    installed in the current Ray worker environment."""
    return get_imported_packages()

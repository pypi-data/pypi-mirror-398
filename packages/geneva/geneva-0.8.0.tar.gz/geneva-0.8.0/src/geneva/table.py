# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import contextlib
import hashlib
import json
import logging
import platform
from collections.abc import Iterable, Iterator
from datetime import timedelta
from functools import cached_property
from typing import Any, Literal

import attrs
import lance
import lancedb
import numpy as np
import pyarrow as pa
from lancedb import AsyncConnection, connect_async
from lancedb._lancedb import MergeResult
from lancedb.common import DATA, VECTOR_COLUMN_NAME
from lancedb.index import IndexConfig
from lancedb.merge import LanceMergeInsertBuilder
from lancedb.namespace import AsyncLanceNamespaceDBConnection
from lancedb.query import LanceQueryBuilder, LanceTakeQueryBuilder
from lancedb.query import Query as LanceQuery
from lancedb.table import IndexStatistics, TableStatistics, Tags
from lancedb.table import LanceTable as LanceLocalTable
from lancedb.table import Table as LanceTable
from lancedb.types import OnBadVectorsType
from pyarrow.fs import FileSystem, LocalFileSystem

# Python 3.10 compatibility
from typing_extensions import TYPE_CHECKING, Never, Optional, override  # noqa: UP035
from yarl import URL

from geneva.checkpoint import (
    CheckpointStore,
    InMemoryCheckpointStore,
)
from geneva.db import Connection, connect
from geneva.query import (
    MATVIEW_META_BASE_VERSION,
    MATVIEW_META_VERSION,
    GenevaQueryBuilder,
)
from geneva.transformer import UDF, UDFArgType
from geneva.utils import status_updates
from geneva.utils.batch_size import resolve_batch_size

if TYPE_CHECKING:
    from lance_namespace import LanceNamespace

_LOG = logging.getLogger(__name__)

# Metadata key for tracking the last successfully refreshed source version
MATVIEW_LAST_REFRESHED_VERSION = "geneva::mv::last_refreshed_version"


def _get_last_refreshed_version(table: "Table") -> int | None:
    """Read last refreshed version from __source_row_id column metadata.

    Returns None if the table doesn't have __source_row_id column or
    if the metadata key doesn't exist (backwards compatibility).
    """
    schema = table.schema
    if "__source_row_id" not in schema.names:
        return None
    field = schema.field("__source_row_id")
    if field.metadata is None:
        return None
    version_bytes = field.metadata.get(MATVIEW_LAST_REFRESHED_VERSION.encode())
    if version_bytes is None:
        return None
    return int(version_bytes.decode())


def _set_last_refreshed_version(table: "Table", version: int) -> None:
    """Write last refreshed version to __source_row_id column metadata."""
    field = table.schema.field("__source_row_id")
    # Convert existing bytes metadata to string dict for update
    existing: dict[str, str] = {}
    if field.metadata:
        for k, v in field.metadata.items():
            key = k.decode() if isinstance(k, bytes) else k
            val = v.decode() if isinstance(v, bytes) else v
            existing[key] = val
    existing[MATVIEW_LAST_REFRESHED_VERSION] = str(version)
    table._ltbl.replace_field_metadata("__source_row_id", existing)  # type: ignore[attr-defined]


@attrs.define
class JobFuture:
    job_id: str

    def done(self, timeout: float | None = None) -> bool:
        raise NotImplementedError("JobFuture.done() must be implemented in subclasses")

    def result(self, timeout: float | None = None) -> Any:
        raise NotImplementedError(
            "JobFuture.result() must be implemented in subclasses"
        )

    def status(self, timeout: float | None = None) -> None:
        raise NotImplementedError(
            "JobFuture.status() must be implemented in subclasses"
        )


@attrs.define(order=True)
class TableReference:
    """
    Serializable reference to a Geneva Table.

    Used to pass through ray.remote calls
    """

    table_id: list[str]
    version: int | None

    db_uri: str | None

    namespace_impl: str | None = attrs.field(default=None)
    namespace_properties: dict[str, str] | None = attrs.field(default=None)
    system_namespace: list[str] | None = attrs.field(default=None)

    @property
    def table_name(self) -> str:
        """Return the table name (last element of table_id)."""
        return self.table_id[-1] if self.table_id else ""

    def open_checkpoint_store(self) -> CheckpointStore:
        """Open a Lance checkpoint store for this table."""
        try:
            # Get namespace if available
            namespace_client = self.connect_namespace()
            if namespace_client:
                from lance_namespace import DescribeTableRequest

                # For namespace tables: use location from describe_table as root
                response = namespace_client.describe_table(
                    DescribeTableRequest(id=self.table_id)
                )
                table_location = response.location
                assert table_location is not None, "Table location must be set"
                checkpoint_uri = str(URL(table_location) / "_ckp")
            else:
                # For non-namespace tables: construct from db_uri
                table_uri = str(URL(str(self.db_uri)) / f"{self.table_name}.lance")
                checkpoint_uri = str(URL(table_uri) / "_ckp")

            # Create checkpoint store with namespace support
            from geneva.checkpoint import LanceCheckpointStore

            return LanceCheckpointStore(
                checkpoint_uri,
                namespace_client=namespace_client,
                table_id=self.table_id,
            )
        except Exception:
            # Fallback to in-memory checkpoint store if Lance store fails
            return InMemoryCheckpointStore()

    def open_db(self) -> Connection:
        """Open a connection to the Lance database.
        Set read consistency interval to 0 for strongly consistent reads."""
        cp = self.open_checkpoint_store()
        interval = timedelta(0)

        if self.namespace_impl is not None:
            assert self.namespace_properties is not None, (
                "namespace_properties must be set when namespace_impl is set"
            )
            return connect(
                namespace_impl=self.namespace_impl,
                namespace_properties=self.namespace_properties,
                system_namespace=self.system_namespace,
                checkpoint=cp,
                read_consistency_interval=interval,
            )

        assert self.db_uri is not None, "db_uri must be set"
        return connect(
            self.db_uri,
            checkpoint=cp,
            read_consistency_interval=interval,
        )

    async def open_db_async(
        self,
    ) -> AsyncConnection | AsyncLanceNamespaceDBConnection:
        """Open an async connection to the Lance database.
        This uses native lancedb AsyncConnection and doesn't support checkpoint store.
        Currently used by JobTracker only.
        """
        if namespace := self.connect_namespace():
            return AsyncLanceNamespaceDBConnection(
                namespace,
                read_consistency_interval=timedelta(0),
            )

        assert self.db_uri is not None, "db_uri must be set"
        return await connect_async(
            self.db_uri,
            read_consistency_interval=timedelta(0),
        )

    def open(self) -> "Table":
        # Extract namespace from table_id (everything except the last element)
        namespace = self.table_id[:-1] if len(self.table_id) > 1 else []
        return self.open_db().open_table(
            self.table_name, version=self.version, namespace=namespace
        )

    def connect_namespace(self) -> Optional["LanceNamespace"]:
        """Connect using the Lance namespace if configured"""
        if self.namespace_impl and self.namespace_properties:
            from lance_namespace import connect as namespace_connect

            return namespace_connect(self.namespace_impl, self.namespace_properties)
        return None


class Table(LanceTable):
    """Table in Geneva.

    A Table is a Lance dataset
    """

    def __init__(
        self,
        conn: Connection,
        name: str,
        *,
        namespace: list[str] | None = None,
        version: int | None = None,
        storage_options: dict[str, str] | None = None,
        index_cache_size: int | None = None,
        **kwargs,
    ) -> None:
        self._conn_uri = conn.uri
        self._name = name

        if namespace is None:
            namespace = []
        self._namespace = namespace
        self._table_id = namespace + [name]

        self._conn = conn

        self._uri = self._get_table_uri(conn, name)

        self._version: int | None = version
        self._index_cache_size = index_cache_size
        self._storage_options = storage_options

        # Load table
        self._ltbl  # noqa

    def __repr__(self) -> str:
        return f"<Table {self._table_id}>"

    # TODO: This annotation sucks
    def __reduce__(self):  # noqa: ANN204
        return (self.__class__, (self._conn, self._name))

    def get_reference(self) -> TableReference:
        return TableReference(
            table_id=self._table_id,
            version=self._version,
            db_uri=self._conn.uri,
            namespace_impl=self._conn.namespace_impl,
            namespace_properties=self._conn.namespace_properties,
            system_namespace=self._conn.system_namespace,
        )

    def get_fragments(self) -> list[lance.LanceFragment]:
        return self.to_lance().get_fragments()

    @cached_property
    def _ltbl(self) -> lancedb.table.Table:
        inner = self._conn._connect

        # remote db, open table directly
        if self._conn_uri.startswith("db://"):
            tbl = inner.open_table(self._name, namespace=self._namespace)
        else:
            _LOG.debug(
                f"opening table {self._table_id} {self.uri=} {type(self)=} {inner=} "
            )
            tbl = inner.open_table(self.name, namespace=self._namespace)

        # Check out the specified version regardless of database type
        if self._version:
            tbl.checkout(self._version)
        return tbl

    @property
    def name(self) -> str:
        """Get the name of the table."""
        return self._name

    @property
    def version(self) -> int:
        """Get the current version of the table"""
        return self._ltbl.version

    @property
    def schema(self) -> pa.Schema:
        """The Arrow Schema of the Table."""
        return self._ltbl.schema

    @property
    def uri(self) -> str:
        return self._uri

    @property
    def embedding_functions(self) -> Never:
        raise NotImplementedError("Embedding functions are not supported.")

    def add(
        self,
        data,
        mode: str = "append",
        on_bad_vectors: str = "error",
        fill_value: float = 0.0,
    ) -> None:
        self._ltbl.add(
            data,
            mode=mode,  # type: ignore[arg-type]
            on_bad_vectors=on_bad_vectors,  # type: ignore[arg-type]
            fill_value=fill_value,
        )

    def checkout(self, version: int) -> None:
        self._version = version
        self._ltbl.checkout(version)

    def checkout_latest(self) -> None:
        self._ltbl.checkout_latest()

    def add_columns(
        self, transforms: dict[str, str | UDF | tuple[UDF, list[str]]], *args, **kwargs
    ) -> None:
        """
        Add columns or UDF-based columns to the Geneva table.

        For UDF columns, this method validates that:
        - All input columns exist in the table schema
        - Column types are compatible with UDF type annotations (if present)
        - RecordBatch UDFs do not have input_columns defined

        This early validation helps catch configuration errors before job execution.

        Parameters
        ----------
        transforms : dict[str, str | UDF | tuple[UDF, list[str]]]
            The key is the column name to add and the value is a
            specification of the column type/value.

            * If the spec is a string, it is expected to be a datafusion
              sql expression. (e.g "cast(null as string)")
            * If the spec is a UDF, a virtual column is added with input
              columns inferred from the UDF's argument names.
            * If the spec is a tuple, the first element is a UDF and the
              second element is a list of input column names.

        Raises
        ------
        ValueError
            If UDF validation fails (missing columns, type mismatches, etc.)

        Warns
        -----
        UserWarning
            If type validation is skipped due to missing type annotations

        Examples
        --------
        >>> @udf(data_type=pa.int32())
        ... def double(a: int) -> int:
        ...     return a * 2
        >>> table.add_columns({"doubled": double})  # Validates 'a' column exists

        """
        # handle basic columns
        basic_cols = {k: v for k, v in transforms.items() if isinstance(v, str)}
        if len(basic_cols) > 0:
            self._ltbl.add_columns(basic_cols, *args)

        # handle UDF virtual columns
        udf_cols = {k: v for k, v in transforms.items() if not isinstance(v, str)}
        for k, v in udf_cols.items():
            if isinstance(v, UDF):
                # infer column names from udf arguments
                udf = v
                self._add_virtual_columns(
                    {k: udf}, *args, input_columns=udf.input_columns, **kwargs
                )
            else:
                # explicitly specify input columns
                (udf, cols) = v
                self._add_virtual_columns({k: udf}, *args, input_columns=cols, **kwargs)

    def _add_virtual_columns(
        self,
        mapping: dict[str, UDF],  # this breaks the non udf mapping
        *args,
        input_columns: list[str] | None = None,
        **kwargs,
    ) -> None:
        """
        This is an internal method and not intended to be called directly.

        Add udf based virtual columns to the Geneva table.
        """

        if len(mapping) != 1:
            raise ValueError("Only one UDF is supported for now.")

        _LOG.info("Adding column: udf=%s", mapping)
        col_name = next(iter(mapping))
        udf = mapping[col_name]

        if not isinstance(udf, UDF):
            # Stateful udfs are implemenated as Callable classses, and look
            # like partial functions here.  Instantiate to get the return
            # data_type annotations.
            udf = udf()

        # Validate input columns exist in table schema before adding the column
        self._validate_udf_input_columns(udf, input_columns)

        # Check for circular dependencies before adding the column
        cols_to_check = (
            input_columns if input_columns is not None else udf.input_columns
        )
        if (
            udf.arg_type != UDFArgType.RECORD_BATCH
            and cols_to_check
            and col_name in cols_to_check
        ):
            raise ValueError(
                f"UDF output column {col_name} is not allowed to be in"
                f" input {cols_to_check}"
            )

        self._ltbl.add_columns(pa.field(col_name, udf.data_type))
        self._configure_computed_column(col_name, udf, input_columns)

    def _validate_udf_input_columns(
        self, udf: UDF, input_columns: list[str] | None
    ) -> None:
        """
        Validate that UDF input columns exist in the table schema.

        This method delegates to the UDF's validate_against_schema() method
        for consolidated validation logic.

        Parameters
        ----------
        udf: UDF
            The UDF to validate
        input_columns: list[str] | None
            The input column names to validate

        Raises
        ------
        ValueError: If input columns don't exist in table schema or have type mismatches
        """
        # Delegate to UDF's consolidated validation method
        udf.validate_against_schema(self._ltbl.schema, input_columns)

    def refresh(
        self,
        *,
        where: str | None = None,
        src_version: int | None = None,
        max_rows_per_fragment: int | None = None,
        **kwargs,
    ) -> None:
        """
        Refresh the specified materialized view.

        Parameters
        ----------
        where: str | None
            TODO: sql expression filter used to only backfill selected rows
        src_version: int | None
            Optional source table version to refresh from. If None (default),
            uses the latest version of the source table.
        max_rows_per_fragment: int | None
            Optional maximum number of rows per destination fragment when adding
            placeholder rows for new source data. If None, uses LanceDB's default
            (1 million rows). Use smaller values to control fragment granularity.

        Raises
        ------
        RuntimeError
            If attempting to refresh to a different version without stable row IDs
            enabled on the source table. This is because compaction may have
            invalidated the __source_row_id values, breaking incremental refresh.
        """
        if where:
            raise NotImplementedError(
                "where clauses on materialized view refresh not implemented yet."
            )

        # Check if source table has stable row IDs and validate version compatibility
        schema = self.to_arrow().schema
        metadata = schema.metadata or {}

        # Get MV format version from metadata
        # Version 1: fragment+offset encoding, no stable row IDs
        # Version 2: stable row IDs enabled
        mv_version_bytes = metadata.get(MATVIEW_META_VERSION.encode(), b"1")
        mv_version = int(mv_version_bytes.decode())
        has_stable_row_ids = mv_version >= 2

        # Get the base version (version when MV was created)
        base_version_str = metadata.get(MATVIEW_META_BASE_VERSION.encode())
        # If no base version metadata, assume it's safe to proceed
        # (for backwards compatibility with MVs created before this feature)
        base_version = int(base_version_str.decode()) if base_version_str else None

        # Resolve src_version to actual version number if None (implicit latest)
        if src_version is None:
            # Get the source table to find its latest version
            from geneva.query import MATVIEW_META_BASE_DBURI, MATVIEW_META_BASE_TABLE

            source_table_name = metadata.get(MATVIEW_META_BASE_TABLE.encode())
            source_db_uri = metadata.get(MATVIEW_META_BASE_DBURI.encode())

            if source_table_name and source_db_uri:
                # Check if source is in the same database
                if source_db_uri.decode() == self._conn._uri:
                    # Same database - reuse connection
                    source_conn = self._conn
                else:
                    # Different database - create new connection
                    source_conn = connect(source_db_uri.decode())
                source_table = source_conn.open_table(source_table_name.decode())
                src_version = source_table.version

        # Validate: if no stable row IDs and src_version differs from base, fail
        if (
            not has_stable_row_ids
            and base_version is not None
            and src_version is not None
            and src_version != base_version
        ):
            raise RuntimeError(
                f"Cannot refresh materialized view to version {src_version} "
                "because the source table does not have stable row IDs "
                f"enabled.\n\n"
                f"This materialized view was created from source version "
                f"{base_version}. "
                "Without stable row IDs, incremental refresh is only supported "
                "when refreshing to the SAME version it was created from.\n\n"
                "This limitation exists because compaction operations may have "
                "changed the physical row IDs between versions, which would "
                "break the materialized view's ability to track source rows.\n\n"
                "To enable refresh across all versions, recreate the source "
                "table with stable row IDs:\n"
                "  db.create_table(\n"
                "      name='table_name',\n"
                "      data=data,\n"
                "      storage_options={'new_table_enable_stable_row_ids': True}\n"
                "  )"
            )

        # Note: backwards refresh (point-in-time refresh to older versions) is now
        # supported when stable row IDs are enabled. The actual rollback logic
        # (deleting rows not in the target version) is handled in run_ray_copy_table.

        from geneva.runners.ray.pipeline import run_ray_copy_table

        # Use table-specific checkpoint store
        table_ref = self.get_reference()
        checkpoint_store = table_ref.open_checkpoint_store()
        run_ray_copy_table(
            table_ref,
            self._conn._packager,
            checkpoint_store,
            src_version=src_version,
            max_rows_per_fragment=max_rows_per_fragment,
        )

        # Update last refreshed version in metadata
        if src_version is not None:
            _set_last_refreshed_version(self, src_version)

        self.checkout_latest()

    def backfill_async(
        self,
        col_name: str,
        *,
        udf: UDF | None = None,
        where: str | None = None,
        _enable_job_tracker_saves: bool = True,
        **kwargs,
    ) -> JobFuture:
        """
        Backfills the specified column asynchronously.

        Returns job future. Call .result() to wait for completion.

        Parameters
        ----------
        col_name: str
            Target column name to backfill
        udf: UDF | None
            Optionally override the UDF used to backfill the column.
        where: str | None
            SQL expression filter used select rows to apply backfills.
        concurrency: int
            (default = 8) This controls the number of processes that tasks run
            concurrently. For max throughput, ideally this is larger than the number
            of nodes in the k8s cluster.   This is the number of Ray actor processes
            are started.
        intra_applier_concurrency: int
            (default = 1) This controls the number of threads used to execute tasks
            within a process. Multiplying this times `concurrency` roughly corresponds
            to the number of cpu's being used.
        commit_granularity: int | None
            (default = 64) Show a partial result everytime this number of fragments
            are completed. If None, the entire result is committed at once.
        read_version: int | None
            (default = None) The version of the table to read from.  If None, the
            latest version is used.
        task_shuffle_diversity: int | None
            (default = 8) ??
        batch_size: int | None (deprecated)
            (default = 10240) Legacy alias for checkpoint_size. Prefer checkpoint_size.
        checkpoint_size: int | None
            The max number of rows per checkpoint.
            This influences how often progress and proof of life is presented.
        task_size: int | None
            The max number of rows read per concurrent worker task. This increases
            the parallelism possible with a job. (Not implemented yet).
        num_frags: int | None
            (default = None) The number of table fragments to process.  If None,
            process all fragments.
        _enable_job_tracker_saves: bool
            (default = False) Experimentally enable persistence of job metrics to the
            database. When disabled, metrics are tracked in-memory only.
        """

        from geneva.runners.ray.pipeline import (
            dispatch_run_ray_add_column,
            validate_backfill_args,
        )

        self._normalize_backfill_batch_kwargs(kwargs)

        read_version = kwargs.get("read_version")
        if read_version is None:
            read_version = self.version
            kwargs["read_version"] = read_version

        validate_backfill_args(self, col_name, udf, read_version=read_version)

        fut = dispatch_run_ray_add_column(
            self.get_reference(),
            col_name,
            udf=udf,
            where=where,
            enable_job_tracker_saves=_enable_job_tracker_saves,
            **kwargs,
        )
        return fut

    def backfill(
        self,
        col_name,
        *,
        udf: UDF | None = None,
        where: str | None = None,
        concurrency: int = 8,
        intra_applier_concurrency: int = 1,
        refresh_status_secs: float = 2.0,
        _enable_job_tracker_saves: bool = True,
        **kwargs,
    ) -> str:
        """
        Backfills the specified column.

        Returns job_id string

        Parameters
        ----------
        col_name: str
            Target column name to backfill
        udf: UDF | None
            Optionally override the UDF used to backfill the column.
        where: str | None
            SQL expression filter used select rows to apply backfills.
        concurrency: int
            (default = 8) This controls the number of processes that tasks run
            concurrently. For max throughput, ideally this is larger than the number
            of nodes in the k8s cluster.   This is the number of Ray actor processes
            are started.
        intra_applier_concurrency: int
            (default = 1) This controls the number of threads used to execute tasks
            within a process. Multiplying this times `concurrency` roughly corresponds
            to the number of cpu's being used.
        commit_granularity: int | None
            (default = 64) Show a partial result everytime this number of fragments
            are completed. If None, the entire result is committed at once.
        read_version: int | None
            (default = None) The version of the table to read from.  If None, the
            latest version is used.
        task_shuffle_diversity: int | None
            (default = 8) ??
        batch_size: int | None (deprecated)
            (default = 100) Legacy alias for checkpoint_size. Prefer checkpoint_size.
            If 0, the batch will be the total number of rows from a fragment.
        checkpoint_size: int | None
            The max number of rows per checkpoint.
            This influences how often progress and proof of life is presented.
        task_size: int | None
            The max number of rows read per concurrent worker task. This increases
            the parallelism possible with a job. (Not implemented yet).
        num_frags: int | None
            (default = None) The number of table fragments to process.  If None,
            process all fragments.
        _enable_job_tracker_saves: bool
            (default = False) Experimentally enable persistence of job metrics to the
            database. When disabled, metrics are tracked in-memory only.
        """
        # Input validation
        from geneva.runners.ray.pipeline import validate_backfill_args

        self._normalize_backfill_batch_kwargs(kwargs)

        read_version = kwargs.get("read_version")
        if read_version is None:
            read_version = self.version
            kwargs["read_version"] = read_version

        validate_backfill_args(self, col_name, udf, read_version=read_version)

        # get cluster status
        from geneva.runners.ray.raycluster import ClusterStatus

        cs = ClusterStatus()
        try:
            with status_updates(cs.get_status, refresh_status_secs):
                # Kick off the job
                fut = self.backfill_async(
                    col_name,
                    udf=udf,
                    where=where,
                    concurrency=concurrency,
                    intra_applier_concurrency=intra_applier_concurrency,
                    _enable_job_tracker_saves=_enable_job_tracker_saves,
                    **kwargs,
                )

            while not fut.done(timeout=refresh_status_secs):
                # wait for the backfill to complete, updating statuses
                cs.get_status()
                fut.status()

            cs.get_status()
            fut.status()

            # Check for errors - this will raise if the job failed
            fut.result()

            # updates came from an external writer, so get the latest version.
            self._ltbl.checkout_latest()
            return fut.job_id
        finally:
            with contextlib.suppress(Exception):
                cs.close()

    @staticmethod
    def _normalize_backfill_batch_kwargs(kwargs: dict[str, Any]) -> None:
        """Normalize batch-size kwargs, enforcing a single effective value."""
        checkpoint_size = kwargs.pop("checkpoint_size", None)
        task_size = kwargs.pop("task_size", None)
        if task_size is not None:
            _LOG.warning(
                "task_size is not supported for backfill; ignoring value %s", task_size
            )

        batch_size = kwargs.pop("batch_size", None)

        resolved = resolve_batch_size(
            batch_size=batch_size,
            checkpoint_size=checkpoint_size,
        )

        kwargs["checkpoint_size"] = resolved

    def alter_columns(self, *alterations: dict[str, Any], **kwargs) -> None:
        """
        Alter columns in the table.  This can change the computed columns' udf

        Parameters
        ----------
        alterations:  Iterable[dict[str, Any]]
            This is a list of alterations to apply to the table.


        Example:
            >>> alter_columns({ "path": "col1", "udf": col1_udf_v2, })`
            >>> t.alter_columns(b
            ...     { "path": "col1", "udf": col1_udf_v2, },
            ...     { "path": "col2", "udf": col2_udf})

        """
        basic_column_alterations = []
        for alter in alterations:
            if "path" not in alter:
                raise ValueError("path is required to alter computed column's udf")

            if "virtual_column" in alter:  # deprecated
                udf = alter.get("virtual_column")
                if not isinstance(udf, UDF):
                    raise ValueError("virtual_column must be a UDF")
                _LOG.warning(
                    "alter_columns 'virtual_column' is deprecated, use 'udf' instead."
                )
            elif "udf" in alter:
                udf = alter.get("udf")
                if not isinstance(udf, UDF):
                    raise ValueError("udf must be a UDF")
            else:
                basic_column_alterations.append(alter)
                continue

            col_name = alter["path"]

            input_cols = alter.get("input_columns", None)
            if input_cols is None:
                input_cols = udf.input_columns

            self._configure_computed_column(col_name, udf, input_cols)

        if len(basic_column_alterations) > 0:
            self._ltbl.alter_columns(*basic_column_alterations)

    def _configure_computed_column(
        self,
        col_name: str,
        udf: UDF,
        input_cols: list[str] | None,
    ) -> None:
        """
        Configure a column to be a computed column for the given UDF.

        This procedure includes:
        - Packaging the UDF
        - Uploading the UDF to the dataset
        - Updating the field metadata to include the UDF information

        Note that the column should already exist on the table.
        """
        # record batch udf's don't specify inputs
        if (
            udf.arg_type != UDFArgType.RECORD_BATCH
            and udf.input_columns
            and col_name in udf.input_columns
        ):
            raise ValueError(
                f"UDF output column {col_name} is not allowed to be in"
                f" input {udf.input_columns}"
            )

        udf_spec = self._conn._packager.marshal(udf, table_ref=self.get_reference())

        # upload the UDF to the dataset URL
        if not isinstance(self._ltbl, LanceLocalTable):
            raise TypeError(
                "adding udf column is currently only supported for local tables"
            )

        # upload the packaged UDF to some location inside the dataset:
        ds = self.to_lance()
        fs, root_uri = FileSystem.from_uri(ds.uri)
        checksum = hashlib.sha256(udf_spec.udf_payload).hexdigest()
        udf_location = f"_udfs/{checksum}"

        # TODO -- only upload the UDF if it doesn't exist
        if isinstance(fs, LocalFileSystem):
            # Object storage filesystems like GCS and S3 will create the directory
            # automatically, but local filesystem will not, so we create explicitly
            fs.create_dir(f"{root_uri}/_udfs")

        with fs.open_output_stream(f"{root_uri}/{udf_location}") as f:
            f.write(udf_spec.udf_payload)

        # TODO rename this from virtual_column to computed column
        field_metadata = udf.field_metadata | {
            "virtual_column": "true",
            "virtual_column.udf_backend": udf_spec.backend,
            "virtual_column.udf_name": udf_spec.name,
            "virtual_column.udf": "_udfs/" + checksum,
            "virtual_column.udf_inputs": json.dumps(input_cols),
            "virtual_column.platform.system": platform.system(),
            "virtual_column.platform.arch": platform.machine(),
            "virtual_column.platform.python_version": platform.python_version(),
        }

        # Add the column metadata:
        self._ltbl.replace_field_metadata(col_name, field_metadata)

    def create_index(
        self,
        metric: str = "L2",
        num_partitions: int | None = None,
        num_sub_vectors: int | None = None,
        vector_column_name: str = VECTOR_COLUMN_NAME,
        replace: bool = True,
        accelerator=None,
        index_cache_size=None,
        *,
        index_type: Literal[
            "IVF_FLAT",
            "IVF_PQ",
            "IVF_HNSW_SQ",
            "IVF_HNSW_PQ",
        ] = "IVF_PQ",
        num_bits: int = 8,
        max_iterations: int = 50,
        sample_rate: int = 256,
        m: int = 20,
        ef_construction: int = 300,
    ) -> None:
        """Create Vector Index"""
        self._ltbl.create_index(
            metric,
            num_partitions or 256,
            num_sub_vectors or 96,
            vector_column_name,
            replace,
            accelerator,
            index_cache_size,
            index_type=index_type,
            num_bits=num_bits,
            max_iterations=max_iterations,
            sample_rate=sample_rate,
            m=m,
            ef_construction=ef_construction,
        )

    @override
    def create_fts_index(
        self,
        field_names: str | list[str],
        *,
        ordering_field_names: str | list[str] | None = None,
        replace: bool = False,
        writer_heap_size: int | None = None,
        tokenizer_name: str | None = None,
        with_position: bool = True,
        base_tokenizer: Literal["simple", "raw", "whitespace"] = "simple",
        language: str = "English",
        max_token_length: int | None = 40,
        lower_case: bool = True,
        stem: bool = False,
        remove_stop_words: bool = False,
        ascii_folding: bool = False,
        **_kwargs,
    ) -> None:
        self._ltbl.create_fts_index(
            field_names,
            ordering_field_names=ordering_field_names,
            replace=replace,
            writer_heap_size=writer_heap_size,
            tokenizer_name=tokenizer_name,
            with_position=with_position,
            base_tokenizer=base_tokenizer,
            language=language,
            max_token_length=max_token_length,
            lower_case=lower_case,
            stem=stem,
            remove_stop_words=remove_stop_words,
            ascii_folding=ascii_folding,
            use_tantivy=False,
        )

    @override
    def create_scalar_index(
        self,
        column: str,
        *,
        replace: bool = True,
        index_type: Literal["BTREE", "BITMAP", "LABEL_LIST"] = "BTREE",
    ) -> None:
        self._ltbl.create_scalar_index(
            column,
            replace=replace,
            index_type=index_type,
        )

    @override
    def _do_merge(
        self,
        merge: LanceMergeInsertBuilder,
        new_data: DATA,
        on_bad_vectors: OnBadVectorsType,
        fill_value: float,
    ) -> MergeResult:
        return self._ltbl._do_merge(merge, new_data, on_bad_vectors, fill_value)

    @override
    def _execute_query(
        self,
        query: LanceQuery,
        batch_size: int | None = None,
    ) -> pa.RecordBatchReader:
        return self._ltbl._execute_query(query, batch_size=batch_size)

    def list_versions(self) -> list[dict[str, Any]]:
        return self._ltbl.list_versions()

    @override
    def cleanup_old_versions(
        self,
        older_than: timedelta | None = None,
        *,
        delete_unverified=False,
    ) -> Any:  # lance.CleanupStats not available in type stubs
        return self._ltbl.cleanup_old_versions(
            older_than,
            delete_unverified=delete_unverified,
        )

    def to_batches(self, batch_size: int | None = None) -> Iterator[pa.RecordBatch]:
        from .query import Query

        if isinstance(self._ltbl, Query):
            return self._ltbl.to_batches(batch_size)  # type: ignore[attr-defined]
        return self.to_lance().to_batches(batch_size)  # type: ignore[arg-type]

    """This is the signature for the standard LanceDB table.search call"""

    def search(  # type: ignore[override]
        self,
        query: list | pa.Array | pa.ChunkedArray | np.ndarray | None = None,
        vector_column_name: str | None = None,
        query_type: Literal["vector", "fts", "hybrid", "auto"] = "auto",
        ordering_field_name: str | None = None,
        fts_columns: str | list[str] | None = None,
    ) -> GenevaQueryBuilder | LanceQueryBuilder:
        if query is None:
            return GenevaQueryBuilder(self)
        else:
            return self._ltbl.search(
                query, vector_column_name, query_type, ordering_field_name, fts_columns
            )

    @override
    def drop_columns(self, columns: Iterable[str]) -> None:
        self._ltbl.drop_columns(columns)

    @override
    def to_arrow(self) -> pa.Table:
        return self._ltbl.to_arrow()

    @override
    def count_rows(self, filter: str | None = None) -> int:
        return self._ltbl.count_rows(filter)

    @override
    def update(
        self,
        where: str | None = None,
        values: dict | None = None,
        *,
        values_sql: dict[str, str] | None = None,
    ) -> None:
        self._ltbl.update(where, values, values_sql=values_sql)

    @override
    def delete(self, where: str) -> None:
        self._ltbl.delete(where)

    @override
    def list_indices(self) -> Iterable[IndexConfig]:
        return self._ltbl.list_indices()

    @override
    def index_stats(self, index_name: str) -> IndexStatistics | None:
        return self._ltbl.index_stats(index_name)

    @override
    def optimize(
        self,
        *,
        cleanup_older_than: timedelta | None = None,
        delete_unverified: bool = False,
    ) -> None:
        return self._ltbl.optimize(
            cleanup_older_than=cleanup_older_than,
            delete_unverified=delete_unverified,
        )

    @override
    def compact_files(self) -> None:
        self._ltbl.compact_files()

    @override
    def restore(self, *args, **kwargs) -> None:
        self._ltbl.restore(*args, **kwargs)

    # TODO: This annotation sucks
    # NOTE: When using blob columns with stable row IDs enabled (e.g., for
    # materialized views), pylance >= 1.1.0b2 is required. Earlier versions
    # have a bug where take_blobs fails on fragments created via DataReplacement.
    def take_blobs(self, indices: list[int] | pa.Array, column: str):  # noqa: ANN201
        return self.to_lance().take_blobs(blob_column=column, indices=indices)

    def to_lance(self) -> lance.LanceDataset:
        return self._ltbl.to_lance()  # type: ignore[attr-defined]

    def uses_v2_manifest_paths(self) -> bool:
        return self._ltbl.uses_v2_manifest_paths()

    def migrate_v2_manifest_paths(self) -> None:
        return self._ltbl.migrate_v2_manifest_paths()

    def _analyze_plan(self, query: LanceQuery) -> str:
        return self._ltbl._analyze_plan(query)

    def _explain_plan(self, query: LanceQuery, verbose: bool | None = False) -> str:
        return self._ltbl._explain_plan(query, verbose=verbose)

    def stats(self) -> TableStatistics:
        return self._ltbl.stats()

    @property
    def tags(self) -> Tags:
        return self._ltbl.tags

    def take_offsets(self, offsets: list[int]) -> LanceTakeQueryBuilder:
        return self._ltbl.take_offsets(offsets)

    def take_row_ids(self, row_ids: list[int]) -> LanceTakeQueryBuilder:
        return self._ltbl.take_row_ids(row_ids)

    def get_errors(
        self,
        job_id: str | None = None,
        column_name: str | None = None,
        error_type: str | None = None,
    ) -> list[Any]:
        """Get error records for this table.

        Parameters
        ----------
        job_id : str, optional
            Filter errors by job ID
        column_name : str, optional
            Filter errors by column name
        error_type : str, optional
            Filter errors by exception type

        Returns
        -------
        list[ErrorRecord]
            List of error records matching the filters

        Examples
        --------
        >>> # Get all errors for this table
        >>> errors = table.get_errors()
        >>>
        >>> # Get errors for a specific job
        >>> errors = table.get_errors(job_id="abc123")
        >>>
        >>> # Get errors for a specific column
        >>> errors = table.get_errors(column_name="my_column")
        """
        from geneva.debug.error_store import ErrorStore

        error_store = ErrorStore(self._conn, namespace=self._conn.system_namespace)
        return error_store.get_errors(
            job_id=job_id,
            table_name=self._name,
            column_name=column_name,
            error_type=error_type,
        )

    def get_failed_row_addresses(self, job_id: str, column_name: str) -> list[int]:
        """Get row addresses for all failed rows in a job.

        Parameters
        ----------
        job_id : str
            Job ID to query
        column_name : str
            Column name to filter by

        Returns
        -------
        list[int]
            List of row addresses that failed

        Examples
        --------
        >>> # Get failed row addresses
        >>> failed_rows = table.get_failed_row_addresses(
        ...     job_id="abc123", column_name="my_col"
        ... )
        >>>
        >>> # Retry processing only failed rows
        >>> row_ids = ','.join(map(str, failed_rows))
        >>> table.backfill("my_col", where=f"_rowaddr IN ({row_ids})")
        """
        from geneva.debug.error_store import ErrorStore

        error_store = ErrorStore(self._conn, namespace=self._conn.system_namespace)
        return error_store.get_failed_row_addresses(
            job_id=job_id, column_name=column_name
        )

    @override
    def _output_schema(self, query: LanceQuery) -> pa.Schema:
        return self._ltbl._output_schema(query)

    def _get_table_uri(self, conn: Connection, name: str) -> str:
        """Get the table URI from the namespace or connection URI"""
        # For namespace connections, get the actual table location from describe_table
        if conn.namespace_impl is not None and conn.namespace_properties is not None:
            # Get the actual table location from the namespace
            from lance_namespace import DescribeTableRequest

            ns = conn.namespace_client
            if ns is not None:
                response = ns.describe_table(DescribeTableRequest(id=self._table_id))
                if response.location is None:
                    raise ValueError(
                        f"Table location is None for table {self._table_id}"
                    )
                return response.location
            else:
                return f"{name}.lance"
        else:
            # For non-namespace connections, construct URI from base path
            base_uri = URL(conn.uri)
            return str(base_uri / f"{name}.lance")

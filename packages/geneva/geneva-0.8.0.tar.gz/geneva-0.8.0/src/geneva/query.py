# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

import pyarrow as pa
from lancedb.query import LanceEmptyQueryBuilder, Query
from lancedb.rerankers.base import Reranker
from numpy.random import default_rng
from pydantic import BaseModel

# Self / override is not available in python 3.10
from typing_extensions import Self, override  # noqa: UP035

from geneva.db import Connection, has_stable_row_ids
from geneva.packager import UDFPackager, UDFSpec
from geneva.transformer import BACKFILL_SELECTED, UDF


def _resolve_field(schema: pa.Schema, name: str) -> pa.Field:
    """Resolve a possibly dotted column path to a PyArrow field.

    For dotted struct paths (e.g., ``info.left``), walk the struct children and
    return a field whose name is the dotted path and whose type/nullable flag
    come from the leaf field.
    """

    if "." not in name:
        return schema.field(name)

    parts = name.split(".")
    if parts[0] not in schema.names:
        raise KeyError(f"Column {name} does not exist in schema")

    field = schema.field(parts[0])
    dtype = field.type
    nullable = field.nullable

    for part in parts[1:]:
        if not pa.types.is_struct(dtype):
            raise KeyError(f"Column {name} does not exist in schema")
        idx = dtype.get_field_index(part)
        if idx == -1:
            raise KeyError(f"Column {name} does not exist in schema")
        child_field = dtype.field(idx)
        dtype = child_field.type
        nullable = nullable or child_field.nullable

    return pa.field(name, dtype, nullable)


if TYPE_CHECKING:
    from lance import LanceDataset

    from geneva.table import Table

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.INFO)

MATVIEW_META = "geneva::view::"
MATVIEW_META_QUERY = f"{MATVIEW_META}query"
MATVIEW_META_BASE_TABLE = f"{MATVIEW_META}base_table"
MATVIEW_META_BASE_DBURI = f"{MATVIEW_META}base_table_db_uri"
MATVIEW_META_BASE_VERSION = f"{MATVIEW_META}base_table_version"
MATVIEW_META_VERSION = f"{MATVIEW_META}version"


class PydanticUDFSpec(BaseModel):
    name: str
    backend: str
    udf_payload: bytes
    runner_payload: bytes | None

    @classmethod
    def from_attrs(cls, spec: UDFSpec) -> "PydanticUDFSpec":
        return PydanticUDFSpec(
            name=spec.name,
            backend=spec.backend,
            udf_payload=spec.udf_payload,
            runner_payload=spec.runner_payload,
        )

    def to_attrs(self) -> UDFSpec:
        return UDFSpec(
            name=self.name,
            backend=self.backend,
            udf_payload=self.udf_payload,
            runner_payload=self.runner_payload,
        )


class ColumnUDF(BaseModel):
    output_index: int
    output_name: str
    udf: PydanticUDFSpec


@dataclass
class ExtractedTransform:
    output_index: int
    output_name: str
    udf: UDF


class GenevaQuery(BaseModel):
    base: Query
    shuffle: bool | None = None
    shuffle_seed: int | None = None
    fragment_ids: list[int] | None = None
    with_row_address: bool | None = None
    column_udfs: list[ColumnUDF] | None = None

    def extract_column_udfs(self, packager: UDFPackager) -> list[ExtractedTransform]:
        """
        Loads a set of transforms that reflect the column_udfs and map_batches_udfs
        of the query.
        """
        transforms = []
        if self.column_udfs is not None:
            for column_udf in self.column_udfs:
                udf = packager.unmarshal(column_udf.udf.to_attrs())
                transforms.append(
                    ExtractedTransform(
                        output_index=column_udf.output_index,
                        output_name=column_udf.output_name,
                        udf=udf,
                    )
                )
        return transforms


class GenevaQueryBuilder(LanceEmptyQueryBuilder):
    """A proxy that wraps LanceQueryBuilder and adds geneva-specific functionality."""

    def __init__(self, table: "Table") -> None:
        super().__init__(table)
        self._table = table
        self._shuffle = None
        self._shuffle_seed = None
        self._fragment_ids = None
        self._with_row_address = None
        self._internal_api_enabled = False
        self._column_udfs = None
        self._with_where_as_bool_column = False

    def _internal_api_only(self) -> None:
        if not self._internal_api_enabled:
            raise ValueError(
                "This method is for internal use only and subject to change. "
                "Call enable_internal_api() first to enable."
            )

    @override
    def select(self, columns: list[str] | Mapping[str, str | UDF]) -> Self:
        """
        Select the output columns of the query.

        Parameters
        ----------
        columns: list[str] | dict[str, str] | dict[str, UDF]
            The columns to select.

            If a list of strings, each string is the name of a column to select.

            If a dictionary of strings then the key is the output name of the column
            and the value is either an SQL expression (str) or a UDF.
        """
        if isinstance(columns, dict):
            self._column_udfs = {
                key: (value, index)
                for (index, (key, value)) in enumerate(columns.items())
                if isinstance(value, UDF)
            }
            # Filter out UDFs and create a proper dict for super().select()
            filtered_columns: dict[str, str] = {
                key: str(value)  # Convert to string if needed
                for key, value in columns.items()
                if not isinstance(value, UDF)
            }
            super().select(filtered_columns)
        else:
            super().select(columns)  # type: ignore[arg-type]
        return self

    def shuffle(self, seed: int | None = None) -> Self:
        """Shuffle the rows of the table"""
        self._shuffle = True
        self._shuffle_seed = seed
        return self

    def enable_internal_api(self) -> Self:
        """
        Enable internal APIs
        WARNING: Internal APIs are subject to change
        """
        self._internal_api_enabled = True
        return self

    def with_fragments(self, fragments: list[int] | int) -> Self:
        """
        Filter the rows of the table to only include the specified fragments.
        """
        self._internal_api_only()
        self._fragment_ids = [fragments] if isinstance(fragments, int) else fragments
        return self

    def with_row_address(self) -> Self:
        """
        Include the physical row address in the result
        WARNING: INTERNAL API DETAIL
        """
        self._internal_api_only()
        self._with_row_address = True
        return self

    def with_where_as_bool_column(self) -> Self:
        """
        Include the filter selected column in the result instead of just selected rows
        """
        self._internal_api_only()
        self._with_where_as_bool_column = True
        return self

    @override
    def to_query_object(self) -> GenevaQuery:  # type: ignore
        query = super().to_query_object()
        result = GenevaQuery(
            base=query,
            shuffle=self._shuffle,
            shuffle_seed=self._shuffle_seed,
            fragment_ids=self._fragment_ids,
            with_row_address=self._with_row_address,
        )
        if self._column_udfs:
            result.column_udfs = [
                ColumnUDF(
                    output_index=index,
                    output_name=name,
                    udf=PydanticUDFSpec.from_attrs(
                        self._table._conn._packager.marshal(udf)
                    ),
                )
                for (name, (udf, index)) in self._column_udfs.items()
            ]
        return result

    @classmethod
    def from_query_object(
        cls, table: "Table", query: GenevaQuery
    ) -> "GenevaQueryBuilder":
        result = GenevaQueryBuilder(table)

        # TODO: Add from_query_object to lancedb.  For now, this will work
        # for simple (non-vector, non-fts) queries.
        if query.base.columns is not None:
            result.select(query.base.columns)
        if query.base.filter:
            result.where(query.base.filter)
        if query.base.limit:
            result.limit(query.base.limit)
        if query.base.offset:
            result.offset(query.base.offset)
        if query.base.with_row_id:
            result.with_row_id(True)

        result._shuffle = query.shuffle
        result._shuffle_seed = query.shuffle_seed
        if query.column_udfs:
            result._column_udfs = {}
            for column_udf in query.column_udfs:
                udf = table._conn._packager.unmarshal(column_udf.udf.to_attrs())
                result._column_udfs[column_udf.output_name] = (
                    udf,
                    column_udf.output_index,
                )
        result._fragment_ids = query.fragment_ids
        result._with_row_address = query.with_row_address
        result._internal_api_enabled = True
        return result

    def take_rows(self, rows: list[int]) -> pa.Table:
        query = self.to_query_object()
        return self._table.to_lance()._take_rows(rows, query.base.columns)

    def _schema_for_query(self, include_metacols: bool = True) -> pa.Schema:
        schema = self._table.schema

        base_query = super().to_query_object()

        if base_query.columns is not None:
            if isinstance(base_query.columns, list):
                fields = [_resolve_field(schema, col) for col in base_query.columns]
            else:
                fields = []
                for dest_name, expr in base_query.columns.items():
                    try:
                        field = _resolve_field(schema, expr)
                    except KeyError as e:
                        if dest_name == BACKFILL_SELECTED:
                            # HACK special case for BACKFILL_SELECTED
                            field = pa.field(dest_name, pa.bool_(), True)
                        else:
                            # TODO: Need to get output type from SQL expression
                            raise NotImplementedError(
                                f"SQL expression {expr} not yet supported"
                            ) from e

                    fields.append(pa.field(dest_name, field.type, field.nullable))

        else:
            fields = list(schema)

        if self._column_udfs is not None:
            for output_name, (udf, output_index) in self._column_udfs.items():
                fields.insert(
                    output_index,
                    pa.field(output_name, udf.data_type, metadata=udf.field_metadata),
                )

        if include_metacols and base_query.with_row_id:
            fields += [pa.field("_rowid", pa.int64())]

        if include_metacols and self._with_row_address:
            fields += [pa.field("_rowaddr", pa.int64())]

        return pa.schema(fields)

    @property
    def schema(self) -> pa.Schema:
        return self._schema_for_query()

    @override
    def to_batches(
        self, /, batch_size: int | None = None, *, timeout: timedelta | None = None
    ) -> pa.RecordBatchReader:
        schema_no_meta = self._schema_for_query(include_metacols=False)

        # Collect blob columns.
        blob_columns: dict[str, int] = {
            f.name: idx
            for idx, f in enumerate(schema_no_meta)
            if f.metadata and f.metadata.get(b"lance-encoding:blob") == b"true"
        }

        base_query = super().to_query_object()
        orig_filter = base_query.filter

        # Enforce row_id if we need blobs or where-as-column
        if blob_columns or (self._with_where_as_bool_column and orig_filter):
            base_query.with_row_id = True

        # UDF extra-column bookkeeping
        extra_columns: list[str] = []
        if self._column_udfs and base_query.columns is not None:
            # collect all needed inputs
            current_cols = (
                set(base_query.columns)
                if isinstance(base_query.columns, list)
                else set(base_query.columns.keys())
            )
            for udf, _ in self._column_udfs.values():
                for inp in udf.input_columns or []:
                    if inp not in current_cols:
                        extra_columns.append(inp)
                        current_cols.add(inp)

        # append extra_columns into the query, track their positions
        added_columns: list[int] = []
        if base_query.columns is not None and extra_columns:
            if isinstance(base_query.columns, list):
                pos = len(base_query.columns)
                for col in extra_columns:
                    added_columns.append(pos)
                    base_query.columns.append(col)
                    pos += 1
            else:
                pos = len(base_query.columns)
                for col in extra_columns:
                    added_columns.append(pos)
                    base_query.columns[col] = col
                    pos += 1

        # sanity‐check unsupported features
        if self._shuffle:
            raise NotImplementedError("Shuffle is not yet implemented")
        if base_query.vector:
            raise NotImplementedError("Vector search not yet implemented")
        if base_query.full_text_query:
            raise NotImplementedError("FTS search not yet implemented")

        dataset: LanceDataset = self._table.to_lance()
        fragments = (
            [dataset.get_fragment(fid) for fid in self._fragment_ids]
            if self._fragment_ids
            else list(dataset.get_fragments())
        )

        schema_with_meta = self._schema_for_query(include_metacols=True)

        # Fragment‐by‐fragment generator
        def gen() -> Iterator[pa.RecordBatch]:
            for frag in fragments:
                # build per‐fragment matching_ids if we’re doing where-as-column
                frag_ids: set[int] | None = None
                if self._with_where_as_bool_column and orig_filter:
                    frag_ids = set()
                    id_scan = dataset.scanner(
                        columns=["_rowid"],
                        with_row_id=True,
                        filter=orig_filter,
                        fragments=[frag],
                    )
                    for id_batch in id_scan.to_batches():
                        rowid_list = id_batch["_rowid"].to_pylist()
                        # Filter out None values and convert to ints
                        valid_ids = [int(rid) for rid in rowid_list if rid is not None]
                        frag_ids.update(valid_ids)

                # choose filter for main scan
                scan_filter = None if frag_ids is not None else orig_filter

                # run the main scan over this fragment
                main_scan = dataset.scanner(
                    columns=base_query.columns,
                    with_row_id=base_query.with_row_id,
                    with_row_address=self._with_row_address,
                    filter=scan_filter,
                    batch_size=batch_size,
                    offset=base_query.offset,
                    limit=base_query.limit,
                    fragments=[frag],
                )
                for batch in main_scan.to_batches():
                    # blob injection
                    if blob_columns:
                        rowid_list = batch["_rowid"].to_pylist()  # type: ignore[index]
                        ids = [int(rid) for rid in rowid_list if rid is not None]
                        for col_name in blob_columns:
                            if hasattr(batch, "to_pylist"):
                                batch = batch.to_pylist()  # type: ignore[attr-defined]
                            else:
                                # batch is already a list
                                pass
                            try:
                                blob_files = dataset.take_blobs(col_name, ids=ids)
                                for elem, blob in zip(batch, blob_files, strict=True):  # type: ignore[arg-type]
                                    elem[col_name] = blob  # type: ignore[index]
                            except ValueError:
                                # not blobfile? (maybe because null?) return Null.
                                for elem in batch:
                                    elem[col_name] = None  # type: ignore[index]
                    # UDFs and drop UDF-only columns
                    if self._column_udfs:
                        for col_name, (udf, insert_idx) in self._column_udfs.items():
                            arr = udf(batch)
                            if hasattr(batch, "add_column"):
                                batch = batch.add_column(  # type: ignore[attr-defined]
                                    insert_idx, pa.field(col_name, arr.type), arr
                                )
                            else:
                                # Handle case where batch is a list
                                pass
                        # remove the extra_columns we only pulled for UDF inputs
                        for drop_idx in reversed(added_columns):
                            if hasattr(batch, "remove_column"):
                                batch = batch.remove_column(  # type: ignore[attr-defined]
                                    drop_idx + len(self._column_udfs)
                                )
                            else:
                                # Handle case where batch is a list
                                pass

                    # where-as-column mask
                    if frag_ids is not None:
                        if isinstance(batch, list):
                            # blob case -- a list of dicts
                            ids = [row["_rowid"] for row in batch]
                            mask = pa.array(
                                [rid in frag_ids for rid in ids], pa.bool_()
                            )
                            for i, _row in enumerate(batch):
                                batch[i][BACKFILL_SELECTED] = mask[i]

                        else:
                            # normal case - pa.RecordBatch
                            ids = batch["_rowid"].to_pylist()
                            mask = pa.array(
                                [rid in frag_ids for rid in ids], pa.bool_()
                            )
                            batch = batch.add_column(
                                batch.num_columns,
                                pa.field(BACKFILL_SELECTED, pa.bool_()),
                                mask,
                            )

                    yield batch  # type: ignore[misc]

        if blob_columns:
            return list(gen())  # type: ignore[return-value]
        return pa.RecordBatchReader.from_batches(schema_with_meta, gen())  # type: ignore[arg-type]

    @override
    def to_arrow(self, *args, timeout: timedelta | None = None) -> pa.Table:
        return pa.Table.from_batches(self.to_batches(*args, timeout=timeout))

    @override
    def rerank(self, reranker: Reranker) -> Self:
        raise NotImplementedError("rerank is not yet implemented")

    def create_materialized_view(self, conn: Connection, view_name: str) -> "Table":
        """
        Creates a materialized view of the table.

        The materialized view will be a table that contains the result of the query.
        The view will be populated via a pipeline job.

        Parameters
        ----------
        conn: Connection
            A connection to the database to create the view in.
        view_name: str
            The name of the view to create.

        Warnings
        --------
        UserWarning
            If the source table does not have stable row IDs enabled. Without stable
            row IDs, incremental refresh is only supported when refreshing to the
            same source version. Attempting to refresh to a different version will fail.
        """
        import warnings

        # Check if source table has stable row IDs enabled
        source_lance_ds = self._table.to_lance()
        fragments = list(source_lance_ds.get_fragments())

        # Validate that source table is not empty
        if not fragments:
            raise ValueError(
                f"Cannot create materialized view from empty table "
                f"'{self._table._ltbl.name}'.\n\n"
                "Materialized views require at least one row in the source "
                "table to determine storage characteristics (such as whether "
                "stable row IDs are enabled).\n\n"
                "Please add data to the source table before creating a "
                "materialized view."
            )

        source_has_stable_row_ids = has_stable_row_ids(fragments)

        if not source_has_stable_row_ids:
            warnings.warn(
                f"Creating materialized view from table '{self._table._ltbl.name}' "
                "without stable row IDs enabled.\n\n"
                "Without stable row IDs, you can only refresh the materialized view "
                "to the SAME source version it was created from. Attempting to refresh "
                "to a different version will fail because compaction operations may "
                "have changed row IDs.\n\n"
                "For full incremental refresh support across all versions, create the "
                "source table with stable row IDs enabled:\n"
                "  db.create_table(\n"
                "      name='table_name',\n"
                "      data=data,\n"
                "      storage_options={'new_table_enable_stable_row_ids': 'true'}\n"
                "  )\n\n"
                "Note: Both 'true' (string) and True (boolean) are accepted.\n\n"
                "Stable row IDs is a Lance feature (added in 0.21.0) exposed via "
                "lancedb's new_table_enable_stable_row_ids option (added in 0.25.4b3).",
                UserWarning,
                stacklevel=2,
            )

        view_schema = self._schema_for_query(include_metacols=True)
        view_schema = view_schema.insert(0, pa.field("__is_set", pa.bool_()))
        view_schema = view_schema.insert(0, pa.field("__source_row_id", pa.int64()))

        query = self.to_query_object()

        # Capture source columns at creation time if no explicit select was used.
        # This ensures that when new columns are added to the source table,
        # the MV refresh only reads the columns that existed at creation time.
        if query.base.columns is None:
            query.base.columns = [
                n
                for n in self._table.schema.names
                if n not in ["__is_set", "__source_row_id"]
            ]

        view_schema = view_schema.with_metadata(
            {
                MATVIEW_META_QUERY: query.model_dump_json(),
                MATVIEW_META_BASE_TABLE: self._table._ltbl.name,
                MATVIEW_META_BASE_DBURI: self._table._conn_uri,
                MATVIEW_META_BASE_VERSION: str(self._table._ltbl.version),
                # Store materialized view format version.
                # Version 1: fragment+offset encoding (fragment_id << 32 | offset)
                #   - Used for v0.7.x and earlier (always)
                #   - Used for v0.8.x+ without stable row IDs
                #   - Source table does NOT have stable row IDs
                #   - Refresh only supported to same source version
                # Version 2: stable row IDs (v0.8.x+ with stable row IDs enabled)
                #   - Source table HAS stable row IDs
                #   - Refresh supported across source versions
                MATVIEW_META_VERSION: "2" if source_has_stable_row_ids else "1",
                # TODO: Add the base DB URI (should be possible
                # to get from lancedb table in future)
            }
        )

        row_ids_query = GenevaQuery(
            fragment_ids=query.fragment_ids,
            base=query.base,
        )
        row_ids_query.base.with_row_id = True
        row_ids_query.base.columns = []
        row_ids_query.column_udfs = None
        row_ids_query.with_row_address = None

        row_ids_query_builder = GenevaQueryBuilder.from_query_object(
            self._table, row_ids_query
        )

        row_ids_table = row_ids_query_builder.to_arrow()
        row_ids_table = row_ids_table.combine_chunks()
        # Copy is needed so that the array is not read-only
        row_ids = row_ids_table["_rowid"].to_numpy().copy()

        if query.shuffle:
            rng = default_rng(query.shuffle_seed)
            rng.shuffle(row_ids)

        initial_view_table_data = pa.table(
            [
                pa.array(row_ids, type=pa.int64()),
                pa.array([False] * len(row_ids), type=pa.bool_()),
            ],
            names=["__source_row_id", "__is_set"],
        )

        # Create the MV table with stable row IDs enabled to support chaining MVs
        # We use lance directly when not using namespaces, since lancedb doesn't
        # expose new_table_enable_stable_row_ids yet. For namespace connections,
        # fall back to lancedb (without stable row IDs on the MV table).
        from .table import Table

        # Check if using namespace connection
        is_namespace = conn.namespace_impl is not None

        if not is_namespace:
            # Use lance directly to enable stable row IDs
            import lance

            table_uri = f"{conn._uri}/{view_name}.lance"

            # Create empty table with full schema first
            # This ensures all columns exist (including UDF columns)
            empty_data = view_schema.empty_table()
            lance.write_dataset(
                empty_data,
                table_uri,
                mode="create",
                enable_stable_row_ids=True,
            )

            # Open the table through lancedb
            view_table = Table(conn, view_name)

            # Add the initial row ID data
            view_table.add(initial_view_table_data)
        else:
            # For namespaces, use lancedb's API (no stable row IDs on MV table yet)
            # Need to create table in two steps because partial schema is not allowed
            # on initial create_table call.
            view_table = conn.create_table(
                view_name, data=None, schema=view_schema, mode="create"
            )
            view_table.add(initial_view_table_data)

        for udf_col, (udf, _output_index) in (self._column_udfs or {}).items():
            input_cols = udf.input_columns
            view_table._configure_computed_column(udf_col, udf, input_cols)

        return view_table


class Column:
    """Present a Column in the Table."""

    def __init__(self, name: str) -> None:
        """Define a column."""
        self.name = name

    def alias(self, alias: str) -> "Column":
        return AliasColumn(self, alias)

    def blob(self) -> "Column":
        return BlobColumn(self)

    def apply(self, batch: pa.RecordBatch) -> tuple[str, pa.Array]:
        return (self.name, batch[self.name])


class BlobColumn(Column):
    def __init__(self, col: Column) -> None:
        self.inner = col


class AliasColumn(Column):
    def __init__(self, col: Column, alias: str) -> None:
        self.col = col
        self._alias = alias

    def apply(self, batch: pa.RecordBatch) -> tuple[str, pa.Array]:
        _, arr = self.col.apply(batch)
        return (self._alias, arr)

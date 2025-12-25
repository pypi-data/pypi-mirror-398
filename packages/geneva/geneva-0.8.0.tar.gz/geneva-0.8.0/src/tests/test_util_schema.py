# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors


from __future__ import annotations

from typing import Optional

import attrs
import lancedb
import numpy as np
import pyarrow as pa
import pytest

from geneva.utils.schema import alter_or_create_table, attrs_to_arrow_schema

# ---------- fixtures ----------


@pytest.fixture
def db(tmp_path) -> lancedb.Connection:
    return lancedb.connect(str(tmp_path))


# ---------- models used in tests ----------


@attrs.define
class SupportedAll:
    # primitives
    s: str = attrs.field(metadata={"pa_type": pa.string()}, default="")
    i: int = attrs.field(metadata={"pa_type": pa.int64()}, default=0)
    f: float = attrs.field(metadata={"pa_type": pa.float64()}, default=0.0)
    b: bool = attrs.field(metadata={"pa_type": pa.bool_()}, default=False)
    by: bytes | None = attrs.field(metadata={"pa_type": pa.binary()}, default=None)

    # optionals
    os_: Optional[str] = attrs.field(metadata={"pa_type": pa.string()}, default=None)
    of: Optional[float] = attrs.field(metadata={"pa_type": pa.float64()}, default=None)
    oi: Optional[int] = attrs.field(metadata={"pa_type": pa.int64()}, default=None)
    ob: Optional[bool] = attrs.field(metadata={"pa_type": pa.bool_()}, default=None)
    oby: Optional[bytes] = attrs.field(metadata={"pa_type": pa.binary()}, default=None)

    # lists
    tags: list[str] = attrs.field(
        metadata={"pa_type": pa.list_(pa.string())}, factory=list
    )


@attrs.define
class MinimalV1:
    id: int = attrs.field(metadata={"pa_type": pa.int64()}, default=0)


@attrs.define
class MinimalV2(MinimalV1):
    # new columns to be added later
    s: str = attrs.field(metadata={"pa_type": pa.string()}, default="hi")
    f: float = attrs.field(metadata={"pa_type": pa.float64()}, default=1.5)
    b: bool = attrs.field(metadata={"pa_type": pa.bool_()}, default=True)
    by: bytes | None = attrs.field(metadata={"pa_type": pa.binary()}, default=b"")
    tags: list[str] = attrs.field(
        metadata={"pa_type": pa.list_(pa.string())}, default=["a", "b"]
    )


@attrs.define
class UnsupportedDict:
    id: int = attrs.field(metadata={"pa_type": pa.int64()}, default=0)
    meta: dict[str, int] = attrs.field(default={})  # not supported by inference


@attrs.define
class Inner:
    a: int = attrs.field(metadata={"pa_type": pa.int64()}, default=0)


@attrs.define
class UnsupportedNestedList:
    id: int = attrs.field(metadata={"pa_type": pa.int64()}, default=0)
    items: list[Inner] = attrs.field(factory=list)  # not supported by inference


@attrs.define
class MapSupportedWithPaType:
    id: int = attrs.field(metadata={"pa_type": pa.int64()}, default=0)
    # explicitly specify Arrow type for a dict-like column
    dims: dict[str, float] = attrs.field(
        metadata={"pa_type": pa.map_(pa.string(), pa.float64())}, factory=dict
    )


# ---------- tests ----------


def test_create_with_all_supported_types(db) -> None:
    tbl = alter_or_create_table(db, "t_supported", SupportedAll())
    sch = tbl.schema

    # types
    assert sch.field("s").type == pa.string()
    assert sch.field("i").type == pa.int64()
    assert sch.field("f").type == pa.float64()
    assert sch.field("b").type == pa.bool_()
    assert sch.field("by").type == pa.binary()
    assert sch.field("tags").type == pa.list_(pa.string())

    # nullability: optionals should be nullable, others depend on default/annotation
    assert sch.field("os_").nullable
    assert sch.field("of").nullable
    assert sch.field("oi").nullable
    assert sch.field("ob").nullable
    assert sch.field("oby").nullable

    # round-trip: table exists, no changes on re-run
    tbl2 = alter_or_create_table(db, "t_supported", SupportedAll())
    assert tbl2.schema == sch


def test_overwrite_on_empty_when_new_cols_added(db) -> None:
    # create table (empty)
    tbl = alter_or_create_table(db, "t_empty_overwrite", MinimalV1())
    assert len(tbl) == 0

    # now "evolve" schema while table is still empty → should overwrite
    tbl2 = alter_or_create_table(db, "t_empty_overwrite", MinimalV2())
    sch = tbl2.schema
    assert set(sch.names) >= {"id", "s", "f", "b", "by", "tags"}


def _to_py_list(v) -> list:
    # Arrow ListScalar -> Python list
    if isinstance(v, pa.lib.ListScalar):
        return v.as_py()
    # NumPy array -> list
    if isinstance(v, np.ndarray):
        return v.tolist()
    # already a list/tuple
    if isinstance(v, list | tuple):
        return list(v)
    # pandas might give object-dtyped scalar that *is* a list already
    try:
        return list(v)  # last resort (will raise for non-iterables)
    except Exception:
        return v  # let the assert fail noisily


def test_add_columns_on_non_empty_applies_defaults(db) -> None:
    tbl = alter_or_create_table(db, "t_add_cols", MinimalV1())
    tbl.add([{"id": 42}])

    # evolve → newly added columns will be NULL for existing rows
    # (changed behavior: now defaults to NULL instead of model default values)
    tbl = alter_or_create_table(db, "t_add_cols", MinimalV2())
    df = tbl.to_pandas()

    assert set(df.columns) >= {"id", "s", "f", "b", "by", "tags"}
    row = df.iloc[0]
    assert row["id"] == 42
    # Newly added columns are NULL for existing rows
    assert row["s"] is None or (isinstance(row["s"], float) and np.isnan(row["s"]))
    assert row["f"] is None or (isinstance(row["f"], float) and np.isnan(row["f"]))
    assert row["b"] is None or (isinstance(row["b"], float) and np.isnan(row["b"]))
    assert row["by"] is None
    assert row["tags"] is None or (
        isinstance(row["tags"], float) and np.isnan(row["tags"])
    )


def test_drop_columns(db) -> None:
    # make table with extra columns first
    tbl = alter_or_create_table(db, "t_drop", MinimalV2())
    # drop back to MinimalV1
    tbl = alter_or_create_table(db, "t_drop", MinimalV1(), del_cols=True)
    assert set(tbl.schema.names) == {"id"}


def test_unsupported_types_raise_on_create(db) -> None:
    # dict[...] cannot be inferred → TypeError during initial create
    with pytest.raises(TypeError):
        alter_or_create_table(db, "t_bad_dict", UnsupportedDict())

    # list[nested-attrs] cannot be inferred → TypeError during initial create
    with pytest.raises(TypeError):
        alter_or_create_table(db, "t_bad_nested_list", UnsupportedNestedList())


def test_explicit_map_type_builds_schema_but_create_fails(db) -> None:
    # Building a schema with pa.map_ is possible, but Lance does not support Map
    # at table creation time, so we expect a runtime error.
    @attrs.define
    class MapSupportedWithPaType:
        id: int = attrs.field(metadata={"pa_type": pa.int64()}, default=0)
        dims: dict[str, float] = attrs.field(
            metadata={"pa_type": pa.map_(pa.string(), pa.float64())}, factory=dict
        )

    schema = attrs_to_arrow_schema(MapSupportedWithPaType())
    assert schema.field("dims").type == pa.map_(pa.string(), pa.float64())

    with pytest.raises(RuntimeError):
        alter_or_create_table(db, "t_map_unsupported", MapSupportedWithPaType())


def test_attrs_to_arrow_schema_map_builds_schema_only() -> None:
    @attrs.define
    class MapCol:
        id: int = attrs.field(metadata={"pa_type": pa.int64()}, default=0)
        dims: dict[str, float] = attrs.field(
            metadata={"pa_type": pa.map_(pa.string(), pa.float64())}, factory=dict
        )

    schema = attrs_to_arrow_schema(MapCol())
    assert schema.field("dims").type == pa.map_(pa.string(), pa.float64())


@pytest.mark.xfail(
    reason="LanceDB currently does not support Arrow Map type in table schemas"
)
def test_create_with_map_type_xfail(db) -> None:
    @attrs.define
    class MapCol:
        id: int = attrs.field(metadata={"pa_type": pa.int64()}, default=0)
        dims: dict[str, float] = attrs.field(
            metadata={"pa_type": pa.map_(pa.string(), pa.float64())}, factory=dict
        )

    # This is expected to fail at create time; xfail handles the runtime error.
    alter_or_create_table(db, "t_map_unsupported", MapCol())


def test_struct_override_allows_create(db) -> None:
    @attrs.define
    class WithStruct:
        id: int = attrs.field(metadata={"pa_type": pa.int64()}, default=0)
        info: dict[str, int] = attrs.field(
            metadata={"pa_type": pa.struct([pa.field("a", pa.int64())])},
            default={"a": 0},
        )

    tbl = alter_or_create_table(db, "t_struct_ok", WithStruct())
    assert set(tbl.schema.names) == {"id", "info"}
    assert tbl.schema.field("info").type == pa.struct([pa.field("a", pa.int64())])

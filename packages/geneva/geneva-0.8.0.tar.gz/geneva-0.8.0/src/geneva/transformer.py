# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import contextlib
import enum
import functools
import hashlib
import inspect
import logging
import typing
import warnings
from collections.abc import Callable
from types import NoneType, UnionType
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Optional,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

import attrs
import numpy
import pyarrow as pa
from attrs import validators as valid
from lance.blob import BlobFile

import geneva.cloudpickle as pickle
from geneva.checkpoint_utils import format_checkpoint_prefix
from geneva.utils.batch_size import resolve_batch_size

if TYPE_CHECKING:
    from geneva.debug.error_store import ErrorHandlingConfig

_LOG = logging.getLogger(__name__)

# special column name used to mark the rows that were not selected
# for backfilling.  This is used to avoid calling expensive UDFs
# on rows that are not selected.
BACKFILL_SELECTED = "__geneva_backfill_selected"


# ---------------------------------------------------------------------------
# Helpers for dotted column paths (struct.field)
# ---------------------------------------------------------------------------


def _split_column_path(col_name: str) -> list[str]:
    return col_name.split(".") if "." in col_name else [col_name]


def _get_field_type_from_schema(schema: pa.Schema, col_name: str) -> pa.DataType:
    """Resolve the leaf PyArrow type for a (possibly dotted) column path.

    Supports nested struct paths such as ``info.left`` or ``info.nested.x`` by
    traversing struct children until the leaf field is found.
    """

    parts = _split_column_path(col_name)

    if parts[0] not in schema.names:
        raise KeyError(parts[0])

    field = schema.field(parts[0])
    dtype = field.type

    for part in parts[1:]:
        if not pa.types.is_struct(dtype):
            raise KeyError(col_name)

        idx = dtype.get_field_index(part)
        if idx == -1:
            raise KeyError(col_name)
        dtype = dtype.field(idx).type

    return dtype


def _get_array_from_record_batch(batch: pa.RecordBatch, col_name: str) -> pa.Array:
    """Fetch column data from a RecordBatch, supporting dotted struct paths."""

    parts = _split_column_path(col_name)

    # If the full dotted path is already a column (projected subfield), return directly
    if col_name in batch.schema.names:
        return batch[col_name]

    if parts[0] not in batch.schema.names:
        raise KeyError(parts[0])

    arr: pa.Array = batch[parts[0]]

    for part in parts[1:]:
        if not pa.types.is_struct(arr.type):
            raise KeyError(col_name)
        # pyarrow guarantees RecordBatch columns are Arrays; cast to StructArray
        # after the struct type check so static typing knows ``field`` exists.
        arr = cast("pa.StructArray", arr).field(part)  # pyright: ignore[reportAttributeAccessIssue]

    return arr


def _get_value_from_row(row: dict[str, Any], col_name: str) -> Any:
    """Fetch a value from a row dict with dotted paths."""

    parts = _split_column_path(col_name)
    cur: Any = row

    for part in parts:
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(col_name)
        cur = cur[part]
        if cur is None:
            # Early exit: once None, deeper fields are also None
            break

    return cur


class UDFArgType(enum.Enum):
    """
    The type of arguments that the UDF expects.
    """

    # Scalar Batch
    SCALAR = 0
    # Array mode
    ARRAY = 1
    # Pass a pyarrow RecordBatch
    RECORD_BATCH = 2


@attrs.define
class UDF(Callable[[pa.RecordBatch], pa.Array]):  # type: ignore
    """User-defined function (UDF) to be applied to a Lance Table."""

    # The reference to the callable
    func: Callable = attrs.field()
    name: str = attrs.field(default="")
    cuda: Optional[bool] = attrs.field(default=False)
    num_cpus: Optional[float] = attrs.field(
        default=1.0,
        converter=lambda v: None if v is None else float(v),
        validator=valid.optional(valid.ge(0.0)),
        on_setattr=[attrs.setters.convert, attrs.setters.validate],
    )
    num_gpus: Optional[float] = attrs.field(
        default=None,
        converter=lambda v: None if v is None else float(v),
        validator=valid.optional(valid.ge(0.0)),
        on_setattr=[attrs.setters.convert, attrs.setters.validate],
    )
    memory: int | None = attrs.field(default=None)
    batch_size: int | None = attrs.field(default=None)
    checkpoint_size: int | None = attrs.field(default=None)
    task_size: int | None = attrs.field(default=None)

    # Error handling configuration
    error_handling: Optional["ErrorHandlingConfig"] = attrs.field(default=None)

    def _record_batch_input(self) -> bool:
        sig = inspect.signature(self.func)
        if len(sig.parameters) == 1:
            param = list(sig.parameters.values())[0]
            return param.annotation == pa.RecordBatch
        return False

    @property
    def arg_type(self) -> UDFArgType:
        if self._record_batch_input():
            return UDFArgType.RECORD_BATCH
        if _is_batched_func(self.func):
            return UDFArgType.ARRAY
        return UDFArgType.SCALAR

    input_columns: list[str] | None = attrs.field(default=None)

    data_type: pa.DataType = attrs.field(default=None)

    version: str = attrs.field(default="")

    _checkpoint_key_override: str | None = attrs.field(
        default=None, alias="checkpoint_key", repr=False
    )

    field_metadata: dict[str, str] = attrs.field(factory=dict)

    def __attrs_post_init__(self) -> None:
        """
        Initialize UDF fields and normalize num_gpus after all fields are set:
          1) if cuda=True and num_gpus is None or 0.0 -> set to 1.0
          2) otherwise ignore cuda and just use num_gpus setting
        """
        # Set default name
        if not self.name:
            if inspect.isfunction(self.func):
                self.name = self.func.__name__
            elif isinstance(self.func, Callable):
                self.name = self.func.__class__.__name__
            else:
                raise ValueError(
                    f"func must be a function or a callable, got {self.func}"
                )

        # Set default input_columns
        if self.input_columns is None:
            sig = inspect.signature(self.func)
            params = list(sig.parameters.keys())
            if self._record_batch_input():
                self.input_columns = None
            else:
                self.input_columns = params

        # Validate input_columns
        if self.arg_type == UDFArgType.RECORD_BATCH:
            if self.input_columns is not None:
                raise ValueError(
                    "RecordBatch input UDF must not declare any input columns. "
                    "RecordBatch UDFs receive the entire batch and should not "
                    "specify input_columns. Consider using a stateful RecordBatch "
                    "UDF and parameterize it or use UDF with Array inputs."
                )
        else:
            if self.input_columns is None:
                raise ValueError("Array and Scalar input UDF must declare input column")

        # Set default data_type
        if self.data_type is None:
            if self.arg_type != UDFArgType.SCALAR:
                raise ValueError(
                    "batched UDFs do not support data_type inference yet,"
                    " please specify data_type",
                )
            self.data_type = _infer_func_arrow_type(self.func, None)  # type: ignore[arg-type]

        # Validate data_type
        if self.data_type is None:
            raise ValueError("data_type must be set")
        if not isinstance(self.data_type, pa.DataType):
            raise ValueError(
                f"data_type must be a pyarrow.DataType, got {self.data_type}"
            )

        # Set default version
        if not self.version:
            hasher = hashlib.md5()
            hasher.update(pickle.dumps(self.func))
            self.version = hasher.hexdigest()

        # Normalize override
        if not self._checkpoint_key_override:
            self._checkpoint_key_override = None

        # Handle cuda/num_gpus normalization
        if self.cuda:
            warnings.warn(
                "The 'cuda' flag is deprecated. Please set 'num_gpus' explicitly "
                "(0.0 for CPU, >=1.0 for GPU).",
                DeprecationWarning,
                stacklevel=2,
            )

        if self.num_gpus is None:
            self.num_gpus = 1.0 if self.cuda is True else 0.0
        # otherwise fall back to user specified num_gpus

    @property
    def checkpoint_key(self) -> str:
        """Base checkpoint identifier for the UDF."""

        return self._checkpoint_key_override or f"{self.name}:{self.version}"

    @checkpoint_key.setter
    def checkpoint_key(self, value: str | None) -> None:
        self._checkpoint_key_override = value or None

    def checkpoint_prefix(
        self,
        *,
        column: str,
        dataset_uri: str,
        dataset_version: int | str | None,
        where: str | None = None,
    ) -> str:
        """Build the prefix portion of a checkpoint key for this UDF."""

        return format_checkpoint_prefix(
            udf_name=self.name,
            udf_version=self._checkpoint_key_override or self.version,
            column=column,
            where=where,
            dataset_uri=dataset_uri,
            dataset_version=dataset_version,
        )

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

    def _scalar_func_record_batch_call(self, record_batch: pa.RecordBatch) -> pa.Array:
        """
        We use this when the UDF uses single call like
        `func(x_int, y_string, ...) -> type`

        this function automatically dispatches rows to the func and returns `pa.Array`
        """
        # Fallback to legacy pylist path if a list of dicts is provided
        if not isinstance(record_batch, pa.RecordBatch):
            return self._scalar_func_record_batch_call_py(record_batch)

        annotations = _get_annotations(self.func)
        sig = inspect.signature(self.func)
        params = list(sig.parameters.values())
        pos_params = [
            p
            for p in params
            if p.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        varargs_param = next(
            (p for p in params if p.kind == inspect.Parameter.VAR_POSITIONAL),
            None,
        )
        required_pos_count = sum(
            1 for p in pos_params if p.default is inspect.Parameter.empty
        )
        input_cols = cast("list[str]", self.input_columns)  # type: ignore[arg-type]

        if len(input_cols) > len(pos_params) and varargs_param is None:
            raise ValueError(
                f"UDF '{self.name}' expects {len(pos_params)} parameters but "
                f"{len(input_cols)} input_columns were provided."
            )

        if len(input_cols) < required_pos_count:
            raise ValueError(
                f"UDF '{self.name}' expects at least {required_pos_count} parameters "
                f"but {len(input_cols)} input_columns were provided."
            )

        # Build value accessors for each input column to avoid pylist conversion.
        accessors = []
        for idx, col in enumerate(input_cols):
            param = pos_params[idx] if idx < len(pos_params) else varargs_param
            expected_type = annotations.get(param.name) if param else None
            accessors.append(
                _make_value_accessor(
                    _get_array_from_record_batch(record_batch, col), expected_type
                )
            )

        backfill_mask = (
            record_batch[BACKFILL_SELECTED]
            if BACKFILL_SELECTED in record_batch.schema.names
            else None
        )

        def _iter_arrow():  # noqa: ANN202
            for idx in range(record_batch.num_rows):
                if backfill_mask is not None and not backfill_mask[idx].as_py():
                    # Row not selected for backfill - keep placeholder
                    yield None
                    continue

                args = [accessor(idx) for accessor in accessors]
                yield self.func(*args)

        arr = pa.array(_iter_arrow(), type=self.data_type)
        # this should always by an Array, never should we get a ChunkedArray back here
        assert isinstance(arr, pa.Array)
        return arr

    def _scalar_func_record_batch_call_py(self, rows: list[dict[str, Any]]) -> pa.Array:
        """Legacy pylist path used when a RecordBatch is not provided."""

        def _iter():  # noqa: ANN202
            for item in rows:
                if BACKFILL_SELECTED not in item or item.get(BACKFILL_SELECTED):
                    # we know input_columns is not none here
                    args = [
                        _get_value_from_row(item, col)
                        for col in self.input_columns  # pyright: ignore[reportOptionalIterable]
                    ]  # type: ignore
                    yield self.func(*args)
                else:
                    yield None

        arr = pa.array(_iter(), type=self.data_type)
        assert isinstance(arr, pa.Array)
        return arr

    def _input_columns_validator(self, attribute, value) -> None:
        """Validate input_columns attribute for attrs compatibility."""
        if self.arg_type == UDFArgType.RECORD_BATCH:
            if value is not None:
                raise ValueError(
                    "RecordBatch input UDF must not declare any input columns. "
                    "RecordBatch UDFs receive the entire batch and should not "
                    "specify input_columns."
                )
        else:
            if value is None:
                raise ValueError("Array and Scalar input UDF must declare input column")

    def validate_against_schema(
        self, table_schema: pa.Schema, input_columns: list[str] | None = None
    ) -> None:
        """
        Validate UDF against table schema.

        This is the primary validation method that should be called before executing
        a UDF. It performs comprehensive validation including:

        1. **Column Existence**: Verifies all input columns exist in the table schema
        2. **Type Compatibility**: Checks that column types match UDF type annotations
           (if present)
        3. **RecordBatch Constraints**: Ensures RecordBatch UDFs don't have
           input_columns defined

        The validation happens at two points in the UDF lifecycle:
        - At `add_columns()` time when defining the column
        - At `backfill()` time when executing (if input_columns are overridden)

        Parameters
        ----------
        table_schema: pa.Schema
            The schema of the table being processed
        input_columns: list[str] | None
            The input column names to validate. If None, uses self.input_columns.

        Raises
        ------
        ValueError: If validation fails for any of the following reasons:
            - Input columns don't exist in table schema
            - Type mismatch between table and UDF expectations
            - RecordBatch UDF has input_columns defined
            - Array/Scalar UDF has no input_columns defined

        Warns
        -----
        UserWarning: If type validation is skipped due to:
            - UDF has no type annotations
            - Type annotation can't be mapped to PyArrow types

        Examples
        --------
        >>> @udf(data_type=pa.int32())
        ... def my_udf(a: int) -> int:
        ...     return a * 2
        >>> my_udf.validate_against_schema(table.schema)  # Validates column 'a' exists
        """

        # Determine which columns to validate
        cols_to_validate = (
            input_columns if input_columns is not None else self.input_columns
        )

        # Check RecordBatch UDFs
        if self.arg_type == UDFArgType.RECORD_BATCH:
            # Error if input_columns are specified for RecordBatch UDFs
            if cols_to_validate is not None:
                raise ValueError(
                    f"UDF '{self.name}' is a RecordBatch UDF but has input_columns "
                    f"{cols_to_validate} specified. RecordBatch UDFs receive the "
                    f"entire batch and should not declare input_columns. "
                    f"Remove the input_columns parameter."
                )
            # RecordBatch UDFs don't need column validation
            return

        # For Array and Scalar UDFs, input_columns must be defined
        if cols_to_validate is None:
            arg_type_name = self.arg_type.name if self.arg_type else "UNKNOWN"
            raise ValueError(
                f"UDF '{self.name}' (type: {arg_type_name}) has no input_columns "
                f"defined. Array and Scalar UDFs must specify input columns either "
                f"through function parameter names or the input_columns parameter."
            )

        # Validate all input columns exist in table schema
        missing_columns: list[str] = []

        for col in cols_to_validate:
            try:
                _get_field_type_from_schema(table_schema, col)
            except KeyError:  # noqa: PERF203
                missing_columns.append(col)

        if missing_columns:
            raise ValueError(
                f"UDF '{self.name}' expects input columns {missing_columns} which are "
                f"not found in table schema. Available columns: {table_schema.names}. "
                f"Check your UDF's function parameter names or input_columns parameter."
            )

        # Validate type compatibility for each input column
        self._validate_column_types(table_schema, cols_to_validate)

    def _validate_column_types(
        self, table_schema: pa.Schema, input_columns: list[str]
    ) -> None:
        """
        Validate type compatibility between table schema and UDF expectations.

        This method checks if the table column types match the UDF's type annotations.
        If no type annotations are present or types can't be mapped, validation is
        skipped with a warning.

        Parameters
        ----------
        table_schema: pa.Schema
            The schema of the table being processed
        input_columns: list[str]
            The input column names to validate types for

        Raises
        ------
        ValueError: If there's a type mismatch between table schema and UDF expectations

        Warns
        -----
        UserWarning: If type validation is skipped due to missing annotations or
            unmappable types
        """
        import warnings

        # Get type annotations from the UDF function
        annotations = _get_annotations(self.func)

        if not annotations:
            # No type annotations found - warn user
            warnings.warn(
                f"UDF '{self.name}' has no type annotations. Type validation will be "
                f"skipped. Consider adding type hints to your UDF function parameters "
                f"for better error detection.",
                UserWarning,
                stacklevel=4,
            )
            return

        # For each input column, validate type if annotation exists.
        sig = inspect.signature(self.func)
        params = list(sig.parameters.values())
        pos_params = [
            p
            for p in params
            if p.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        varargs_param = next(
            (p for p in params if p.kind == inspect.Parameter.VAR_POSITIONAL),
            None,
        )
        required_pos_count = sum(
            1 for p in pos_params if p.default is inspect.Parameter.empty
        )

        if len(input_columns) > len(pos_params) and varargs_param is None:
            raise ValueError(
                f"UDF '{self.name}' expects {len(pos_params)} parameters but "
                f"{len(input_columns)} input_columns were provided."
            )

        if len(input_columns) < required_pos_count:
            raise ValueError(
                f"UDF '{self.name}' expects at least {required_pos_count} parameters "
                f"but {len(input_columns)} input_columns were provided."
            )

        for idx, col_name in enumerate(input_columns):
            param = pos_params[idx] if idx < len(pos_params) else varargs_param
            param_name = param.name if param else f"arg_{idx}"
            expected_type = annotations.get(param_name) if param else None

            # Get the actual type from table schema (supports dotted paths)
            table_type = _get_field_type_from_schema(table_schema, col_name)
            is_list_type = (
                pa.types.is_list(table_type)
                or pa.types.is_large_list(table_type)
                or pa.types.is_fixed_size_list(table_type)
            )

            if expected_type is None:
                continue

            wants_numpy = _annotation_requests_numpy_ndarray(expected_type)
            wants_list = _annotation_requests_list(expected_type)

            if wants_numpy and wants_list:
                raise ValueError(
                    f"Parameter '{param_name}' in UDF '{self.name}' is annotated as "
                    "both numpy.ndarray and list; choose one representation for "
                    "list-backed columns."
                )

            if wants_numpy:
                if is_list_type:
                    # Compatible – skip further validation because dtype/shape
                    # information is not available from the annotation alone.
                    continue
                raise ValueError(
                    f"Type mismatch for column '{col_name}' (parameter '{param_name}') "
                    f"in UDF '{self.name}': table has type {table_type}, but the "
                    "parameter is annotated as numpy.ndarray. numpy.ndarray inputs are "
                    "supported only for list, large_list, or fixed-size list Arrow "
                    "columns."
                )

            if wants_list:
                if is_list_type:
                    continue
                raise ValueError(
                    f"Type mismatch for column '{col_name}' (parameter '{param_name}') "
                    f"in UDF '{self.name}': table has type {table_type}, but the "
                    "parameter is annotated as a Python list. List annotations require "
                    "Arrow list, large_list, or fixed-size list column types."
                )

            # Try to map expected type to PyArrow type for comparison
            try:
                expected_pa_type = self._python_type_to_arrow_type(expected_type)

                # Check if types are compatible
                if not self._types_compatible(table_type, expected_pa_type):
                    raise ValueError(
                        f"Type mismatch for column '{col_name}' (parameter "
                        f"'{param_name}') in UDF '{self.name}': table has type "
                        f"{table_type}, but UDF expects {expected_pa_type} (from "
                        f"annotation {expected_type}). This will likely cause "
                        "serialization or conversion errors during execution."
                    )
            except (ValueError, KeyError):
                # If we can't map the type, skip validation with warning
                warnings.warn(
                    f"Could not validate type for column '{col_name}' (parameter "
                    f"'{param_name}') in UDF '{self.name}' with annotation "
                    f"{expected_type}. Type validation skipped for this column.",
                    UserWarning,
                    stacklevel=4,
                )

    def _python_type_to_arrow_type(self, python_type) -> pa.DataType:
        """
        Convert Python type annotation to PyArrow type.

        Raises ValueError if type cannot be mapped.
        """
        # Handle PyArrow types directly
        if isinstance(python_type, pa.DataType):
            return python_type

        # Handle pa.Array annotation (for batched UDFs)
        if python_type == pa.Array:
            # Can't determine specific array type, so return None to skip validation
            raise ValueError("Cannot validate generic pa.Array type")

        # Map Python/numpy types to PyArrow types
        type_map = {
            bool: pa.bool_(),
            bytes: pa.binary(),
            float: pa.float32(),
            int: pa.int64(),
            str: pa.string(),
            numpy.bool_: pa.bool_(),
            numpy.uint8: pa.uint8(),
            numpy.uint16: pa.uint16(),
            numpy.uint32: pa.uint32(),
            numpy.uint64: pa.uint64(),
            numpy.int8: pa.int8(),
            numpy.int16: pa.int16(),
            numpy.int32: pa.int32(),
            numpy.int64: pa.int64(),
            numpy.float16: pa.float16(),
            numpy.float32: pa.float32(),
            numpy.float64: pa.float64(),
            numpy.str_: pa.string(),
        }

        if python_type in type_map:
            return type_map[python_type]

        raise ValueError(f"Cannot map Python type {python_type} to PyArrow type")

    def _types_compatible(self, actual: pa.DataType, expected: pa.DataType) -> bool:
        """
        Check if actual type is compatible with expected type.

        This is more permissive than exact equality, allowing for:
        - Exact matches
        - Nullable vs non-nullable variants
        """
        # Exact match
        if actual == expected:
            return True

        # Check base types match (ignoring nullability, precision differences)
        # For numeric types, check if they're in the same family
        if pa.types.is_integer(actual) and pa.types.is_integer(expected):
            # Allow integer types if bit width and signedness match
            return actual.bit_width == expected.bit_width and (
                (
                    pa.types.is_signed_integer(actual)
                    and pa.types.is_signed_integer(expected)
                )
                or (
                    pa.types.is_unsigned_integer(actual)
                    and pa.types.is_unsigned_integer(expected)
                )
            )

        if pa.types.is_floating(actual) and pa.types.is_floating(expected):
            # Require exact match for floating point types (float32 vs float64 matters!)
            return actual.bit_width == expected.bit_width

        # For other types, require exact match
        return False

    def __call__(self, *args, use_applier: bool = False, **kwargs) -> pa.Array:
        # dispatch coming from Applier or user calling with a `RecordBatch`
        if use_applier or (len(args) == 1 and isinstance(args[0], pa.RecordBatch)):
            record_batch = args[0]
            match self.arg_type:
                case UDFArgType.SCALAR:
                    return self._scalar_func_record_batch_call(record_batch)
                case UDFArgType.ARRAY:
                    # Validate columns exist before accessing them
                    try:
                        arrs = [
                            _get_array_from_record_batch(record_batch, col)
                            for col in self.input_columns  # pyright: ignore[reportOptionalIterable]
                        ]  # type:ignore
                    except KeyError as e:
                        raise KeyError(
                            f"UDF '{self.name}' failed: column {e} not found in "
                            f"RecordBatch. Available columns: "
                            f"{record_batch.schema.names}. UDF expects "
                            f"input_columns: {self.input_columns}."
                        ) from e
                    return self.func(*arrs)
                case UDFArgType.RECORD_BATCH:
                    if isinstance(record_batch, pa.RecordBatch):
                        return self.func(record_batch)
                    # a list of dicts with BlobFiles that need to de-ref'ed
                    assert isinstance(record_batch, list)
                    rb_list = []
                    for row in record_batch:
                        new_row = {}
                        for k, v in row.items():
                            if isinstance(v, BlobFile):
                                # read the blob file into memory
                                new_row[k] = v.readall()
                                continue
                            new_row[k] = v
                        rb_list.append(new_row)

                    rb = pa.RecordBatch.from_pylist(rb_list)

                    return self.func(rb)
        # dispatch is trying to access the function's original pattern
        return self.func(*args, **kwargs)


def udf(
    func: Callable | None = None,
    *,
    data_type: pa.DataType | None = None,
    version: str | None = None,
    cuda: bool = False,  # deprecated
    field_metadata: dict[str, str] | None = None,
    input_columns: list[str] | None = None,
    num_cpus: int | float | None = None,
    num_gpus: int | float | None = None,
    batch_size: int | None = None,
    checkpoint_size: int | None = None,
    task_size: int | None = None,
    error_handling: Optional["ErrorHandlingConfig"] = None,
    **kwargs,
) -> UDF | functools.partial:
    """Decorator of a User Defined Function ([UDF][geneva.transformer.UDF]).

    Parameters
    ----------
    func: Callable
        The callable to be decorated. If None, returns a partial function.
    data_type: pa.DataType, optional
        The data type of the output PyArrow Array from the UDF.
        If None, it will be inferred from the function signature.
    version: str, optional
        A version string to manage the changes of function.
        If not provided, it will use the hash of the serialized function.
    cuda: bool, optional, Deprecated
        If true, load CUDA optimized kernels.  Equvalent to num_gpus=1
    field_metadata: dict[str, str], optional
        A dictionary of metadata to be attached to the output `pyarrow.Field`.
    input_columns: list[str], optional
        A list of input column names for the UDF. If not provided, it will be
        inferred from the function signature. Or scan all columns.
    num_cpus: int, float, optional
        The (fraction) number of CPUs to acquire to run the job.
    num_gpus: int, float, optional
        The (fraction) number of GPUs to acquire to run the job.  Default 0.
    batch_size: int, optional (deprecated)
        Legacy parameter controlling map/read batch size. Prefer checkpoint_size.
    checkpoint_size: int, optional
        Alias for batch_size; preferred for overriding map-task batch size
        (read and map remain identical today).
    task_size: int, optional
        Reserved for read-task sizing; currently unsupported and will raise.
    error_handling: ErrorHandlingConfig, optional
        Configuration for error handling and retry behavior.

    Notes
    -----
    - **Column/parameter mapping**: For scalar and array UDFs, parameter names map
      directly to input column names. If you want a column to be delivered as a
      ``numpy.ndarray`` without extra copies, annotate the parameter as
      ``numpy.ndarray`` and ensure the column's Arrow type is a list
      (``pa.list_``/``pa.large_list``/``pa.fixed_size_list``). Other column types
      continue to be passed as Python scalars/objects.
    - **Python lists**: When a parameter is annotated as ``list[...]``, the column
      must be an Arrow list/large_list/fixed_size_list. In that case each value is
      delivered to the UDF as a Python list instead of a numpy array.
    - **Return type with numpy.ndarray**: If your function returns a
      ``numpy.ndarray``, you must provide an explicit ``data_type`` (for example,
      ``pa.list_(pa.float32())``); the ndarray shape/dtype cannot be inferred
      automatically from the annotation alone.
    """
    if task_size is not None:
        _LOG.warning("task_size is not supported for UDFs; ignoring provided value.")

    if inspect.isclass(func):

        @functools.wraps(func)
        def _wrapper(*args, **kwargs) -> UDF | functools.partial:
            callable_obj = func(*args, **kwargs)
            return udf(
                callable_obj,
                cuda=cuda,
                data_type=data_type,
                version=version,
                field_metadata=field_metadata,
                input_columns=input_columns,
                num_cpus=num_cpus,
                num_gpus=num_gpus,
                batch_size=batch_size,
                checkpoint_size=checkpoint_size,
                task_size=task_size,
                error_handling=error_handling,
            )

        return _wrapper  # type: ignore

    if func is None:
        return functools.partial(
            udf,
            cuda=cuda,
            data_type=data_type,
            version=version,
            field_metadata=field_metadata,
            input_columns=input_columns,
            num_cpus=num_cpus,
            num_gpus=num_gpus,
            batch_size=batch_size,
            checkpoint_size=checkpoint_size,
            task_size=task_size,
            error_handling=error_handling,
            **kwargs,
        )

    effective_batch_size = resolve_batch_size(
        batch_size=batch_size,
        checkpoint_size=checkpoint_size,
    )

    # we depend on default behavior of attrs to infer the output schema
    def _include_if_not_none(name, value) -> dict[str, Any]:
        if value is not None:
            return {name: value}
        return {}

    args = {
        "func": func,
        "cuda": cuda,
        **_include_if_not_none("data_type", data_type),
        **_include_if_not_none("version", version),
        **_include_if_not_none("field_metadata", field_metadata),
        **_include_if_not_none("input_columns", input_columns),
        **_include_if_not_none("num_cpus", num_cpus),
        **_include_if_not_none("num_gpus", num_gpus),
        **_include_if_not_none("batch_size", effective_batch_size),
        **_include_if_not_none("checkpoint_size", checkpoint_size),
        **_include_if_not_none("task_size", task_size),
        **_include_if_not_none("error_handling", error_handling),
    }
    # can't use functools.update_wrapper because attrs makes certain assumptions
    # and attributes read-only. We will figure out docs and stuff later
    return UDF(**args)


def _get_annotations(func: Callable) -> dict[str, Any]:
    """Get evaluated annotations when possible.

    Many UDF modules use ``from __future__ import annotations`` which stores
    annotations as strings. We attempt to evaluate them so list/ndarray handling
    can honor the developer's intent. If evaluation fails, fall back to raw
    annotations.
    """

    target = func if inspect.isfunction(func) else func.__call__  # type: ignore[union-attr]

    # First try typing.get_type_hints for robust evaluation on Python 3.10+.
    # Cloudpickle/Ray may omit names that are only used in annotations; augment
    # the namespace with typing/builtins so evaluation still succeeds.
    globalns = getattr(target, "__globals__", {}) or {}
    augmented_ns: dict[str, Any] = dict(globalns)
    augmented_ns.update(vars(typing))
    augmented_ns.setdefault("Any", Any)
    augmented_ns.setdefault("Optional", Optional)
    augmented_ns.setdefault("Union", Union)
    augmented_ns.setdefault("list", list)
    augmented_ns.setdefault("dict", dict)
    augmented_ns.setdefault("numpy", numpy)
    augmented_ns.setdefault("np", numpy)
    augmented_ns.setdefault("pa", pa)

    with contextlib.suppress(Exception):
        try:
            return get_type_hints(
                target,
                globalns=augmented_ns,
                localns=augmented_ns,
                include_extras=True,
            )
        except TypeError:
            # include_extras not supported on some versions
            return get_type_hints(target, globalns=augmented_ns, localns=augmented_ns)

    # Fallback to inspect.get_annotations; eval_str may not exist on older versions.
    try:
        return inspect.get_annotations(target, eval_str=True)
    except Exception:
        return inspect.get_annotations(target)


def _is_batched_func(func: Callable) -> bool:
    annotations = _get_annotations(func)
    if "return" not in annotations:
        return False

    ret_type = annotations["return"]
    if ret_type != pa.Array and not isinstance(ret_type, pa.DataType):
        return False

    input_keys = list(annotations.keys() - {"return"})
    if len(input_keys) == 1:
        return all(
            annotations[input_key] in [pa.RecordBatch, pa.Array]
            for input_key in input_keys
        )

    if any(annotations[input_key] == pa.RecordBatch for input_key in input_keys):
        raise ValueError(
            "UDF can not have multiple parameters with 'pa.RecordBatch' type"
        )
    return all(annotations[input_key] in [pa.Array] for input_key in input_keys)


def _annotation_matches_type(annotation: Any | None, target: type) -> bool:
    """Return True if annotation (including Union/Annotated) includes ``target``."""

    if annotation is None:
        return False

    if annotation is target:
        return True

    origin = get_origin(annotation)
    if origin is None:
        return False

    if origin is target:
        return True

    if origin is Annotated:
        base, *_ = get_args(annotation)
        return _annotation_matches_type(base, target)

    if origin in (Union, UnionType):
        return any(
            _annotation_matches_type(arg, target)
            for arg in get_args(annotation)
            if arg is not NoneType
        )

    return False


def _annotation_requests_numpy_ndarray(annotation: Any | None) -> bool:
    return _annotation_matches_type(annotation, numpy.ndarray)


def _annotation_requests_list(annotation: Any | None) -> bool:
    return _annotation_matches_type(annotation, list)


def _make_value_accessor(
    array: pa.Array, expected_type: Any | None = None
) -> Callable[[int], Any]:
    """Return a fast row accessor for a column.

    For list/large_list/fixed_size_list columns we can either:
    - Return Python lists when the parameter is annotated as ``list[...]``
    - Return numpy arrays (zero-copy when possible) when the parameter is annotated
      as ``numpy.ndarray`` or no preference is declared.
    """

    prefers_numpy = _annotation_requests_numpy_ndarray(expected_type)
    prefers_pylist = _annotation_requests_list(expected_type)

    if prefers_numpy and prefers_pylist:
        raise ValueError(
            "Ambiguous type annotation requesting both list and numpy.ndarray for the "
            "same parameter. Please choose one."
        )

    is_list_like = pa.types.is_list(array.type) or pa.types.is_large_list(array.type)
    is_fixed_size_list = pa.types.is_fixed_size_list(array.type)

    if prefers_numpy and not (is_list_like or is_fixed_size_list):
        raise ValueError(
            f"Column has type {array.type} but parameter is "
            "annotated as numpy.ndarray; "
            "numpy.ndarray inputs require list, large_list, or fixed-size list "
            "columns."
        )

    if prefers_pylist and not (is_list_like or is_fixed_size_list):
        raise ValueError(
            f"Column has type {array.type} but parameter is annotated as list; "
            "list annotations require list, large_list, or fixed-size list columns."
        )

    if is_list_like:
        list_array = cast("pa.ListArray | pa.LargeListArray", array)
        if prefers_pylist:
            valid = (
                None
                if list_array.null_count == 0
                else list_array.is_valid().to_numpy(zero_copy_only=False)
            )

            def _getter(i: int) -> Any:
                if valid is not None and not valid[i]:
                    return None
                return list_array[i].as_py()

            return _getter

        try:
            values_np = list_array.values.to_numpy(zero_copy_only=False)
            offsets = list_array.offsets.to_numpy(zero_copy_only=False)
        except (pa.ArrowInvalid, pa.ArrowTypeError, NotImplementedError):
            # Fallback to numpy object array per-row when zero-copy path
            # is unavailable (e.g., nested lists)
            valid = (
                None
                if list_array.null_count == 0
                else list_array.is_valid().to_numpy(zero_copy_only=False)
            )

            def _fallback(i: int) -> Any:
                if valid is not None and not valid[i]:
                    return None
                return numpy.array(list_array[i].as_py(), dtype=object)

            return _fallback

        valid = (
            None
            if list_array.null_count == 0
            else list_array.is_valid().to_numpy(zero_copy_only=False)
        )

        def _getter(i: int) -> Any:
            if valid is not None and not valid[i]:
                return None
            start = offsets[i]
            end = offsets[i + 1]
            return values_np[start:end]

        return _getter

    if is_fixed_size_list:
        fsl_array = cast("pa.FixedSizeListArray", array)

        if prefers_pylist:
            valid = (
                None
                if fsl_array.null_count == 0
                else fsl_array.is_valid().to_numpy(zero_copy_only=False)
            )

            def _getter(i: int) -> Any:
                if valid is not None and not valid[i]:
                    return None
                return fsl_array[i].as_py()

            return _getter

        try:
            values_np = fsl_array.values.to_numpy(zero_copy_only=False)
        except (pa.ArrowInvalid, pa.ArrowTypeError, NotImplementedError):
            valid = (
                None
                if fsl_array.null_count == 0
                else fsl_array.is_valid().to_numpy(zero_copy_only=False)
            )

            def _fallback(i: int) -> Any:
                if valid is not None and not valid[i]:
                    return None
                return numpy.array(fsl_array[i].as_py(), dtype=object)

            return _fallback

        list_size = fsl_array.type.list_size  # type: ignore[assignment]
        base_offset = fsl_array.offset

        valid = (
            None
            if fsl_array.null_count == 0
            else fsl_array.is_valid().to_numpy(zero_copy_only=False)
        )

        def _getter(i: int) -> Any:
            if valid is not None and not valid[i]:
                return None
            start = (base_offset + i) * list_size
            end = start + list_size
            return values_np[start:end]

        return _getter

    return lambda i: array[i].as_py()


# Build numpy type mapping - numpy.bool deprecated in 1.x, reintroduced in 2.x
_NUMPY_TYPE_MAP = {
    bool: pa.bool_(),
    bytes: pa.binary(),
    float: pa.float32(),
    int: pa.int64(),
    str: pa.string(),
    numpy.bool_: pa.bool_(),
    numpy.uint8: pa.uint8(),
    numpy.uint16: pa.uint16(),
    numpy.uint32: pa.uint32(),
    numpy.uint64: pa.uint64(),
    numpy.int8: pa.int8(),
    numpy.int16: pa.int16(),
    numpy.int32: pa.int32(),
    numpy.int64: pa.int64(),
    numpy.float16: pa.float16(),
    numpy.float32: pa.float32(),
    numpy.float64: pa.float64(),
    numpy.str_: pa.string(),
}

# Add numpy.bool if available (numpy 2.x)
# In numpy 2.x, numpy.bool is a proper type, not a deprecated alias
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning, message=".*numpy.bool.*")
    if hasattr(numpy, "bool") and isinstance(numpy.bool, type):
        _NUMPY_TYPE_MAP[numpy.bool] = pa.bool_()


def _infer_func_arrow_type(func: Callable, input_schema: pa.Schema) -> pa.DataType:
    """Infer the output schema of a UDF

    currently independent of the input schema, in the future we may want to
    infer the output schema based on the input schema, or the UDF itself could
    request the input schema to be passed in.
    """
    if isinstance(func, UDF):
        return func.data_type

    annotations = _get_annotations(func)
    if "return" not in annotations:
        raise ValueError(f"UDF {func} does not have a return type annotation")

    data_type = annotations["return"]
    # do dispatch to handle different types of output types
    # e.g. pydantic -> pyarrow type inference
    if isinstance(data_type, pa.DataType):
        return data_type

    if data_type is numpy.ndarray:
        raise ValueError(
            "UDF return annotation 'numpy.ndarray' cannot be mapped to a PyArrow "
            "type automatically. Please supply 'data_type' explicitly, e.g. "
            "pa.list_(pa.float32()) for a float vector output."
        )

    if t := _NUMPY_TYPE_MAP.get(data_type):
        return t

    raise ValueError(f"UDF {func} has an invalid return type annotation {data_type}")

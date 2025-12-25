# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import logging
import warnings
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pytest

from geneva import connect, udf
from geneva.transformer import UDF, UDFArgType


def test_udf_fsl(tmp_path: Path) -> None:
    @udf(data_type=pa.list_(pa.float32(), 4))
    def gen_fsl(b: pa.RecordBatch) -> pa.Array:
        arr = pa.array([b * 1.0 for b in range(8)])
        fsl = pa.FixedSizeListArray.from_arrays(arr, 4)
        return fsl

    assert gen_fsl.data_type == pa.list_(pa.float32(), 4)

    db = connect(tmp_path)
    tbl = pa.table({"a": [1, 2]})
    tbl = db.create_table("t1", tbl)

    # RecordBatch UDFs don't use input_columns - they receive the entire batch
    tbl.add_columns(
        {"embed": gen_fsl},
    )

    tbl = db.open_table("t1")
    assert tbl.schema == pa.schema(
        [
            pa.field("a", pa.int64()),
            pa.field("embed", pa.list_(pa.float32(), 4)),
        ],
    )


def test_udf_data_type_inference() -> None:
    @udf
    def foo(x: int, y: int) -> int:
        return x + y

    assert foo.data_type == pa.int64()
    assert foo.arg_type is UDFArgType.SCALAR

    for np_dtype in [
        np.bool_,
        np.uint8,
        np.uint16,
        np.uint32,
        np.uint64,
        np.int8,
        np.int16,
        np.int32,
        np.int64,
        np.float16,
        np.float32,
        np.float64,
    ]:

        @udf
        def foo_np(x: int, np_dtype=np_dtype) -> np_dtype:
            return np_dtype(x)

        assert foo_np.data_type == pa.from_numpy_dtype(np_dtype)
        assert foo_np.arg_type is UDFArgType.SCALAR

    @udf
    def bool_val(x: int) -> bool:
        return x % 2 == 0

    assert bool_val.data_type == pa.bool_()
    assert bool_val.arg_type is UDFArgType.SCALAR

    @udf
    def foo_str(x: int) -> str:
        return str(x)

    assert foo_str.data_type == pa.string()
    assert foo_str.arg_type is UDFArgType.SCALAR

    @udf
    def np_bool(x: int) -> np.bool_:
        return np.bool_(x % 2 == 0)

    assert np_bool.data_type == pa.bool_()
    assert np_bool.arg_type is UDFArgType.SCALAR


def test_scalar_udf_accepts_numpy_list_inputs() -> None:
    seen = []

    @udf(data_type=pa.list_(pa.float32()))
    def double_vec(x: np.ndarray) -> np.ndarray:
        seen.append(type(x))
        return x * 2

    rb = pa.RecordBatch.from_arrays(
        [pa.array([[1.0, 2.0], [3.0]], type=pa.list_(pa.float32()))],
        ["x"],
    )

    result = double_vec(rb)

    assert result.type == pa.list_(pa.float32())
    assert result.to_pylist() == [[2.0, 4.0], [6.0]]
    assert all(t is np.ndarray for t in seen)


def test_scalar_udf_accepts_numpy_fixed_size_list_inputs() -> None:
    @udf(data_type=pa.list_(pa.float32(), 2))
    def add_one(x: np.ndarray) -> np.ndarray:
        return x + 1

    rb = pa.RecordBatch.from_arrays(
        [pa.array([[0.0, 1.0], [2.0, 3.0]], type=pa.list_(pa.float32(), 2))],
        ["x"],
    )

    result = add_one(rb)

    assert result.type == pa.list_(pa.float32(), 2)
    assert result.to_pylist() == [[1.0, 2.0], [3.0, 4.0]]


def test_scalar_udf_accepts_numpy_list_string_inputs() -> None:
    @udf(data_type=pa.list_(pa.string()))
    def shout(x: np.ndarray) -> np.ndarray:
        return np.array([v.upper() for v in x], dtype=object)

    rb = pa.RecordBatch.from_arrays(
        [pa.array([["a", "b"], ["c", "d", "e"]], type=pa.list_(pa.string()))],
        ["x"],
    )

    result = shout(rb)

    assert result.type == pa.list_(pa.string())
    assert result.to_pylist() == [["A", "B"], ["C", "D", "E"]]


def test_scalar_udf_accepts_numpy_nested_lists() -> None:
    @udf(data_type=pa.list_(pa.list_(pa.int32())))
    def inc_nested(x: np.ndarray) -> np.ndarray:
        return np.array([[v + 1 for v in inner] for inner in x], dtype=object)

    rb = pa.RecordBatch.from_arrays(
        [pa.array([[[1, 2], [3]], [[4], [5, 6]]], type=pa.list_(pa.list_(pa.int32())))],
        ["x"],
    )

    result = inc_nested(rb)

    assert result.type == pa.list_(pa.list_(pa.int32()))
    assert result.to_pylist() == [[[2, 3], [4]], [[5], [6, 7]]]


def test_scalar_udf_list_annotation_returns_python_list() -> None:
    seen: list[type | None] = []

    @udf(data_type=pa.int32())
    def sum_list(x: list[int] | None) -> int | None:
        if x is None:
            seen.append(None)
            return None
        seen.append(type(x))
        return sum(x)

    rb = pa.RecordBatch.from_arrays(
        [pa.array([[1, 2], None, [3, 4]], type=pa.list_(pa.int32()))],
        ["x"],
    )

    result = sum_list(rb)

    assert result == pa.array([3, None, 7], type=pa.int32())
    assert seen == [list, None, list]


def test_scalar_udf_string_list_annotation_returns_python_list() -> None:
    @udf(data_type=pa.int32())
    def sum_list(x: "list[int] | None") -> int | None:
        if x is None:
            return None
        assert isinstance(x, list)
        return sum(x)

    rb = pa.RecordBatch.from_arrays(
        [pa.array([[1, 2], None], type=pa.list_(pa.int32()))],
        ["x"],
    )

    result = sum_list(rb)

    assert result == pa.array([3, None], type=pa.int32())


def test_string_annotation_eval_missing_globals() -> None:
    def sum_list_any(x: "list[dict[str, Any]] | None") -> int | None:
        if x is None:
            return None
        assert isinstance(x, list)
        return len(x)

    # Simulate Ray/cloudpickle dropping names only used in annotations.
    sum_list_any.__globals__.pop("Any", None)

    wrapped = udf(data_type=pa.int32())(sum_list_any)

    struct_type = pa.struct([("a", pa.int32())])
    rb = pa.RecordBatch.from_arrays(
        [
            pa.array(
                [[{"a": 1}, {"a": 2}], None],
                type=pa.list_(struct_type),
            )
        ],
        ["x"],
    )

    result = wrapped(rb)
    assert result == pa.array([2, None], type=pa.int32())


def test_scalar_udf_accepts_list_structs() -> None:
    struct_type = pa.struct([("a", pa.int32()), ("b", pa.string())])

    @udf(data_type=pa.list_(struct_type))
    def bump_struct(x: np.ndarray) -> list[dict[str, object]]:
        # x is a numpy object array of dicts; preserve shape and types
        return [{"a": elem["a"] + 1, "b": elem["b"].upper()} for elem in x]

    rb = pa.RecordBatch.from_arrays(
        [
            pa.array(
                [
                    [{"a": 1, "b": "c"}, {"a": 2, "b": "d"}],
                    [{"a": 10, "b": "e"}],
                ],
                type=pa.list_(struct_type),
            )
        ],
        ["x"],
    )

    result = bump_struct(rb)

    assert result.type == pa.list_(struct_type)
    assert result.to_pylist() == [
        [{"a": 2, "b": "C"}, {"a": 3, "b": "D"}],
        [{"a": 11, "b": "E"}],
    ]


def test_scalar_udf_accepts_list_structs_as_python_list() -> None:
    struct_type = pa.struct([("a", pa.int32()), ("b", pa.string())])

    @udf(data_type=pa.list_(struct_type))
    def bump_struct_pylist(
        x: list[dict[str, object]] | None,
    ) -> list[dict[str, object]] | None:
        if x is None:
            return None
        assert isinstance(x, list)
        return [{"a": elem["a"] + 1, "b": elem["b"].upper()} for elem in x]

    rb = pa.RecordBatch.from_arrays(
        [
            pa.array(
                [
                    [{"a": 1, "b": "c"}, {"a": 2, "b": "d"}],
                    [{"a": 10, "b": "e"}],
                    None,
                ],
                type=pa.list_(struct_type),
            )
        ],
        ["x"],
    )

    result = bump_struct_pylist(rb)

    assert result.type == pa.list_(struct_type)
    assert result.to_pylist() == [
        [{"a": 2, "b": "C"}, {"a": 3, "b": "D"}],
        [{"a": 11, "b": "E"}],
        None,
    ]


def test_udf_as_regular_functions() -> None:
    @udf
    def add_three_numbers(a: int, b: int, c: int) -> int:
        return a + b + c

    assert add_three_numbers(1, 2, 3) == 6
    assert add_three_numbers(10, 20, 30) == 60
    assert add_three_numbers.arg_type is UDFArgType.SCALAR
    assert add_three_numbers.data_type == pa.int64()

    @udf
    def make_string(x: int, y: str) -> str:
        return f"{y}-{x}"

    assert make_string(42, "answer") == "answer-42"
    assert make_string.arg_type is UDFArgType.SCALAR
    assert make_string.data_type == pa.string()

    @udf(data_type=pa.float32())
    def multi_by_two(batch: pa.RecordBatch) -> pa.Array:
        arr = pc.multiply(batch.column(0), 2)
        return arr

    rb = pa.RecordBatch.from_arrays([pa.array([1, 2, 3])], ["col"])
    assert multi_by_two(rb) == pa.array([2, 4, 6])
    assert multi_by_two.arg_type is UDFArgType.RECORD_BATCH

    # Confirm direct calls with multiple arguments still work as expected
    assert make_string(7, "num") == "num-7"
    assert add_three_numbers(2, 3, 4) == 9


def test_udf_with_batch_mode() -> None:
    """Test using a scalar UDF, but filled with batch model"""

    @udf
    def powers(a: int, b: int) -> int:
        return a**b

    # a RecordBatch with a and b columns
    rb = pa.RecordBatch.from_arrays(
        [pa.array([1, 2, 3]), pa.array([4, 5, 6])],
        ["a", "b"],
    )
    result = powers(rb)
    assert result == pa.array([1, 2**5, 3**6])


def test_udf_checkpoint_size_sets_batch_size() -> None:
    @udf(data_type=pa.int64(), checkpoint_size=32)
    def take_batch(x: int) -> int:
        return x

    assert isinstance(take_batch, UDF)
    assert take_batch.batch_size == 32

    @udf(
        data_type=pa.int64(),
        batch_size=16,
        checkpoint_size=32,
    )
    def mismatch(x: int) -> int:
        return x

    assert mismatch.batch_size == 32


def test_udf_task_size_warns(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):

        @udf(data_type=pa.int64(), task_size=10)
        def unsupported(x: int) -> int:
            return x

    assert unsupported.batch_size is None
    assert unsupported.task_size == 10
    assert any("task_size is not supported" in rec.message for rec in caplog.records)


def test_stateful_callable() -> None:
    @udf
    class StatefulFn:
        def __init__(self) -> None:
            self.state = 0

        def __call__(self, x: int) -> int:
            self.state += x
            return self.state

    stateful_fn = StatefulFn()
    assert isinstance(stateful_fn, UDF)
    assert stateful_fn(1) == 1
    assert stateful_fn.arg_type is UDFArgType.SCALAR
    assert stateful_fn.data_type == pa.int64()
    assert stateful_fn.input_columns == ["x"]

    @udf(data_type=pa.int64())
    class StatefulBatchFn:
        def __init__(self) -> None:
            self.state = 0

        def __call__(self, batch: pa.RecordBatch) -> pa.Array:
            self.state += sum(batch.column(0).to_pylist())
            return pa.array([self.state] * batch.num_rows)

    stateful_batch_fn = StatefulBatchFn()
    assert isinstance(stateful_batch_fn, UDF)
    assert stateful_batch_fn.arg_type is UDFArgType.RECORD_BATCH
    assert stateful_batch_fn.data_type == pa.int64()


def test_batched_udf_with_explicity_columns() -> None:
    @udf(data_type=pa.int64())
    def add_columns(a: pa.Array, b: pa.Array) -> pa.Array:
        return pc.add(a, b)

    assert add_columns.arg_type is UDFArgType.ARRAY
    assert add_columns.data_type == pa.int64()
    assert add_columns.input_columns == ["a", "b"]

    with pytest.raises(
        ValueError, match="multiple parameters with 'pa.RecordBatch' type"
    ):

        @udf
        def bad_udf(a: pa.RecordBatch, b: pa.RecordBatch) -> pa.Array:
            return pc.add(a.column(0), b.column(0))


def test_default_no_cuda_no_num_gpus_uses_0_no_warning() -> None:
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")

        @udf
        def f(x: int) -> int:
            return x

        assert isinstance(f, UDF)
        assert f.num_gpus == 0.0
        # No deprecation warning since caller didn't provide cuda
        assert not [w for w in rec if issubclass(w.category, DeprecationWarning)]


@pytest.mark.parametrize(
    ("cuda", "num_gpus", "expected"),
    [
        (True, None, 1.0),  # deprecated behavior
        (False, None, 0.0),  # deprecated behavior
        (False, 1.0, 1.0),  # respect num_gpus over cuda
        (True, 0.0, 0.0),  # respect num_gpus over cuda
        (None, None, 0.0),  # default
        (None, 2.5, 2.5),  # new behavior
        (None, 3, 3.0),  # int to float conversion
    ],
)
def test_fallback_to_cuda_when_num_gpus_none(cuda, num_gpus, expected) -> None:
    ctx = (
        pytest.warns(DeprecationWarning, match=r".*'cuda'.*deprecated.*")
        if cuda
        else nullcontext()
    )
    with ctx:

        @udf(cuda=cuda, num_gpus=num_gpus)
        def f(x: int) -> int:
            return x

    assert f.num_gpus == expected


GE_ZERO_RE = r".*>=\s*0(\.0)?"


def test_negative_num_gpus_rejected_on_init() -> None:
    with pytest.raises(ValueError, match=GE_ZERO_RE):

        @udf(num_gpus=-1)
        def f(x: int) -> int:
            return x


def test_set_time_validation_rejects_negative() -> None:
    @udf(num_gpus=0.0)
    def f(x: int) -> int:
        return x

    with pytest.raises(ValueError, match=GE_ZERO_RE):
        f.num_gpus = -0.1  # on_setattr=attrs.setters.validate should enforce validator


def test_cloudpickle_preserves_num_gpus() -> None:
    """Test that num_gpus is preserved through cloudpickle serialization."""
    import geneva.cloudpickle as cloudpickle

    @udf(num_gpus=2.5)
    def gpu_func(x: int) -> int:
        return x * 2

    # Serialize and deserialize
    pickled = cloudpickle.dumps(gpu_func)
    restored = cloudpickle.loads(pickled)

    # Verify all GPU-related attributes are preserved
    assert restored.num_gpus == 2.5
    assert restored.num_cpus == 1.0
    assert restored.cuda is False


def test_cloudpickle_preserves_cuda_deprecated() -> None:
    """Test that cuda=True (deprecated) is preserved through cloudpickle."""
    import geneva.cloudpickle as cloudpickle

    with pytest.warns(DeprecationWarning, match=r".*'cuda'.*deprecated.*"):

        @udf(cuda=True)
        def cuda_func(x: int) -> int:
            return x * 2

    # Serialize and deserialize
    pickled = cloudpickle.dumps(cuda_func)
    restored = cloudpickle.loads(pickled)

    # cuda=True sets num_gpus=1.0
    assert restored.num_gpus == 1.0
    assert restored.cuda is True


def test_cloudpickle_preserves_cpu_only() -> None:
    """Test that CPU-only UDFs (num_gpus=0) are preserved."""
    import geneva.cloudpickle as cloudpickle

    @udf(num_gpus=0.0)
    def cpu_func(x: int) -> int:
        return x * 2

    pickled = cloudpickle.dumps(cpu_func)
    restored = cloudpickle.loads(pickled)

    assert restored.num_gpus == 0.0
    assert restored.cuda is False


def test_struct_field_input_columns_supported() -> None:
    struct_type = pa.struct(
        [
            ("left", pa.string()),
            ("right", pa.string()),
            ("nested", pa.struct([("x", pa.int32()), ("y", pa.int32())])),
        ]
    )
    schema = pa.schema([pa.field("info", struct_type)])

    @udf(data_type=pa.string(), input_columns=["info.left"])
    def left_upper(left: str | None) -> str | None:
        return left.upper() if left is not None else None

    @udf(data_type=pa.int32(), input_columns=["info.nested.x"])
    def nested_x_plus_one(x: int | None) -> int | None:
        return x + 1 if x is not None else None

    # validate dotted column path against schema
    left_upper.validate_against_schema(schema)
    nested_x_plus_one.validate_against_schema(schema)

    rb = pa.RecordBatch.from_arrays(
        [
            pa.array(
                [
                    {
                        "left": "alpha",
                        "right": "one",
                        "nested": {"x": 1, "y": 10},
                    },
                    {
                        "left": "beta",
                        "right": "two",
                        "nested": {"x": 2, "y": 20},
                    },
                    {
                        "left": None,
                        "right": "three",
                        "nested": {"x": None, "y": None},
                    },
                ],
                type=struct_type,
            )
        ],
        ["info"],
    )

    assert left_upper(rb) == pa.array(["ALPHA", "BETA", None])
    assert nested_x_plus_one(rb) == pa.array([2, 3, None], type=pa.int32())


def test_struct_list_field_numpy_input() -> None:
    struct_type = pa.struct([("vals", pa.list_(pa.int32()))])
    schema = pa.schema([pa.field("info", struct_type)])

    @udf(data_type=pa.int32(), input_columns=["info.vals"])
    def sum_vals(vals: np.ndarray | None) -> int | None:
        if vals is None:
            return None
        assert isinstance(vals, np.ndarray)
        return int(np.sum(vals))

    sum_vals.validate_against_schema(schema)

    rb = pa.RecordBatch.from_arrays(
        [
            pa.array(
                [
                    {"vals": [1, 2, 3]},
                    {"vals": [1]},
                    {"vals": None},
                ],
                type=struct_type,
            )
        ],
        ["info"],
    )

    assert sum_vals(rb) == pa.array([6, 1, None], type=pa.int32())


def test_ndarray_annotation_requires_list_column() -> None:
    schema = pa.schema([pa.field("x", pa.int32())])

    @udf(data_type=pa.list_(pa.int32()))
    def expects_array(x: np.ndarray) -> np.ndarray:
        return x

    with pytest.raises(
        ValueError, match=r"numpy\.ndarray.*list, large_list, or fixed-size"
    ):
        expects_array.validate_against_schema(schema)


def test_list_annotation_requires_list_column() -> None:
    schema = pa.schema([pa.field("x", pa.int32())])

    @udf
    def expects_list(x: list[int]) -> int:
        return len(x)

    with pytest.raises(
        ValueError, match=r"Python list\. List annotations require Arrow list"
    ):
        expects_list.validate_against_schema(schema)


def test_required_params_more_than_input_columns_rejected() -> None:
    schema = pa.schema([pa.field("a", pa.int64()), pa.field("b", pa.int64())])

    @udf(data_type=pa.int64(), input_columns=["a"])
    def add_two(a: int, b: int) -> int:
        return a + b

    with pytest.raises(ValueError, match=r"expects at least 2 parameters"):
        add_two.validate_against_schema(schema)


@pytest.mark.parametrize(
    ("num_gpus", "num_cpus"),
    [
        (0.0, 1.0),
        (1.0, 2.0),
        (2.5, 4.0),
        (None, None),  # None means use defaults
    ],
)
def test_packager_preserves_gpu_cpu_settings(num_gpus, num_cpus) -> None:
    """Test that UDFPackager marshal/unmarshal preserves GPU/CPU settings."""
    from geneva.packager import DockerUDFPackager

    kwargs = {}
    if num_gpus is not None:
        kwargs["num_gpus"] = num_gpus
    if num_cpus is not None:
        kwargs["num_cpus"] = num_cpus

    @udf(**kwargs)
    def compute_func(x: int) -> int:
        return x * 3

    expected_num_gpus = num_gpus if num_gpus is not None else 0.0
    expected_num_cpus = num_cpus if num_cpus is not None else 1.0

    # Create packager without workspace (no workspace zip needed for this test)
    packager = DockerUDFPackager(prebuilt_docker_img="test:latest")

    # Marshal and unmarshal
    spec = packager.marshal(compute_func)
    restored = packager.unmarshal(spec)

    # Verify GPU/CPU settings are preserved
    assert restored.num_gpus == expected_num_gpus
    assert restored.num_cpus == expected_num_cpus
    assert restored.name == compute_func.name


def test_packager_preserves_cuda_deprecated() -> None:
    """Test that packager preserves cuda=True through marshal/unmarshal."""
    from geneva.packager import DockerUDFPackager

    with pytest.warns(DeprecationWarning, match=r".*'cuda'.*deprecated.*"):

        @udf(cuda=True, num_cpus=2.0)
        def cuda_compute(x: int) -> int:
            return x * 4

    packager = DockerUDFPackager(prebuilt_docker_img="test:latest")

    spec = packager.marshal(cuda_compute)
    restored = packager.unmarshal(spec)

    # cuda=True sets num_gpus=1.0
    assert restored.num_gpus == 1.0
    assert restored.cuda is True
    assert restored.num_cpus == 2.0

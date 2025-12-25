# ruff: noqa: ANN201, ANN202, PIE804
# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import numpy as np
import pyarrow as pa
import pytest

import geneva.udfs.embeddings as embedding_mod
from geneva import connect
from geneva.udfs.embeddings import sentence_transformer_udf


class DummySentenceTransformer:
    def __init__(self, model_name, device=None) -> None:
        self.model_name = model_name
        self.device = device

    def get_sentence_embedding_dimension(self) -> int:
        return 2

    def encode(self, values, **kwargs):
        return np.asarray(
            [[float(len(value)), float(len(value) + 1)] for value in values],
            dtype=np.float32,
        )


@pytest.fixture
def mock_sentence_transformers(monkeypatch):
    instances = []

    def _loader(model_name, device=None):
        model = DummySentenceTransformer(model_name, device=device)
        instances.append(model)
        return model

    def _patched_loader(model_name, device=None, trust_remote_code=False):
        return _loader(model_name, device=device)

    monkeypatch.setattr(
        embedding_mod._SentenceTransformersModel,
        "_load_model",
        staticmethod(_patched_loader),
    )
    monkeypatch.setattr(embedding_mod, "_resolve_device", lambda num_gpus: None)
    return instances


def test_mock_embedding_udf_flow(tmp_path, mock_sentence_transformers) -> None:
    db = connect(tmp_path)
    table = db.create_table(
        "documents",
        pa.Table.from_pydict({"body": ["hello", "world"]}),
    )

    udf = sentence_transformer_udf(
        "fake-model/1",
        column="body",
        normalize=False,
    )

    assert udf.func.dimension == 2

    batch = pa.RecordBatch.from_arrays([pa.array(["test"])], ["body"])
    assert udf(batch).to_pylist() == [[4.0, 5.0]]

    # test empty column handling
    empty_batch = pa.RecordBatch.from_arrays([pa.array([], type=pa.string())], ["body"])
    assert udf(empty_batch).to_pylist() == []

    table.add_columns({"embedding": udf})

    # test null handling
    batch_with_nulls = pa.RecordBatch.from_arrays(
        [pa.array(["geneva", None, "udf"])], ["body"]
    )
    assert len(udf(batch_with_nulls).to_pylist()) == 3


def test_missing_column(mock_sentence_transformers) -> None:
    udf = sentence_transformer_udf("fake-model/2", column="title")
    batch = pa.RecordBatch.from_arrays([pa.array(["hello"])], ["body"])
    with pytest.raises(ValueError, match="Column 'title' not found"):
        udf.func(batch)

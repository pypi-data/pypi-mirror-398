# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import attrs
from typing_extensions import Self  # noqa: UP035

from geneva.checkpoint import CheckpointConfig, CheckpointStore
from geneva.config import ConfigBase


@attrs.define
class JobConfig(ConfigBase):
    """Geneva Job Configurations."""

    checkpoint: CheckpointConfig = attrs.field(default=CheckpointConfig("tempfile"))

    batch_size: int = attrs.field(default=10240, converter=int)

    task_shuffle_diversity: int = attrs.field(default=8, converter=int)

    # How many fragments to be committed in one single transaction.
    commit_granularity: int = attrs.field(default=64, converter=int)

    # How many rows to delete per batch during point-in-time MV refresh rollback.
    delete_batch_size: int = attrs.field(default=10000, converter=int)

    @classmethod
    def name(cls) -> str:
        return "job"

    def make_checkpoint_store(self) -> CheckpointStore:
        return (self.checkpoint or CheckpointConfig("tempfile")).make()

    def with_overrides(
        self,
        *,
        batch_size: int | None = None,
        task_shuffle_diversity: int | None = None,
        commit_granularity: int | None = None,
        delete_batch_size: int | None = None,
    ) -> Self:
        if batch_size is not None:
            self.batch_size = batch_size
        if task_shuffle_diversity is not None:
            self.task_shuffle_diversity = task_shuffle_diversity
        if commit_granularity is not None:
            self.commit_granularity = commit_granularity
        if delete_batch_size is not None:
            self.delete_batch_size = delete_batch_size
        return self

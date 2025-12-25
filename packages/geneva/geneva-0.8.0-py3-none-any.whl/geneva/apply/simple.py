# ruff: noqa: PERF203

# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

# super simple applier

import logging

import attrs
import pyarrow as pa

from geneva.apply.applier import BatchApplier
from geneva.apply.error_handling import BatchStrategy, ErrorHandlingContext
from geneva.apply.task import MapTask, ReadTask
from geneva.debug.logger import ErrorLogger

_LOG = logging.getLogger(__name__)


@attrs.define
class SimpleApplier(BatchApplier):
    """
    A simple applier that applies a function to each element in the batch.
    """

    job_id: str = attrs.field(default="unknown")

    def run(
        self,
        read_task: ReadTask,
        map_task: MapTask,
        error_logger: ErrorLogger,
    ) -> pa.RecordBatch:
        batches = []
        for seq, batch in enumerate(
            read_task.to_batches(batch_size=map_task.batch_size())
        ):
            # Create error context and strategy for this batch
            ctx = ErrorHandlingContext.create(map_task, read_task, self.job_id, seq)
            strategy = BatchStrategy.from_context(ctx, map_task, error_logger)

            # Apply strategy - no branching needed!
            result_batch, error_records = strategy.apply(batch)

            # Log errors if any were collected
            if error_records:
                error_logger.log_errors(error_records)

            batches.append(result_batch)

        if not batches:
            return pa.RecordBatch.from_arrays([])

        schema = batches[0].schema
        combined_table = pa.Table.from_batches(batches, schema)
        combined_table = combined_table.combine_chunks()
        combined_batch = combined_table.to_batches()[0]

        _LOG.info(
            f"Simple applier: completed {map_task.name()} for {read_task} with "
            f"{len(combined_batch)} rows"
        )
        return combined_batch

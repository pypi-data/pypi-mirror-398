# ruff: noqa: PERF203
# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

# multi-process applier

import io
import logging
from typing import Literal

import attrs
import multiprocess
import pyarrow as pa

import geneva.cloudpickle as cloudpickle
from geneva.apply.applier import BatchApplier
from geneva.apply.error_handling import BatchStrategy, ErrorHandlingContext
from geneva.apply.task import MapTask, ReadTask
from geneva.debug.logger import ErrorLogger

_LOG = logging.getLogger(__name__)


def _buf_to_batch(
    data: bytes | memoryview,
    *,
    coalesce: bool = False,
) -> list[pa.RecordBatch] | pa.RecordBatch:
    """
    Convert a buffer to a record batch.
    """
    buf = io.BytesIO(data)
    with pa.ipc.open_stream(buf) as f:
        t = f.read_all()
    if not coalesce:
        return t.to_batches()
    else:
        return t.combine_chunks().to_batches()[0]


def _batch_to_buf(
    batch: pa.RecordBatch,
) -> bytes:
    """
    Convert a record batch to a buffer.
    """
    buf = io.BytesIO()
    with pa.ipc.new_stream(buf, schema=batch.schema) as f:
        f.write_batch(batch)
    buf.seek(0)
    return buf.getvalue()


def _apply_with_stream_buf(
    apply: bytes,
    buf: bytes,
) -> bytes:
    """
    Apply a function to a record batch using a stream buffer.
    """
    func = cloudpickle.loads(apply)
    out_buf = io.BytesIO()
    out_batches = [func(batch) for batch in _buf_to_batch(buf)]
    with pa.ipc.new_stream(out_buf, schema=out_batches[0].schema) as f:
        for batch in out_batches:
            f.write_batch(batch)

    return out_buf.getvalue()


@attrs.define
class MultiProcessBatchApplier(BatchApplier):
    """
    A multi-process applier that applies a function to each element in the batch.
    """

    num_processes: int = attrs.field(validator=attrs.validators.ge(1))

    method: Literal["fork", "spawn"] = attrs.field(default="fork")

    job_id: str = attrs.field(default="unknown")

    @staticmethod
    def _worker_apply(
        map_task_bytes: bytes,
        buf: bytes,
        error_config_bytes: bytes | None,
        job_id: str,
        task_context: dict,
        seq: int,
        udf_name: str,
        udf_version: str,
    ) -> tuple[bytes, bytes]:
        """Worker process: Apply strategy to batch with error handling

        This function runs in worker subprocesses. It deserializes the task,
        reconstructs the error handling strategy, and applies it to batches.

        Security Note:
            cloudpickle.loads() is safe here because this worker function only
            runs in subprocesses created by multiprocess.Pool from the same
            parent process. The serialized data originates from trusted code in
            the parent process, not from external/untrusted sources.

        Args:
            map_task_bytes: Pickled MapTask
            buf: Serialized RecordBatch(es)
            error_config_bytes: Pickled ErrorHandlingConfig (or None)
            job_id: Job identifier
            task_context: Table context (uri, version, fragment_id)
            seq: Batch sequence number
            udf_name: UDF name for logging
            udf_version: UDF version for logging

        Returns:
            tuple[bytes, bytes]: (result_batch_bytes, error_records_bytes)
                Both are serialized for return to main process
        """
        # Safe: deserializing trusted data from parent process
        map_task = cloudpickle.loads(map_task_bytes)
        error_config = (
            cloudpickle.loads(error_config_bytes) if error_config_bytes else None
        )

        # Create error handling context
        ctx = ErrorHandlingContext(
            job_id=job_id,
            task_context=task_context,
            seq=seq,
            udf_name=udf_name,
            udf_version=udf_version,
            error_config=error_config,
        )

        # Create strategy (no error_logger in worker process)
        strategy = BatchStrategy.from_context(ctx, map_task, error_logger=None)

        batches = _buf_to_batch(buf, coalesce=False)
        out_batches = []
        all_error_records = []

        # Ensure batches is always a list
        if isinstance(batches, pa.RecordBatch):
            batches = [batches]

        # Apply strategy to each batch - no branching!
        for batch in batches:
            result_batch, error_records = strategy.apply(batch)
            out_batches.append(result_batch)
            all_error_records.extend(error_records)

        out_buf = io.BytesIO()
        with pa.ipc.new_stream(out_buf, schema=out_batches[0].schema) as f:
            for batch in out_batches:
                f.write_batch(batch)

        # Serialize error records
        error_records_bytes = cloudpickle.dumps(all_error_records)

        return (out_buf.getvalue(), error_records_bytes)

    def _process_future_result(
        self,
        fut,
        ctx: ErrorHandlingContext,
        error_logger: ErrorLogger,
        all_error_records: list,
    ) -> pa.RecordBatch | list[pa.RecordBatch]:
        """Process a single future result with error handling"""
        try:
            result = fut.get()
            if ctx.error_config:
                # Unpack result and error records
                result_bytes, error_records_bytes = result
                error_records = cloudpickle.loads(error_records_bytes)
                all_error_records.extend(error_records)
                return _buf_to_batch(result_bytes, coalesce=True)
            else:
                return _buf_to_batch(result, coalesce=True)
        except Exception as e:
            # Log error with full context
            if ctx.error_config and ctx.error_config.log_errors:
                error_record = ctx.create_error_record(
                    exception=e,
                    row_address=None,
                    attempt=1,
                    max_attempts=1,
                )
                error_logger.log_error(error_record)
            raise

    def run(
        self,
        read_task: ReadTask,
        map_task: MapTask,
        error_logger: ErrorLogger,
    ) -> pa.RecordBatch:
        mp_ctx = (
            multiprocess.context.ForkContext()
            if self.method == "fork"
            else multiprocess.context.SpawnContext()
        )

        with mp_ctx.Pool(self.num_processes) as pool:
            # don't pull new batches until the previous ones are done
            # this way we reduce the number of batches in memory
            all_error_records = []  # Collect all errors for bulk write
            should_log_errors = None  # Track from first batch's context

            def _run_with_backpressure():  # noqa: ANN202
                nonlocal should_log_errors
                futs = []
                ctxs = []

                for seq, batch in enumerate(
                    read_task.to_batches(batch_size=map_task.batch_size())
                ):
                    # Create error context for this batch
                    ctx = ErrorHandlingContext.create(
                        map_task, read_task, self.job_id, seq
                    )
                    ctxs.append(ctx)

                    # Track error logging config from first batch
                    if should_log_errors is None:
                        should_log_errors = (
                            ctx.error_config and ctx.error_config.log_errors
                        )
                    data = _batch_to_buf(batch)

                    # Choose worker function based on error handling config
                    if ctx.error_config:
                        # Use error handling worker - returns tuple with error records
                        map_task_data = cloudpickle.dumps(map_task)
                        error_config_data = cloudpickle.dumps(ctx.error_config)
                        futs.append(
                            pool.apply_async(
                                MultiProcessBatchApplier._worker_apply,
                                args=(
                                    map_task_data,
                                    data,
                                    error_config_data,
                                    self.job_id,
                                    ctx.task_context,
                                    seq,
                                    ctx.udf_name,
                                    ctx.udf_version,
                                ),
                            )
                        )
                    else:
                        # Use simple worker - legacy behavior without error handling
                        udf_data = cloudpickle.dumps(map_task.apply)
                        futs.append(
                            pool.apply_async(
                                _apply_with_stream_buf, args=(udf_data, data)
                            )
                        )

                    # don't start waiting till we have primed the queue
                    if len(futs) >= self.num_processes + 1:
                        ctx = ctxs.pop(0)
                        fut = futs.pop(0)
                        yield self._process_future_result(
                            fut,
                            ctx,
                            error_logger,
                            all_error_records,
                        )

                while futs:
                    ctx = ctxs.pop(0)
                    fut = futs.pop(0)
                    yield self._process_future_result(
                        fut,
                        ctx,
                        error_logger,
                        all_error_records,
                    )

            batches = list(_run_with_backpressure())

            # Bulk write all collected error records
            if should_log_errors and all_error_records:
                error_logger.log_errors(all_error_records)

            if not batches:
                return pa.RecordBatch.from_arrays([])

            # Flatten any nested lists of batches
            flattened_batches: list[pa.RecordBatch] = []
            for item in batches:
                if isinstance(item, list):
                    flattened_batches.extend(item)
                else:
                    flattened_batches.append(item)

            if not flattened_batches:
                return pa.RecordBatch.from_arrays([])

            schema = flattened_batches[0].schema
            combined_table = pa.Table.from_batches(flattened_batches, schema)
            combined_table = combined_table.combine_chunks()
            combined_batch = combined_table.to_batches()[0]

            return combined_batch

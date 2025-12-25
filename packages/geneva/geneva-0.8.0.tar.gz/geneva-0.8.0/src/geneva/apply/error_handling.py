# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Error handling for batch processing.

This module provides:
- ErrorHandlingContext: Bundles job/task metadata for error logging
- BatchStrategy: Strategy pattern for different error handling behaviors
  - FailFastStrategy: No error handling, fail immediately
  - BatchRetryStrategy: Retry entire batch with tenacity
  - SkipRowsStrategy: Process rows individually, skip failures

All error handling logic is centralized here to eliminate branching in appliers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

import attrs
import pyarrow as pa
from tenacity import Retrying

from geneva.apply.task import BackfillUDFTask, MapTask, ReadTask
from geneva.debug.error_store import (
    ErrorHandlingConfig,
    FaultIsolation,
    make_error_record_from_exception,
)
from geneva.debug.logger import ErrorLogger

_LOG = logging.getLogger(__name__)


# =============================================================================
# Utility Functions
# =============================================================================


def get_max_attempts(retry_config) -> int:
    """Extract max attempts from retry config"""
    if hasattr(retry_config.stop, "max_attempt_number"):
        return retry_config.stop.max_attempt_number  # type: ignore[attr-defined]
    return 1


def build_retry_kwargs(retry_config, reraise: bool | None = None) -> dict:
    """Build tenacity Retrying kwargs from RetryConfig"""
    kwargs = {
        "retry": retry_config.retry,
        "stop": retry_config.stop,
        "wait": retry_config.wait,
        "reraise": reraise if reraise is not None else retry_config.reraise,
    }
    if retry_config.before_sleep is not None:
        kwargs["before_sleep"] = retry_config.before_sleep
    if retry_config.after_attempt is not None:
        kwargs["after"] = retry_config.after_attempt
    return kwargs


def extract_table_name(table_uri: str) -> str:
    """Extract table name from URI"""
    return table_uri.split("/")[-1].replace(".lance", "")


def create_result_batch(
    results: list,
    row_addr: pa.Array,
    col_name: str,
    output_type: pa.DataType,
    field_metadata: dict,
) -> pa.RecordBatch:
    """Create result RecordBatch with row addresses"""
    result_array = pa.array(results, type=output_type)
    schema = pa.schema(
        [
            pa.field(col_name, output_type, metadata=field_metadata),
            pa.field("_rowaddr", pa.uint64()),
        ]
    )
    return pa.record_batch([result_array, row_addr], schema=schema)


def get_error_handling_config(map_task: MapTask) -> ErrorHandlingConfig | None:
    """Extract error handling config from map task's UDF"""
    if isinstance(map_task, BackfillUDFTask):
        _, udf = next(iter(map_task.udfs.items()))
        if hasattr(udf, "error_handling"):
            return udf.error_handling
    return None


def _stable_udf_version(map_task: MapTask) -> str:
    """Return a stable identifier for logging (does not vary per batch)."""
    try:
        return map_task.checkpoint_prefix(
            dataset_uri="unknown",
            dataset_version=None,
            where=getattr(map_task, "where", None),
        )
    except Exception:
        try:
            return map_task.name()
        except Exception:
            return "unknown"


def extract_context_from_task(read_task: ReadTask) -> dict:
    """Extract table context from read task for error logging"""
    context: dict = {}
    try:
        context["table_uri"] = read_task.table_uri()
    except Exception:
        if hasattr(read_task, "uri"):
            context["table_uri"] = read_task.uri  # type: ignore[attr-defined]
    if hasattr(read_task, "version"):
        context["table_version"] = read_task.version  # type: ignore[attr-defined]
    if hasattr(read_task, "frag_id"):
        context["fragment_id"] = read_task.frag_id  # type: ignore[attr-defined]
    return context


# =============================================================================
# Error Handling Context
# =============================================================================


@attrs.define
class ErrorHandlingContext:
    """Bundles common error handling parameters to reduce repetition"""

    job_id: str
    task_context: dict  # table_uri, version, fragment_id
    seq: int
    udf_name: str
    udf_version: str
    error_config: ErrorHandlingConfig | None = None

    @classmethod
    def create(
        cls,
        map_task: MapTask,
        read_task: ReadTask,
        job_id: str,
        seq: int,
    ) -> "ErrorHandlingContext":
        """Create error handling context from tasks

        Args:
            map_task: The map task being executed
            read_task: The read task providing data
            job_id: Job identifier
            seq: Batch sequence number

        Returns:
            ErrorHandlingContext configured for the given tasks
        """
        error_config = get_error_handling_config(map_task)

        if error_config:
            error_config.validate_compatibility(map_task)

        task_context = extract_context_from_task(read_task)

        # Extract UDF info directly from map_task methods
        udf_name = map_task.name() if hasattr(map_task, "name") else "unknown"
        dataset_uri = task_context.get("table_uri", "unknown")
        dataset_version = task_context.get("table_version")
        where = getattr(map_task, "where", None)
        try:
            udf_version = map_task.checkpoint_prefix(
                dataset_uri=dataset_uri,
                dataset_version=dataset_version,
                where=where,
            )
        except Exception:
            udf_version = _stable_udf_version(map_task)

        return cls(
            job_id=job_id,
            task_context=task_context,
            seq=seq,
            udf_name=udf_name,
            udf_version=udf_version,
            error_config=error_config,
        )

    def create_error_record(
        self,
        exception: Exception,
        row_address: int | None,
        attempt: int,
        max_attempts: int,
    ) -> Any:
        """Create error record with this context"""
        table_uri = self.task_context.get("table_uri", "unknown")
        return make_error_record_from_exception(
            exception=exception,
            job_id=self.job_id,
            table_uri=table_uri,
            table_name=extract_table_name(table_uri),
            table_version=self.task_context.get("table_version"),
            column_name=self.udf_name,
            udf_name=self.udf_name,
            udf_version=self.udf_version,
            batch_index=self.seq,
            fragment_id=self.task_context.get("fragment_id"),
            row_address=row_address,
            attempt=attempt,
            max_attempts=max_attempts,
        )


# =============================================================================
# Batch Processing Strategies
# =============================================================================


class BatchStrategy(ABC):
    """Base class for batch processing strategies with error handling"""

    def __init__(
        self,
        ctx: ErrorHandlingContext,
        map_task: MapTask,
        error_logger: ErrorLogger | None = None,
    ) -> None:
        """
        Args:
            ctx: Error handling context with job/task metadata
            map_task: The task to apply to batches
            error_logger: Optional logger for errors (None in worker processes)
        """
        self.ctx = ctx
        self.map_task = map_task
        self.error_logger = error_logger

    @classmethod
    def from_context(
        cls,
        ctx: ErrorHandlingContext,
        map_task: MapTask,
        error_logger: ErrorLogger | None = None,
    ) -> "BatchStrategy":
        """Factory method to create appropriate strategy based on context

        Args:
            ctx: Error handling context
            map_task: The task to apply
            error_logger: Optional error logger

        Returns:
            Appropriate strategy instance
        """
        if not ctx.error_config:
            return FailFastStrategy(ctx, map_task, error_logger)

        if ctx.error_config.fault_isolation == FaultIsolation.SKIP_ROWS:
            return SkipRowsStrategy(ctx, map_task, error_logger)

        if ctx.error_config.retry_config:
            return BatchRetryStrategy(ctx, map_task, error_logger)

        return FailFastStrategy(ctx, map_task, error_logger)

    @abstractmethod
    def apply(self, batch: pa.RecordBatch) -> tuple[pa.RecordBatch, list[Any]]:
        """Apply the strategy to a batch

        Returns:
            (result_batch, error_records) - error_records may be empty
        """


class FailFastStrategy(BatchStrategy):
    """No error handling - fail immediately on any error"""

    def apply(self, batch: pa.RecordBatch) -> tuple[pa.RecordBatch, list[Any]]:
        """Apply without error handling, fail on first error"""
        try:
            result = self.map_task.apply(batch)
            return (result, [])
        except Exception as e:
            # Log error if error_logger is provided (either explicitly configured
            # via error_config.log_errors or just passed in)
            if self.error_logger and (
                not self.ctx.error_config or self.ctx.error_config.log_errors
            ):
                error_record = self.ctx.create_error_record(
                    exception=e,
                    row_address=None,
                    attempt=1,
                    max_attempts=1,
                )
                self.error_logger.log_error(error_record)
            raise


class BatchRetryStrategy(BatchStrategy):
    """Retry entire batch on failure, eventually fail the batch"""

    def apply(self, batch: pa.RecordBatch) -> tuple[pa.RecordBatch, list[Any]]:
        """Apply with retry logic, fail batch if retries exhausted"""
        if not self.ctx.error_config or not self.ctx.error_config.retry_config:
            raise ValueError("BatchRetryStrategy requires retry_config")

        retry_config = self.ctx.error_config.retry_config
        retry_kwargs = build_retry_kwargs(retry_config)
        max_attempts = get_max_attempts(retry_config)

        for attempt in Retrying(**retry_kwargs):
            with attempt:
                try:
                    result = self.map_task.apply(batch)

                    # Log successful retry if configured
                    if (
                        self.ctx.error_config.log_retry_attempts
                        and attempt.retry_state.attempt_number > 1
                    ):
                        _LOG.info(
                            f"UDF {self.ctx.udf_name} succeeded on attempt "
                            f"{attempt.retry_state.attempt_number} "
                            f"for batch {self.ctx.seq}"
                        )

                    return (result, [])

                except Exception as e:
                    self._log_retry_failure(
                        e, attempt.retry_state.attempt_number, max_attempts
                    )
                    raise

        raise RuntimeError("Retry loop exited unexpectedly")

    def _log_retry_failure(
        self, exception: Exception, current_attempt: int, max_attempts: int
    ) -> None:
        """Log retry failure with appropriate detail level"""
        should_log_to_store = (
            self.error_logger
            and self.ctx.error_config
            and self.ctx.error_config.log_errors
            and (
                self.ctx.error_config.log_retry_attempts
                or current_attempt >= max_attempts
            )
        )

        if should_log_to_store:
            error_record = self.ctx.create_error_record(
                exception=exception,
                row_address=None,
                attempt=current_attempt,
                max_attempts=max_attempts,
            )
            self.error_logger.log_error(error_record)  # type: ignore[union-attr]
        elif current_attempt > 1:
            # In worker process without logger, or not logging to store
            _LOG.warning(
                f"Retry attempt {current_attempt} failed "
                f"for batch {self.ctx.seq}: {exception}"
            )


class SkipRowsStrategy(BatchStrategy):
    """Process rows individually, skip failures, return partial results"""

    def apply(self, batch: pa.RecordBatch) -> tuple[pa.RecordBatch, list[Any]]:
        """Apply row-by-row, collecting results and errors"""
        if not isinstance(self.map_task, BackfillUDFTask):
            # Fall back to normal apply for non-UDF tasks
            return (self.map_task.apply(batch), [])

        col_name, udf = next(iter(self.map_task.udfs.items()))

        # Process each row, collecting results and errors
        results = []
        error_records = []

        for row_idx in range(len(batch)):
            row_batch = batch.slice(row_idx, 1)
            row_address_value = batch["_rowaddr"][row_idx].as_py()

            if row_address_value is None:
                _LOG.warning(f"Row {row_idx} has null _rowaddr, skipping")
                results.append(None)
                continue

            row_address = int(row_address_value)

            # Process single row (with retry if configured)
            result_value, error_record = self._process_row(
                row_batch, row_address, col_name
            )

            results.append(result_value)
            if error_record is not None:
                error_records.append(error_record)

        # Create result batch
        result_batch = create_result_batch(
            results=results,
            row_addr=batch["_rowaddr"],
            col_name=col_name,
            output_type=udf.data_type,
            field_metadata=udf.field_metadata,
        )

        return (result_batch, error_records)

    def _process_row(
        self, row_batch: pa.RecordBatch, row_address: int, col_name: str
    ) -> tuple[Any, Any]:
        """Process a single row, with retry if configured"""
        if self._should_retry():
            return self._process_row_with_retry(row_batch, row_address, col_name)
        else:
            return self._process_row_once(row_batch, row_address, col_name)

    def _should_retry(self) -> bool:
        """Check if row-level retry is configured"""
        if not self.ctx.error_config or not self.ctx.error_config.retry_config:
            return False
        max_attempts = get_max_attempts(self.ctx.error_config.retry_config)
        return max_attempts > 1

    def _process_row_once(
        self, row_batch: pa.RecordBatch, row_address: int, col_name: str
    ) -> tuple[Any, Any]:
        """Process row without retry"""
        try:
            result_batch = self.map_task.apply(row_batch)
            result_value = result_batch[col_name][0].as_py()
            return (result_value, None)
        except Exception as e:
            error_record = None
            if self.ctx.error_config and self.ctx.error_config.log_errors:
                error_record = self.ctx.create_error_record(
                    exception=e,
                    row_address=row_address,
                    attempt=1,
                    max_attempts=1,
                )

            _LOG.warning(
                f"Skipping row {row_address} in batch {self.ctx.seq} due to error: {e}"
            )
            return (None, error_record)

    def _process_row_with_retry(
        self, row_batch: pa.RecordBatch, row_address: int, col_name: str
    ) -> tuple[Any, Any]:
        """Process row with retry logic"""
        if not self.ctx.error_config or not self.ctx.error_config.retry_config:
            raise ValueError("_process_row_with_retry requires retry_config")

        retry_config = self.ctx.error_config.retry_config
        max_attempts = get_max_attempts(retry_config)
        retry_kwargs = build_retry_kwargs(retry_config, reraise=True)

        last_exception = None
        try:
            for attempt in Retrying(**retry_kwargs):
                with attempt:
                    try:
                        result_batch = self.map_task.apply(row_batch)
                        result_value = result_batch[col_name][0].as_py()

                        # Log successful retry if configured
                        if (
                            self.ctx.error_config.log_retry_attempts
                            and attempt.retry_state.attempt_number > 1
                        ):
                            _LOG.info(
                                f"UDF {self.ctx.udf_name} succeeded on attempt "
                                f"{attempt.retry_state.attempt_number} "
                                f"for row {row_address}"
                            )

                        return (result_value, None)

                    except Exception as e:
                        last_exception = e
                        if attempt.retry_state.attempt_number > 1:
                            _LOG.warning(
                                f"Retry attempt {attempt.retry_state.attempt_number} "
                                f"failed for row {row_address}: {e}"
                            )
                        raise

        except Exception:
            # Retries exhausted - skip this row
            _LOG.warning(
                f"Skipping row {row_address} in batch {self.ctx.seq} after "
                f"{max_attempts} attempts due to error: {last_exception}"
            )

            error_record = None
            if self.ctx.error_config.log_errors and last_exception:
                error_record = self.ctx.create_error_record(
                    exception=last_exception,
                    row_address=row_address,
                    attempt=max_attempts,
                    max_attempts=max_attempts,
                )

            return (None, error_record)

        # Fallback: should never reach here with reraise=True
        return (None, None)

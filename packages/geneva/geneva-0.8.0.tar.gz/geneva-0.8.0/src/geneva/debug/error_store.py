# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""Error storage and retry configuration for UDF execution"""

import enum
import logging
import traceback
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any, Optional

import attrs
import pyarrow as pa
from tenacity import (
    RetryCallState,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tenacity.retry import retry_base
from tenacity.stop import stop_base
from tenacity.wait import wait_base

from geneva.state.manager import BaseManager
from geneva.utils import dt_now_utc, escape_sql_string, retry_lance

_LOG = logging.getLogger(__name__)

GENEVA_ERRORS_TABLE_NAME = "geneva_errors"


class FaultIsolation(enum.Enum):
    """Strategy for isolating UDF failures"""

    FAIL_BATCH = "fail_batch"  # Fail entire batch on any error (default)
    SKIP_ROWS = "skip_rows"  # Skip individual failing rows (scalar UDFs only)


@attrs.define
class UDFRetryConfig:
    """Retry configuration for UDF execution using tenacity semantics"""

    # Tenacity retry condition - which exceptions to retry
    retry: retry_base = attrs.field(
        factory=lambda: retry_if_exception_type(())  # No retries by default
    )

    # Stop condition - when to give up
    stop: stop_base = attrs.field(factory=lambda: stop_after_attempt(1))

    # Wait strategy - how long to wait between retries
    wait: wait_base = attrs.field(
        factory=lambda: wait_exponential(multiplier=1, min=1, max=60)
    )

    # Optional callbacks
    before_sleep: Callable[[RetryCallState], None] | None = attrs.field(default=None)
    after_attempt: Callable[[RetryCallState], None] | None = attrs.field(default=None)

    # Whether to reraise exception after retries exhausted
    reraise: bool = attrs.field(default=True)

    @classmethod
    def no_retry(cls) -> "UDFRetryConfig":
        """No retries - fail immediately (default behavior)"""
        return cls()

    @classmethod
    def retry_transient(cls, max_attempts: int = 3) -> "UDFRetryConfig":
        """Retry common transient errors (network, timeouts)

        Parameters
        ----------
        max_attempts : int
            Maximum number of attempts including the initial try
        """
        return cls(
            retry=retry_if_exception_type((OSError, TimeoutError, ConnectionError)),
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=1, max=60),
        )


@attrs.define
class ErrorHandlingConfig:
    """Configuration for UDF error handling behavior"""

    # Retry policy using tenacity
    retry_config: UDFRetryConfig = attrs.field(factory=UDFRetryConfig.no_retry)

    # How to isolate failures
    fault_isolation: FaultIsolation = attrs.field(default=FaultIsolation.FAIL_BATCH)

    # Whether to log errors to the error table
    log_errors: bool = attrs.field(default=True)

    # Whether to log all retry attempts (not just final failures)
    log_retry_attempts: bool = attrs.field(default=False)

    def validate_compatibility(self, map_task) -> None:
        """Validate that this error config is compatible with the given task

        Args:
            map_task: The MapTask to validate against

        Raises:
            ValueError: If SKIP_ROWS is used with RecordBatch UDF
        """
        from geneva.apply.task import BackfillUDFTask
        from geneva.transformer import UDFArgType

        if self.fault_isolation != FaultIsolation.SKIP_ROWS:
            return

        # SKIP_ROWS only works with scalar/array UDFs, not RecordBatch UDFs
        if isinstance(map_task, BackfillUDFTask):
            _, udf = next(iter(map_task.udfs.items()))
            if hasattr(udf, "arg_type") and udf.arg_type == UDFArgType.RECORD_BATCH:
                raise ValueError(
                    "SKIP_ROWS fault isolation cannot be used with "
                    "RecordBatch UDFs. RecordBatch UDFs process entire "
                    "batches and cannot skip individual rows. "
                    "Use FAIL_BATCH instead."
                )


@attrs.define(kw_only=True)
class ErrorRecord:
    """UDF execution error record, stored in geneva_errors table"""

    # Unique error ID
    error_id: str = attrs.field(factory=lambda: str(uuid.uuid4()))

    # Error details
    error_type: str = attrs.field()  # Exception.__class__.__name__
    error_message: str = attrs.field()
    error_trace: str = attrs.field()  # Full traceback

    # Job/Table context
    job_id: str = attrs.field()
    table_uri: str = attrs.field()  # Full URI to the table
    table_name: str = attrs.field()
    table_version: Optional[int] = attrs.field(default=None)  # Read version
    column_name: str = attrs.field()

    # UDF context
    udf_name: str = attrs.field()
    udf_version: str = attrs.field()

    # Execution context (Ray/distributed)
    actor_id: Optional[str] = attrs.field(default=None)
    fragment_id: Optional[int] = attrs.field(default=None)
    batch_index: int = attrs.field()  # Sequence number within fragment

    # Row-level granularity (for scalar UDFs)
    row_address: Optional[int] = attrs.field(default=None)

    # Retry context
    attempt: int = attrs.field(default=1)
    max_attempts: int = attrs.field(default=1)

    # Timestamp
    timestamp: datetime = attrs.field(
        factory=dt_now_utc, metadata={"pa_type": pa.timestamp("us", tz="UTC")}
    )


class ErrorStore(BaseManager):
    """Store and query error records in a Lance table"""

    def get_model(self) -> Any:
        return ErrorRecord(
            error_type="InitError",
            error_message="init",
            error_trace="",
            job_id="init",
            table_uri="init",
            table_name="init",
            column_name="init",
            udf_name="init",
            udf_version="init",
            batch_index=0,
            table_version=0,
        )

    def get_table_name(self) -> str:
        return GENEVA_ERRORS_TABLE_NAME

    @retry_lance
    def log_error(self, error: ErrorRecord) -> None:
        """Log an error record to the error table

        Parameters
        ----------
        error : ErrorRecord
            The error record to log
        """
        self.get_table().add([attrs.asdict(error)])
        _LOG.info(
            f"Logged error {error.error_id}: {error.error_type} in "
            f"{error.table_name}.{error.column_name} (attempt {error.attempt})"
        )

    @retry_lance
    def log_errors(self, errors: list[ErrorRecord]) -> None:
        """Log multiple error records to the error table in a single operation

        Parameters
        ----------
        errors : list[ErrorRecord]
            The error records to log
        """
        if not errors:
            return

        self.get_table().add([attrs.asdict(error) for error in errors])
        _LOG.info(f"Logged {len(errors)} errors in bulk")

    def get_errors(
        self,
        job_id: str | None = None,
        table_name: str | None = None,
        column_name: str | None = None,
        error_type: str | None = None,
    ) -> list[ErrorRecord]:
        """Query error records with optional filters

        Parameters
        ----------
        job_id : str, optional
            Filter by job ID
        table_name : str, optional
            Filter by table name
        column_name : str, optional
            Filter by column name
        error_type : str, optional
            Filter by error type (exception class name)

        Returns
        -------
        list[ErrorRecord]
            List of matching error records
        """
        wheres = []
        if job_id:
            wheres.append(f"job_id = '{escape_sql_string(job_id)}'")
        if table_name:
            wheres.append(f"table_name = '{escape_sql_string(table_name)}'")
        if column_name:
            wheres.append(f"column_name = '{escape_sql_string(column_name)}'")
        if error_type:
            wheres.append(f"error_type = '{escape_sql_string(error_type)}'")

        query = self.get_table(True).search()
        if wheres:
            query = query.where(" and ".join(wheres))

        # Only select known fields for forward compatibility
        known_fields = [f.name for f in attrs.fields(ErrorRecord)]
        results = query.select(known_fields).to_arrow().to_pylist()

        return [self._safe_error_record(rec) for rec in results]

    def _safe_error_record(self, rec_dict: dict) -> ErrorRecord:
        """Create ErrorRecord from dict, ignoring unknown fields"""
        known_fields = {f.name for f in attrs.fields(ErrorRecord)}
        filtered = {k: v for k, v in rec_dict.items() if k in known_fields}
        return ErrorRecord(**filtered)

    def get_failed_row_addresses(self, job_id: str, column_name: str) -> list[int]:
        """Get row addresses for all failed rows in a job

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
        """
        errors = self.get_errors(job_id=job_id, column_name=column_name)
        row_addresses = [
            err.row_address for err in errors if err.row_address is not None
        ]
        return row_addresses


def make_error_record_from_exception(
    exception: Exception,
    *,
    job_id: str,
    table_uri: str,
    table_name: str,
    table_version: int | None,
    column_name: str,
    udf_name: str,
    udf_version: str,
    batch_index: int,
    fragment_id: int | None = None,
    actor_id: str | None = None,
    row_address: int | None = None,
    attempt: int = 1,
    max_attempts: int = 1,
) -> ErrorRecord:
    """Factory function to create an ErrorRecord from an exception

    Parameters
    ----------
    exception : Exception
        The exception that occurred
    job_id : str
        Job ID
    table_uri : str
        URI of the table being processed
    table_name : str
        Name of the table
    table_version : int | None
        Version of the table being read
    column_name : str
        Column being computed
    udf_name : str
        Name of the UDF
    udf_version : str
        Version of the UDF
    batch_index : int
        Batch sequence number
    fragment_id : int | None, optional
        Fragment ID if applicable
    actor_id : str | None, optional
        Ray actor ID if applicable
    row_address : int | None, optional
        Row address for row-level errors
    attempt : int, optional
        Current retry attempt number
    max_attempts : int, optional
        Maximum retry attempts

    Returns
    -------
    ErrorRecord
        The constructed error record
    """
    return ErrorRecord(
        error_type=type(exception).__name__,
        error_message=str(exception),
        error_trace=traceback.format_exc(),
        job_id=job_id,
        table_uri=table_uri,
        table_name=table_name,
        table_version=table_version,
        column_name=column_name,
        udf_name=udf_name,
        udf_version=udf_version,
        actor_id=actor_id,
        fragment_id=fragment_id,
        batch_index=batch_index,
        row_address=row_address,
        attempt=attempt,
        max_attempts=max_attempts,
    )

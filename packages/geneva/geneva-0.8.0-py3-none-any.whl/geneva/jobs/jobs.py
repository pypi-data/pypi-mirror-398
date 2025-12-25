# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import base64
import enum
import json
import logging
import uuid
from datetime import datetime
from enum import Enum, unique
from typing import Any, Optional

import attrs
import pyarrow as pa

from geneva.db import Connection
from geneva.state.manager import BaseManager
from geneva.utils import current_user, dt_now_utc, escape_sql_string, retry_lance

GENEVA_JOBS_TABLE_NAME = "geneva_jobs"

_LOG = logging.getLogger(__name__)


@unique
class JobStatus(Enum):
    """Status of a Job"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


@attrs.define(kw_only=True)
class JobMetric:
    name: str = attrs.field()
    n: int = attrs.field()
    total: int = attrs.field()
    done: bool = attrs.field()
    desc: str = attrs.field()


@attrs.define(kw_only=True)
class JobRecord:
    """A Feature Engineering Job record.

    When a backfill or refresh is triggered, these records contain the job's details for
    history tracking and also provides references for jobs if they are still running
    so other users can track it.

    User should not directly construct this object.
    """

    table_name: str = attrs.field()
    column_name: str = attrs.field()
    job_id: str = attrs.field(factory=lambda: str(uuid.uuid4()))
    job_type: str = attrs.field(default="BACKFILL")
    object_ref: Optional[str] = attrs.field(default=None)
    status: JobStatus = attrs.field(
        default=JobStatus.PENDING, metadata={"pa_type": pa.string()}
    )
    launched_at: datetime = attrs.field(
        factory=lambda: dt_now_utc(), metadata={"pa_type": pa.timestamp("us", tz="UTC")}
    )
    completed_at: Optional[datetime] = attrs.field(
        default=None, metadata={"pa_type": pa.timestamp("us", tz="UTC")}
    )
    config: str = attrs.field(default="{}")

    # v0.2.x additions
    launched_by: Optional[str] = attrs.field(factory=current_user)

    # 0.4.x additions
    manifest_id: Optional[str] = attrs.field(default=None)
    manifest_checksum: Optional[str] = attrs.field(default=None)

    metrics: Optional[list[JobMetric]] = attrs.field(
        default=[],
        metadata={"pa_type": pa.list_(pa.string())},
    )

    events: Optional[list[str]] = attrs.field(
        default=[], metadata={"pa_type": pa.list_(pa.string())}
    )

    # 0.9.x additions
    updated_at: Optional[datetime] = attrs.field(
        default=None, metadata={"pa_type": pa.timestamp("us", tz="UTC")}
    )


def _safe_job_record(jr_dict: dict) -> JobRecord:
    """Create JobRecord from dict, ignoring unknown fields for forward compatibility.

    This allows old clients to read tables with new columns they don't understand.
    """
    known_fields = {f.name for f in attrs.fields(JobRecord)}
    filtered = {k: v for k, v in jr_dict.items() if k in known_fields}
    jm = []
    for m in filtered.get("metrics", []) or []:
        if m:
            jm.append(JobMetric(**json.loads(m)))  # noqa: PERF401
    filtered["metrics"] = jm

    return JobRecord(**filtered)


class JobStateManager(BaseManager):
    def __init__(
        self,
        genevadb: Connection,
        jobs_table_name: str | None = None,
        namespace: list[str] | None = None,
    ) -> None:
        super().__init__(genevadb, jobs_table_name, namespace=namespace)

    def get_table_name(self) -> str:
        return GENEVA_JOBS_TABLE_NAME

    def get_model(self) -> Any:
        return JobRecord(table_name="dummytable", column_name="dummycol")

    @retry_lance
    def launch(self, table_name: str, column_name: str, **kwargs) -> JobRecord:
        args = kwargs.copy()
        args.pop("udf", None)  # Remove the udf argument (TODO serialized it)

        # Extract manifest fields if provided
        manifest_id = args.pop("manifest_id", None)
        manifest_checksum = args.pop("manifest_checksum", None)

        jr = JobRecord(
            table_name=table_name,
            column_name=column_name,
            config=json.dumps(args),
            manifest_id=manifest_id,
            manifest_checksum=manifest_checksum,
            launched_at=dt_now_utc(),
            updated_at=dt_now_utc(),
        )
        self.get_table().add(
            [
                attrs.asdict(
                    jr,
                    value_serializer=lambda obj, a, v: v.value
                    if isinstance(v, enum.Enum)
                    else v,
                )
            ]
        )
        return jr

    @retry_lance
    def set_object_ref(self, job_id: str, object_ref: bytes) -> None:
        self.get_table().update(
            where=f"job_id = '{escape_sql_string(job_id)}'",
            # TODO why can't lance handle bytes in an update directly?
            values={
                "object_ref": base64.b64encode(object_ref).decode("utf-8"),
                "updated_at": dt_now_utc(),
            },
        )

    @retry_lance
    def update_metrics(self, job_id: str, metrics: dict[str, dict]) -> None:
        # convert to list of json strings for storage
        m = []
        for name, v in metrics.items():
            vm = dict(v)
            vm["name"] = name
            m.append(json.dumps(vm))

        _LOG.debug(f"upsert metrics: {m}")

        self.get_table().update(
            where=f"job_id = '{escape_sql_string(job_id)}'",
            values={
                "metrics": m,
                "updated_at": dt_now_utc(),
            },
        )

    @retry_lance
    def _set_status(self, job_id: str, status: JobStatus) -> None:
        self.get_table().update(
            where=f"job_id = '{escape_sql_string(job_id)}'",
            values={
                "status": status.value,
                "updated_at": dt_now_utc(),
            },
        )

    @retry_lance
    def _add_event(self, job_id: str, event: str) -> None:
        jobs = self.get(job_id)
        if not jobs:
            raise ValueError(f"Job with ID {job_id} not found")
        job = jobs[0]
        events = job.events or []
        # this is not atomic - can we use sql to append?
        new_events = events + [event]
        self.get_table().update(
            where=f"job_id = '{escape_sql_string(job_id)}'",
            values={"events": new_events, "updated_at": dt_now_utc()},
        )

    def set_running(self, job_id: str) -> None:
        self._add_event(job_id, "Job started")
        self._set_status(job_id, JobStatus.RUNNING)

    def set_failed(self, job_id: str, msg: str) -> None:
        self._add_event(job_id, f"Job failed: {msg}")
        self._set_status(job_id, JobStatus.FAILED)

    @retry_lance
    def list_jobs(
        self, table_name: str | None = None, status: str | None = "RUNNING"
    ) -> list[JobRecord]:
        # TODO: Currently need to use tbl._ltbl.search() instead of tbl.search()
        # because geneva table semantics are not consistent with lancedb's currently
        known_cols = [f.name for f in attrs.fields(JobRecord)]

        wheres = (
            [f"table_name = '{escape_sql_string(table_name)}'"] if table_name else []
        )

        if status is not None:
            wheres.append(f"status == '{status}'")

        jrs = (
            self.get_table(True)
            .search()
            .where(" and ".join(wheres))
            .select(known_cols)
            .to_arrow()
            .to_pylist()
        )
        return [_safe_job_record(jr) for jr in jrs]

    @retry_lance
    def get(self, job_id: str) -> list[JobRecord]:
        # TODO: Currently need to use tbl._ltbl.search() instead of tbl.search()
        # because geneva table semantics are not consistent with lancedb's currently
        # Need to get latest because updates can come from other processes
        known_cols = [f.name for f in attrs.fields(JobRecord)]
        q = (
            self.get_table(True)
            .search()
            .where(f"job_id = '{escape_sql_string(job_id)}'")
            .select(known_cols)
        )
        return [_safe_job_record(jr) for jr in q.to_arrow().to_pylist()]

    @retry_lance
    def set_completed(self, job_id: str, status: str = "DONE") -> None:
        self._add_event(job_id, f"Job completed with status {status}")
        self.get_table().update(
            where=f"job_id = '{escape_sql_string(job_id)}'",
            values={
                "status": status,
                "completed_at": dt_now_utc(),
                "updated_at": dt_now_utc(),
            },
        )

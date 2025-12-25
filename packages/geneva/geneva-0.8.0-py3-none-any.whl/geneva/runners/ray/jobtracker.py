# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors
import json
import logging
import time

import attr
import attrs
import ray
from lancedb import AsyncConnection, AsyncTable
from lancedb.namespace import AsyncLanceNamespaceDBConnection
from lancedb.util import (
    value_to_sql,
)

from geneva.jobs.jobs import GENEVA_JOBS_TABLE_NAME
from geneva.table import TableReference
from geneva.utils import dt_now_utc, escape_sql_string

_LOG = logging.getLogger(__name__)


@ray.remote
@attrs.define
class JobTracker:
    """
    Centralized progress ledger for a job.
    - Metrics are arbitrary strings -> {n, total, done, desc}
    - All ops are atomic via the actor's mailbox.
    - DB saves can be disabled entirely with enable_saves=False
    """

    job_id: str

    table_ref: TableReference = attrs.field()

    metrics: dict[str, dict] = attrs.field(factory=dict)

    enable_saves: bool = attrs.field(default=True)

    min_time_between_updates_secs: float = attrs.field(default=5.0)

    # use async lancedb connection to avoid blocking Ray Tasks
    _db: AsyncConnection | AsyncLanceNamespaceDBConnection | None = attrs.field(
        init=False, default=None
    )

    _jobs_table: AsyncTable | None = attrs.field(init=False, default=None)

    _last_updated: float = attrs.field(init=False, default=-float("inf"))

    async def _upsert(
        self, name: str, *, total: int | None = None, desc: str | None = None
    ) -> None:
        """
        Given a metric 'name', ensure that the metric entry is present with specified
        values or initialized with 0s.
        This will flush the metrics to the underlying lance table if
        min_time_between_updates_secs is exceeded
        """
        m = self.metrics.get(name)
        if m is None:
            m = {"n": 0, "total": 0, "done": False, "desc": name}
            self.metrics[name] = m
        if total is not None:
            m["total"] = int(total)
        if desc is not None:
            m["desc"] = desc
        # auto-done if we're already at/over total
        if m["total"] and m["n"] >= m["total"]:
            m["done"] = True

        await self._save_with_throttle()

    # Generic metric API
    async def set_total(self, name: str, total: int) -> None:
        await self._upsert(name, total=total)

    async def set_desc(self, name: str, desc: str) -> None:
        await self._upsert(name, desc=desc)

    async def set(self, name: str, n: int) -> None:
        await self._upsert(name)
        m = self.metrics[name]
        m["n"] = int(n)
        if m["total"] and m["n"] >= m["total"]:
            m["done"] = True
            await self._save_with_throttle(force=True)

    async def increment(self, name: str, delta: int = 1) -> None:
        await self._upsert(name)
        m = self.metrics[name]
        m["n"] += int(delta)
        if m["total"] and m["n"] >= m["total"]:
            m["done"] = True
            await self._save_with_throttle(force=True)

    async def mark_done(self, name: str) -> None:
        await self._upsert(name)
        self.metrics[name]["done"] = True
        await self._save_with_throttle(force=True)

    # Read APIs
    async def get_progress(self, name: str) -> dict:
        await self._upsert(name)
        m = self.metrics[name]
        return {"n": m["n"], "total": m["total"], "done": m["done"], "desc": m["desc"]}

    def get_all(self) -> dict[str, dict]:
        # Shallow copy for safety
        return {k: dict(v) for k, v in self.metrics.items()}

    async def _save_with_throttle(self, force: bool = False) -> None:
        """Save metrics to DB, optionally bypassing throttle."""
        current_time = time.time()
        if (
            not force
            and self._last_updated + self.min_time_between_updates_secs > current_time
        ):
            # don't update metrics too frequently to avoid excessive DB writes
            return

        # bump last update and save metrics
        self._last_updated = current_time
        await self._save_metrics(attr.asdict(self)["metrics"])

    async def _save_metrics(self, _metrics: dict[str, dict]) -> None:
        if not self.enable_saves:
            return
        if not _metrics:
            return

        try:
            # lazy load db and table
            if not self._db:
                if not self.table_ref:
                    _LOG.error(
                        "JobTracker missing table_ref, metrics will not be saved"
                    )
                    return
                self._db = await self.table_ref.open_db_async()
                # Use system_namespace if available (for namespace connections)
                namespace = (
                    self.table_ref.system_namespace
                    if self.table_ref.system_namespace
                    else []
                )
                self._jobs_table = await self._db.open_table(
                    GENEVA_JOBS_TABLE_NAME, namespace=namespace
                )

            updates = {
                "metrics": self._convert_metrics(_metrics),
                "updated_at": dt_now_utc(),
            }
            updates_sql = {k: value_to_sql(v) for k, v in updates.items()}
            _LOG.debug(f"Saving metrics for job {self.job_id}: {updates_sql}")
            start = time.time()

            await self._jobs_table.update(
                where=f"job_id = '{escape_sql_string(self.job_id)}'",
                updates_sql=updates_sql,
            )
            _LOG.info(
                f"Saved metrics for job "
                f"{self.job_id} in {(time.time() - start) * 1000:.0f}ms"
            )

        except AttributeError as e:
            _LOG.warning(
                f"unable to save metrics. The execution manifest"
                f"may be using an older Geneva version than the client"
                f": {e}"
            )
        except Exception as e:
            _LOG.error(f"error saving metrics {e}")
            self._db = None  # force retry on next save

    def _convert_metrics(self, _metrics: dict[str, dict]) -> list[str]:
        """Convert metrics to list of json strings for storage"""
        m = []
        for name, v in _metrics.items():
            vm = dict(v)
            vm["name"] = name
            m.append(json.dumps(vm))
        return m

    def __str__(self) -> str:
        return f"JobTracker(job_id={self.job_id})"

    def __repr__(self) -> str:
        return str(self)

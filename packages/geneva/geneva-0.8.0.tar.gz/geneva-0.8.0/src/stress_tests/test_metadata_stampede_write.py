# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

# Reproduces a thundering write herd against the GCS auth token metadata server from
# Ray workers.

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pytest
import ray
from yarl import URL

if TYPE_CHECKING:
    from geneva.runners.ray.raycluster import RayCluster

_LOG = logging.getLogger(__name__)

KEY_PREFIX: str = "stampede-test/ckpts"  # subdir under root


@ray.remote(num_cpus=0.1, memory=256 * 1024**2, max_restarts=1, max_task_retries=3)
class StoreWriter:
    """
    One actor = one process = one CheckpointStore.
    Writes a *disjoint* shard of keys: [start, start+count).
    """

    def __init__(self, root: str, checkpointer: str) -> None:
        # one checkpointer per actor
        from geneva.checkpoint import LanceCheckpointStore

        self.store = LanceCheckpointStore(root)

    def run_range(self, start: int, count: int) -> int:
        ok = 0
        # Write *distinct* keys so no two writers collide
        for i in range(count):
            key = f"{start + i:08d}"
            # vary payload to avoid storage-side no-ops
            batch = pa.record_batch({"a": [start + i]})  # type: ignore[arg-type]
            self.store[key] = batch
            ok += 1
        _LOG.info(
            "writer %s wrote %d keys (start=%d, count=%d)",
            ray.get_runtime_context().get_actor_id(),
            ok,
            start,
            count,
        )
        return ok


def _maybe_pin_to_one_node() -> dict[str, Any]:
    from ray.util.scheduling_strategies import NodeAffinitySchedulingStrategy

    nodes: list[dict[str, Any]] = [n for n in ray.nodes() if n.get("Alive")]
    target: dict[str, Any] = next(
        (n for n in nodes if not n["Resources"].get("node:__ray_head__")), nodes[0]
    )
    return {
        "scheduling_strategy": NodeAffinitySchedulingStrategy(
            node_id=target["NodeID"], soft=True
        )
    }


def _shard_counts(total: int, parts: int) -> list[int]:
    """
    Split `total` as evenly as possible across `parts`, preserving sum(total).
    Example: total=10, parts=3 -> [4,3,3]
    """
    base = total // parts
    rem = total % parts
    return [base + (1 if i < rem else 0) for i in range(parts)]


@pytest.mark.skip(
    reason="This test does not realisticly capture how geneva would recover."
)
@pytest.mark.limit
@pytest.mark.gcp_only
@pytest.mark.parametrize("scale", [120])  # number of writer actors
@pytest.mark.parametrize(
    "keys_total", [100000]
)  # total distinct keys across all writers
@pytest.mark.parametrize(
    "checkpointer",
    [
        "session",
        pytest.param(
            "file",
            marks=pytest.mark.xfail(
                strict=True, reason="expected to fail under distributed write load"
            ),
        ),
    ],
)
def test_lance_checkpoint_single_store_many_unique_writes(
    beefy_cluster: RayCluster,
    geneva_test_bucket: str,
    checkpointer: str,
    scale: int,
    keys_total: int,
) -> None:
    """
    WRITE-path stress: N writers, each responsible for a *disjoint* key range.
    Targets 20k unique keys total (configurable), avoiding key-level hotspots while
    stressing connection reuse, auth/metadata churn, and object PUT throughput.
    """
    ckp_root = str(URL(geneva_test_bucket) / "stampede-test" / KEY_PREFIX)
    if not ckp_root.startswith("gs://"):
        pytest.skip(
            "Set GENEVA_LANCE_CKPT_ROOT=gs://<bucket>/<prefix> to run this test."
        )

    _LOG.info(
        "starting unique-key writes: checkpointer=%s actors=%d total_keys=%d",
        checkpointer,
        scale,
        keys_total,
    )

    with beefy_cluster:
        pin_opts = _maybe_pin_to_one_node()

        # Create writers
        writers = [
            StoreWriter.options(num_cpus=0.25, **pin_opts).remote(
                ckp_root, checkpointer
            )
            for _ in range(scale)
        ]

        # Partition the 0..keys_total-1 keyspace across writers
        counts = _shard_counts(keys_total, scale)
        starts = []
        acc = 0
        for c in counts:
            starts.append(acc)
            acc += c

        # Launch disjoint-range writes
        refs = [
            w.run_range.remote(start, count)  # type: ignore[attr-defined]
            for w, start, count in zip(writers, starts, counts, strict=False)
        ]

        failures = 0
        successes = 0
        # Allow for PUT latency; scale with total writes per actor
        max_actor_count = max(counts) if counts else 0
        per_actor_timeout = max(300.0, max_actor_count * 0.25)  # ~4 writes/sec floor

        for ref in refs:
            try:
                successes += ray.get(ref, timeout=per_actor_timeout)  # type: ignore[operator]
            except Exception as e:  # noqa: PERF203
                failures += 1
                _LOG.warning("writer actor failed: %r", e)

        _LOG.info(
            "unique-writes summary: checkpointer=%s actors=%d total_keys=%d "
            "successes=%d failures=%d root=%s",
            checkpointer,
            scale,
            keys_total,
            successes,
            failures,
            ckp_root,
        )

    # Sessionized store should pass; file-backed expected to fail under load.
    assert failures == 0, f"Expected all to complete; saw {failures} failures"

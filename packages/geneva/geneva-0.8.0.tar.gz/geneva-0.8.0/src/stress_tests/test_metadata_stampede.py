# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

# Reproduces a thundering read herd against the GCS auth token metadata server from Ray
# workers.

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

KEYSET_SIZE: int = 500  # unique checkpoint files to cycle over
KEY_PREFIX: str = "stampede-test/ckpts"  # subdir under root


def _maybe_pin_to_one_node() -> dict[str, Any]:
    from ray.util.scheduling_strategies import NodeAffinitySchedulingStrategy

    nodes: list[dict[str, Any]] = [n for n in ray.nodes() if n.get("Alive")]
    target: dict[str, Any] = next(
        (n for n in nodes if not n["Resources"].get("node:__ray_head__")), nodes[0]
    )
    # soft pin needed becausd if False, can get stuck
    strat = NodeAffinitySchedulingStrategy(node_id=target["NodeID"], soft=True)
    return {"scheduling_strategy": strat}


def _ensure_keyset(store, n: int) -> list[str]:
    """Create n tiny checkpoint files if missing; return their keys."""
    keys: list[str] = []
    batch = pa.record_batch({"a": [1]})  # type: ignore[arg-type]
    for i in range(n):
        key = f"{i:06d}"
        keys.append(key)
        # avoid double-touch: try get and write only if absent
        try:
            if key not in store:
                store[key] = batch
        except Exception:
            # Some stores (or perms) might not allow contains; fall back to best effort
            try:
                store[key] = batch
            except Exception as e:
                raise RuntimeError(
                    f"Failed to prepare checkpoint key {key}: {e}"
                ) from e
    return keys


@ray.remote(num_cpus=0.1, memory=256 * 1024**2, max_restarts=1, max_task_retries=3)
class StoreReader:
    """One actor = one process = one LanceCheckpointStore. Single-threaded, many
    sequential reads."""

    def __init__(self, root: str, mode: str, checkpointer: str) -> None:
        # one checkpointer per actor
        self.mode = mode
        from geneva.checkpoint import LanceCheckpointStore

        self.store = LanceCheckpointStore(root)

    def run(self, keys: list[str], ops: int) -> int:
        ok = 0
        if self.mode == "getitem":
            for i in range(ops):
                _ = self.store[keys[i % len(keys)]]
                ok += 1
            _LOG.info(
                "reader %s completed %d getitem ops",
                ray.get_runtime_context().get_actor_id(),
                ok,
            )
            return ok

        # "contains" mode
        for i in range(ops):
            _ = keys[i % len(keys)] in self.store
            ok += 1
        _LOG.info(
            "reader %s completed %d contains ops",
            ray.get_runtime_context().get_actor_id(),
            ok,
        )
        return ok


@pytest.mark.limit
@pytest.mark.gcp_only
@pytest.mark.parametrize("mode", ["getitem"])  #  "contains"
@pytest.mark.parametrize("scale", [40])  # 10, 40
@pytest.mark.parametrize("ops_per_actor", [10000])  # this blows up when it is 10k
@pytest.mark.parametrize(
    "checkpointer",
    [
        "session",
        pytest.param(
            "file",
            marks=pytest.mark.xfail(
                strict=True, reason="expected to fail under stampede"
            ),
        ),
    ],
)  # LanceCheckpointStore
def test_lance_checkpoint_single_store_many_reads_per_file(
    beefy_cluster: RayCluster,
    geneva_test_bucket: str,
    mode: str,
    scale: int,
    checkpointer: str,
    ops_per_actor: int,
) -> None:
    """
    Simulates the real workload: each actor builds ONE LanceCheckpointStore and performs
    many sequential checkpoint reads. This exercises connection/cred caching and avoids
    the "one store per call" anti-pattern.

    Env knobs:
      mode           # testing different ops in checkpointstore (getitem|contains)
      scale          # number of actors (processes)
      ops_pe_actor   # sequential reads per actor (default 20k)
      checkpointer    # use file|session (session for >= pylance-0.36.0)
    """
    ckp_root = str(URL(geneva_test_bucket) / "stampede-test" / KEY_PREFIX)

    if not ckp_root.startswith("gs://"):
        pytest.skip(
            "Set GENEVA_LANCE_CKPT_ROOT=gs://<bucket>/<prefix> to run this test."
        )

    _LOG.info(
        f"starting single-store-many-reads: checkpointer={checkpointer}"
        f" mode={mode} actors={scale}"
        f" ops/actor={ops_per_actor}"
    )

    with beefy_cluster:
        # Prepare a small keyset once (on driver) so each actor cycles through the
        # same store/files
        from geneva.checkpoint import LanceCheckpointStore

        prep_store = LanceCheckpointStore(ckp_root)
        keys = _ensure_keyset(prep_store, KEYSET_SIZE)
        keys_ref = ray.put(keys)  # broadcast to actors efficiently
        _LOG.info(f"keys {keys}")

        pin_opts = _maybe_pin_to_one_node()

        # Spin up actors (each with its own single store)
        readers = [
            StoreReader.options(num_cpus=0.25, **pin_opts).remote(
                ckp_root, mode, checkpointer
            )
            for _ in range(scale)
        ]

        # Run sequential reads in each actor
        refs = [r.run.remote(keys_ref, ops_per_actor) for r in readers]  # type: ignore[attr-defined]

        failures = 0
        successes = 0
        # Give plenty of time: sequential ops per actor
        per_actor_timeout = max(180.0, ops_per_actor * 0.15)

        for ref in refs:
            try:
                successes += ray.get(ref, timeout=per_actor_timeout)  # type: ignore[operator]
            except Exception as e:  # noqa: PERF203
                failures += 1
                _LOG.warning("actor run failed: %r", e)

        _LOG.info(
            "stampede single-store-many-reads: checkpointer=%s actors=%d ops/actor=%d"
            " keyset=%d mode=%s successes=%d failures=%d root=%s",
            checkpointer,
            scale,
            ops_per_actor,
            KEYSET_SIZE,
            mode,
            successes,
            failures,
            ckp_root,
        )
    # expect this to pass cleanly for session, but have failures with file
    assert failures == 0, f"Expected all to complete; saw {failures} failures"

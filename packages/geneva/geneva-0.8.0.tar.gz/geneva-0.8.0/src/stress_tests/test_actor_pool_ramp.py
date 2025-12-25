# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

from __future__ import annotations

import contextlib
import json
import logging
import os
import statistics
import time
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Optional

import pytest
import ray

from geneva.runners.ray.actor_pool import ActorPool

if TYPE_CHECKING:
    from geneva.runners.ray.raycluster import RayCluster

_LOG = logging.getLogger(__name__)


@dataclass(slots=True)
class ActorRampResult:
    num_actors: int
    actors_observed: int
    num_tasks: int
    busy_ms: float
    start_monotonic: float
    elapsed_to_full_saturation: float
    p50_s: float
    p90_s: float
    p99_s: float
    max_s: float
    events: list[dict[str, Any]]


@ray.remote
class BenchWorker:
    def __init__(self) -> None:
        # Store the first time this actor started processing a task
        self._first_start: Optional[float] = None
        # Stable id for grouping results by actor
        self._actor_id: str = ray.get_runtime_context().get_actor_id()

    def __ray_ready__(self) -> None:  # required by ActorPool
        return None

    def run(self, value: int, busy_ms: float = 0.0) -> dict[str, Any]:
        start = time.monotonic()
        if self._first_start is None:
            self._first_start = start
        if busy_ms and busy_ms > 0:
            time.sleep(busy_ms / 1000.0)
        return {
            "actor_id": self._actor_id,
            "first_start": self._first_start,
            "task_start": start,
            "value": value,
            "pid": os.getpid(),
        }


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    k = max(0, min(len(values) - 1, int(round((pct / 100.0) * (len(values) - 1)))))
    return sorted(values)[k]


def run_bench(
    num_actors: int,
    num_tasks: int,
    busy_ms: float,
    address: Optional[str],
    timeout_s: float,
    json_out: Optional[str],
) -> ActorRampResult:
    if ray.is_initialized():
        pass
    else:
        if address:
            ray.init(address=address)
        else:
            # Local default to make it easy to run without a cluster
            ray.init()

    start_t0 = time.monotonic()

    # Build the pool
    factory = lambda: BenchWorker.remote()  # noqa: E731
    pool = ActorPool(factory, num_actors)

    # Submit a lot more tasks than actors, to ensure the pool can saturate
    total_tasks = max(num_tasks, num_actors * 4)
    values_iter = range(total_tasks)

    # Kick off mapping through the pool
    it = pool.map_unordered(lambda a, v: a.run.remote(v, busy_ms=busy_ms), values_iter)

    # Measure the first time each actor processes a task
    first_seen: dict[str, float] = {}
    events: list[dict[str, Any]] = []

    deadline = start_t0 + timeout_s if timeout_s > 0 else None
    for res in it:
        actor_id = res["actor_id"]
        first_start = float(res["first_start"]) if res.get("first_start") else None
        if actor_id not in first_seen and first_start is not None:
            first_seen[actor_id] = first_start
            events.append(
                {
                    "actor_id": actor_id,
                    "first_start": first_start,
                    "since_start_s": first_start - start_t0,
                }
            )

        # Stop once we have the first event for every actor
        if len(first_seen) >= num_actors:
            break

        # Respect timeout if set
        if deadline is not None and time.monotonic() > deadline:
            break

    # Shutdown pool actors (idle only; remaining will exit when driver exits)
    with contextlib.suppress(Exception):
        pool.shutdown()

    # Prepare metrics
    deltas = [t - start_t0 for t in first_seen.values()]
    deltas.sort()
    result = ActorRampResult(
        num_actors=num_actors,
        actors_observed=len(first_seen),
        num_tasks=total_tasks,
        busy_ms=busy_ms,
        start_monotonic=start_t0,
        elapsed_to_full_saturation=max(deltas) if deltas else 0.0,
        p50_s=statistics.median(deltas) if deltas else 0.0,
        p90_s=_percentile(deltas, 90.0),
        p99_s=_percentile(deltas, 99.0),
        max_s=max(deltas) if deltas else 0.0,
        events=events,
    )

    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(asdict(result), f, indent=2)

    return result


@pytest.mark.limit
@pytest.mark.parametrize(
    "config",
    [
        pytest.param(
            {
                "num_actors": 120,
                "num_tasks": 480,
                "busy_ms": 10000.0,
                "timeout_s": 600.0,
            },
            id="high-ramp-saturation",
        ),
    ],
)
def test_actor_pool_ramp_up_saturates(
    beefy_cluster: RayCluster, config: dict[str, float | int]
) -> None:
    """
    Ensure an ActorPool reaches full saturation on a beefy Ray cluster without timeouts.
    """

    _LOG.info("Actor pool ramp config: %s", config)

    with beefy_cluster:
        result = run_bench(
            num_actors=int(config["num_actors"]),
            num_tasks=int(config["num_tasks"]),
            busy_ms=float(config["busy_ms"]),
            address=None,
            timeout_s=float(config["timeout_s"]),
            json_out=None,
        )

    _LOG.info("Actor pool ramp result: %s", asdict(result))

    assert result.actors_observed == config["num_actors"], (
        f"Expected {config['num_actors']} actors observed, got {result.actors_observed}"
    )
    assert result.actors_observed == result.num_actors, (
        f"Expected full saturation of {result.num_actors} actors, "
        f"but only observed {result.actors_observed}"
    )
    assert result.num_tasks == config["num_tasks"], (
        f"Expected {config['num_tasks']} tasks submitted, got {result.num_tasks}"
    )
    assert result.busy_ms == config["busy_ms"], (
        f"Expected busy_ms {config['busy_ms']}, got {result.busy_ms}"
    )

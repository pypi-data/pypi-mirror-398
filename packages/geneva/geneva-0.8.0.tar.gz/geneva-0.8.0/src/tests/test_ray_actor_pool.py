# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import itertools
import random

import pytest
import ray

from geneva.runners.ray.actor_pool import ActorPool


@ray.remote
class TestActor:
    def echo(self, i: int) -> int:
        return i


@pytest.mark.parametrize(
    ("num_calls", "num_actors"),
    list(itertools.product([1000], [7])),
)
@pytest.mark.ray
def test_actor_pool(
    num_calls: int,
    num_actors: int,
) -> None:
    # do it twice should not affect the result
    pool = ActorPool(TestActor.remote, num_actors)
    unordered_res = pool.map_unordered(
        lambda actor, i: actor.echo.remote(i), range(num_calls)
    )
    unordered_res = list(unordered_res)
    assert list(range(num_calls)) == sorted(unordered_res)
    assert len(unordered_res) == num_calls
    assert list(range(num_calls)) != unordered_res
    pool.shutdown()


@pytest.mark.parametrize(
    ("num_calls", "num_actors"),
    list(itertools.product([1000], [7])),
)
@pytest.mark.ray
def test_actor_pool_fault_tolerance(
    num_calls: int, num_actors: int, monkeypatch
) -> None:
    # do it twice should not affect the result
    original_return_actor = ActorPool._return_actor

    def faulty_return_actor(self, actor) -> None:
        if random.random() < 0.01:
            ray.kill(actor)

        original_return_actor(self, actor)

    monkeypatch.setattr(ActorPool, "_return_actor", faulty_return_actor)

    pool = ActorPool(TestActor.remote, num_actors)
    for _ in range(2):
        unordered_res = pool.map_unordered(
            lambda actor, i: actor.echo.remote(i), range(num_calls)
        )
        unordered_res = list(unordered_res)
        assert list(range(num_calls)) == sorted(unordered_res)
        assert len(unordered_res) == num_calls
        assert list(range(num_calls)) != unordered_res
    pool.shutdown()

# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Ray Authors
# SPDX-FileCopyrightText: Copyright The Geneva Authors

# forked actor pool from ray.util.actor_pool
# we added support for FT and autoscaling to this implementation
# ordered map supoort is dropped atm, but can be added back if needed

import contextlib
import logging
import time
from collections.abc import Callable, Iterable, Iterator
from typing import Any, TypeVar

import ray
import ray.actor
import ray.exceptions
from ray import ObjectRef
from ray.actor import ActorHandle

from geneva.runners.ray.jobtracker import JobTracker
from geneva.runners.ray.raycluster import ray_tqdm

V = TypeVar("V")

_LOG = logging.getLogger(__name__)


class ActorPool:
    """Utility class to operate on a fixed pool of actors.

    Arguments:
        actor_factory: Factory used to create actors. This should be a callable
            that returns a new actor handle when called. The factory will be called
            num_actors times to create the initial pool of actors.
        num_actors: Number of actors to create in the pool.
        worker_tracker: Optional ObjectRef for tracking worker progress.

    Examples:
        .. testcode::

            import ray
            from ray.util.actor_pool import ActorPool

            @ray.remote
            class Actor:
                def double(self, v):
                    return 2 * v

            a1, a2 = Actor.remote(), Actor.remote()
            pool = ActorPool([a1, a2])
            print(list(pool.map(lambda a, v: a.double.remote(v),
                                [1, 2, 3, 4])))

        .. testoutput::

            [2, 4, 6, 8]
    """

    def __init__(
        self,
        actors_factory: Callable[[], Any],
        num_actors: int,
        *,
        job_tracker: ObjectRef | ActorHandle | None = None,
        worker_metric: str = "workers",
    ) -> None:
        # factory to create actors
        self._actor_factory = actors_factory

        # number of actors # added
        self._num_actors = num_actors

        # readyness future to actor # added
        self._ready_fut_to_actor = {}

        # actors to be used
        self._idle_actors = []

        # get actor from future
        self._future_to_actor = {}

        # get future from index
        self._index_to_future = {}

        # next task to do
        self._next_task_index = 0

        # next work depending when actors free
        self._pending_submits = []

        # the task that was submitted # added
        self._future_to_task = {}

        self.worker_metric = worker_metric

        self.job_tracker = job_tracker or JobTracker.remote("fake job id", None)  # type: ignore[call-arg]
        self.job_tracker.set_total.remote(worker_metric, num_actors)  # type: ignore[attr-defined]
        self.job_tracker.set.remote(worker_metric, 0)  # type: ignore[attr-defined]
        ray_tqdm([], self.job_tracker, worker_metric)

        for _ in range(num_actors):
            self._queue_actor_startup()

    def _queue_actor_startup(self) -> None:
        new_actor = self._actor_factory()
        ready_fut = new_actor.__ray_ready__.remote()
        self.job_tracker.increment.remote(self.worker_metric, 1)  # type: ignore[attr-defined]
        self._ready_fut_to_actor[ready_fut] = new_actor

    def _collect_ready_actors(self) -> None:
        # Non‑blocking drain of all currently ready actors. This avoids throttling
        # ramp‑up without waiting for not‑yet‑ready actors.
        while True:
            futs = list(self._ready_fut_to_actor.keys())
            if not futs:
                return
            ready, _ = ray.wait(futs, num_returns=1, timeout=0.0)
            if not ready:
                # No more ready actors at this moment
                return

            for fut in ready:
                _LOG.debug("Adding ready actors to pool: %s", fut)
                actor = self._ready_fut_to_actor.pop(fut)
                try:
                    ray.get(fut)
                    self._return_actor(actor)
                except (
                    ray.exceptions.ActorDiedError,
                    ray.exceptions.ActorUnavailableError,
                ):
                    _LOG.exception("Actor died or unavailable, cleaning it up")
                    ray.kill(actor)
                    self._queue_actor_startup()

    def _map(
        self,
        fn: Callable[["ray.actor.ActorHandle", V], Any],
        values: Iterable[V],
        *,
        ordered: bool,
    ) -> Iterator[Any]:
        # Ignore/Cancel all the previous submissions
        # by calling `has_next` and `gen_next` repeteadly.
        while self.has_next():
            with contextlib.suppress(TimeoutError):
                self.get_next_unordered(timeout=0)

        it = iter(values)

        def _maybe_submit() -> bool:
            try:
                v = next(it)
            except StopIteration:
                return False
            self.submit(fn, v)
            return True

        # prime the workers
        # always have one pending task so when we call get_next or get_next_unordered
        # we can submit task immediately without waiting for the puller to yield back
        submits = self._num_actors + 1
        while submits and _maybe_submit():
            submits -= 1

        next_fn = self.get_next_unordered

        while self.has_next():
            yield next_fn()
            _maybe_submit()

    def map_unordered(
        self, fn: Callable[["ray.actor.ActorHandle", V], Any], values: Iterable[V]
    ) -> Iterator[Any]:
        """Similar to map(), but returning an unordered iterator.

        This returns an unordered iterator that will return results of the map
        as they finish. This can be more efficient that map() if some results
        take longer to compute than others.

        Arguments:
            fn: Function that takes (actor, value) as argument and
                returns an ObjectRef computing the result over the value. The
                actor will be considered busy until the ObjectRef completes.
            values: Iterable of values that fn(actor, value) should be
                applied to.

        Returns:
            Iterator over results from applying fn to the actors and values.

        Examples:
            .. testcode::

                import ray
                from ray.util.actor_pool import ActorPool

                @ray.remote
                class Actor:
                    def double(self, v):
                        return 2 * v

                a1, a2 = Actor.remote(), Actor.remote()
                pool = ActorPool([a1, a2])
                print(list(pool.map_unordered(lambda a, v: a.double.remote(v),
                                              [1, 2, 3, 4])))

            .. testoutput::
                :options: +MOCK

                [6, 8, 4, 2]
        """
        yield from self._map(fn, values, ordered=False)

    def submit(self, fn, value) -> None:
        """Schedule a single task to run in the pool.

        This has the same argument semantics as map(), but takes on a single
        value instead of a list of values. The result can be retrieved using
        get_next() / get_next_unordered().

        Arguments:
            fn: Function that takes (actor, value) as argument and
                returns an ObjectRef computing the result over the value. The
                actor will be considered busy until the ObjectRef completes.
            value: Value to compute a result for.

        Examples:
            .. testcode::

                import ray
                from ray.util.actor_pool import ActorPool

                @ray.remote
                class Actor:
                    def double(self, v):
                        return 2 * v

                a1, a2 = Actor.remote(), Actor.remote()
                pool = ActorPool([a1, a2])
                pool.submit(lambda a, v: a.double.remote(v), 1)
                pool.submit(lambda a, v: a.double.remote(v), 2)
                print(pool.get_next(), pool.get_next())

            .. testoutput::

                2 4
        """
        if self._idle_actors:
            actor = self._idle_actors.pop()
            future = fn(actor, value)
            future_key = tuple(future) if isinstance(future, list) else future
            self._future_to_actor[future_key] = (self._next_task_index, actor)
            self._index_to_future[self._next_task_index] = future
            self._next_task_index += 1
            self._future_to_task[future_key] = (fn, value)
        else:
            self._pending_submits.append((fn, value))

    def has_next(self) -> bool:
        """Returns whether there are any pending results to return.

        Returns:
            True if there are any pending results not yet returned.

        Examples:
            .. testcode::

                import ray
                from ray.util.actor_pool import ActorPool

                @ray.remote
                class Actor:
                    def double(self, v):
                        return 2 * v

                a1, a2 = Actor.remote(), Actor.remote()
                pool = ActorPool([a1, a2])
                pool.submit(lambda a, v: a.double.remote(v), 1)
                print(pool.has_next())
                print(pool.get_next())
                print(pool.has_next())

            .. testoutput::

                True
                2
                False
        """
        return bool(self._future_to_actor) or bool(self._pending_submits)

    class NoResult: ...

    def _get_next_by_fut(self, futures, timeout=None) -> Any | NoResult:
        timeout_msg = "Timed out waiting for result"

        # get_next will just pass a single future
        # get_next_unordered will pass a list of futures
        res, _ = ray.wait(futures, num_returns=1, timeout=timeout, fetch_local=True)
        if res:
            [future] = res
        else:
            raise TimeoutError(timeout_msg)

        i, a = self._future_to_actor.pop(future)
        fn, task = self._future_to_task.pop(future)
        del self._index_to_future[i]

        try:
            # this is fast because ray.wait already fetched the result
            res = ray.get(future)
            # don't return the future till we get the result
            # because the actor could be dead
            self._return_actor(a)
        except (ray.exceptions.ActorDiedError, ray.exceptions.ActorUnavailableError):
            _LOG.exception("Actor died or unavailable, cleaning it up")
            ray.kill(a)
            # queue a new actor
            self._queue_actor_startup()
            # resubmit the task
            self.submit(fn, task)
            return self.NoResult

        return res

    def get_next_unordered(self, timeout=None) -> Any:
        """Returns any of the next pending results.

        This returns some result produced by submit(), blocking for up to
        the specified timeout until it is available. Unlike get_next(), the
        results are not always returned in same order as submitted, which can
        improve performance.

        Returns:
            The next result.

        Raises:
            TimeoutError: if the timeout is reached.

        Examples:
            .. testcode::

                import ray
                from ray.util.actor_pool import ActorPool

                @ray.remote
                class Actor:
                    def double(self, v):
                        return 2 * v

                a1, a2 = Actor.remote(), Actor.remote()
                pool = ActorPool([a1, a2])
                pool.submit(lambda a, v: a.double.remote(v), 1)
                pool.submit(lambda a, v: a.double.remote(v), 2)
                print(pool.get_next_unordered())
                print(pool.get_next_unordered())

            .. testoutput::
                :options: +MOCK

                4
                2
        """
        if not self.has_next():
            raise StopIteration("No more results to get")

        # Use a short default timeout to interleave collecting newly-ready actors
        poll_timeout = 0.05  # 50ms default poll interval
        deadline = None
        if timeout is not None:
            # Respect explicit timeout while still polling frequently
            timeout = max(timeout, 0.0)
            deadline = time.monotonic() + timeout
            # If the requested timeout is shorter than our poll interval, use it
            poll_timeout = min(poll_timeout, timeout)

        while True:
            # Always collect any actors that became ready since last iteration
            self._collect_ready_actors()

            futs = list(self._future_to_actor)
            if not futs:
                # No inflight yet; spin until at least one submission exists
                self._collect_ready_actors()
                futs = list(self._future_to_actor)
                if not futs:
                    continue

            current_timeout = poll_timeout
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Timed out waiting for result")
                current_timeout = min(current_timeout, remaining)

            try:
                item = self._get_next_by_fut(futs, current_timeout)
            except TimeoutError:
                if deadline is not None and deadline - time.monotonic() <= 0:
                    raise
                # No task finished within the poll interval; loop to collect more actors
                continue

            if item is not self.NoResult:
                return item

    def _return_actor(self, actor) -> None:
        self._idle_actors.append(actor)
        # while self._idle_actors and self._pending_submits:
        if self._pending_submits:
            self.submit(*self._pending_submits.pop(0))

    def has_free(self) -> bool:
        """Returns whether there are any idle actors available.

        Returns:
            True if there are any idle actors and no pending submits.

        Examples:
            .. testcode::

                import ray
                from ray.util.actor_pool import ActorPool

                @ray.remote
                class Actor:
                    def double(self, v):
                        return 2 * v

                a1 = Actor.remote()
                pool = ActorPool([a1])
                pool.submit(lambda a, v: a.double.remote(v), 1)
                print(pool.has_free())
                print(pool.get_next())
                print(pool.has_free())

            .. testoutput::

                False
                2
                True
        """
        return len(self._idle_actors) > 0 and len(self._pending_submits) == 0

    def pop_idle(self) -> ray.actor.ActorHandle | None:
        """Removes an idle actor from the pool.

        Returns:
            An idle actor if one is available.
            None if no actor was free to be removed.

        Examples:
            .. testcode::

                import ray
                from ray.util.actor_pool import ActorPool

                @ray.remote
                class Actor:
                    def double(self, v):
                        return 2 * v

                a1 = Actor.remote()
                pool = ActorPool([a1])
                pool.submit(lambda a, v: a.double.remote(v), 1)
                assert pool.pop_idle() is None
                assert pool.get_next() == 2
                assert pool.pop_idle() == a1

        """
        if self.has_free():
            return self._idle_actors.pop()
        return None

    def shutdown(self) -> None:
        while (actor := self.pop_idle()) is not None:
            _LOG.debug("Shutting down actor %s", actor)
            ray.kill(actor)
            self.job_tracker.increment.remote("workers", -1)  # type: ignore[attr-defined]

    def push(self, actor) -> None:
        """Pushes a new actor into the current list of idle actors.

        Examples:
            .. testcode::

                import ray
                from ray.util.actor_pool import ActorPool

                @ray.remote
                class Actor:
                    def double(self, v):
                        return 2 * v

                a1, a2 = Actor.remote(), Actor.remote()
                pool = ActorPool([a1])
                pool.push(a2)
        """
        busy_actors = []
        if self._future_to_actor.values():
            _, busy_actors = zip(*self._future_to_actor.values(), strict=False)
        if actor in self._idle_actors or actor in busy_actors:
            raise ValueError("Actor already belongs to current ActorPool")
        else:
            self._return_actor(actor)

# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import logging
import random
import time

import pytest

from geneva.utils import deep_merge, retry_lance


def test_preserves_function_metadata() -> None:
    """Wrapper should preserve __name__ and __doc__ via functools.wraps."""

    def fn(a, b) -> int:
        """original doc"""
        return a + b

    wrapped = retry_lance(fn)
    assert wrapped.__name__ == fn.__name__
    assert wrapped.__doc__ == fn.__doc__


def test_success_no_retries(monkeypatch) -> None:
    """If the function succeeds immediately, no sleep or warning should occur."""
    called = []

    def fast_fn(x) -> list:
        called.append(x)
        return x * 2

    # spy on sleep and uniform
    monkeypatch.setattr(
        time,
        "sleep",
        lambda s: (_ for _ in ()).throw(AssertionError("sleep should not be called")),
    )
    monkeypatch.setattr(random, "uniform", lambda a, b: b)

    wrapped = retry_lance(fast_fn)
    result = wrapped(10)
    assert result == 20
    assert called == [10]


def test_retries_and_backoff(monkeypatch, caplog) -> None:
    """Function fails twice then succeeds on 3rd attempt with correct sleep calls and
    logs."""
    attempts = {"count": 0}
    sleep_calls = []

    def flaky(x) -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError(f"fail #{attempts['count']}")
        return "ok"

    # force deterministic jitter = full delay
    monkeypatch.setattr(random, "uniform", lambda a, b: b)
    # record sleep calls
    monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

    # capture warnings
    caplog.set_level(logging.WARNING)

    wrapped = retry_lance(flaky)

    res = wrapped(0)
    assert res == "ok"

    assert sleep_calls == [1.5, 2.0]

    # check that two warning logs were emitted
    warning_texts = [
        r.getMessage() for r in caplog.records if r.levelno == logging.WARNING
    ]
    assert any("as it raised ValueError: fail #1" in text for text in warning_texts)
    assert any("as it raised ValueError: fail #2" in text for text in warning_texts)


def test_max_attempts_exhaustion(monkeypatch, caplog) -> None:
    """After max_attempts is reached, the exception is re-raised and an error is
    logged."""

    def always_fail() -> None:
        raise ValueError("no hope")

    sleep_calls = []
    monkeypatch.setattr(random, "uniform", lambda a, b: 0)  # jitter=0 for clarity
    monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

    caplog.set_level(logging.ERROR)
    wrapped = retry_lance(always_fail)

    with pytest.raises(ValueError, match="no hope"):
        wrapped()

    # should have slept once (only one retry before giving up)
    assert sleep_calls == [0.5, 1.0, 2.0, 4.0, 8.0, 16.0]

    # check error log
    errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert any(
        "always_fail' failed after 7 attempts; giving up." in msg for msg in errors
    )


def test_non_retryable_exception(monkeypatch) -> None:
    """Exceptions not in the tuple should propagate immediately (no retry)."""
    sleep_calls = []
    monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

    @retry_lance
    def raises_type() -> None:
        raise TypeError("wrong kind")

    with pytest.raises(TypeError):
        raises_type()

    assert sleep_calls == []  # no backoff/sleep occurred


# Tests for deep_merge


def test_deep_merge_simple_dicts() -> None:
    """Test merging simple dictionaries."""
    base = {"a": 1, "b": 2}
    override = {"b": 3, "c": 4}
    result = deep_merge(base, override)

    assert result == {"a": 1, "b": 3, "c": 4}
    # Ensure original dicts are not modified
    assert base == {"a": 1, "b": 2}
    assert override == {"b": 3, "c": 4}


def test_deep_merge_nested_dicts() -> None:
    """Test merging nested dictionaries."""
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"d": 4, "e": 5}, "f": 6}
    result = deep_merge(base, override)

    assert result == {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}


def test_deep_merge_deeply_nested() -> None:
    """Test merging deeply nested dictionaries."""
    base = {"a": {"b": {"c": {"d": 1}}}}
    override = {"a": {"b": {"c": {"e": 2}}}}
    result = deep_merge(base, override)

    assert result == {"a": {"b": {"c": {"d": 1, "e": 2}}}}


def test_deep_merge_lists_append() -> None:
    """Test that lists are appended, not replaced."""
    base = {"containers": [{"name": "ray", "image": "ray:2.44.0"}]}
    override = {"containers": [{"name": "sidecar", "image": "sidecar:1.0"}]}
    result = deep_merge(base, override)

    assert len(result["containers"]) == 2
    assert result["containers"][0] == {"name": "ray", "image": "ray:2.44.0"}
    assert result["containers"][1] == {"name": "sidecar", "image": "sidecar:1.0"}


def test_deep_merge_empty_override() -> None:
    """Test merging with empty override returns base copy."""
    base = {"a": 1, "b": 2}
    override = {}
    result = deep_merge(base, override)

    assert result == base
    assert result is not base  # Should be a copy


def test_deep_merge_empty_base() -> None:
    """Test merging empty base with override."""
    base = {}
    override = {"a": 1, "b": 2}
    result = deep_merge(base, override)

    assert result == override


def test_deep_merge_type_mismatch_override_wins() -> None:
    """Test that when types mismatch, override value replaces base."""
    base = {"a": {"nested": "dict"}}
    override = {"a": "string"}  # Different type
    result = deep_merge(base, override)

    assert result == {"a": "string"}


def test_deep_merge_kubernetes_example() -> None:
    """Test realistic Kubernetes spec deep merge."""
    base = {
        "template": {
            "spec": {
                "containers": [
                    {
                        "name": "ray",
                        "image": "rayproject/ray:2.44.0",
                        "resources": {"limits": {"cpu": "4", "memory": "16Gi"}},
                    }
                ]
            }
        }
    }

    override = {
        "template": {
            "spec": {
                "securityContext": {"runAsNonRoot": True, "fsGroup": 1000},
                "initContainers": [{"name": "init", "image": "busybox:1.35"}],
            }
        }
    }

    result = deep_merge(base, override)

    # Original container should be preserved
    assert result["template"]["spec"]["containers"][0]["name"] == "ray"
    assert (
        result["template"]["spec"]["containers"][0]["image"] == "rayproject/ray:2.44.0"
    )

    # New fields should be added
    assert result["template"]["spec"]["securityContext"] == {
        "runAsNonRoot": True,
        "fsGroup": 1000,
    }
    assert len(result["template"]["spec"]["initContainers"]) == 1
    assert result["template"]["spec"]["initContainers"][0]["name"] == "init"


def test_deep_merge_nested_lists() -> None:
    """Test merging with nested lists in dicts."""
    base = {"spec": {"env": [{"name": "A", "value": "1"}]}}
    override = {"spec": {"env": [{"name": "B", "value": "2"}]}}
    result = deep_merge(base, override)

    # Lists should be appended
    assert len(result["spec"]["env"]) == 2
    assert result["spec"]["env"][0] == {"name": "A", "value": "1"}
    assert result["spec"]["env"][1] == {"name": "B", "value": "2"}

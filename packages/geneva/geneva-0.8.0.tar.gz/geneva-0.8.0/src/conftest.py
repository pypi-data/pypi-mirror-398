# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Shared pytest fixtures for integ_tests, stress_tests, and e2e_tests.

This file contains common fixtures used across all test suites.
Test-suite-specific fixtures are kept in their respective conftest.py files.
"""

import contextlib
import logging
import random
import warnings

import kubernetes
import pytest

from geneva.cluster import K8sConfigMethod
from geneva.runners.ray._mgr import ray_cluster
from geneva.runners.ray.raycluster import (
    ExitMode,
    _HeadGroupSpec,
    _WorkerGroupSpec,
)
from geneva.utils import dt_now_utc

# Try to load kubernetes config - only needed for integration/stress/e2e tests
# Unit tests don't need this, so it's okay if it fails
with contextlib.suppress(kubernetes.config.config_exception.ConfigException):
    kubernetes.config.load_kube_config()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# it's okay, we are in a test
warnings.filterwarnings(
    "ignore", "Using port forwarding for Ray cluster is not recommended for production"
)
_LOG = logging.getLogger(__name__)


# ============================================================================
# Common pytest options
# ============================================================================


def pytest_addoption(parser) -> None:
    """Add common command-line options for all test suites."""
    parser.addoption(
        "--csp",
        action="store",
        default="gcp",
        choices=["gcp", "aws"],
        help="CSP to deploy to for tests (e.g., 'gcp', 'aws')",
    )
    parser.addoption(
        "--test-slug",
        action="store",
        default=None,
        help="Test slug to identify a test run. Typically used to "
        "cleanup external resources like rayclusters",
    )
    parser.addoption(
        "--bucket-path",
        action="store",
        default=None,
        help="Bucket path to use for test data (e.g., gs://bucket/path or s3://bucket/path)",
    )
    parser.addoption(
        "--manifest",
        action="store",
        default=None,
        help="Optional custom manifest",
    )


# ============================================================================
# Common fixtures
# ============================================================================


@pytest.fixture(autouse=True, scope="session")
def geneva_k8s_service_account(csp: str) -> str:
    """
    A preconfigured service account for the test session.
    This service account should have all the permissions needed to run the tests.
    """
    return "geneva-service-account"


@pytest.fixture(autouse=True, scope="session")
def geneva_test_bucket(request, slug) -> str:
    """
    Test bucket path - can be overridden with --bucket-path or defaults based on CSP.

    Falls back to default paths for local development if --bucket-path is not provided.
    """
    bucket_path = request.config.getoption("--bucket-path")

    if not bucket_path:
        csp = request.config.getoption("--csp")
        if csp == "gcp":
            bucket_path = f"gs://lancedb-lancedb-dev-us-central1/{slug}/data"
        elif csp == "aws":
            bucket_path = f"s3://geneva-integ-test-devland-us-east-1/{slug}/data"
        else:
            raise ValueError(f"Unsupported --csp arg: {csp}")
        _LOG.info(f"Using default bucket path: {bucket_path}")
    else:
        _LOG.info(f"Using provided bucket path: {bucket_path}")

    return bucket_path


@pytest.fixture(scope="session")
def csp(request, geneva_test_bucket) -> str:
    """
    Cloud service provider (gcp or aws).

    Also sets up Geneva config overrides for checkpoint and upload paths
    based on geneva_test_bucket.
    """
    from geneva.config import override_config_kv

    csp = request.config.getoption("--csp")

    # Derive upload and checkpoint paths from the bucket path
    # If bucket path is: gs://bucket/slug/data
    # Then: gs://bucket/slug/data/zips and gs://bucket/slug/data/checkpoints
    override_config_kv(
        {
            "job.checkpoint.mode": "object_store",
            "job.checkpoint.object_store.path": f"{geneva_test_bucket}/checkpoints",
        }
    )

    return csp


@pytest.fixture(scope="session")
def manifest(request) -> str | None:
    """
    Optionally use a saved manifest instead of uploading new
    manifest
    """

    try:
        return request.config.getoption("--manifest")
    except ValueError:
        return None


@pytest.fixture(scope="session")
def slug(request) -> str | None:
    """Test slug for identifying test runs and cleanup."""
    return request.config.getoption("--test-slug") or str(random.randint(0, 10000))  # type: ignore[return-value]


@pytest.fixture(scope="session")
def region(csp) -> str:
    """Default region for the CSP."""
    return "us-east-1" if csp == "aws" else "us-central1"


@pytest.fixture(scope="session")
def k8s_config_method(csp) -> K8sConfigMethod:
    """Kubernetes config method based on CSP."""
    return K8sConfigMethod.EKS_AUTH if csp == "aws" else K8sConfigMethod.LOCAL


@pytest.fixture(scope="session")
def k8s_namespace(csp) -> str:
    """Kubernetes namespace for Ray clusters."""
    # only used for EKS auth currently
    return "geneva"


@pytest.fixture(scope="session")
def k8s_cluster_name(csp) -> str:
    """Kubernetes cluster name."""
    # only used for EKS auth currently
    return "lancedb"


@pytest.fixture(scope="session")
def head_node_selector(csp: str) -> dict:
    """Node selector for Ray head nodes."""
    return {"geneva.lancedb.com/ray-head": "true"}


@pytest.fixture(scope="session")
def worker_node_selector(csp: str) -> dict:
    """Node selector for Ray worker nodes (CPU)."""
    return {"geneva.lancedb.com/ray-worker-cpu": "true"}


@pytest.fixture(scope="session")
def num_gpus() -> int:
    """Number of GPUs required for tests (default: 0)."""
    return 0


@pytest.fixture
def standard_cluster(
    geneva_k8s_service_account: str,
    k8s_config_method: K8sConfigMethod,
    k8s_namespace: str,
    csp: str,
    region: str,
    head_node_selector: dict,
    worker_node_selector: dict,
    k8s_cluster_name: str,
    slug: str | None,
) -> contextlib.AbstractContextManager:
    """Standard Ray cluster for integration and e2e tests."""
    ray_cluster_name = "test-cluster"
    ray_cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

    _LOG.info(f"creating ray cluster {ray_cluster_name}")

    head_spec = _HeadGroupSpec(  # type: ignore[call-arg]
        service_account=geneva_k8s_service_account,
        num_cpus=1,
        memory=3 * 1024**3,
        node_selector=head_node_selector,
    )

    # IMPORTANT: min_replicas must be ≥1 for worker groups with custom resources.
    #
    # Background: Workers with num_gpus=0 advertise a custom Ray resource via
    # rayStartParams (see raycluster.py:462-465). Each worker advertises
    # 100,000 units of the "cpu-only" custom resource to Ray.
    #
    # The Problem (Resource Discovery Bootstrapping):
    # 1. With min_replicas=0, cluster starts with zero workers
    # 2. Ray custom resources are only advertised by running workers
    # 3. When actors request cpu-only resources, Ray reports demand to autoscaler
    # 4. Kuberay autoscaler v2 cannot determine which worker group provides
    #    "cpu-only" resource because no workers are running to advertise it
    # 5. Autoscaler doesn't know which group to scale up → deadlock
    #
    # The Solution:
    # - min_replicas=1 ensures at least one worker is always running
    # - This worker advertises the cpu-only custom resource to Ray
    # - Autoscaler can now match resource demand to the correct worker group
    # - Additional workers scale up normally based on demand
    #
    # References:
    # - Ray custom resources: https://docs.ray.io/en/latest/ray-core/scheduling/resources.html
    # - Kuberay autoscaling: https://docs.ray.io/en/latest/cluster/kubernetes/user-guides/configuring-autoscaling.html
    # - Related issue: test_ray_add_column_pipeline_cpu_only_pool hung for 1.5+ hours
    #   when min_replicas=0, causing 10% of integration test failures
    worker_spec = _WorkerGroupSpec(  # type: ignore[call-arg]
        name="worker",
        min_replicas=1,
        service_account=geneva_k8s_service_account,
        num_cpus=2,
        memory=4 * 1024**3,
        node_selector=worker_node_selector,
    )

    return ray_cluster(
        name=ray_cluster_name,
        namespace=k8s_namespace,
        config_method=k8s_config_method,
        region=region,
        use_portforwarding=True,
        head_group=head_spec,
        worker_groups=[worker_spec],
        cluster_name=k8s_cluster_name,
        role_name="geneva-client-role",
        on_exit=ExitMode.DELETE,
        extra_env={
            "RAY_BACKEND_LOG_LEVEL": "info",
            "RAY_LOG_TO_DRIVER": "1",
            "RAY_ENABLE_RECORD_ACTOR_TASK_LOGGING": "1",
            "RAY_RUNTIME_ENV_LOG_TO_DRIVER_ENABLED": "true",
        },
        log_to_driver=True,
        logging_level=logging.INFO,
    )


@pytest.fixture
def beefy_cluster(
    geneva_k8s_service_account: str,
    k8s_config_method: K8sConfigMethod,
    k8s_namespace: str,
    csp: str,
    region: str,
    head_node_selector: dict,
    worker_node_selector: dict,
    k8s_cluster_name: str,
    slug: str | None,
    geneva_test_bucket: str,
) -> contextlib.AbstractContextManager:
    """Large Ray cluster for stress/e2e tests with high CPU/memory workers."""
    from geneva.packager.uploader import Uploader

    ray_cluster_name = "beefy-cluster"
    ray_cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

    _LOG.info(f"creating beefy ray cluster {ray_cluster_name}")

    # Create uploader for packaging local environment
    uploader = Uploader(upload_dir=f"{geneva_test_bucket}/zips")

    head_spec = _HeadGroupSpec(  # type: ignore[call-arg]
        service_account=geneva_k8s_service_account,
        num_cpus=1,
        memory=3 * 1024**3,
        node_selector=head_node_selector,
    )

    worker_spec = _WorkerGroupSpec(  # type: ignore[call-arg]
        name="worker",
        min_replicas=0,
        service_account=geneva_k8s_service_account,
        num_cpus=14,
        memory=56 * 1024**3,
        node_selector=worker_node_selector,
        env_vars={
            "LANCE_IO_THREADS": "4",
            "LANCE_PROCESS_IO_THREADS_LIMIT": "8",
        },
    )

    return ray_cluster(
        name=ray_cluster_name,
        namespace=k8s_namespace,
        config_method=k8s_config_method,
        region=region,
        use_portforwarding=True,
        head_group=head_spec,
        worker_groups=[worker_spec],
        cluster_name=k8s_cluster_name,
        role_name="geneva-client-role",
        on_exit=ExitMode.DELETE,
        uploader=uploader,
    )

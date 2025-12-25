# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Integration test-specific fixtures.

Common fixtures are inherited from src/conftest.py.
This file only contains fixtures specific to integration tests.
"""

# Import the logger from shared conftest
import logging
import os
import uuid
from collections.abc import Generator
from contextlib import AbstractContextManager

import kubernetes
import pytest
import yaml
from rich import pretty
from rich.logging import RichHandler

import geneva
from geneva.cluster import K8sConfigMethod
from geneva.cluster.builder import (
    GenevaClusterBuilder,
    HeadGroupBuilder,
    WorkerGroupBuilder,
    default_image,
)
from geneva.manifest.builder import GenevaManifestBuilder
from geneva.manifest.mgr import GenevaManifest
from geneva.runners.kuberay.client import KuberayClients
from geneva.runners.ray.raycluster import RayCluster
from geneva.utils import dt_now_utc

_LOG = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, force=True, handlers=[RichHandler()])
pretty.install()


# ============================================================================
# Integration test configuration
# ============================================================================


def pytest_configure(config) -> None:
    """Configure pytest for integration tests."""
    # Set default timeout of 10 minutes for all integration tests
    # Individual tests can override with @pytest.mark.timeout(N)
    config.option.timeout = 600


# ============================================================================
# Integration test-specific fixtures
# ============================================================================


@pytest.fixture(autouse=False, scope="session")
def kuberay_clients(
    k8s_config_method: K8sConfigMethod, region: str, k8s_cluster_name: str
) -> KuberayClients:
    """KubeRay API clients for integration tests."""
    return KuberayClients(
        config_method=k8s_config_method,
        region=region,
        cluster_name=k8s_cluster_name,
        role_name="geneva-client-role",
    )


@pytest.fixture(autouse=False)
def k8s_temp_service_account(
    kuberay_clients: KuberayClients,
    k8s_namespace: str,
) -> Generator[str, None, None]:
    """Create and cleanup a temporary Kubernetes service account for tests."""
    name = f"geneva-test-{uuid.uuid4().hex}"
    # note: this requires RBAC permissions beyond what we require for Geneva end users
    # namely: ```
    # - apiGroups:
    #   - ""
    #   resources:
    #   - serviceaccounts
    #   verbs:
    #   - create
    #   - delete```
    kuberay_clients.core_api.create_namespaced_service_account(
        namespace=k8s_namespace,
        body={
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": name,
                "namespace": k8s_namespace,
            },
        },
    )
    yield name
    kuberay_clients.core_api.delete_namespaced_service_account(
        name=name,
        namespace=k8s_namespace,
        body=kubernetes.client.V1DeleteOptions(),
    )


@pytest.fixture(autouse=False)
def k8s_temp_config_map(
    kuberay_clients: KuberayClients,
    k8s_namespace: str,
    csp: str,
) -> Generator[str, None, None]:
    """Create and cleanup a temporary Kubernetes ConfigMap for cluster configuration."""
    src = os.path.join(
        os.path.dirname(__file__),
        "../tests/test_configs/raycluster-configmap.yaml",
    )
    name = f"geneva-test-cluster-config-{uuid.uuid4().hex}"
    with open(src) as f:
        cm_spec = yaml.safe_load(f)
        # override metadata name/namespace
        cm_spec.setdefault("metadata", {})
        cm_spec["metadata"]["name"] = name
        cm_spec["metadata"]["namespace"] = k8s_namespace

        body = kubernetes.client.V1ConfigMap(
            api_version=cm_spec.get("apiVersion"),
            kind=cm_spec.get("kind"),
            metadata=kubernetes.client.V1ObjectMeta(**cm_spec["metadata"]),
            data=cm_spec.get("data", {}),
        )
        kuberay_clients.core_api.create_namespaced_config_map(
            namespace=k8s_namespace,
            body=body,
        )
        yield name
    kuberay_clients.core_api.delete_namespaced_config_map(
        name=name,
        namespace=k8s_namespace,
    )


@pytest.fixture(autouse=False)
def cluster_from_config_map(
    k8s_temp_config_map: str,
    k8s_config_method: K8sConfigMethod,
    k8s_namespace: str,
    region: str,
    k8s_cluster_name: str,
    slug: str | None,
) -> RayCluster:
    """Create a Ray cluster from a Kubernetes ConfigMap."""
    from geneva.runners.ray.raycluster import RayCluster
    from geneva.utils import dt_now_utc

    ray_cluster_name = "configmap-cluster"
    ray_cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

    return RayCluster.from_config_map(
        k8s_namespace,
        k8s_cluster_name,
        k8s_temp_config_map,
        ray_cluster_name,
        # only needed for EKS auth
        config_method=k8s_config_method,
        aws_region=region,
    )


@pytest.fixture(autouse=False, scope="session")
def default_manifest(slug: str) -> GenevaManifest:
    manifest_name = "integ-manifest"
    if slug:
        manifest_name += f"-{slug}"

    return (
        GenevaManifestBuilder()
        .create(manifest_name)
        # always use x86 images even if running tests on arm64
        # all of our integ test environments use x86
        .head_image(default_image(arm=False))
        .worker_image(default_image(arm=False))
        .add_pip("pyarrow>=16.0.0")
        .build()
    )


@pytest.fixture(autouse=False, scope="session")
def session_manifest(
    geneva_test_bucket: str,
    slug: str | None,
    default_manifest: GenevaManifest,
    manifest: str | None,  # optional custom manifest via --manifest
) -> str:
    """Upload and save default manifest per-session and return the name.
    Cleans up after test session ends.
    """
    # use custom manifest name if passed to tests with --manifest arg
    if manifest:
        yield manifest
    else:
        db = geneva.connect(geneva_test_bucket)

        # package and upload the manifest
        db.define_manifest(
            default_manifest.name,
            default_manifest,
        )

        yield default_manifest.name
        db.delete_manifest(default_manifest.name)


@pytest.fixture(autouse=False, scope="session")
def session_cluster(
    geneva_test_bucket: str,
    geneva_k8s_service_account: str,
    k8s_config_method: K8sConfigMethod,
    k8s_namespace: str,
    csp: str,
    region: str,
    head_node_selector: dict,
    worker_node_selector: dict,
    k8s_cluster_name: str,
    slug: str | None,
) -> str:
    """Save default cluster per-session and return the name.
    Cleans up after test session ends.
    """
    db = geneva.connect(geneva_test_bucket)
    cluster_name = f"integ-cluster-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

    cluster = (
        GenevaClusterBuilder()
        .name(cluster_name)
        .namespace(k8s_namespace)
        .config_method(k8s_config_method)
        .aws_config(region=region)
        .head_group_builder(
            HeadGroupBuilder()
            .node_selector(head_node_selector)
            .service_account(geneva_k8s_service_account)
        )
        .add_worker_group(
            WorkerGroupBuilder()
            .node_selector(worker_node_selector)
            .service_account(geneva_k8s_service_account)
        )
        .build()
    )

    db.define_cluster(cluster_name, cluster)

    yield cluster_name
    db.delete_cluster(cluster_name)


@pytest.fixture(autouse=False, scope="session")
def session_context(
    geneva_test_bucket: str,
    session_cluster: str,
    session_manifest: str,
) -> AbstractContextManager:
    """Start a Geneva context for the session cluster and manifest.
    This will start the ray cluster and delete it after the session.
    """
    db = geneva.connect(geneva_test_bucket)

    with db.context(
        manifest=session_manifest, cluster=session_cluster, log_to_driver=True
    ) as ctx:
        yield ctx

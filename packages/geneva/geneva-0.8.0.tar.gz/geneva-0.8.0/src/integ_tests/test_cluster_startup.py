# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import importlib
import logging
import subprocess
import sys
from contextlib import suppress

import pytest
import ray

import geneva
from geneva.cluster import GenevaClusterType, K8sConfigMethod
from geneva.cluster.builder import (
    GenevaClusterBuilder,
    HeadGroupBuilder,
    WorkerGroupBuilder,
)
from geneva.cluster.mgr import (
    GenevaCluster,
    HeadGroupConfig,
    KubeRayConfig,
    WorkerGroupConfig,
)
from geneva.manifest.mgr import GenevaManifest
from geneva.runners.kuberay.client import KuberayClients
from geneva.runners.ray._mgr import ray_cluster
from geneva.runners.ray.raycluster import (
    CPU_ONLY_NODE,
    RayCluster,
    _HeadGroupSpec,
    _WorkerGroupSpec,
    get_ray_image,
)
from geneva.utils import dt_now_utc
from integ_tests.utils import ray_get_with_retry

logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger(__name__)


def test_kube_auth(
    geneva_test_bucket: str,
    k8s_config_method: K8sConfigMethod,
    k8s_cluster_name: str,
    region: str,
) -> None:
    geneva.connect(geneva_test_bucket)
    clients = KuberayClients(
        config_method=k8s_config_method,
        region=region,
        role_name="geneva-client-role",
        cluster_name=k8s_cluster_name,
    )
    clients.core_api.list_namespaced_pod("geneva")


def test_cluster_startup(
    head_node_selector: dict,
    worker_node_selector: dict,
    slug: str | None,
    geneva_test_bucket: str,
    k8s_config_method: K8sConfigMethod,
    k8s_cluster_name: str,
    region: str,
    default_manifest: GenevaManifest,
) -> None:
    geneva.connect(geneva_test_bucket)
    cluster_name = "geneva-integ-test"
    cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

    with ray_cluster(
        name=cluster_name,
        manifest=default_manifest,
        namespace="geneva",
        head_group=_HeadGroupSpec(
            node_selector=head_node_selector, image=default_manifest.head_image
        ),  # type: ignore[call-arg]
        # allocate at least a single worker so the test runs faster
        # that we save time on waiting for the actor to start
        worker_groups=[
            _WorkerGroupSpec(  # type: ignore[call-arg]
                name="worker",
                min_replicas=1,
                node_selector=worker_node_selector,
                image=default_manifest.worker_image,
            )
        ],
        use_portforwarding=True,
        config_method=k8s_config_method,
        region=region,
        cluster_name=k8s_cluster_name,
    ):
        ray_get_with_retry(ray.remote(lambda: 1).remote())


@pytest.mark.skip(
    "This test requires configmaps:create/delete RBAC permissions. "
    "We don't grant these permissions to client roles by default in "
    "managed environments"
)
def test_cluster_startup_config_map(
    cluster_from_config_map: RayCluster,
    slug: str | None,
    geneva_test_bucket: str,
    default_manifest: GenevaManifest,
) -> None:
    """Test cluster startup from a Kubernetes ConfigMap.

    This test takes ~10 minutes because it creates its own Ray cluster
    (not a shared session cluster):
    - Cluster startup: ~3-4 min (K8s pod scheduling, image pull, Ray init)
    - Test execution: ~1 min
    - Cluster teardown: ~1-2 min
    """
    geneva.connect(geneva_test_bucket)
    cluster_name = "geneva-integ-test"
    cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

    with ray_cluster(ray_cluster=cluster_from_config_map, manifest=default_manifest):
        res = ray_get_with_retry(ray.remote(lambda: __import__("sys").version).remote())
        _LOG.info(f"***done {res=}")


def test_eks_token_refresh(
    geneva_test_bucket: str,
    slug: str | None,
    geneva_k8s_service_account: str,
    k8s_namespace: str,
    head_node_selector: dict,
    worker_node_selector: dict,
    region: str,
    k8s_config_method: K8sConfigMethod,
    default_manifest: GenevaManifest,
    monkeypatch,
) -> None:
    geneva.connect(geneva_test_bucket)
    cluster_name = "geneva-integ-test"
    cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"
    monkeypatch.setattr(
        "geneva.eks.TOKEN_EXPIRATION_S",
        5,
    )
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

    try:
        with ray_cluster(
            ray_cluster=cluster.to_ray_cluster(), manifest=default_manifest
        ):
            res = ray_get_with_retry(
                ray.remote(lambda: __import__("sys").version).remote()
            )
            _LOG.info(f"***done {res=}")
    finally:
        monkeypatch.setattr(
            "geneva.eks.TOKEN_EXPIRATION_S",
            1800,
        )


def test_cluster_startup_persisted_with_context(
    geneva_test_bucket: str,
    slug: str | None,
    geneva_k8s_service_account: str,
    k8s_namespace: str,
    head_node_selector: dict,
    worker_node_selector: dict,
    region: str,
    k8s_config_method: K8sConfigMethod,
) -> None:
    db = geneva.connect(geneva_test_bucket)

    cluster_name = "geneva-integ-test"
    cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"
    manifest_name = f"test-manifest-{slug}"

    tolerations = [
        {
            "key": "test_toleration",
            "operator": "Exists",
            "effect": "NoExecute",
        },
    ]
    img = get_ray_image(
        ray.__version__, f"{sys.version_info.major}{sys.version_info.minor}"
    )
    cluster_def = GenevaCluster(
        name=cluster_name,
        cluster_type=GenevaClusterType.KUBE_RAY,
        kuberay=KubeRayConfig(
            namespace=k8s_namespace,
            config_method=k8s_config_method,
            aws_region=region,
            aws_role_name="geneva-client-role",
            use_portforwarding=True,
            head_group=HeadGroupConfig(
                image=img,
                service_account=geneva_k8s_service_account,
                num_cpus=2,
                memory="4Gi",
                node_selector=head_node_selector,
                labels={"foo": "bar", "baz": "fu"},
                tolerations=tolerations,
                num_gpus=0,
            ),
            worker_groups=[
                WorkerGroupConfig(
                    image=img,
                    service_account=geneva_k8s_service_account,
                    num_cpus=2,
                    memory="4Gi",
                    node_selector=worker_node_selector,
                    labels={"foo": "bar"},
                    tolerations=tolerations,
                    num_gpus=0,
                ),
                WorkerGroupConfig(
                    image=img,
                    service_account=geneva_k8s_service_account,
                    num_cpus=2,
                    memory="4Gi",
                    node_selector=worker_node_selector,
                    labels={"foo": "bar"},
                    tolerations=tolerations,
                    num_gpus=0,
                ),
            ],
        ),
    )

    try:
        # persist the cluster definition
        db.define_cluster(cluster_name, cluster_def)

        clusters = db.list_clusters()
        _LOG.info(f"clusters: {clusters}")
        assert any(c.name == cluster_name for c in clusters), (
            f"couldn't find cluster {cluster_name}"
        )

        # load the cluster def and provision the ray cluster
        success = False
        with db.context(cluster=cluster_name):
            res = ray_get_with_retry(
                ray.remote(lambda: __import__("sys").version).remote()
            )
            _LOG.info(f"***done {res=}")
            success = True
        assert success, f"cluster {cluster_name} was not started successfully"

        # run with a custom manifest
        success = False
        db.define_manifest(
            manifest_name,
            GenevaManifest(
                manifest_name,
                delete_local_zips=True,
                skip_site_packages=True,
                pip=["lancedb"],
                py_modules=["./"],
            ),
        )
        with db.context(cluster=cluster_name, manifest=manifest_name):
            res = ray_get_with_retry(
                ray.remote(lambda: __import__("sys").version).remote()
            )
            _LOG.info(f"***done {res=}")
            success = True

        assert success, f"cluster {cluster_name} was not started successfully"
    finally:
        db.delete_cluster(cluster_name)
        db.delete_manifest(manifest_name)


def test_cluster_startup_from_builder(
    geneva_test_bucket: str,
    slug: str | None,
    geneva_k8s_service_account: str,
    k8s_namespace: str,
    head_node_selector: dict,
    worker_node_selector: dict,
    region: str,
    k8s_config_method: K8sConfigMethod,
    default_manifest: GenevaManifest,
    session_manifest: str,
) -> None:
    geneva.connect(geneva_test_bucket)
    cluster_name = "geneva-integ-test"
    cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

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

    res = None
    with ray_cluster(ray_cluster=cluster.to_ray_cluster(), manifest=default_manifest):
        res = ray_get_with_retry(ray.remote(lambda: __import__("sys").version).remote())
        _LOG.info(f"{res=}")
    assert res, f"cluster {cluster_name} was not started successfully"


def test_cluster_startup_no_account(
    k8s_config_method: K8sConfigMethod,
    head_node_selector: dict,
    worker_node_selector: dict,
    slug: str | None,
    default_manifest: GenevaManifest,
    session_manifest: str,
) -> None:
    """
    Test the if we try to import geneva, which uses gcs for
    workspace packaging magic, errors when the service account
    doesn't have permission to access the gcs bucket.
    """

    cluster_name = "geneva-integ-test"
    cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

    with (
        pytest.raises(ValueError, match=r"Service account .* does not exist"),
        ray_cluster(
            name=cluster_name,
            manifest=default_manifest,
            namespace="geneva",
            config_method=k8s_config_method,
            use_portforwarding=True,
            head_group=_HeadGroupSpec(node_selector=head_node_selector),  # type: ignore[call-arg]
            # allocate at least a single worker so the test runs faster
            # that we save time on waiting for the actor to start
            worker_groups=[
                _WorkerGroupSpec(  # type: ignore[call-arg]
                    name="worker",
                    min_replicas=1,
                    service_account="bogus-service-account",
                    node_selector=worker_node_selector,
                )
            ],
        ),
    ):
        ray.get(ray.remote(lambda: importlib.import_module("geneva")).remote())


@pytest.mark.skip("Need to create a service account with no permissions")
def test_cluster_startup_no_gcs_permission(
    k8s_config_method: K8sConfigMethod,
    head_node_selector: dict,
    worker_node_selector: dict,
    slug: str | None,
) -> None:
    """
    Test the if we try to import geneva, which uses gcs for
    workspace packaging magic, errors when the service account
    doesn't have permission to access the gcs bucket.
    """

    cluster_name = "geneva-integ-test"
    cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

    with (
        ray_cluster(
            name=cluster_name,
            namespace="geneva",
            config_method=k8s_config_method,
            use_portforwarding=True,
            # allocate at least a single worker so the test runs faster
            # that we save time on waiting for the actor to start
            head_group=_HeadGroupSpec(node_selector=head_node_selector),  # type: ignore[call-arg]
            worker_groups=[
                _WorkerGroupSpec(  # type: ignore[call-arg]
                    name="worker",
                    min_replicas=1,
                    service_account="valid-no-perms-service-account",
                    node_selector=worker_node_selector,
                )
            ],
        ),
        pytest.raises(PermissionError, match="PERMISSION_DENIED"),
    ):
        ray.get(ray.remote(lambda: importlib.import_module("geneva")).remote())


def test_cluster_startup_can_import_geneva_and_lance(
    geneva_k8s_service_account: str,
    geneva_test_bucket: str,
    head_node_selector: dict,
    worker_node_selector: dict,
    k8s_config_method: K8sConfigMethod,
    k8s_cluster_name: str,
    region: str,
    slug: str | None,
    session_manifest: str,
) -> None:
    from geneva.manifest.mgr import ManifestConfigManager

    # Connect to bucket and load manifest object
    db = geneva.connect(geneva_test_bucket)
    manifest_mgr = ManifestConfigManager(db, namespace=db.system_namespace)
    manifest_def = manifest_mgr.load(session_manifest)

    cluster_name = "geneva-integ-test"
    cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

    with ray_cluster(
        name=cluster_name,
        namespace="geneva",
        use_portforwarding=True,
        manifest=manifest_def,
        head_group=_HeadGroupSpec(  # type: ignore[call-arg]
            service_account=geneva_k8s_service_account,
            node_selector=head_node_selector,
        ),
        # allocate at least a single worker so the test runs faster
        # that we save time on waiting for the actor to start
        worker_groups=[
            _WorkerGroupSpec(  # type: ignore[call-arg]
                name="worker",
                min_replicas=1,
                service_account=geneva_k8s_service_account,
                node_selector=worker_node_selector,
            )
        ],
        config_method=k8s_config_method,
        region=region,
        cluster_name=k8s_cluster_name,
    ):
        ray_get_with_retry(
            ray.remote(lambda: importlib.import_module("geneva")).remote()
        )
        ray_get_with_retry(
            ray.remote(lambda: importlib.import_module("lance")).remote()
        )


def test_cluster_startup_skip_site(
    geneva_k8s_service_account: str,
    head_node_selector: dict,
    worker_node_selector: dict,
    k8s_config_method: K8sConfigMethod,
    k8s_cluster_name: str,
    region: str,
    slug: str | None,
    default_manifest: GenevaManifest,
    session_manifest: str,
) -> None:
    """
    Test that if we try to import geneva, which uses gcs for
    workspace packaging magic, errors because we skipped site
    packages and can't find
    """

    cluster_name = "geneva-integ-test"
    cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

    with (
        ray_cluster(
            name=cluster_name,
            namespace="geneva",
            use_portforwarding=True,
            head_group=_HeadGroupSpec(  # type: ignore[call-arg]
                service_account=geneva_k8s_service_account,
                node_selector=head_node_selector,
            ),
            # allocate at least a single worker so the test runs faster
            # that we save time on waiting for the actor to start
            worker_groups=[
                _WorkerGroupSpec(  # type: ignore[call-arg]
                    name="worker",
                    min_replicas=1,
                    service_account=geneva_k8s_service_account,
                    node_selector=worker_node_selector,
                )
            ],
            skip_site_packages=True,
            config_method=k8s_config_method,
            region=region,
            cluster_name=k8s_cluster_name,
            manifest=default_manifest,
        ),
        pytest.raises(ImportError, match=r"^(?!.*(geneva)).+"),
    ):
        # match the word geneva is not in the error message
        # so we know that geneva is uploaded but not lance, which
        # is expected because we skipped site packages
        ray.get(ray.remote(lambda: importlib.import_module("geneva")).remote())


def test_cluster_startup_cpu_only_tag(
    geneva_k8s_service_account: str,
    head_node_selector: dict,
    worker_node_selector: dict,
    csp: str,
    k8s_config_method: K8sConfigMethod,
    k8s_cluster_name: str,
    region: str,
    slug: str | None,
    default_manifest: GenevaManifest,
    session_manifest: str,
) -> None:
    """
    Test that if we force a CPU only task, it runs only on a CPU worker.

    If we request a GPU worker, it can run GPU worker, if we don't request a GPU worker
    without the cpu-only tag, it can be scheduled to runs on either a CPU or GPU worker.

    Oftentimes GPU workers fail to provision so we let the test pass in this case.
    """

    cluster_name = "geneva-integ-test"
    cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

    with ray_cluster(
        name=cluster_name,
        namespace="geneva",
        use_portforwarding=True,
        head_group=_HeadGroupSpec(  # type: ignore[call-arg]
            service_account=geneva_k8s_service_account,
            node_selector=head_node_selector,
        ),
        # allocate both GPU and CPU workers
        worker_groups=[
            _WorkerGroupSpec(  # type: ignore[call-arg]
                name="cpu",
                min_replicas=0,
                service_account=geneva_k8s_service_account,
                num_cpus=2,
                node_selector=worker_node_selector,
            ),
            _WorkerGroupSpec(  # type: ignore[call-arg]
                name="gpu",
                min_replicas=1,
                service_account=geneva_k8s_service_account,
                num_gpus=1,
                num_cpus=2,
                node_selector={"geneva.lancedb.com/ray-worker-gpu": "true"},
            ),
        ],
        config_method=k8s_config_method,
        region=region,
        cluster_name=k8s_cluster_name,
        manifest=default_manifest,
    ):
        try:
            ray.get(
                ray.remote(num_gpus=1)(
                    lambda: subprocess.run("nvidia-smi", check=True)
                ).remote(),
                timeout=300,
            )
        except ray.exceptions.GetTimeoutError:
            pytest.skip(
                "Skipping test due to Ray cluster startup failure "
                "(likely cannot provision GPU node)"
            )

        # running a CPU only task but we have a GPU worker
        # should schedule on the GPU worker but may schedule on CPU
        with suppress(ray.exceptions.RayTaskError, ray.exceptions.GetTimeoutError):
            ray_get_with_retry(
                ray.remote(lambda: subprocess.run("nvidia-smi", check=True)).remote()
            )

        # running a CPU only task + force it to run on CPU
        # should only schedule on the CPU worker and should always raise exception
        with pytest.raises(
            ray.exceptions.RayTaskError,
            match="No such file or directory: 'nvidia-smi'",
        ):
            ray.get(
                ray.remote(resources={CPU_ONLY_NODE: 1})(
                    lambda: subprocess.run("nvidia-smi", check=True)
                ).remote()
            )

# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors
import re

import pytest

from geneva.cluster import GenevaClusterType, K8sConfigMethod
from geneva.cluster.builder import (
    GenevaClusterBuilder,
    HeadGroupBuilder,
    WorkerGroupBuilder,
    default_image,
)


def test_builder_basic_creation() -> None:
    """Test basic cluster creation with minimal configuration."""
    cluster = GenevaClusterBuilder.create("test-cluster").build()

    assert cluster.name == "test-cluster"
    assert cluster.cluster_type == GenevaClusterType.KUBE_RAY
    assert cluster.kuberay is not None
    assert cluster.kuberay.namespace == "geneva"
    assert cluster.kuberay.config_method == K8sConfigMethod.LOCAL
    assert cluster.kuberay.use_portforwarding is True


def test_builder_requires_name() -> None:
    """Test that builder requires a name to be set."""
    with pytest.raises(ValueError, match="Cluster name is required"):
        GenevaClusterBuilder().build()


def test_builder_fluent_configuration() -> None:
    """Test fluent configuration methods."""
    cluster = (
        GenevaClusterBuilder()
        .name("fluent-test")
        .namespace("custom-ns")
        .config_method(K8sConfigMethod.IN_CLUSTER)
        .portforwarding(False)
        .aws_config(region="us-west-2", role_name="test-role")
        .build()
    )

    assert cluster.name == "fluent-test"
    assert cluster.kuberay.namespace == "custom-ns"
    assert cluster.kuberay.config_method == K8sConfigMethod.IN_CLUSTER
    assert cluster.kuberay.use_portforwarding is False
    assert cluster.kuberay.aws_region == "us-west-2"
    assert cluster.kuberay.aws_role_name == "test-role"


def test_builder_head_group_configuration() -> None:
    """Test head group configuration."""
    cluster = (
        GenevaClusterBuilder()
        .name("head-test")
        .head_group(
            image="custom:latest",
            cpus=8,
            memory="16Gi",
            gpus=1,
            service_account="custom-sa",
            node_selector={"node-type": "head"},
            labels={"role": "head"},
            tolerations=[{"key": "test", "operator": "Equal", "value": "true"}],
        )
        .build()
    )

    head = cluster.kuberay.head_group
    assert head.image == "custom:latest"
    assert head.num_cpus == 8
    assert head.memory == "16Gi"
    assert head.num_gpus == 1
    assert head.service_account == "custom-sa"
    assert head.node_selector == {"node-type": "head"}
    assert head.labels == {"role": "head"}
    assert head.tolerations == [{"key": "test", "operator": "Equal", "value": "true"}]


def test_builder_add_cpu_worker_group() -> None:
    """Test adding CPU worker groups."""
    cluster = (
        GenevaClusterBuilder()
        .name("cpu-worker-test")
        .add_cpu_worker_group(cpus=8, memory="16Gi")
        .add_cpu_worker_group(
            cpus=4,
            memory="8Gi",
            image="worker:latest",
            service_account="worker-sa",
            node_selector={"node-type": "worker"},
            labels={"role": "worker"},
            tolerations=[{"key": "worker", "operator": "Equal", "value": "true"}],
        )
        .build()
    )

    workers = cluster.kuberay.worker_groups
    assert len(workers) == 2

    # First worker group (basic)
    worker1 = workers[0]
    assert worker1.num_cpus == 8
    assert worker1.memory == "16Gi"
    assert worker1.num_gpus == 0
    assert worker1.image == default_image()  # Default head image

    # Second worker group (custom)
    worker2 = workers[1]
    assert worker2.num_cpus == 4
    assert worker2.memory == "8Gi"
    assert worker2.num_gpus == 0
    assert worker2.image == "worker:latest"
    assert worker2.service_account == "worker-sa"
    assert worker2.node_selector == {"node-type": "worker"}
    assert worker2.labels == {"role": "worker"}
    assert worker2.tolerations == [
        {"key": "worker", "operator": "Equal", "value": "true"}
    ]


def test_builder_add_gpu_worker_group() -> None:
    """Test adding GPU worker groups."""
    cluster = (
        GenevaClusterBuilder()
        .name("gpu-worker-test")
        .add_gpu_worker_group(cpus=16, memory="32Gi", gpus=2)
        .build()
    )

    workers = cluster.kuberay.worker_groups
    assert len(workers) == 1

    worker = workers[0]
    assert worker.num_cpus == 16
    assert worker.memory == "32Gi"
    assert worker.num_gpus == 2


def test_builder_default_worker_group() -> None:
    """Test that a default CPU worker group is added if none specified."""
    cluster = GenevaClusterBuilder.create("default-worker-test").build()

    workers = cluster.kuberay.worker_groups
    assert len(workers) == 1

    worker = workers[0]
    assert worker.num_cpus == 4
    assert worker.memory == "8Gi"
    assert worker.num_gpus == 0
    assert worker.service_account == "geneva-service-account"  # Head group default


def test_builder_local_cpu_cluster_preset() -> None:
    """Test the local CPU cluster preset."""
    cluster = GenevaClusterBuilder.local_cpu_cluster("local-test").build()

    assert cluster.name == "local-test"
    assert cluster.kuberay.namespace == "geneva"
    assert cluster.kuberay.config_method == K8sConfigMethod.LOCAL
    assert cluster.kuberay.use_portforwarding is True

    # Check head group
    head = cluster.kuberay.head_group
    assert head.num_cpus == 2
    assert head.memory == "4Gi"
    assert head.num_gpus == 0

    # Check worker group
    workers = cluster.kuberay.worker_groups
    assert len(workers) == 1
    worker = workers[0]
    assert worker.num_cpus == 4
    assert worker.memory == "8Gi"
    assert worker.num_gpus == 0


def test_builder_gpu_cluster_preset() -> None:
    """Test the GPU cluster preset."""
    cluster = GenevaClusterBuilder.gpu_cluster("gpu-test", namespace="custom").build()

    assert cluster.name == "gpu-test"
    assert cluster.kuberay.namespace == "custom"
    assert cluster.kuberay.config_method == K8sConfigMethod.IN_CLUSTER
    assert cluster.kuberay.use_portforwarding is False

    # Check head group
    head = cluster.kuberay.head_group
    assert head.num_cpus == 2
    assert head.memory == "4Gi"
    assert head.num_gpus == 0

    # Check worker groups
    workers = cluster.kuberay.worker_groups
    assert len(workers) == 1

    # GPU worker
    w = workers[0]
    assert w.num_cpus == 4
    assert w.memory == "8Gi"
    assert w.num_gpus == 1


def test_builder_chaining_configuration() -> None:
    """Test that method chaining works correctly."""
    builder = (
        GenevaClusterBuilder()
        .name("chain-test")
        .namespace("test")
        .head_group(cpus=4)
        .add_cpu_worker_group(cpus=8)
        .add_gpu_worker_group(gpus=2)
    )

    # Should be able to continue chaining
    cluster = builder.portforwarding(False).aws_config(region="eu-west-1").build()

    assert cluster.name == "chain-test"
    assert cluster.kuberay.namespace == "test"
    assert cluster.kuberay.use_portforwarding is False
    assert cluster.kuberay.aws_region == "eu-west-1"
    assert len(cluster.kuberay.worker_groups) == 2


def test_builder_partial_head_group_config() -> None:
    """Test that partial head group configuration preserves defaults."""
    cluster = (
        GenevaClusterBuilder()
        .name("partial-test")
        .head_group(cpus=8)  # Only change CPUs
        .build()
    )

    head = cluster.kuberay.head_group
    assert head.num_cpus == 8  # Changed
    assert head.memory == "4Gi"  # Default preserved
    assert head.image == default_image()  # Default preserved
    assert head.service_account == "geneva-service-account"  # Default preserved


def test_builder_to_ray_cluster_compatibility() -> None:
    """Test that built cluster can be converted to RayCluster."""
    cluster = (
        GenevaClusterBuilder()
        .name("compat-test")
        .namespace("test-ns")
        .add_cpu_worker_group(cpus=4)
        .build()
    )

    # Should not raise an exception
    ray_cluster = cluster.to_ray_cluster()
    assert ray_cluster.name == "compat-test"
    assert ray_cluster.namespace == "test-ns"


def test_head_group_builder_basic() -> None:
    """Test basic HeadGroupBuilder functionality."""
    head = HeadGroupBuilder().build()

    # Check defaults
    assert head.image == default_image()
    assert head.num_cpus == 2
    assert head.memory == "4Gi"
    assert head.num_gpus == 0
    assert head.service_account == "geneva-service-account"
    assert head.node_selector == {"geneva.lancedb.com/ray-head": "true"}
    assert head.labels == {}
    assert head.tolerations == []


def test_head_group_builder_fluent_interface() -> None:
    """Test HeadGroupBuilder fluent interface."""
    head = (
        HeadGroupBuilder()
        .image("custom:latest")
        .cpus(8)
        .memory("16Gi")
        .gpus(1)
        .service_account("custom-sa")
        .node_selector({"node-type": "head"})
        .labels({"role": "head"})
        .add_label("env", "test")
        .tolerations([{"key": "dedicated", "operator": "Equal", "value": "head"}])
        .add_toleration("test", "Equal", "true", "NoSchedule")
        .build()
    )

    assert head.image == "custom:latest"
    assert head.num_cpus == 8
    assert head.memory == "16Gi"
    assert head.num_gpus == 1
    assert head.service_account == "custom-sa"
    assert head.node_selector == {"node-type": "head"}
    assert head.labels == {"role": "head", "env": "test"}
    assert len(head.tolerations) == 2
    assert {
        "key": "dedicated",
        "operator": "Equal",
        "value": "head",
    } in head.tolerations
    assert {
        "key": "test",
        "operator": "Equal",
        "value": "true",
        "effect": "NoSchedule",
    } in head.tolerations


def test_head_group_builder_presets() -> None:
    """Test HeadGroupBuilder preset configurations."""
    # CPU head preset
    cpu_head = HeadGroupBuilder.cpu_head(cpus=4, memory="8Gi").build()
    assert cpu_head.num_cpus == 4
    assert cpu_head.memory == "8Gi"
    assert cpu_head.num_gpus == 0


def test_worker_group_builder_basic() -> None:
    """Test basic WorkerGroupBuilder functionality."""
    worker = WorkerGroupBuilder().build()

    # Check defaults
    assert worker.image == default_image()
    assert worker.num_cpus == 4
    assert worker.memory == "8Gi"
    assert worker.num_gpus == 0
    assert worker.service_account == "geneva-service-account"
    assert worker.node_selector == {"geneva.lancedb.com/ray-worker-cpu": "true"}
    assert worker.labels == {}
    assert worker.tolerations == []


def test_worker_group_builder_fluent_interface() -> None:
    """Test WorkerGroupBuilder fluent interface."""
    worker = (
        WorkerGroupBuilder()
        .image("worker:latest")
        .cpus(16)
        .memory("32Gi")
        .gpus(2)
        .service_account("worker-sa")
        .node_selector({"node-type": "worker"})
        .labels({"role": "worker"})
        .add_label("team", "ml")
        .tolerations([{"key": "gpu", "operator": "Equal", "value": "true"}])
        .add_toleration("intensive", effect="NoSchedule")
        .build()
    )

    assert worker.image == "worker:latest"
    assert worker.num_cpus == 16
    assert worker.memory == "32Gi"
    assert worker.num_gpus == 2
    assert worker.service_account == "worker-sa"
    assert worker.node_selector == {"node-type": "worker"}
    assert worker.labels == {"role": "worker", "team": "ml"}
    assert len(worker.tolerations) == 2
    assert {"key": "gpu", "operator": "Equal", "value": "true"} in worker.tolerations
    assert {
        "key": "intensive",
        "operator": "Equal",
        "effect": "NoSchedule",
    } in worker.tolerations


def test_worker_group_builder_presets() -> None:
    """Test WorkerGroupBuilder preset configurations."""
    # CPU worker preset
    cpu_worker = WorkerGroupBuilder.cpu_worker(cpus=8, memory="16Gi").build()
    assert cpu_worker.num_cpus == 8
    assert cpu_worker.memory == "16Gi"
    assert cpu_worker.num_gpus == 0

    # GPU worker preset
    gpu_worker = WorkerGroupBuilder.gpu_worker(cpus=16, memory="32Gi", gpus=4).build()
    assert gpu_worker.num_cpus == 16
    assert gpu_worker.memory == "32Gi"
    assert gpu_worker.num_gpus == 4


def test_cluster_builder_with_head_group_builder() -> None:
    """Test GenevaClusterBuilder integration with HeadGroupBuilder."""
    head_builder = (
        HeadGroupBuilder().cpus(8).memory("16Gi").service_account("custom-head")
    )

    cluster = (
        GenevaClusterBuilder()
        .name("builder-test")
        .head_group_builder(head_builder)
        .build()
    )

    assert cluster.kuberay.head_group.num_cpus == 8
    assert cluster.kuberay.head_group.memory == "16Gi"
    assert cluster.kuberay.head_group.service_account == "custom-head"


def test_cluster_builder_with_worker_group_builder_gpu() -> None:
    worker_builder = (
        WorkerGroupBuilder()
        .cpus(16)
        .memory("32Gi")
        .gpus(2)
        .labels({"role": "gpu-worker"})
    )

    cluster = (
        GenevaClusterBuilder()
        .name("worker-builder-test")
        .head_group(service_account="head-sa", image="head:latest")
        .add_worker_group(worker_builder)
        .build()
    )

    workers = cluster.kuberay.worker_groups
    assert len(workers) == 1

    worker = workers[0]
    assert worker.num_cpus == 16
    assert worker.memory == "32Gi"
    assert worker.num_gpus == 2
    assert worker.labels == {"role": "gpu-worker"}
    assert worker.service_account == "geneva-service-account"

    # should use GPU image because num_gpus > 0
    assert worker.image == default_image(True)


def test_cluster_builder_with_worker_group_builder_no_gpu() -> None:
    worker_builder = (
        WorkerGroupBuilder().cpus(16).memory("32Gi").labels({"role": "gpu-worker"})
    )

    cluster = (
        GenevaClusterBuilder()
        .name("worker-builder-test")
        .add_worker_group(worker_builder)
        .build()
    )

    workers = cluster.kuberay.worker_groups
    assert len(workers) == 1

    worker = workers[0]
    assert worker.num_cpus == 16
    assert worker.memory == "32Gi"
    assert worker.num_gpus == 0
    assert worker.labels == {"role": "gpu-worker"}
    assert worker.service_account == "geneva-service-account"
    assert worker.image == default_image(False)


def test_cluster_builder_mixed_worker_approaches() -> None:
    """Test mixing different worker group addition methods."""
    worker_builder = WorkerGroupBuilder.gpu_worker(gpus=4)

    cluster = (
        GenevaClusterBuilder()
        .name("mixed-test")
        .add_cpu_worker_group(cpus=8)  # Direct method
        .add_worker_group(worker_builder)  # Builder method
        .add_gpu_worker_group(gpus=2, memory="64Gi")  # Direct method again
        .build()
    )

    workers = cluster.kuberay.worker_groups
    assert len(workers) == 3

    # CPU worker (direct)
    assert workers[0].num_cpus == 8
    assert workers[0].num_gpus == 0

    # GPU worker (builder)
    assert workers[1].num_cpus == 8  # From preset
    assert workers[1].num_gpus == 4

    # GPU worker (direct)
    assert workers[2].num_gpus == 2
    assert workers[2].memory == "64Gi"


def test_cluster_builder_must_be_kuberay() -> None:
    with pytest.raises(
        ValueError, match=re.escape("cluster_type must be one of ['KUBE_RAY']")
    ):
        GenevaClusterBuilder().name("mixed-test").cluster_type(
            GenevaClusterType.LOCAL_RAY
        ).build()


def test_builder_ray_init_kwargs() -> None:
    """Test that ray_init_kwargs can be set and are passed through."""
    conda_env = {
        "conda": {
            "channels": ["conda-forge"],
            "dependencies": [
                "python=3.10",
                "ffmpeg<8",
                "torchvision=0.22.1",
                {"pip": ["transformers==4.57.1", "torchcodec==0.5.0"]},
            ],
        },
        "config": {"eager_install": True},
    }

    cluster = (
        GenevaClusterBuilder()
        .name("ray-init-test")
        .ray_init_kwargs({"runtime_env": conda_env})
        .build()
    )

    assert cluster.kuberay.ray_init_kwargs == {"runtime_env": conda_env}

    # Verify it's passed through to RayCluster
    ray_cluster = cluster.to_ray_cluster()
    assert ray_cluster.ray_init_kwargs == {"runtime_env": conda_env}


def test_builder_ray_init_kwargs_default_empty() -> None:
    """Test that ray_init_kwargs defaults to empty dict."""
    cluster = GenevaClusterBuilder.create("default-test").build()

    assert cluster.kuberay.ray_init_kwargs == {}


def test_builder_ray_init_kwargs_immutable() -> None:
    """Test that ray_init_kwargs makes a copy to avoid mutation."""
    original_kwargs = {"runtime_env": {"conda": {"dependencies": ["python=3.10"]}}}

    builder = (
        GenevaClusterBuilder().name("immutable-test").ray_init_kwargs(original_kwargs)
    )

    # Mutate the original
    original_kwargs["runtime_env"]["conda"]["dependencies"].append("numpy")

    cluster = builder.build()

    # Should not have been affected by mutation
    assert cluster.kuberay.ray_init_kwargs["runtime_env"]["conda"]["dependencies"] == [
        "python=3.10"
    ]

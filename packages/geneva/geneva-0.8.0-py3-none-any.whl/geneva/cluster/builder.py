# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import copy
import platform
import sys

import ray

from geneva.cluster import GenevaClusterType, K8sConfigMethod
from geneva.cluster.mgr import (
    GenevaCluster,
    HeadGroupConfig,
    KubeRayConfig,
    WorkerGroupConfig,
)
from geneva.utils.ray import (
    GENEVA_RAY_CPU_NODE,
    GENEVA_RAY_GPU_NODE,
    GENEVA_RAY_HEAD_NODE,
    get_ray_image,
)


class HeadGroupBuilder:
    """Builder for HeadGroupConfig. This can be used to build the configuration for
    a Ray head group with reasonable defaults. See GenevaClusterBuilder for examples"""

    def __init__(self) -> None:
        self._image: str = default_image()
        self._num_cpus: int = 2
        self._memory: str = "4Gi"
        self._num_gpus: int = 0
        self._service_account: str = "geneva-service-account"
        self._node_selector: dict[str, str] = {GENEVA_RAY_HEAD_NODE: "true"}
        self._labels: dict[str, str] = {}
        self._tolerations: list[dict[str, str]] = []

    def image(self, image: str) -> "HeadGroupBuilder":
        """Set the container image."""
        self._image = image
        return self

    def cpus(self, cpus: int) -> "HeadGroupBuilder":
        """Set the number of CPUs."""
        self._num_cpus = cpus
        return self

    def memory(self, memory: str) -> "HeadGroupBuilder":
        """Set the memory allocation (e.g., '4Gi', '8Gi')."""
        self._memory = memory
        return self

    def gpus(self, gpus: int) -> "HeadGroupBuilder":
        """Set the number of GPUs."""
        self._num_gpus = gpus
        return self

    def service_account(self, service_account: str) -> "HeadGroupBuilder":
        """Set the Kubernetes service account."""
        self._service_account = service_account
        return self

    def node_selector(self, node_selector: dict[str, str]) -> "HeadGroupBuilder":
        """Set the node selector for pod placement."""
        self._node_selector = node_selector.copy()
        return self

    def labels(self, labels: dict[str, str]) -> "HeadGroupBuilder":
        """Set the pod labels."""
        self._labels = labels.copy()
        return self

    def tolerations(self, tolerations: list[dict[str, str]]) -> "HeadGroupBuilder":
        """Set the pod tolerations."""
        self._tolerations = tolerations.copy()
        return self

    def add_label(self, key: str, value: str) -> "HeadGroupBuilder":
        """Add a single label."""
        self._labels[key] = value
        return self

    def add_toleration(
        self, key: str, operator: str = "Equal", value: str = "", effect: str = ""
    ) -> "HeadGroupBuilder":
        """Add a single toleration."""
        toleration = {"key": key, "operator": operator}
        if value:
            toleration["value"] = value
        if effect:
            toleration["effect"] = effect
        self._tolerations.append(toleration)
        return self

    def build(self) -> HeadGroupConfig:
        """Build the HeadGroupConfig."""
        return HeadGroupConfig(
            service_account=self._service_account,
            num_cpus=self._num_cpus,
            memory=self._memory,
            image=self._image,
            num_gpus=self._num_gpus,
            node_selector=self._node_selector,
            labels=self._labels,
            tolerations=self._tolerations,
        )

    @classmethod
    def create(cls) -> "HeadGroupBuilder":
        """Create a new head group builder with defaults."""
        return cls()

    @classmethod
    def cpu_head(cls, cpus: int = 2, memory: str = "4Gi") -> "HeadGroupBuilder":
        """Create a CPU-only head group."""
        return cls().cpus(cpus).memory(memory).gpus(0)


class WorkerGroupBuilder:
    """Builder for WorkerGroupConfig. This can be used to build the configuration for
    a Ray worker group with reasonable defaults. See GenevaClusterBuilder for
    examples"""

    def __init__(self) -> None:
        self._image: str = default_image()
        self._num_cpus: int = 4
        self._memory: str = "8Gi"
        self._num_gpus: int = 0
        self._service_account: str = "geneva-service-account"
        self._node_selector: dict[str, str] = {GENEVA_RAY_CPU_NODE: "true"}
        self._labels: dict[str, str] = {}
        self._tolerations: list[dict[str, str]] = []

    def image(self, image: str) -> "WorkerGroupBuilder":
        """Set the container image."""
        self._image = image
        return self

    def cpus(self, cpus: int) -> "WorkerGroupBuilder":
        """Set the number of CPUs."""
        self._num_cpus = cpus
        return self

    def memory(self, memory: str) -> "WorkerGroupBuilder":
        """Set the memory allocation (e.g., '8Gi', '16Gi')."""
        self._memory = memory
        return self

    def gpus(self, gpus: int) -> "WorkerGroupBuilder":
        """Set the number of GPUs."""
        self._num_gpus = gpus
        return self

    def service_account(self, service_account: str) -> "WorkerGroupBuilder":
        """Set the Kubernetes service account."""
        self._service_account = service_account
        return self

    def node_selector(self, node_selector: dict[str, str]) -> "WorkerGroupBuilder":
        """Set the node selector for pod placement."""
        self._node_selector = node_selector.copy()
        return self

    def labels(self, labels: dict[str, str]) -> "WorkerGroupBuilder":
        """Set the pod labels."""
        self._labels = labels.copy()
        return self

    def tolerations(self, tolerations: list[dict[str, str]]) -> "WorkerGroupBuilder":
        """Set the pod tolerations."""
        self._tolerations = tolerations.copy()
        return self

    def add_label(self, key: str, value: str) -> "WorkerGroupBuilder":
        """Add a single label."""
        self._labels[key] = value
        return self

    def add_toleration(
        self, key: str, operator: str = "Equal", value: str = "", effect: str = ""
    ) -> "WorkerGroupBuilder":
        """Add a single toleration."""
        toleration = {"key": key, "operator": operator}
        if value:
            toleration["value"] = value
        if effect:
            toleration["effect"] = effect
        self._tolerations.append(toleration)
        return self

    def build(self) -> WorkerGroupConfig:
        """Build the WorkerGroupConfig."""
        # modify default image to enable GPU if GPUs are requested
        if self._image == default_image() and self._num_gpus > 0:
            self._image = default_image(gpu=True)

        return WorkerGroupConfig(
            service_account=self._service_account,
            num_cpus=self._num_cpus,
            memory=self._memory,
            image=self._image,
            num_gpus=self._num_gpus,
            node_selector=self._node_selector,
            labels=self._labels,
            tolerations=self._tolerations,
        )

    @classmethod
    def create(cls) -> "WorkerGroupBuilder":
        """Create a new worker group builder with defaults."""
        return cls()

    @classmethod
    def cpu_worker(cls, cpus: int = 4, memory: str = "8Gi") -> "WorkerGroupBuilder":
        """Create a CPU worker group."""
        return cls().cpus(cpus).memory(memory).gpus(0)

    @classmethod
    def gpu_worker(
        cls, cpus: int = 8, memory: str = "16Gi", gpus: int = 1
    ) -> "WorkerGroupBuilder":
        """Create a GPU worker group."""
        return (
            cls()
            .cpus(cpus)
            .node_selector({GENEVA_RAY_GPU_NODE: "true"})
            .memory(memory)
            .gpus(gpus)
        )


class GenevaClusterBuilder:
    """Fluent builder for GenevaCluster. `name` is required, all optional
    fields will use defaults.
        example usage:
         >>> GenevaClusterBuilder
         >>>    .name("my-cluster")
         >>>    .head_group_builder(HeadGroupBuilder().cpus(8).memory("16Gi"))
         >>>    .add_worker_group(WorkerGroupBuilder()
         >>>                         .gpu_worker(memory="8Gi", gpus=1))
         >>>    .build()
    """

    def __init__(self) -> None:
        self._name: str | None = None
        self._cluster_type: GenevaClusterType = GenevaClusterType.KUBE_RAY
        self._namespace: str = "geneva"
        self._config_method: K8sConfigMethod = K8sConfigMethod.LOCAL
        self._use_portforwarding: bool = True
        self._aws_region: str | None = None
        self._aws_role_name: str | None = None
        self._ray_init_kwargs: dict = {}

        # Head group defaults
        self._head_image: str = default_image()
        self._head_cpus: int = 2
        self._head_memory: str = "4Gi"
        self._head_gpus: int = 0
        self._head_service_account: str = "geneva-service-account"
        self._head_node_selector: dict[str, str] = {}
        self._head_labels: dict[str, str] = {}
        self._head_tolerations: list[dict[str, str]] = []

        # Worker group defaults
        self._worker_groups: list[WorkerGroupConfig] = []

    def name(self, name: str) -> "GenevaClusterBuilder":
        """Set the cluster name."""
        self._name = name
        return self

    def cluster_type(self, cluster_type: GenevaClusterType) -> "GenevaClusterBuilder":
        """Set the cluster type."""
        self._cluster_type = cluster_type
        return self

    def namespace(self, namespace: str) -> "GenevaClusterBuilder":
        """Set the Kubernetes namespace."""
        self._namespace = namespace
        return self

    def config_method(self, method: K8sConfigMethod) -> "GenevaClusterBuilder":
        """Set the Kubernetes config method."""
        self._config_method = method
        return self

    def portforwarding(self, enabled: bool = True) -> "GenevaClusterBuilder":
        """Enable or disable port forwarding."""
        self._use_portforwarding = enabled
        return self

    def aws_config(
        self, region: str | None = None, role_name: str | None = None
    ) -> "GenevaClusterBuilder":
        """Configure AWS settings."""
        self._aws_region = region
        self._aws_role_name = role_name
        return self

    def ray_init_kwargs(self, kwargs: dict) -> "GenevaClusterBuilder":
        """
        Set arbitrary kwargs to pass to ray.init() when starting the cluster.

        Commonly used for runtime_env configuration with conda or pip
        dependencies.

        Example:
            >>> builder.ray_init_kwargs({
            ...     "runtime_env": {
            ...         "conda": {
            ...             "channels": ["conda-forge"],
            ...             "dependencies": [
            ...                 "python=3.10", "ffmpeg<8", "torchvision=0.22.1"
            ...             ]
            ...         },
            ...         "config": {"eager_install": True}
            ...     }
            ... })

        WARNING: This accepts arbitrary kwargs without validation allowing for injection
        of fault or potentially malicious configuration. Use with caution.
        """
        self._ray_init_kwargs = copy.deepcopy(kwargs)
        return self

    # Head group configuration
    def head_group(
        self,
        *,
        image: str | None = None,
        cpus: int | None = None,
        memory: str | None = None,
        gpus: int | None = None,
        service_account: str | None = None,
        node_selector: dict[str, str] | None = None,
        labels: dict[str, str] | None = None,
        tolerations: list[dict[str, str]] | None = None,
    ) -> "GenevaClusterBuilder":
        """Configure the head group with optional parameters."""
        if image is not None:
            self._head_image = image
        if cpus is not None:
            self._head_cpus = cpus
        if memory is not None:
            self._head_memory = memory
        if gpus is not None:
            self._head_gpus = gpus
        if service_account is not None:
            self._head_service_account = service_account
        if node_selector is not None:
            self._head_node_selector = node_selector
        if labels is not None:
            self._head_labels = labels
        if tolerations is not None:
            self._head_tolerations = tolerations
        return self

    def head_group_builder(self, builder: HeadGroupBuilder) -> "GenevaClusterBuilder":
        """Configure the head group using a HeadGroupBuilder."""
        head_config = builder.build()
        self._head_image = head_config.image
        self._head_cpus = head_config.num_cpus
        self._head_memory = head_config.memory
        self._head_gpus = head_config.num_gpus
        self._head_service_account = head_config.service_account
        self._head_node_selector = head_config.node_selector
        self._head_labels = head_config.labels
        self._head_tolerations = head_config.tolerations
        return self

    def add_cpu_worker_group(
        self,
        *,
        image: str | None = None,
        cpus: int = 4,
        memory: str = "8Gi",
        service_account: str | None = None,
        node_selector: dict[str, str] | None = None,
        labels: dict[str, str] | None = None,
        tolerations: list[dict[str, str]] | None = None,
    ) -> "GenevaClusterBuilder":
        """Add a CPU worker group."""
        worker = WorkerGroupConfig(
            image=image or self._head_image,
            num_cpus=cpus,
            memory=memory,
            num_gpus=0,
            service_account=service_account or "geneva-service-account",
            node_selector=node_selector or {GENEVA_RAY_CPU_NODE: "true"},
            labels=labels or {},
            tolerations=tolerations or [],
        )
        self._worker_groups.append(worker)
        return self

    def add_gpu_worker_group(
        self,
        *,
        image: str | None = None,
        cpus: int = 4,
        memory: str = "8Gi",
        gpus: int = 1,
        service_account: str | None = None,
        node_selector: dict[str, str] | None = None,
        labels: dict[str, str] | None = None,
        tolerations: list[dict[str, str]] | None = None,
    ) -> "GenevaClusterBuilder":
        """Add a GPU worker group."""
        worker = WorkerGroupConfig(
            image=image or self._head_image,
            num_cpus=cpus,
            memory=memory,
            num_gpus=gpus,
            service_account=service_account or "geneva-service-account",
            node_selector=node_selector or {GENEVA_RAY_GPU_NODE: "true"},
            labels=labels or {},
            tolerations=tolerations or [],
        )
        self._worker_groups.append(worker)
        return self

    def add_worker_group(self, builder: WorkerGroupBuilder) -> "GenevaClusterBuilder":
        """Add a worker group using a WorkerGroupBuilder."""
        worker = builder.build()
        self._worker_groups.append(worker)
        return self

    def build(self) -> GenevaCluster:
        """Build the GenevaCluster with the configured settings."""
        if self._name is None:
            raise ValueError("Cluster name is required. Use .name() to set it.")

        # Build head group config
        head_group = HeadGroupConfig(
            service_account=self._head_service_account,
            num_cpus=self._head_cpus,
            memory=self._head_memory,
            image=self._head_image,
            num_gpus=self._head_gpus,
            node_selector=self._head_node_selector,
            labels=self._head_labels,
            tolerations=self._head_tolerations,
        )

        # Use worker group configs directly (already WorkerGroupConfig objects)
        worker_groups = self._worker_groups.copy()

        # If no worker groups were explicitly added, add a default CPU worker
        if not worker_groups:
            worker_groups.append(
                WorkerGroupConfig(
                    service_account=self._head_service_account,
                    num_cpus=4,
                    memory="8Gi",
                    image=default_image(False),
                    num_gpus=0,
                    node_selector={GENEVA_RAY_CPU_NODE: "true"},
                    labels={},
                    tolerations=[],
                )
            )

        supported_cluster_types = [GenevaClusterType.KUBE_RAY]
        if self._cluster_type not in supported_cluster_types:
            raise ValueError(
                f"cluster_type must be one of "
                f"{[e.name for e in supported_cluster_types]}"
            )

        kuberay_config = KubeRayConfig(
            namespace=self._namespace,
            head_group=head_group,
            worker_groups=worker_groups,
            config_method=self._config_method,
            use_portforwarding=self._use_portforwarding,
            aws_region=self._aws_region,
            aws_role_name=self._aws_role_name,
            ray_init_kwargs=self._ray_init_kwargs,
        )

        # Build and return the cluster
        return GenevaCluster(
            cluster_type=self._cluster_type,
            name=self._name,
            kuberay=kuberay_config,
        )

    @classmethod
    def create(cls, name: str) -> "GenevaClusterBuilder":
        """Create a new builder with the given cluster name."""
        return cls().name(name)

    @classmethod
    def local_cpu_cluster(
        cls, name: str, namespace: str = "geneva"
    ) -> "GenevaClusterBuilder":
        """Create a builder for a local CPU-only cluster with good defaults."""
        return (
            cls()
            .name(name)
            .namespace(namespace)
            .config_method(K8sConfigMethod.LOCAL)
            .portforwarding(True)
            .head_group(cpus=2, memory="4Gi")
            .add_cpu_worker_group(cpus=4, memory="8Gi")
        )

    @classmethod
    def gpu_cluster(
        cls, name: str, namespace: str = "geneva"
    ) -> "GenevaClusterBuilder":
        """Create a builder for a GPU cluster with good defaults."""
        return (
            cls()
            .name(name)
            .namespace(namespace)
            .config_method(K8sConfigMethod.IN_CLUSTER)
            .portforwarding(False)
            .head_group(cpus=2, memory="4Gi")
            .add_gpu_worker_group(cpus=4, memory="8Gi", gpus=1)
        )


def default_image(
    gpu: bool = False, arm: bool = platform.processor() in {"aarch64", "arm"}
) -> str:
    """Get the default Ray image"""
    ray_version = ray.__version__
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    return get_ray_image(
        ray_version,
        python_version,
        gpu=gpu,
        arm=arm,
    )

# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors
import enum
import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

import attrs
import cattrs
import pyarrow as pa
from attr import asdict

from geneva.cluster import GenevaClusterType, K8sConfigMethod
from geneva.state.manager import BaseManager
from geneva.utils import current_user, escape_sql_string, retry_lance

if TYPE_CHECKING:
    from geneva.runners.ray.raycluster import RayCluster

CLUSTER_TABLE_NAME = "geneva_cluster_definitions"

_LOG = logging.getLogger(__name__)


@attrs.define
class RayGroupConfig:
    """Configuration for Ray pods"""

    service_account: str = attrs.field()
    num_cpus: int = attrs.field()
    memory: str = attrs.field()
    image: str = attrs.field()
    node_selector: dict[str, str] = attrs.field()
    labels: dict[str, str] = attrs.field()
    tolerations: list[dict[str, str]] = attrs.field()
    num_gpus: int = attrs.field(default=0)


@attrs.define
class HeadGroupConfig(RayGroupConfig):
    """Configuration for Ray Head pod"""

    # Escape hatch for arbitrary Kubernetes/KubeRay spec customizations.
    # Allows setting any K8s fields not exposed as direct parameters.
    # Values are deep-merged into the generated K8s spec in definition().
    # Examples: priority_class, securityContext, initContainers, volumes, etc.
    k8s_spec_override: dict[str, Any] | None = attrs.field(
        default=None, metadata={"pa_type": "string", "nullable": True}
    )


@attrs.define
class WorkerGroupConfig(RayGroupConfig):
    """Configuration for Ray Worker pods"""

    # Escape hatch for arbitrary Kubernetes/KubeRay spec customizations.
    # Allows setting any K8s fields not exposed as direct parameters.
    # Values are deep-merged into the generated K8s spec in definition().
    # Examples: replicas, min_replicas, max_replicas, securityContext, etc.
    k8s_spec_override: dict[str, Any] | None = attrs.field(
        default=None,
    )


@attrs.define
class KubeRayConfig:
    namespace: str = attrs.field()
    head_group: HeadGroupConfig = attrs.field()
    worker_groups: list[WorkerGroupConfig] = attrs.field()
    config_method: K8sConfigMethod = attrs.field(default=K8sConfigMethod.LOCAL)
    use_portforwarding: bool = attrs.field(default=True)
    aws_region: Optional[str] = attrs.field(default=None)
    aws_role_name: Optional[str] = attrs.field(default=None)

    # Arbitrary kwargs to pass to ray.init()
    ray_init_kwargs: Optional[dict[str, Any]] = attrs.field(
        factory=dict,
    )


@attrs.define
class GenevaCluster:
    """A Geneva Cluster represents the backend compute infrastructure
    for the execution environment."""

    cluster_type: GenevaClusterType = attrs.field(metadata={"pa_type": pa.string()})
    name: str = attrs.field()

    # serialize nested structs as json strings, so we can add new fields
    # without requiring schema evolution
    kuberay: Optional[KubeRayConfig] = attrs.field(
        default=None, metadata={"pa_type": "string"}
    )
    created_at: datetime = attrs.field(
        factory=lambda: datetime.now(timezone.utc),
        metadata={"pa_type": pa.timestamp("us", tz="UTC")},
    )
    created_by: str = attrs.field(factory=current_user)

    def validate(self) -> None:
        # use attrs validation on RayCluster
        self.to_ray_cluster()

    def to_ray_cluster(self) -> "RayCluster":
        """Convert the persisted cluster definition into internal RayCluster model"""
        from geneva.runners.ray.raycluster import (
            RayCluster,
            _HeadGroupSpec,
            _WorkerGroupSpec,
        )

        c = asdict(self)
        k = c["kuberay"]
        k.pop("use_portforwarding")
        k["region"] = k.pop("aws_region")
        k["role_name"] = k.pop("aws_role_name")
        k["name"] = c["name"]
        k["config_method"] = K8sConfigMethod(k["config_method"])

        # Create spec objects directly - k8s_spec_override deep-merged in definition()
        k["head_group"] = _HeadGroupSpec(**k["head_group"])
        k["worker_groups"] = [_WorkerGroupSpec(**wg) for wg in k["worker_groups"]]

        # Extract ray_init_kwargs
        ray_init_kwargs = k.pop("ray_init_kwargs", {})
        rc = RayCluster(**k, ray_init_kwargs=ray_init_kwargs)
        return rc

    def as_dict(self) -> dict:
        return attrs.asdict(
            self,
            value_serializer=lambda obj, a, v: v.value
            if isinstance(v, enum.Enum)
            else v,
        )


class ClusterConfigManager(BaseManager):
    def get_table_name(self) -> str:
        return CLUSTER_TABLE_NAME

    def get_model(self) -> Any:
        # Create a complete dummy model with all nested fields populated
        # so schema inference can correctly determine nullability of nested fields
        head_group = HeadGroupConfig(
            service_account="dummy",
            num_cpus=1,
            memory="1Gi",
            image="dummy",
            node_selector={},
            labels={},
            tolerations=[],
            k8s_spec_override=None,  # Include to ensure schema has nullable field
        )
        kuberay_config = KubeRayConfig(
            namespace="dummy",
            head_group=head_group,
            worker_groups=[],
            ray_init_kwargs={},  # Include to ensure schema has nullable field
        )
        return GenevaCluster(
            cluster_type=GenevaClusterType.KUBE_RAY,
            name="dummy",
            kuberay=kuberay_config,
        )

    @retry_lance
    def upsert(self, cluster: GenevaCluster) -> None:
        val = cluster.as_dict()
        val["kuberay"] = json.dumps(val["kuberay"])

        # note: merge_insert with fails with schema errors - use delete+add for now
        self.delete(cluster.name)
        self.get_table().add([val])

    @retry_lance
    def list(self, limit: int = 1000) -> list[GenevaCluster]:
        res = self.get_table(True).search().limit(limit).to_arrow().to_pylist()
        return [_make_cluster(cluster) for cluster in res]

    @retry_lance
    def load(self, name: str) -> GenevaCluster | None:
        res = (
            self.get_table(True)
            .search()
            .where(f"name = '{escape_sql_string(name)}'")
            .limit(1)
            .to_arrow()
            .to_pylist()
        )
        if not res:
            return None
        return _make_cluster(res[0])

    @retry_lance
    def delete(self, name: str) -> None:
        self.get_table().delete(f"name = '{escape_sql_string(name)}'")


def _make_cluster(args: dict) -> GenevaCluster:
    # parse stringified json fields
    args["kuberay"] = json.loads(args["kuberay"])

    converter = cattrs.Converter()
    converter.register_structure_hook(
        datetime,
        lambda ts, _: datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if isinstance(ts, str)
        else ts,
    )
    res = converter.structure(args, GenevaCluster)

    return res

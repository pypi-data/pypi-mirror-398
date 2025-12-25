# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors
from enum import Enum


class GenevaClusterType(Enum):
    """Type of Geneva Cluster"""

    KUBE_RAY = "KUBE_RAY"
    LOCAL_RAY = "LOCAL_RAY"


class K8sConfigMethod(Enum):
    """Method for retrieving kubernetes config.
    LOCAL: Load the kube config from the local environment.
    EKS_AUTH: Load the kube config from AWS EKS service (requires AWS credentials)
    IN_CLUSTER: Load the kube config when running inside a pod in the cluster
    """

    EKS_AUTH = "EKS_AUTH"
    IN_CLUSTER = "IN_CLUSTER"
    LOCAL = "LOCAL"

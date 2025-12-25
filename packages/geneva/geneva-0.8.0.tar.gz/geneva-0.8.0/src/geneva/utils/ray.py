# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

GENEVA_RAY_HEAD_NODE = "geneva.lancedb.com/ray-head"
GENEVA_RAY_CPU_NODE = "geneva.lancedb.com/ray-worker-cpu"
GENEVA_RAY_GPU_NODE = "geneva.lancedb.com/ray-worker-gpu"

CPU_ONLY_NODE = "cpu-only"


def get_ray_image(
    version: str, python_version: str, *, gpu: bool = False, arm: bool = False
) -> str:
    py_version = python_version.replace(".", "")
    image = f"rayproject/ray:{version}-py{py_version}"
    if gpu:
        image += "-gpu"
    if arm:
        # todo: is this needed? ray provides multi-platform images
        image += "-aarch64"
    return image

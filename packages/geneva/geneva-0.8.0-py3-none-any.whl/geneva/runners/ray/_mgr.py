# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

# manage ray cluster setup

"""
Why?
Setting up a cluster involves a lot of state and resource management
for different users the resources created during cluster setup can
include:
- Kuberay Cluster
- Portforwarding Server
- packaged zips
- ray context initialization

There are three issues:
1. We want to make sure the api for setting up a cluster is simple, which
means everything should be in a single place instead of requiring a bunch
of different context managers to be created. Consider
```python
with(
    KuberayCluster(),
    PortforwardingServer(),
    PackagedZips(),
    RayContextInit()
):
    # do something with the cluster
)
```
We do not want to require the user to do this. However if we keep everything
in a single context manager a second issue arises.

2. We want to make sure that the resources are cleaned up when the context
manager exits, that includes when resource setup fails. Doing this in a single
context manager is difficult. Consider
```python
def __enter__(self):
    try:
        do_kuberay_cluster_setup()
    except Exception as e:
        # cleanup resources
        raise e

    try:
        start_portforwarding_server()
    except Exception as e:
        # cleanup resources
        raise e

    ...

def __exit__(self, exc_type, exc_value, traceback):
    try:
        shutdown_ray_context()
    except Exception as e:
        # cleanup resources
        raise e

    try:
        shutdown_portforwarding_server()
    except Exception as e:
        # cleanup resources
        raise e

    ...
```

3. Users may want start at any one of the following points:
  - only has k8s + kuberay installed
  - has a ray cluster
  - has dependency already setup in the ray cluster
  We need a way to allow users to start at any one of these points

To solve the first two issues we create a setup_cluster func, to help with
entering and exiting the context manager
```python
with ray_cluster(
    cluster_settings={...},
    use_portforwarding=True,
    delete_packaged_zips=False,
    ...
) as m:
    # do something with the cluster
```
As long as the manager deligates the setup and teardown error handling
to contextlib.ExitStack, we can be sure that all resources are cleaned up
correctly.

The third issue is solved by allowing the user to pass in a ray address
to the setup_cluster function.
"""

import base64
import contextlib
import json
import logging
import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pyarrow as pa
import ray
from emoji import emojize
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

import geneva
from geneva.manifest.mgr import GenevaManifest
from geneva.packager.autodetect import upload_local_env
from geneva.packager.uploader import Uploader
from geneva.runners.ray._portforward import PortForward
from geneva.runners.ray.raycluster import RayCluster

_LOG = logging.getLogger(__name__)

# Default number of retry attempts for ray.init() connection failures
# Can be overridden via GENEVA_RAY_INIT_MAX_RETRIES environment variable
RAY_INIT_MAX_RETRIES = int(os.environ.get("GENEVA_RAY_INIT_MAX_RETRIES", "5"))


@contextlib.contextmanager
def init_ray(
    *,
    addr: str | None,
    zips: list[list[str]],
    pip: list[str] | None = None,
    local: bool = False,
    py_modules: list | None = None,
    extra_env: dict[str, str] | None = None,
    log_to_driver: bool = False,
    logging_level=logging.INFO,
    ray_init_kwargs: dict | None = None,
    uploader: Uploader | None = None,
    cluster: RayCluster | None = None,
) -> Generator[None, None, None]:
    if ray.is_initialized():
        raise RuntimeError("Ray is already initialized, we cannot start a new cluster")

    # Build payload with namespace info for downloading zips
    payload: dict[str, Any] = {"zips": zips}
    if uploader is not None and uploader.namespace_impl is not None:
        payload["namespace"] = {
            "impl": uploader.namespace_impl,
            "properties": uploader.namespace_properties,
            "table_id": uploader.table_id,
        }
    geneva_zip_payload = base64.b64encode(json.dumps(payload).encode()).decode()

    # note: can we remove these to improve cold start times?
    default_modules = [geneva, pa]
    if not py_modules:
        py_modules = default_modules

    # modules result in "TypeError: cannot pickle 'module' object" in local ray
    modules = [] if local else py_modules

    # Configure pip to use custom PyPI indexes for Ray workers
    # This allows workers to install packages from private indexes
    # configured in pyproject.toml
    pip_extra_index_url = " ".join(
        [
            "https://pypi.fury.io/lancedb/",
            "https://pypi.fury.io/lance-format/",
        ]
    )

    runtime_env = {
        "env_vars": {
            "PIP_EXTRA_INDEX_URL": pip_extra_index_url,
            "GENEVA_ZIPS": geneva_zip_payload,
            **(extra_env or {}),
        },
        **({"pip": pip} if pip else {}),
    }
    if modules:
        runtime_env.update(py_modules=modules)

    # Merge runtime_env from ray_init_kwargs if provided
    # Note on Ray runtime_env constraints:
    # - conda and pip cannot be specified simultaneously
    # - container works alone or only with config/env_vars
    # If user creates invalid combinations (e.g., Geneva sets pip via parameter
    # and user sets conda via ray_init_kwargs), Ray will validate and raise an
    # error. Users can override by explicitly setting conflicting fields to None.
    if ray_init_kwargs and "runtime_env" in ray_init_kwargs:
        user_runtime_env = ray_init_kwargs.get("runtime_env", {})
        if user_runtime_env:
            # Make a shallow copy to avoid mutating input
            ray_init_kwargs = {
                k: v for k, v in ray_init_kwargs.items() if k != "runtime_env"
            }

        # Merge env_vars
        if "env_vars" in user_runtime_env:
            runtime_env["env_vars"] = {
                **runtime_env["env_vars"],
                **user_runtime_env["env_vars"],
            }
            user_runtime_env = {
                k: v for k, v in user_runtime_env.items() if k != "env_vars"
            }
        # Merge remaining runtime_env keys (user settings override Geneva defaults)
        runtime_env = {**runtime_env, **user_runtime_env}

    _LOG.debug(f"initializing ray at {addr or 'local'} with {runtime_env=}")

    # Build ray.init kwargs
    init_kwargs = {
        "address": addr,
        "runtime_env": runtime_env,
        "log_to_driver": log_to_driver,
        "logging_level": logging_level,
        **(ray_init_kwargs or {}),
    }

    # Define tenacity-decorated inner function for retrying ray.init()
    # Retries on transient connection errors with exponential backoff + jitter
    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        stop=stop_after_attempt(RAY_INIT_MAX_RETRIES),
        wait=wait_exponential_jitter(initial=1, max=30),
        before_sleep=before_sleep_log(_LOG, logging.WARNING),
        reraise=True,
    )
    def _ray_init_with_retry() -> None:
        ray.init(**init_kwargs)

    try:
        _ray_init_with_retry()
        yield
    except ConnectionError as e:
        raise RuntimeError(
            "Geneva was unable to connect to the Ray head. "
            "The Ray head probably failed to start. Please ensure "
            "the head image matches the node architecture. "
            f"Ray cluster: {cluster.definition if cluster else None}"
        ) from e

    finally:
        with contextlib.suppress(Exception):
            if ray.is_initialized():
                ray.shutdown()


@contextlib.contextmanager
def ray_cluster(
    addr: str | None = None,
    *,
    use_portforwarding: bool = True,
    zip_output_dir: Path | str | None = None,
    uploader: Uploader | None = None,
    delete_local_packaged_zips: bool = False,
    skip_site_packages: bool = False,
    pip: list[str] | None = None,
    ray_cluster: RayCluster | None = None,
    manifest: GenevaManifest | None = None,
    local: bool = False,
    extra_env: dict[str, str] | None = None,
    log_to_driver: bool = False,
    logging_level=logging.INFO,
    ray_init_kwargs: dict | None = None,
    **ray_cluster_kwargs,
) -> Generator[None, None, None]:
    """
    Context manager for setting up a Ray cluster.

    Args:
        addr: The address of the Ray cluster. If None, a new cluster will be
            created.
        use_portforwarding: Whether to use port forwarding for the cluster.
            Defaults to True.
        zip_output_dir: The output directory for the zip files. If None, a
            temporary directory will be used.
        uploader: The uploader to use for uploading the zip files. If None,
            the default uploader will be used.
        delete_local_packaged_zips: Whether to delete the local zip files
            after uploading them. Defaults to False.
        skip_site_packages: Do not include files in site-packages in the manifest.
            Defaults to False.
        pip: A list of pip packages to install in the Ray cluster. If None,
            no pip packages will be installed.
        ray_cluster: An optional RayCluster. If provided, the ray_cluster_kwargs
            will be ignored.
        local: If set, will use a local Ray cluster using ray.init()
        ray_init_kwargs: Arbitrary kwargs to pass to ray.init(). These will be
            merged with kwargs from the RayCluster (if any), with these taking
            precedence. Can be used to pass runtime_env, namespace, etc.
        **ray_cluster_kwargs: Additional arguments to pass to the RayCluster
            constructor.

    If addr is provided and use_portforwarding is True, a ValueError will be
    raised. This is because port forwarding is not supported for existing
    clusters.

    Similarly, if addr is None and ray_cluster_kwargs are provided, a
    ValueError will be raised.
    """
    if addr is not None and ray_cluster_kwargs:
        raise ValueError(
            "Cannot provide both addr and ray_cluster_kwargs. "
            "If addr is provided, use_portforwarding will be ignored."
        )

    # TODO: allow inspecting an existing RayCluster in k8s and allow
    # port forwarding to it
    # https://linear.app/lancedb/issue/GEN-23/define-geneva-ray-hookup-api-and-document
    if addr is not None and use_portforwarding:
        raise ValueError(
            "Cannot use port forwarding with an existing cluster. "
            "If addr is provided, use_portforwarding will be ignored."
        )

    cluster = None
    with contextlib.ExitStack() as stack:
        # Extract ray_init_kwargs from RayCluster if available
        cluster_ray_init_kwargs = {}
        if addr is None:
            if local:
                _LOG.info("starting local ray cluster")
            else:
                _LOG.debug(f"creating ray cluster {ray_cluster_kwargs=}")
                cluster = (
                    ray_cluster
                    if ray_cluster is not None
                    else RayCluster(**ray_cluster_kwargs)
                )
                # Attach manifest to cluster for job tracking
                if manifest is not None:
                    cluster.manifest = manifest
                # Extract ray_init_kwargs from the cluster
                cluster_ray_init_kwargs = cluster.ray_init_kwargs or {}
                ray_ip = stack.enter_context(cluster)
                ray_port = "10001"
                if use_portforwarding:
                    pf = stack.enter_context(PortForward.to_head_node(cluster))
                    ray_ip = "localhost"
                    ray_port = pf.local_port

                    ui_pf = PortForward.to_ui(cluster)
                    if ui_pf:
                        # start a portforward to the remote UI if it is
                        # deployed and running
                        ui_pf_ctx = stack.enter_context(ui_pf)

                        # todo: can we deep link with db url populated?
                        _LOG.info(
                            emojize(
                                f"   :sparkles: Geneva UI is available "
                                f"at http://localhost:{ui_pf_ctx.local_port}"
                            )
                        )

                addr = f"ray://{ray_ip}:{ray_port}"
                _LOG.info(f"connecting to ray cluster at {addr}")

        py_modules = None
        if manifest is not None:
            # use a previously defined manifest
            zips = manifest.zips
            pip = manifest.pip
            # Combine manifest py_modules with default modules (geneva, pa)
            # Default modules are needed even when using a manifest

            # note: including pyarrow breaks using a saved x-platform manifest
            py_modules = [geneva] + (manifest.py_modules or [])
        else:
            # build an ad-hoc manifest
            zips = (
                stack.enter_context(
                    upload_local_env(
                        zip_output_dir=zip_output_dir,
                        uploader=uploader,
                        delete_local_zips=delete_local_packaged_zips,
                        skip_site_packages=skip_site_packages,
                    )
                )
                if not local
                else []
            )

        # Merge ray_init_kwargs: parameter > cluster > default
        merged_ray_init_kwargs = {**cluster_ray_init_kwargs, **(ray_init_kwargs or {})}

        stack.enter_context(
            init_ray(
                addr=addr,
                zips=zips,
                pip=pip,
                local=local,
                py_modules=py_modules,
                extra_env=extra_env,
                log_to_driver=log_to_driver,
                logging_level=logging_level,
                ray_init_kwargs=merged_ray_init_kwargs,
                uploader=uploader,
                cluster=cluster,
            )
        )

        yield

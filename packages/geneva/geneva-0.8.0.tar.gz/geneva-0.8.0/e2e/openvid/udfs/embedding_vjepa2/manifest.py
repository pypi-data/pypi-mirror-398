# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Manifest factory for video embeddings UDF.

This module creates GenevaManifest objects by reading dependencies
from pyproject.toml, providing a single source of truth for UDF dependencies.
"""

from pathlib import Path

from geneva.manifest.mgr import GenevaManifest


def create_manifest(name: str | None = None) -> GenevaManifest:
    """
    Create a GenevaManifest for video embeddings UDF.

    Reads dependencies from pyproject.toml and creates a manifest
    that can be uploaded to Ray workers.

    NOTE: This UDF requires torch, torchvision, torchcodec, and transformers
    with FFmpeg system libraries. These MUST be provided by the cluster's
    conda environment (ray_init_kwargs), not via pip, because:
    - torchcodec needs FFmpeg shared libraries (libavutil.so, etc.)
    - Pip installs into isolated virtualenv without conda's system libs

    The manifest only includes minimal dependencies not in the cluster env.

    Args:
        name: Optional manifest name. If not provided, uses project name from pyproject.toml

    Returns:
        GenevaManifest configured with minimal dependencies
    """
    # Python 3.10 compatibility - use tomli backport if tomllib not available
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]

    udf_dir = Path(__file__).parent
    pyproject_path = udf_dir / "pyproject.toml"

    with pyproject_path.open("rb") as f:
        pyproject = tomllib.load(f)

    manifest_name = name or pyproject["project"]["name"]

    # Return empty pip dependencies - all deps provided by cluster's conda environment
    # Ray doesn't allow mixing 'pip' and 'conda' fields in runtime_env, so when
    # using a cluster with conda (ray_init_kwargs), the manifest must have NO pip deps.
    return GenevaManifest(
        name=manifest_name,
        pip=[],  # Empty - all deps in cluster's conda environment
        py_modules=[],  # Empty - UDF modules are in zips, extracted via GENEVA_ZIPS
        skip_site_packages=True,  # Do not include site-packages
        delete_local_zips=True,
    )

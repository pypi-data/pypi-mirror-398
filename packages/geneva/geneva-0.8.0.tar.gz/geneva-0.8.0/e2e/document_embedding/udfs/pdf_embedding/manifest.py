# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""Manifest factory for the document embedding UDFs."""

from pathlib import Path

from geneva.manifest.mgr import GenevaManifest


def create_manifest(name: str | None = None) -> GenevaManifest:
    try:
        import tomllib
    except ModuleNotFoundError:  # Python 3.10 compatibility
        import tomli as tomllib  # type: ignore[no-redef]

    udf_dir = Path(__file__).parent
    pyproject_path = udf_dir / "pyproject.toml"

    with pyproject_path.open("rb") as f:
        pyproject = tomllib.load(f)

    manifest_name = name or pyproject["project"]["name"]

    return GenevaManifest(
        name=manifest_name,
        pip=pyproject["project"]["dependencies"],
        py_modules=[],  # modules will be included from the uploaded zip
        skip_site_packages=False,
        delete_local_zips=True,
    )

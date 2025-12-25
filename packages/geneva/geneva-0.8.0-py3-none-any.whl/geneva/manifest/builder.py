# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

from typing import TYPE_CHECKING

from geneva.cluster.builder import default_image

if TYPE_CHECKING:
    from .mgr import GenevaManifest


class GenevaManifestBuilder:
    """Fluent builder for GenevaManifest. `name` is required, all optional
    fields will use defaults. Manifests can be saved using db.define_manifest() and
    loaded using db.context()

    Example usage:
        >>> import geneva
        >>> m = GenevaManifestBuilder
        >>>    .create("my-manifest")
        >>>    .pip(["numpy", "pandas"])
        >>>    .py_modules(["mymodule"])
        >>>    .head_image("my-custom-image:latest")
        >>>    .skip_site_packages(True)
        >>>    .build()
        >>> conn = geneva.connect("s3://my-bucket/my-db")
        >>> conn.define_manifest("my-manifest", m)
        >>> with conn.context(cluster="my-cluster", manifest="my-manifest"):
        >>>     conn.open_table("my-table").backfill("my-column")
    """

    def __init__(self) -> None:
        self._name: str | None = None
        self._version: str | None = None
        self._pip: list[str] = []
        self._py_modules: list[str] = []
        self._head_image: str | None = None
        self._worker_image: str | None = None
        self._skip_site_packages: bool = False
        self._delete_local_zips: bool = False
        self._local_zip_output_dir: str | None = None

    def name(self, name: str) -> "GenevaManifestBuilder":
        """Set the manifest name."""
        self._name = name
        return self

    def version(self, version: str) -> "GenevaManifestBuilder":
        """Set the manifest version."""
        self._version = version
        return self

    def pip(self, packages: list[str]) -> "GenevaManifestBuilder":
        """Set the runtime pip packages list.
        See
        https://docs.ray.io/en/latest/ray-core/api/doc/ray.runtime_env.RuntimeEnv.html
        """
        self._pip = packages.copy()
        return self

    def add_pip(self, package: str) -> "GenevaManifestBuilder":
        """Add a single pip package to the runtime environment.
        See
        https://docs.ray.io/en/latest/ray-core/api/doc/ray.runtime_env.RuntimeEnv.html
        """
        self._pip.append(package)
        return self

    def py_modules(self, modules: list[str]) -> "GenevaManifestBuilder":
        """Set the Python modules for the runtime environment.
        See
        https://docs.ray.io/en/latest/ray-core/api/doc/ray.runtime_env.RuntimeEnv.html
        """
        self._py_modules = modules.copy()
        return self

    def add_py_module(self, module: str) -> "GenevaManifestBuilder":
        """Add a single Python module to the runtime environment.
        See
        https://docs.ray.io/en/latest/ray-core/api/doc/ray.runtime_env.RuntimeEnv.html
        """
        self._py_modules.append(module)
        return self

    def head_image(self, head_image: str) -> "GenevaManifestBuilder":
        """Set the container image for Ray head. If set, this will take priority
        over the head image specified in the cluster definition.
        """
        self._head_image = head_image
        return self

    def worker_image(self, worker_image: str) -> "GenevaManifestBuilder":
        """Set the container image for Ray workers. If set, this will take priority
        over the head image specified in the cluster definition.
        """
        self._worker_image = worker_image
        return self

    def default_head_image(self) -> "GenevaManifestBuilder":
        """Set the container image for Ray head to the default for the
        current platform"""
        self._head_image = default_image()
        return self

    def default_worker_image(self) -> "GenevaManifestBuilder":
        """Set the container image for Ray workers to the default for the
        current platform."""
        self._worker_image = default_image()
        return self

    def skip_site_packages(self, skip: bool = True) -> "GenevaManifestBuilder":
        """Set whether to skip site packages during packaging."""
        self._skip_site_packages = skip
        return self

    def delete_local_zips(self, delete: bool = True) -> "GenevaManifestBuilder":
        """Set whether to delete local zip files after upload."""
        self._delete_local_zips = delete
        return self

    def local_zip_output_dir(self, output_dir: str) -> "GenevaManifestBuilder":
        """Set the local directory for zip file output."""
        self._local_zip_output_dir = output_dir
        return self

    def build(self) -> "GenevaManifest":
        """Build the GenevaManifest with the configured settings."""
        if self._name is None:
            raise ValueError("Manifest name is required. Use .name() to set it.")

        from .mgr import GenevaManifest

        return GenevaManifest(
            name=self._name,
            version=self._version,
            pip=self._pip,
            py_modules=self._py_modules,
            head_image=self._head_image,
            worker_image=self._worker_image,
            skip_site_packages=self._skip_site_packages,
            delete_local_zips=self._delete_local_zips,
            local_zip_output_dir=self._local_zip_output_dir,
        )

    @classmethod
    def create(cls, name: str) -> "GenevaManifestBuilder":
        """Create a new builder with the given manifest name."""
        return cls().name(name)

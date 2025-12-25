# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors
import contextlib
import copy
import logging
from collections.abc import Iterable
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import attrs
import lancedb
import pyarrow as pa
from lance_namespace import LanceNamespace
from lance_namespace import connect as namespace_connect
from lancedb import DBConnection, LanceNamespaceDBConnection
from lancedb.common import DATA, Credential
from lancedb.pydantic import LanceModel
from lancedb.util import get_uri_scheme
from overrides import override
from yarl import URL

from geneva.checkpoint import CheckpointStore
from geneva.cluster import GenevaClusterType
from geneva.config import ConfigBase
from geneva.packager import DockerUDFPackager, UDFPackager
from geneva.packager.autodetect import upload_local_env
from geneva.packager.uploader import Uploader

if TYPE_CHECKING:
    import lance
    from flightsql import FlightSQLClient

    from geneva.cluster.mgr import ClusterConfigManager, GenevaCluster
    from geneva.jobs.jobs import JobStateManager
    from geneva.manifest.mgr import GenevaManifest, ManifestConfigManager
    from geneva.query import GenevaQueryBuilder
    from geneva.table import Table

_LOG = logging.getLogger(__name__)


def has_stable_row_ids(fragments: "Iterable[lance.LanceFragment]") -> bool:
    """Check if Lance fragments have stable row IDs enabled.

    Stable row IDs are indicated by presence of row_id_meta on fragment metadata.
    This is a Lance feature (added in v0.21.0) that ensures row identifiers remain
    constant even when table operations like compaction reorganize the physical data.

    Parameters
    ----------
    fragments : Iterable[lance.LanceFragment]
        Lance fragments to check (from dataset.get_fragments())

    Returns
    -------
    bool
        True if any fragment has stable row IDs enabled, False otherwise
    """
    return any(frag.metadata.row_id_meta is not None for frag in fragments)


class Connection(DBConnection):
    """Geneva Connection."""

    def __init__(
        self,
        uri: str,
        *,
        region: str = "us-east-1",
        api_key: Credential | None = None,
        host_override: str | None = None,
        storage_options: dict[str, str] | None = None,
        checkpoint_store: CheckpointStore | None = None,
        packager: UDFPackager | None = None,
        namespace_impl: str | None = None,
        namespace_properties: dict[str, str] | None = None,
        system_namespace: list[str],
        **kwargs,
    ) -> None:
        super().__init__()

        self._uri = uri
        self._region = region
        self._api_key = api_key
        self._host_override = host_override
        self._storage_options = storage_options
        self._ldb: DBConnection | None = None
        self._checkpoint_store = checkpoint_store
        self._packager = packager or DockerUDFPackager()
        self.namespace_impl = namespace_impl
        self.namespace_properties = namespace_properties
        # Default system_namespace to [] if not using namespace
        self.system_namespace = system_namespace if namespace_impl else []

        self._jobs_manager: JobStateManager | None = None
        self._cluster_manager: ClusterConfigManager | None = None
        self._manifest_manager: ManifestConfigManager | None = None
        self._flight_client: FlightSQLClient | None = None
        self._namespace_connection: LanceNamespaceDBConnection | None = None
        self._kwargs = kwargs

    def __repr__(self) -> str:
        return f"<Geneva uri={self.uri}>"

    def __getstate__(self) -> dict:
        return {
            "uri": self._uri,
            "api_key": self._api_key,
            "host_override": self._host_override,
            "storage_options": self._storage_options,
            "region": self._region,
            "system_namespace": self.system_namespace,
        }

    def __setstate__(self, state) -> None:
        self.__init__(state.pop("uri"), **state)

    def __enter__(self) -> "Connection":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
        return None  # Don't suppress exceptions

    def close(self) -> None:
        """Close the connection."""
        if self._flight_client is not None:
            self._flight_client.close()
        if self._ldb is not None and hasattr(self._ldb, "_conn"):
            # go to the async client and eagerly close the connection
            self._ldb._conn.close()  # type: ignore[attr-defined]

    @cached_property
    def namespace_client(self) -> LanceNamespace | None:
        """Returns namespace client if using namespace connection."""
        if self.namespace_impl is not None and self.namespace_properties is not None:
            return namespace_connect(self.namespace_impl, self.namespace_properties)
        return None

    @cached_property
    def _connect(self) -> DBConnection:
        """Returns the underlying lancedb connection. If the connection
        was initialized using a namespace, this will return the
        LanceNamespaceDBConnection.
        """

        # use the namespace connection if set
        if self.namespace_impl is not None:
            if not self._namespace_connection:
                assert self.namespace_properties is not None, (
                    "namespace_properties must be set when namespace_impl is set"
                )
                namespace_client = namespace_connect(
                    self.namespace_impl, self.namespace_properties
                )

                self._namespace_connection = LanceNamespaceDBConnection(
                    namespace_client,
                    storage_options=self._storage_options,
                    **self._kwargs,
                )
            _LOG.info(f"using namespace connection: {self._namespace_connection=}")
            return self._namespace_connection

        if self._ldb is None:
            self._ldb = lancedb.connect(
                self.uri,
                region=self._region,
                api_key=self._api_key,
                host_override=self._host_override,
                storage_options=self._storage_options,
                **self._kwargs,
            )
        return self._ldb

    @cached_property
    def _history(self) -> "JobStateManager":  # noqa: F821
        """Returns a JobStateManager that persists job executions and statuses"""
        from geneva.jobs import JobStateManager

        if self._jobs_manager is None:
            self._jobs_manager = JobStateManager(self, namespace=self.system_namespace)
        return self._jobs_manager

    @cached_property
    def flight_client(self) -> "FlightSQLClient":
        from flightsql import FlightSQLClient

        if self._flight_client is not None:
            return self._flight_client
        url = urlparse(self._host_override)
        hostname = url.hostname
        client = FlightSQLClient(
            host=hostname,
            port=10025,
            token="DATABASE_TOKEN",  # Dummy auth, not plugged in yet
            metadata={"database": self.uri},  # Name of the project-id
            features={"metadata-reflection": "true"},
            insecure=True,  # or False, up to you
        )
        self._flight_client = client
        return client

    @override
    def table_names(
        self, page_token: str | None = None, limit: int | None = None, *args, **kwargs
    ) -> Iterable[str]:
        """List all available tables and views."""
        return self._connect.table_names(
            *args, page_token=page_token, limit=limit or 10, **kwargs
        )

    @override
    def open_table(
        self,
        name: str,
        storage_options: dict[str, str] | None = None,
        index_cache_size: int | None = None,
        version: int | None = None,
        namespace: list[str] | None = None,
        *args,
        **kwargs,
    ) -> "Table":
        """Open a Lance Table.

        Parameters
        ----------
        name: str
            Name of the table.
        storage_options: dict[str, str], optional
            Additional options for the storage backend.
            Options already set on the connection will be inherited by the table,
            but can be overridden here. See available options at
            [https://lancedb.github.io/lancedb/guides/storage/](https://lancedb.github.io/lancedb/guides/storage/)
        namespace: list[str], optional
            Namespace path for the table (e.g., ["workspace"] for workspace.t)

        """
        from .table import Table

        storage_options = storage_options or self._storage_options
        namespace = namespace if namespace is not None else []

        return Table(
            self,
            name,
            namespace=namespace,
            index_cache_size=index_cache_size,
            storage_options=storage_options,
            version=version,
        )

    def _validate_existing_table_has_stable_row_ids(self, name: str) -> None:
        """Validate that an existing table has stable row IDs enabled.

        Called when exist_ok=True and stable row IDs are requested, to ensure
        the existing table matches the requested configuration.

        Raises:
            ValueError: If table exists with data but doesn't have stable row IDs
        """
        # Use lancedb table API (not lance.dataset directly) to support namespaces
        if name not in self._connect.table_names():
            return

        try:
            table = self._connect.open_table(name)
            fragments = list(table.to_lance().get_fragments())  # type: ignore[union-attr]
            if fragments:
                if not has_stable_row_ids(fragments):
                    raise ValueError(
                        f"Cannot open table '{name}' with exist_ok=True: "
                        f"table exists but does not have stable row IDs enabled.\n\n"
                        f"You requested stable row IDs, but the existing table "
                        f"was created without them.\n\n"
                        f"Options:\n"
                        f"  1. Drop and recreate the table with stable row IDs\n"
                        f"  2. Remove storage_options if stable row IDs are "
                        f"not required\n"
                        f"  3. Use mode='overwrite' to replace the table"
                    )
            else:
                _LOG.warning(
                    f"Table '{name}' exists but is empty - cannot verify "
                    f"if stable row IDs are enabled."
                )
        except ValueError:
            raise
        except Exception as e:
            _LOG.debug(
                f"Could not check stable row ID status for existing table '{name}': {e}"
            )

    @override
    def create_table(  # type: ignore
        self,
        name: str,
        data: DATA | None = None,
        schema: pa.Schema | LanceModel | None = None,
        mode: str = "create",
        exist_ok: bool = False,
        on_bad_vectors: str = "error",
        fill_value: float = 0.0,
        storage_options: dict[str, str] | None = None,
        *args,
        **kwargs,
    ) -> "Table":  # type: ignore
        """Create a Table in the lake

        Parameters
        ----------
        name: str
            The name of the table
        data: The data to initialize the table, *optional*
            User must provide at least one of `data` or `schema`.
            Acceptable types are:

            - list-of-dict
            - pandas.DataFrame
            - pyarrow.Table or pyarrow.RecordBatch
        schema: The schema of the table, *optional*
            Acceptable types are:

            - pyarrow.Schema
            - [LanceModel][lancedb.pydantic.LanceModel]
        mode: str; default "create"
            The mode to use when creating the table.
            Can be either "create" or "overwrite".
            By default, if the table already exists, an exception is raised.
            If you want to overwrite the table, use mode="overwrite".
        exist_ok: bool, default False
            If a table by the same name already exists, then raise an exception
            if exist_ok=False. If exist_ok=True, then open the existing table;
            it will not add the provided data but will validate against any
            schema that's specified.
        on_bad_vectors: str, default "error"
            What to do if any of the vectors are not the same size or contain NaNs.
            One of "error", "drop", "fill".
        """
        from .table import Table

        # Handle new_table_enable_stable_row_ids validation and normalization
        # Accept both string "true" and boolean True for user convenience
        if storage_options:
            enable_stable = storage_options.get("new_table_enable_stable_row_ids")
            if enable_stable in ("true", True, 1):
                # Normalize to string "true" for lancedb
                storage_options = dict(storage_options)
                storage_options["new_table_enable_stable_row_ids"] = "true"

                # Validate exist_ok: ensure existing table has stable row IDs
                if exist_ok:
                    self._validate_existing_table_has_stable_row_ids(name)

        # Create table through lancedb
        self._connect.create_table(
            name,
            data,
            schema,
            mode,
            *args,
            exist_ok=exist_ok,
            on_bad_vectors=on_bad_vectors,
            fill_value=fill_value,
            storage_options=storage_options,
            **kwargs,
        )
        # Extract namespace from kwargs to pass to Table
        namespace = kwargs.get("namespace")
        return Table(self, name, namespace=namespace, storage_options=storage_options)

    def create_view(
        self,
        name: str,
        query: str,
        materialized: bool = False,
    ) -> "Table":
        """Create a View from a Query.

        Parameters
        ----------
        name: str
            Name of the view.
        query: str
            SQL query to create the view.
        materialized: bool, optional
            If True, the view is materialized.
        """
        if materialized:
            # idea, rename the provided name, and use it as the basis for the
            # materialized view.
            # - how do we add the udfs to the final materialized view table?
            NotImplementedError(
                "creating materialized view via sql query is not supported yet."
            )

        # TODO add test coverage here
        self.sql(f"CREATE VIEW {name} AS ({query})")
        return self.open_table(name)

    def create_materialized_view(
        self,
        name: str,
        query: "GenevaQueryBuilder",
        with_no_data: bool = True,
    ) -> "Table":
        """
        Create a materialized view

        Parameters
        ----------
        name: str
            Name of the materialized view.
        query: GenevaQueryBuilder
            Query to create the view.
        with_no_data: bool, optional
            If True, the view is materialized, if false it is ready for refresh.
        """
        from geneva.query import GenevaQueryBuilder

        if not isinstance(query, GenevaQueryBuilder):
            raise ValueError(
                "Materialized views only support plain queries (where, select)"
            )

        tbl = query.create_materialized_view(self, name)
        if not with_no_data and hasattr(tbl, "refresh_view"):
            tbl.refresh_view(name)  # type: ignore[attr-defined]

        return tbl

    def drop_view(self, name: str) -> pa.Table:
        """Drop a view."""
        return self.sql(f"DROP VIEW {name}")

    @override
    def drop_table(self, name: str, *args, **kwargs) -> None:
        """Drop a table."""
        self._connect.drop_table(name, *args, **kwargs)

    def define_cluster(self, name: str, cluster: "GenevaCluster") -> None:  # noqa: F821
        """
        Define a persistent Geneva cluster. This will upsert the cluster definition by
        name. The cluster can then be provisioned using `context(cluster=name)`.

        Parameters
        ----------
        name: str
            Name of the cluster. This will be used as the key when upserting and
            provisioning the cluster. The cluster name must comply with RFC 12123.
        cluster: GenevaCluster
            The cluster definition to store.
        """
        from geneva.cluster.mgr import ClusterConfigManager

        if self._cluster_manager is None:
            self._cluster_manager = ClusterConfigManager(
                self, namespace=self.system_namespace
            )

        cluster.name = name
        cluster.validate()
        self._cluster_manager.upsert(cluster)

    def list_clusters(self) -> list["GenevaCluster"]:  # noqa: F821
        """
        List the cluster definitions. These can be defined using `define_cluster()`.

        Returns
        -------
        Iterable of GenevaCluster
            List of Geneva cluster definitions
        """
        from geneva.cluster.mgr import ClusterConfigManager

        if self._cluster_manager is None:
            self._cluster_manager = ClusterConfigManager(
                self, namespace=self.system_namespace
            )
        return self._cluster_manager.list()

    def delete_cluster(self, name: str) -> None:  # noqa: F821
        """
        Delete a Geneva cluster definition.

        Parameters
        ----------
        name: str
            Name of the cluster to delete.
        """
        from geneva.cluster.mgr import ClusterConfigManager

        if self._cluster_manager is None:
            self._cluster_manager = ClusterConfigManager(
                self, namespace=self.system_namespace
            )

        self._cluster_manager.delete(name)

    def define_manifest(
        self,
        name: str,
        manifest: "GenevaManifest",  # noqa: F821
        uploader: Uploader | None = None,
    ) -> None:
        """
        Define a persistent Geneva Manifest that represents the files and dependencies
        used in the execution environment. This will upsert the manifest definition by
        name and upload the required artifacts. The manifest can then be used with
        `context(manifest=name)`.

        Parameters
        ----------
        name: str
            Name of the manifest. This will be used as the key when upserting and
            loading the manifest.
        manifest: GenevaManifest
            The manifest definition to use.
        uploader: Uploader, optional
            An optional, custom Uploader to use. If not provided, the uploader will be
            auto-detected based on the
            environment configuration.
        """
        from geneva.manifest.mgr import ManifestConfigManager

        if self._manifest_manager is None:
            self._manifest_manager = ManifestConfigManager(
                self, namespace=self.system_namespace
            )

        # Ensure the manifest table exists before creating Uploader
        # This guarantees the table location can be queried
        _ = self._manifest_manager.get_table()

        # If no uploader is provided, create one with manifest table context
        if uploader is None:
            from geneva.manifest.mgr import MANIFEST_TABLE_NAME

            if self.namespace_impl and self.namespace_properties:
                # Create uploader for namespace table
                # Build table_id for manifest table
                table_id = self.system_namespace + [MANIFEST_TABLE_NAME]
                uploader = Uploader(
                    namespace_impl=self.namespace_impl,
                    namespace_properties=self.namespace_properties,
                    table_id=table_id,
                )
            else:
                # For local databases, use database-level manifest table
                # Build table_id with just the table name
                table_id = [MANIFEST_TABLE_NAME]
                uploader = Uploader(
                    db_uri=self.uri,
                    table_id=table_id,
                )

        with upload_local_env(
            # todo: implement excludes
            uploader=uploader,
            zip_output_dir=manifest.local_zip_output_dir,
            delete_local_zips=manifest.delete_local_zips,
            skip_site_packages=manifest.skip_site_packages,
        ) as zips:
            m = copy.deepcopy(manifest)
            m.name = name
            m.zips = zips
            m.checksum = manifest.compute_checksum()
            self._manifest_manager.upsert(m)

    def list_manifests(self) -> list["GenevaManifest"]:  # noqa: F821
        """
        List the manifest definitions. These can be defined using `define_manifest()`.

        Returns
        -------
        Iterable of GenevaManifest
            List of Geneva manifest definitions
        """
        from geneva.manifest.mgr import ManifestConfigManager

        if self._manifest_manager is None:
            self._manifest_manager = ManifestConfigManager(
                self, namespace=self.system_namespace
            )
        return self._manifest_manager.list()

    def delete_manifest(self, name: str) -> None:  # noqa: F821
        """
        Delete a Geneva manifest definition.

        Parameters
        ----------
        name: str
            Name of the manifest to delete.
        """
        from geneva.manifest.mgr import ManifestConfigManager

        if self._manifest_manager is None:
            self._manifest_manager = ManifestConfigManager(
                self, namespace=self.system_namespace
            )

        self._manifest_manager.delete(name)

    def context(
        self,
        cluster: str | None = None,
        manifest: str | None = None,
        cluster_type=GenevaClusterType.KUBE_RAY,
        on_exit=None,
        log_to_driver: bool = True,
        logging_level=logging.INFO,
    ) -> contextlib.AbstractContextManager[None]:
        """Context manager for a Geneva Execution Environment.
            This will provision a cluster based on the cluster
            definition and the manifest provided.
            By default, the context manager will delete the cluster on exit.
            This can be configured with the on_exit parameter.
        Parameters
        ----------
        cluster: str
            Name of the persisted cluster definition to use. This will
            raise an exception if the cluster definition was not
            defined via `define_cluster()`. This parameter is ignored
            if `cluster_type` is `GenevaClusterType.LOCAL_RAY`.
        manifest: str
            Name of the persisted manifest to use. This will
            raise an exception if the manifest definition was not
            defined via `define_manifest()`.
        cluster_type: GenevaClusterType, optional, default GenevaClusterType.KUBE_RAY
            Type of the cluster to use. By default, KUBE_RAY will be used.
            To start a local Ray cluster, use `GenevaClusterType.LOCAL_RAY`.
        on_exit: ExitMode, optional, default ExitMode.DELETE
            Exit mode for the cluster. By default, the cluster will be deleted when the
            context manager exits.
            To retain the cluster on errors, use `ExitMode.DELETE_ON_SUCCESS`.
            To always retain the cluster, use `ExitMode.RETAIN`.
        log_to_driver: bool, optional, default True
            Whether to send Ray worker logs to the driver. Defaults to True for
            better visibility in tests and debugging.
        logging_level: int, optional, default logging.INFO
            The logging level for Ray workers. Use logging.DEBUG for detailed logs.
        """
        from geneva.cluster.mgr import ClusterConfigManager
        from geneva.manifest.mgr import ManifestConfigManager
        from geneva.runners.ray._mgr import ray_cluster
        from geneva.runners.ray.raycluster import ExitMode

        if self._cluster_manager is None:
            self._cluster_manager = ClusterConfigManager(
                self, namespace=self.system_namespace
            )
        if self._manifest_manager is None:
            self._manifest_manager = ManifestConfigManager(
                self, namespace=self.system_namespace
            )

        if GenevaClusterType(cluster_type) == GenevaClusterType.LOCAL_RAY:
            if manifest is not None:
                raise ValueError("custom manifest not supported with LOCAL_RAY")
            return ray_cluster(
                local=True, log_to_driver=log_to_driver, logging_level=logging_level
            )

        if cluster is None:
            raise ValueError("cluster name is required for non-LOCAL_RAY cluster types")
        cluster_def = self._cluster_manager.load(cluster)
        if cluster_def is None:
            raise Exception(
                f"cluster definition '{cluster}' not found. "
                f"Create a new cluster with define_cluster()"
            )

        supported_types = {GenevaClusterType.KUBE_RAY}
        if GenevaClusterType(cluster_def.cluster_type) not in supported_types:
            raise ValueError(
                f"cluster_type must be one of {supported_types} to use context()"
            )
        use_portforwarding = cluster_def.as_dict()["kuberay"].get(
            "use_portforwarding", True
        )
        rc = cluster_def.to_ray_cluster()
        rc.on_exit = on_exit or ExitMode.DELETE

        manifest_def = None
        if manifest is not None:
            manifest_def = self._manifest_manager.load(manifest)
            if manifest_def is None:
                raise Exception(
                    f"manifest definition '{manifest}' not found. "
                    f"Create a new manifest with define_manifest()"
                )

            # image explicitly provided in manifest takes precedence
            if img := manifest_def.head_image:
                _LOG.debug(f"overriding cluster head image from manifest: {img}")
                rc.head_group.image = img
            if img := manifest_def.worker_image:
                _LOG.debug(f"overriding cluster worker image from manifest: {img}")
                for wg in rc.worker_groups:
                    wg.image = img

        return ray_cluster(
            use_portforwarding=use_portforwarding,
            ray_cluster=rc,
            manifest=manifest_def,
            extra_env={
                "RAY_BACKEND_LOG_LEVEL": "info",
                "RAY_LOG_TO_DRIVER": "1",
                "RAY_RUNTIME_ENV_LOG_TO_DRIVER_ENABLED": "true",
            },
            log_to_driver=log_to_driver,
            logging_level=logging_level,
        )

    def sql(self, query: str) -> pa.Table:
        """Execute a raw SQL query.

        It uses the Flight SQL engine to execute the query.

        Parameters
        ----------
        query: str
            SQL query to execute

        Returns
        -------
        pyarrow.Table
            Result of the query in a `pyarrow.Table`

        TODO
        ----
        - Support pagination
        - Support query parameters
        """
        info = self.flight_client.execute(query)
        return self.flight_client.do_get(info.endpoints[0].ticket).read_all()


@attrs.define
class _GenavaConnectionConfig(ConfigBase):
    region: str = attrs.field(default="us-east-1")
    api_key: str | None = attrs.field(default=None)
    host_override: str | None = attrs.field(default=None)
    checkpoint: str | None = attrs.field(default=None)
    system_namespace: list[str] = attrs.field(factory=lambda: ["default"])

    @classmethod
    @override
    def name(cls) -> str:
        return "connection"


def _ensure_system_namespace_exists(conn: Connection) -> None:
    """Ensure system_namespace exists, creating it if necessary.

    This is called once at connection time for namespace connections to ensure
    the system namespace is ready before any system tables are created.
    For nested namespaces, creates parent namespaces first.

    Args:
        conn: The Geneva connection

    Raises:
        RuntimeError: If the namespace doesn't exist and cannot be created
    """
    from lance_namespace import CreateNamespaceRequest, DescribeNamespaceRequest

    if conn.namespace_client is None:
        return

    try:
        # Check if namespace exists
        conn.namespace_client.describe_namespace(
            DescribeNamespaceRequest(id=conn.system_namespace)
        )
        _LOG.info(f"System namespace {conn.system_namespace} exists")
    except Exception as e:
        # Namespace doesn't exist, try to create it
        if "not found" in str(e).lower():
            try:
                # For nested namespaces, create parents first
                for i in range(1, len(conn.system_namespace) + 1):
                    parent_ns = conn.system_namespace[:i]
                    try:
                        conn.namespace_client.describe_namespace(
                            DescribeNamespaceRequest(id=parent_ns)
                        )
                        _LOG.debug(f"Namespace {parent_ns} already exists")
                    except Exception:
                        _LOG.info(f"Creating namespace {parent_ns}...")
                        conn.namespace_client.create_namespace(
                            CreateNamespaceRequest(id=parent_ns)
                        )
                        _LOG.info(f"Created namespace {parent_ns}")

                _LOG.info(f"System namespace {conn.system_namespace} is ready")
            except Exception as create_error:
                raise RuntimeError(
                    f"Cannot create system namespace {conn.system_namespace}: "
                    f"{create_error}"
                ) from create_error
        else:
            # Some other error, re-raise
            raise


def connect(
    uri: str | Path | None = None,
    *,
    region: str | None = None,
    api_key: Credential | str | None = None,
    host_override: str | None = None,
    storage_options: dict[str, str] | None = None,
    checkpoint: str | CheckpointStore | None = None,
    system_namespace: list[str] | None = None,
    namespace_impl: str | None = None,
    namespace_properties: dict[str, str] | None = None,
    **kwargs,
) -> Connection:
    """Create a Geneva Connection to an existing database.

    Examples
    --------
        >>> import geneva
        >>> # Connect to a database in object storage
        >>> conn = geneva.connect("s3://my-storage-bucket/my-database")
        >>> # Connect using directory namespace
        >>> conn = geneva.connect(
        ...     namespace_impl="dir", namespace_properties={"root": "/path"}
        ... )
        >>> # Connect using REST namespace
        >>> conn = geneva.connect(
        ...     namespace_impl="rest", namespace_properties={"uri": f"http://127.0.0.1:1234"}
        ... )
        >>> tbl = conn.open_table("youtube_dataset")

    Parameters
    ----------
    uri: geneva URI, or Path, optional
        LanceDB Database URI, or a S3/GCS path.
        If not provided and namespace_impl is set, defaults to "namespace://".
    region: str | None
        LanceDB cloud region. Set to `None` on LanceDB Enterprise
    api_key: str | None
        API key to connect to the DB instance.
    host_override: str | None
        Set to the host of the enterprise stack
    system_namespace: list[str] | None
        Namespace for system tables (manifests, clusters, jobs, errors).
        Defaults to config value if not provided.
    namespace_impl: str | None
        The namespace implementation to use (e.g., "dir", "rest").
        If provided, connects using namespace instead of local database.
    namespace_properties: dict[str, str] | None
        Configuration properties for the namespace implementation.
    Returns
    -------
    Connection - A LanceDB connection
    """

    api_key, checkpoint_store, host_override, region, uri, system_namespace = (
        _pre_connect(
            api_key,
            checkpoint,
            host_override,
            region,
            uri,
            namespace_impl,
            namespace_properties,
            system_namespace,
        )
    )

    conn = Connection(
        str(uri),
        region=region,
        api_key=api_key,
        host_override=host_override,
        storage_options=storage_options,
        checkpoint_store=checkpoint_store,
        namespace_impl=namespace_impl,
        namespace_properties=namespace_properties,
        system_namespace=system_namespace,
        **kwargs,
    )

    # Set up default uploader if not already configured
    # This is needed for cluster operations (like upload_local_env) that don't have
    # table context
    from geneva.config import override_config_kv

    try:
        Uploader.get()
    except (TypeError, ValueError):
        # Uploader not configured - set a default upload_dir
        default_upload_dir = f"{str(uri)}/zips"
        override_config_kv({"uploader.upload_dir": default_upload_dir})

    # Validate and create system_namespace if using namespace connection
    if namespace_impl is not None:
        _ensure_system_namespace_exists(conn)

    return conn


def _pre_connect(
    api_key: Credential | str | None,
    checkpoint: str | CheckpointStore | None,
    host_override: str | None,
    region: str | None,
    uri: str | Path | None,
    namespace_impl: str | None,
    namespace_properties: dict[str, str] | None,
    system_namespace: list[str] | None,
) -> tuple[
    Credential | None,
    CheckpointStore,
    str | None,
    str,
    str | Path,
    list[str],
]:
    # load values from config if not provided via arguments
    config = _GenavaConnectionConfig.get()
    region = region or config.region or "us-east-1"
    api_key = api_key or config.api_key
    api_key = Credential(api_key) if isinstance(api_key, str) else api_key
    host_override = host_override or config.host_override
    system_namespace = system_namespace or config.system_namespace
    # handle local relative paths
    is_local = isinstance(uri, Path) or (
        uri is not None and get_uri_scheme(uri) == "file"
    )
    if is_local and uri:
        if isinstance(uri, str):
            uri = Path(uri)
        uri = uri.expanduser().absolute()
        uri.mkdir(parents=True, exist_ok=True)

    # Default URI for namespace connections
    if uri is None:
        uri = "namespace://"

    if checkpoint is None:
        checkpoint = str(URL(str(uri)) / "ckp")
    if isinstance(checkpoint, str):
        checkpoint_store = CheckpointStore.from_uri(checkpoint)
    else:
        checkpoint_store = checkpoint

    _LOG.debug(f"using checkpoint store: {type(checkpoint_store)}")

    return api_key, checkpoint_store, host_override, region, uri, system_namespace

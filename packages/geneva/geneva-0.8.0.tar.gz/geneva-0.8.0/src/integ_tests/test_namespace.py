# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import logging
import uuid

import pyarrow as pa
import pytest

import geneva
from geneva.cluster import K8sConfigMethod
from geneva.cluster.builder import GenevaClusterBuilder
from geneva.manifest import GenevaManifestBuilder
from geneva.table import Table
from geneva.utils import dt_now_utc
from integ_tests.utils import ray_get_with_retry

_LOG = logging.getLogger(__name__)


@geneva.udf(data_type=pa.int64(), num_cpus=1, version=uuid.uuid4().hex)
def plus_one(a: int) -> int:
    return a + 1


SIZE = 128


@pytest.mark.timeout(900)
def test_backfill_with_dir_namespace_child(
    slug: str | None,
    geneva_test_bucket: str,
    manifest: str | None,
    k8s_namespace: str,
    head_node_selector: dict,
    worker_node_selector: dict,
    region: str,
    k8s_config_method: K8sConfigMethod,
    geneva_k8s_service_account: str,
) -> None:
    """Test backfill with directory namespace and child namespace on S3.

    This test also verifies that all system tables (manifests, clusters, jobs, errors)
    are correctly created in the configured system_namespace.

    This test takes ~10 minutes because it creates its own Ray cluster
    (not a shared session cluster):
    - Cluster startup: ~3-4 min (K8s pod scheduling, image pull, Ray init)
    - Namespace/table setup: ~1 min
    - Backfill execution: ~2-3 min
    - Cluster teardown: ~1-2 min
    """
    from lance_namespace import CreateNamespaceRequest

    from geneva.runners.ray.pipeline import get_imported

    # Setup directory namespace with custom system_namespace
    system_ns_name = f"system-{uuid.uuid4().hex[:8]}"
    db = geneva.connect(
        namespace_impl="dir",
        namespace_properties={"root": geneva_test_bucket},
        system_namespace=[system_ns_name],
    )

    cluster_name = "namespace-backfill"
    cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"
    manifest_name = f"test-manifest-{slug}"

    # Create unique names to avoid conflicts
    namespace_name = f"workspace-{uuid.uuid4().hex[:8]}"
    table_name = f"test-table-{uuid.uuid4().hex[:8]}"
    namespace = [namespace_name]

    try:
        if manifest:
            # saved manifest provided via --manifest arg
            manifest_name = manifest
        else:
            db.define_manifest(
                manifest_name,
                GenevaManifestBuilder.create(manifest_name)
                # pylance must be explicitly installed for the worker
                # to download the manifest when using namespaces
                .add_pip("pylance==1.0.0b9")
                .build(),
            )

        db.define_cluster(
            cluster_name,
            (
                GenevaClusterBuilder()
                .name(cluster_name)
                .namespace(k8s_namespace)
                .config_method(k8s_config_method)
                .aws_config(region=region, role_name="geneva-client-role")
                .head_group(
                    service_account=geneva_k8s_service_account,
                    node_selector=head_node_selector,
                )
                .add_cpu_worker_group(
                    service_account=geneva_k8s_service_account,
                    node_selector=worker_node_selector,
                )
                .build()
            ),
        )

        # Verify system_namespace is set correctly
        assert db.system_namespace == [system_ns_name], (
            f"Expected system_namespace={[system_ns_name]}, got {db.system_namespace}"
        )
        _LOG.info(f"Verified system_namespace: {db.system_namespace}")

        # Create child namespace (system namespace already created by connect())
        ns = db.namespace_client
        assert ns is not None, "This test requires a namespace connection"
        ns.create_namespace(CreateNamespaceRequest(id=namespace))
        _LOG.info(f"Created namespace: {namespace}")

        # Trigger system table creation by accessing managers
        # This will create tables in the system namespace
        _ = db._history  # Creates geneva_jobs table
        manifests = db.list_manifests()  # Creates geneva_manifests table
        clusters = db.list_clusters()  # Creates geneva_cluster_definitions table
        _LOG.info(
            f"Accessed system tables: {len(manifests)} manifests, "
            f"{len(clusters)} clusters"
        )

        # Verify system tables exist in the correct namespace
        system_tables = db.table_names(namespace=[system_ns_name])
        _LOG.info(f"System tables in namespace {[system_ns_name]}: {system_tables}")

        # Check that expected system tables are present
        expected_tables = {
            "geneva_manifests",
            "geneva_cluster_definitions",
            "geneva_jobs",
        }
        for table in expected_tables:
            assert table in system_tables, (
                f"Expected system table '{table}' not found in namespace "
                f"{[system_ns_name]}"
            )
        _LOG.info(f"Verified all system tables exist in {[system_ns_name]}")

        # Create table in the child namespace (for actual data)
        schema = pa.schema(
            [
                pa.field("a", pa.int64()),
            ]
        )
        db.create_table(table_name, schema=schema, namespace=namespace)
        tbl = Table(db, table_name, namespace=namespace)
        _LOG.info(f"Created table: {table_name} in namespace {namespace}")

        # Add data
        data = pa.table({"a": pa.array(range(SIZE))})
        tbl.add(data)
        _LOG.info(f"Added {SIZE} rows to table")

        # Add UDF column and backfill with remote cluster
        with db.context(
            cluster=cluster_name,
            manifest=manifest_name,
            log_to_driver=True,
        ):
            _LOG.info("Manifest packages:")
            pkgs = ray_get_with_retry(get_imported.remote())
            for pkg, ver in sorted(pkgs.items()):
                _LOG.info(f"{pkg}=={ver}")

            tbl.add_columns(
                {"b": plus_one},
                batch_size=32,
                concurrency=2,
            )
            tbl.backfill("b")

        # Verify results
        tbl.checkout_latest()
        result = tbl.to_arrow()
        assert result["a"].to_pylist() == list(range(SIZE))
        assert result["b"].to_pylist() == list(range(1, SIZE + 1))
        _LOG.info("Backfill verification passed")

    finally:
        # Cleanup
        try:
            db.drop_table(table_name, namespace=namespace)
            _LOG.info(f"Dropped table: {table_name}")
        except Exception as e:
            _LOG.warning(f"Failed to drop table: {e}")

        db.close()

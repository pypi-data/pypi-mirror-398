# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
E2E fixtures for the document embedding suite.

This file is self-contained (does not import src/conftest.py) and mirrors the
structure used in e2e/openvid and e2e/oxford-pets.
"""

import contextlib
import logging
import os
import random
import subprocess
import sys
import uuid
import warnings
from pathlib import Path

import kubernetes
import pytest
from dataset import SOURCE_METADATA_PATH, load_document_metadata

from geneva.cluster import K8sConfigMethod
from geneva.cluster.builder import GenevaClusterBuilder, WorkerGroupBuilder
from geneva.cluster.mgr import WorkerGroupConfig

SYNC_CMD = ["uv", "sync", "--index-strategy", "unsafe-best-match"]

# Make UDF modules importable when tests unpickle them
_udfs_dir = Path(__file__).parent / "udfs"
for udf_package in ["pdf_embedding"]:
    udf_path = _udfs_dir / udf_package
    if udf_path.exists() and str(udf_path) not in sys.path:
        sys.path.insert(0, str(udf_path))

# Load kubeconfig when available (needed for cluster provisioning)
with contextlib.suppress(kubernetes.config.config_exception.ConfigException):
    kubernetes.config.load_kube_config()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
warnings.filterwarnings(
    "ignore", "Using port forwarding for Ray cluster is not recommended for production"
)

_LOG = logging.getLogger(__name__)
_MANIFESTS_UPLOADED = False
DEFAULT_MANIFEST_NAME = "document-embedding-udfs-v1"


# ============================================================================
# Manifest upload helpers
# ============================================================================


def _upload_all_manifests(bucket_path: str) -> None:
    """
    Upload all UDF manifests and add columns to the table.

    Each upload runs inside the UDF's own environment via `uv run`, ensuring
    heavy ML dependencies stay isolated from the test driver environment.
    """
    import textwrap

    _LOG.info("Uploading UDF manifests to %s", bucket_path)

    udfs_dir = Path(__file__).parent / "udfs"
    udf_packages = ["pdf_embedding"]

    for udf_name in udf_packages:
        udf_dir = udfs_dir / udf_name
        upload_script = udf_dir / "upload_manifest.py"

        if not upload_script.exists():
            _LOG.warning("Upload script missing for %s; skipping", udf_name)
            continue

        _LOG.info("Syncing dependencies for '%s'", udf_name)
        sync_result = subprocess.run(
            SYNC_CMD,
            cwd=str(udf_dir),
            capture_output=True,
            text=True,
        )
        if sync_result.returncode != 0:
            _LOG.error("Dependency sync failed for %s", udf_name)
            if sync_result.stderr:
                _LOG.error(textwrap.indent(sync_result.stderr, "    "))
            raise RuntimeError(f"uv sync failed for {udf_name}")

        _LOG.info("Uploading manifest for '%s'", udf_name)
        result = subprocess.run(
            ["uv", "run", "python", "upload_manifest.py", "--bucket", bucket_path],
            cwd=str(udf_dir),
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )

        # Always surface output for easier debugging
        if result.stdout:
            _LOG.info(textwrap.indent(result.stdout, f"[{udf_name}] "))
        if result.stderr:
            _LOG.warning(textwrap.indent(result.stderr, f"[{udf_name}] "))

        if result.returncode != 0:
            raise RuntimeError(f"Manifest upload failed for {udf_name}")

        _LOG.info("✓ Uploaded manifest for '%s'", udf_name)

    _LOG.info("✓ All manifests uploaded")


# ============================================================================
# Pytest options
# ============================================================================


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--csp",
        action="store",
        default="gcp",
        choices=["gcp", "aws"],
        help="Target cloud service provider",
    )
    parser.addoption(
        "--test-slug",
        action="store",
        default=None,
        help="Slug to namespace buckets/resources",
    )
    parser.addoption(
        "--bucket-path",
        action="store",
        default=None,
        help="Override bucket path (gs://... or s3://...)",
    )
    parser.addoption(
        "--num-docs",
        action="store",
        type=int,
        default=20,
        help="Number of documents to process",
    )
    parser.addoption(
        "--batch-size",
        action="store",
        type=int,
        default=4,
        help="Backfill batch size",
    )


# ============================================================================
# Common fixtures
# ============================================================================


@pytest.fixture(scope="session")
def csp(request) -> str:
    return request.config.getoption("--csp")


@pytest.fixture(scope="session")
def slug(request) -> str:
    return request.config.getoption("--test-slug") or str(random.randint(0, 10000))


@pytest.fixture(scope="session")
def geneva_test_bucket(request, slug, csp) -> str:
    """
    Resolve the test bucket and configure Geneva upload/checkpoint paths.
    """
    from geneva.config import override_config_kv

    bucket_path = request.config.getoption("--bucket-path")
    if not bucket_path:
        if csp == "gcp":
            bucket_path = f"gs://geneva-integ-test/{slug}/data"
        elif csp == "aws":
            bucket_path = f"s3://geneva-integ-test-devland-us-east-1/{slug}/data"
        else:
            raise ValueError(f"Unsupported CSP: {csp}")
        _LOG.info("Using default bucket path: %s", bucket_path)
    else:
        _LOG.info("Using provided bucket path: %s", bucket_path)

    override_config_kv(
        {
            "job.checkpoint.mode": "object_store",
            "uploader.upload_dir": f"{bucket_path}/zips",
            "job.checkpoint.object_store.path": f"{bucket_path}/checkpoints",
        }
    )

    return bucket_path


@pytest.fixture(scope="session")
def geneva_k8s_service_account(csp: str) -> str:
    return "geneva-service-account" if csp == "aws" else "geneva-integ-test"


@pytest.fixture(scope="session")
def region(csp: str) -> str:
    return "us-east-1" if csp == "aws" else "us-central1"


@pytest.fixture(scope="session")
def k8s_config_method(csp: str) -> K8sConfigMethod:
    return K8sConfigMethod.EKS_AUTH if csp == "aws" else K8sConfigMethod.LOCAL


@pytest.fixture(scope="session")
def k8s_namespace(csp: str) -> str:
    return "geneva"


@pytest.fixture(scope="session")
def k8s_cluster_name(csp: str) -> str:
    return "lancedb"


@pytest.fixture(scope="session")
def head_node_selector(csp: str) -> dict:
    return (
        {"geneva.lancedb.com/ray-head": "true"}
        if csp == "aws"
        else {"_PLACEHOLDER": "true"}
    )


@pytest.fixture(scope="session")
def worker_node_selector(csp: str) -> dict:
    return (
        {"geneva.lancedb.com/ray-worker-cpu": "true"}
        if csp == "aws"
        else {"_PLACEHOLDER": "true"}
    )


# ============================================================================
# E2E-specific fixtures
# ============================================================================


@pytest.fixture(scope="session")
def num_docs(request) -> int:
    return request.config.getoption("--num-docs")


@pytest.fixture(scope="session")
def batch_size(request) -> int:
    return request.config.getoption("--batch-size")


@pytest.fixture(scope="session")
def manifest_name() -> str:
    return DEFAULT_MANIFEST_NAME


@pytest.fixture(scope="session")
def document_table(geneva_test_bucket: str, num_docs: int) -> tuple:
    """
    Create a session-scoped table populated with document metadata.

    Manifests are uploaded once per session and columns are added before tests
    run. Returns (connection, table, table_name).
    """
    import geneva

    metadata = load_document_metadata(num_docs, SOURCE_METADATA_PATH)
    if len(metadata) == 0:
        pytest.skip("No document metadata available to build test table")

    conn = geneva.connect(geneva_test_bucket)
    table_name = f"document_embedding_{uuid.uuid4().hex}"

    # Force schema refresh if schema changed between runs
    with contextlib.suppress(Exception):
        conn._db.drop_table("geneva_clusters")

    tbl = conn.create_table(table_name, metadata, mode="overwrite")
    _LOG.info(
        "Created test table '%s' with %s rows and columns %s",
        table_name,
        len(tbl),
        tbl.schema.names,
    )

    os.environ["GENEVA_TABLE_NAME"] = table_name
    _LOG.info("Set GENEVA_TABLE_NAME=%s", table_name)

    global _MANIFESTS_UPLOADED
    if not _MANIFESTS_UPLOADED:
        _upload_all_manifests(geneva_test_bucket)
        _MANIFESTS_UPLOADED = True
        tbl = conn.open_table(table_name)
        _LOG.info("Schema after manifest upload: %s", tbl.schema.names)

    return conn, tbl, table_name


@pytest.fixture
def standard_cluster(
    document_table: tuple,
    geneva_k8s_service_account: str,
    k8s_config_method: K8sConfigMethod,
    k8s_namespace: str,
    region: str,
    head_node_selector: dict,
    worker_node_selector: dict,
) -> str:
    """
    Define a small CPU Ray cluster suitable for the document embedding pipeline.
    """
    conn, _, _ = document_table
    cluster_name = "e2e-document-embedding-cluster"

    builder = (
        GenevaClusterBuilder.create(cluster_name)
        .namespace(k8s_namespace)
        .config_method(k8s_config_method)
        .portforwarding(True)
        .head_group(
            service_account=geneva_k8s_service_account,
            cpus=1,
            memory="3Gi",
            image="rayproject/ray:2.44.0-py310",
            node_selector=head_node_selector,
        )
        .add_worker_group(
            WorkerGroupBuilder.cpu_worker(cpus=4, memory="8Gi")
            .image("rayproject/ray:2.44.0-py310")
            .service_account(geneva_k8s_service_account)
            .node_selector(worker_node_selector)
        )
    )

    if k8s_config_method == K8sConfigMethod.EKS_AUTH:
        builder.aws_config(region=region, role_name="geneva-client-role")

    cluster = builder.build()
    conn.define_cluster(cluster_name, cluster)
    _LOG.info("Defined cluster '%s'", cluster_name)
    return cluster_name


@pytest.fixture
def benchmark_cluster(
    document_table: tuple,
    geneva_k8s_service_account: str,
    k8s_config_method: K8sConfigMethod,
    k8s_namespace: str,
    csp: str,
    region: str,
    head_node_selector: dict,
) -> str:
    """
    Cluster matching ray_data_main.py benchmark expectations: 8 GPU workers,
    worker node selector geneva.lancedb.com/ray-worker-cpu.
    """
    conn, _, _ = document_table
    cluster_name = "e2e-document-embedding-benchmark-cluster"

    worker_selector = {"geneva.lancedb.com/ray-worker-gpu": "true"}
    worker_cfg = WorkerGroupConfig(
        service_account=geneva_k8s_service_account,
        num_cpus=4,
        memory="16Gi",
        image="rayproject/ray:2.44.0-py310",
        num_gpus=1,
        node_selector=worker_selector,
        labels={},
        tolerations=[],
        k8s_spec_override={"replicas": 8, "min_replicas": 8, "max_replicas": 8},
    )

    builder = (
        GenevaClusterBuilder.create(cluster_name)
        .namespace(k8s_namespace)
        .config_method(k8s_config_method)
        .portforwarding(True)
        .head_group(
            service_account=geneva_k8s_service_account,
            cpus=1,
            memory="3Gi",
            image="rayproject/ray:2.44.0-py310",
            node_selector=head_node_selector,
        )
        .add_worker_group(
            WorkerGroupBuilder.gpu_worker(cpus=4, memory="16Gi", gpus=1)
            .image("rayproject/ray:2.44.0-py310")
            .service_account(geneva_k8s_service_account)
            .node_selector(worker_selector)
        )
    )

    if k8s_config_method == K8sConfigMethod.EKS_AUTH:
        builder.aws_config(region=region, role_name="geneva-client-role")

    cluster = builder.build()
    cluster.kuberay.worker_groups = [worker_cfg]

    conn.define_cluster(cluster_name, cluster)
    _LOG.info("Defined benchmark cluster '%s'", cluster_name)
    return cluster_name

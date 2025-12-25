# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
E2E test-specific fixtures for Oxford Pets suite.

This conftest is fully self-contained and does not depend on src/conftest.py.
All fixtures needed for e2e tests are defined here.
"""

import contextlib
import logging
import os
import random
import sys
import uuid
import warnings
from collections.abc import Generator
from pathlib import Path

import kubernetes
import pyarrow as pa
import pytest

from geneva.cluster import GenevaClusterType, K8sConfigMethod
from geneva.cluster.mgr import GenevaCluster, HeadGroupConfig, KubeRayConfig, WorkerGroupConfig
from geneva.utils import dt_now_utc

# Add UDF directories to sys.path so UDF modules can be imported during test validation
# This is needed because tests unpickle UDFs for validation before sending to Ray
_udfs_dir = Path(__file__).parent / "udfs"
for udf_package in ["simple", "openclip", "blip"]:
    udf_path = _udfs_dir / udf_package
    if udf_path.exists() and str(udf_path) not in sys.path:
        sys.path.insert(0, str(udf_path))

# Try to load kubernetes config - only needed for e2e tests
with contextlib.suppress(kubernetes.config.config_exception.ConfigException):
    kubernetes.config.load_kube_config()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

warnings.filterwarnings(
    "ignore", "Using port forwarding for Ray cluster is not recommended for production"
)

_LOG = logging.getLogger(__name__)

# Flag to track if manifests have been uploaded
_MANIFESTS_UPLOADED = False


def _upload_all_manifests(bucket_path: str) -> None:
    """
    Upload all UDF manifests and add columns to the table.

    This runs after the table is created but before tests execute.
    Each upload script runs in its own UDF environment via `uv run`.
    """
    import subprocess
    from pathlib import Path

    _LOG.info("Uploading UDF manifests and adding columns...")

    udfs_dir = Path(__file__).parent / "udfs"
    udf_packages = ["simple", "openclip", "blip", "sentence-transformers"]

    for udf_name in udf_packages:
        udf_dir = udfs_dir / udf_name
        upload_script = udf_dir / "upload_manifest.py"

        _LOG.info(f"Uploading manifest for '{udf_name}' UDF package...")

        # Run upload script in UDF's environment
        # Step 1: Sync dependencies to populate .venv with UDF dependencies
        # (includes geneva and google-cloud-storage from pyproject.toml)
        sync_result = subprocess.run(
            ["uv", "sync", "--index-strategy", "unsafe-best-match"],
            cwd=str(udf_dir),
            capture_output=True,
            text=True,
        )
        if sync_result.returncode != 0:
            _LOG.error(f"Failed to sync dependencies for '{udf_name}':")
            if sync_result.stderr:
                for line in sync_result.stderr.splitlines():
                    _LOG.error(f"  [{udf_name}] {line}")
            raise RuntimeError(f"Dependency sync failed for '{udf_name}'")

        # Step 2: Run upload script from UDF's .venv
        result = subprocess.run(
            ["uv", "run", "python", "upload_manifest.py", "--bucket", bucket_path],
            cwd=str(udf_dir),
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )

        # Always show the output for debugging
        if result.stdout:
            for line in result.stdout.splitlines():
                _LOG.info(f"  [{udf_name}] {line}")
        if result.stderr:
            for line in result.stderr.splitlines():
                _LOG.warning(f"  [{udf_name}] {line}")

        if result.returncode != 0:
            _LOG.error(f"Failed to upload manifest for '{udf_name}':")
            raise RuntimeError(f"Manifest upload failed for '{udf_name}'")

        _LOG.info(f"✓ Manifest '{udf_name}' uploaded successfully")

    _LOG.info("All manifests uploaded and columns added")


# ============================================================================
# E2E test-specific pytest options
# ============================================================================


def pytest_addoption(parser) -> None:
    """Add e2e-specific command-line options."""
    parser.addoption(
        "--csp",
        action="store",
        default="gcp",
        choices=["gcp", "aws"],
        help="CSP to deploy to for tests (e.g., 'gcp', 'aws')",
    )
    parser.addoption(
        "--test-slug",
        action="store",
        default=None,
        help="Test slug to identify a test run",
    )
    parser.addoption(
        "--bucket-path",
        action="store",
        default=None,
        help="Bucket path for test data (e.g., gs://bucket/path or s3://bucket/path)",
    )
    parser.addoption(
        "--num-images",
        action="store",
        type=int,
        default=500,
        help="Number of images to process from Oxford pets dataset",
    )
    parser.addoption(
        "--batch-size",
        action="store",
        type=int,
        default=10,
        help="Batch size for backfill operations",
    )
    parser.addoption(
        "--skip-gpu",
        action="store_true",
        default=False,
        help="Skip GPU-based tests (captions, GPU embeddings)",
    )


# ============================================================================
# Common fixtures (copied from src/conftest.py for independence)
# ============================================================================


@pytest.fixture(scope="session")
def csp(request) -> str:
    """Cloud service provider (gcp or aws)."""
    return request.config.getoption("--csp")


@pytest.fixture(scope="session")
def slug(request) -> str:
    """Test slug for identifying test runs and cleanup."""
    return request.config.getoption("--test-slug") or str(random.randint(0, 10000))


@pytest.fixture(scope="session")
def geneva_test_bucket(request, slug, csp) -> str:
    """
    Test bucket path - can be overridden with --bucket-path or defaults based on CSP.

    Also sets up Geneva config overrides for checkpoint and upload paths.
    """
    from geneva.config import override_config_kv

    bucket_path = request.config.getoption("--bucket-path")

    if not bucket_path:
        if csp == "gcp":
            bucket_path = f"gs://lancedb-lancedb-dev-us-central1/{slug}/data"
        elif csp == "aws":
            bucket_path = f"s3://geneva-integ-test-devland-us-east-1/{slug}/data"
        else:
            raise ValueError(f"Unsupported --csp arg: {csp}")
        _LOG.info(f"Using default bucket path: {bucket_path}")
    else:
        _LOG.info(f"Using provided bucket path: {bucket_path}")

    # Set Geneva config overrides
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
    """Preconfigured service account for the test session."""
    return "geneva-service-account"


@pytest.fixture(scope="session")
def region(csp: str) -> str:
    """Default region for the CSP."""
    return "us-east-1" if csp == "aws" else "us-central1"


@pytest.fixture(scope="session")
def k8s_config_method(csp: str) -> K8sConfigMethod:
    """Kubernetes config method based on CSP."""
    return K8sConfigMethod.EKS_AUTH if csp == "aws" else K8sConfigMethod.LOCAL


@pytest.fixture(scope="session")
def k8s_namespace(csp: str) -> str:
    """Kubernetes namespace for Ray clusters."""
    return "geneva"


@pytest.fixture(scope="session")
def k8s_cluster_name(csp: str) -> str:
    """Kubernetes cluster name."""
    return "lancedb"


@pytest.fixture(scope="session")
def head_node_selector(csp: str) -> dict:
    """Node selector for Ray head nodes."""
    return (
        {"geneva.lancedb.com/ray-head": "true"}
        if csp == "aws"
        else {"_PLACEHOLDER": "true"}
    )


@pytest.fixture(scope="session")
def worker_node_selector(csp: str) -> dict:
    """Node selector for Ray worker nodes (CPU)."""
    return (
        {"geneva.lancedb.com/ray-worker-cpu": "true"}
        if csp == "aws"
        else {"_PLACEHOLDER": "true"}
    )


# ============================================================================
# Dataset Loading Utilities
# ============================================================================

ImageBatchGenerator = Generator[pa.RecordBatch, None, None]


def load_oxford_pets_images(
    num_images: int = 500, frag_size: int = 25
) -> ImageBatchGenerator:
    """
    Load images from the Oxford-IIIT Pet dataset.

    Args:
        num_images: Number of images to load from the dataset
        frag_size: Number of images per fragment

    Yields:
        PyArrow RecordBatch with columns: image (bytes), label (string)

    Raises:
        pytest.skip: If dataset cannot be loaded due to network or API errors
    """
    import io

    import pyarrow as pa
    from datasets import load_dataset

    from geneva.tqdm import tqdm

    _LOG.info(f"Loading {num_images} images from Oxford pets dataset")

    try:
        # there are 3680 images.  If num_images > 3680, it will just load all
        dataset = load_dataset("timm/oxford-iiit-pet", split=f"train[:{num_images}]")
    except Exception as e:
        pytest.skip(
            f"Failed to load Oxford pets dataset from HuggingFace. "
            f"This may be due to network issues or API unavailability. Error: {e}"
        )

    batch = []
    for row in tqdm(dataset):
        buf = io.BytesIO()
        row["image"].save(buf, format="png")
        batch.append({"image": buf.getvalue(), "label": row["label"],
            "image_id":row["image_id"]})

        if len(batch) >= frag_size:
            yield pa.RecordBatch.from_pylist(batch)
            batch = []

    if batch:
        yield pa.RecordBatch.from_pylist(batch)


# ============================================================================
# E2E test-specific fixtures
# ============================================================================


@pytest.fixture(scope="session")
def num_images(request) -> int:
    """Number of images to process in e2e tests."""
    return request.config.getoption("--num-images")


@pytest.fixture(scope="session")
def batch_size(request) -> int:
    """Batch size for backfill operations in e2e tests."""
    return request.config.getoption("--batch-size")


@pytest.fixture(scope="session")
def skip_gpu(request) -> bool:
    """Whether to skip GPU-based tests."""
    return request.config.getoption("--skip-gpu")


@pytest.fixture(scope="session")
def oxford_pets_table(geneva_test_bucket: str, num_images: int) -> tuple:  # type: ignore[misc]
    """
    Session-scoped fixture that creates a shared table with Oxford pets images.

    This table is created once per test session and reused across all e2e tests,
    avoiding repeated dataset downloads.

    Also sets GENEVA_TABLE_NAME environment variable for upload scripts.

    Returns:
        tuple: (connection, table, table_name)
    """
    import geneva

    _LOG.info(f"Creating shared Oxford pets table with {num_images} images")

    conn = geneva.connect(geneva_test_bucket)
    table_name = f"oxford_pets_shared_{uuid.uuid4().hex}"

    # Load images and create table (only happens once per session)
    first = True
    for batch in load_oxford_pets_images(num_images):
        if first:
            tbl = conn.create_table(table_name, batch, mode="overwrite")
            first = False
        else:
            tbl.add(batch)

    _LOG.info(
        f"Shared table created: name='{table_name}', rows={len(tbl)}, "
        f"schema={tbl.schema}. This will be reused across all e2e tests."
    )

    # Export table name as environment variable for upload scripts
    os.environ["GENEVA_TABLE_NAME"] = table_name
    _LOG.info(f"Set GENEVA_TABLE_NAME={table_name}")

    # Upload manifests and add columns (once per session)
    global _MANIFESTS_UPLOADED
    if not _MANIFESTS_UPLOADED:
        _upload_all_manifests(geneva_test_bucket)
        _MANIFESTS_UPLOADED = True

        # Refresh table to pick up newly added columns
        tbl = conn.open_table(table_name)
        _LOG.info(f"Table schema after manifest uploads: {tbl.schema}")

    yield conn, tbl, table_name


@pytest.fixture
def standard_cluster(
    oxford_pets_table: tuple,
    geneva_k8s_service_account: str,
    k8s_config_method: K8sConfigMethod,
    k8s_namespace: str,
    region: str,
    head_node_selector: dict,
    worker_node_selector: dict,
    k8s_cluster_name: str,
    slug: str,
) -> str:
    """
    Define a standard Ray cluster for e2e tests.

    Returns the cluster name for use with conn.context(cluster=name, manifest=name).
    """
    conn, _, _ = oxford_pets_table
    cluster_name = "e2e-standard-cluster"

    _LOG.info(f"Defining standard cluster '{cluster_name}'")

    # Define cluster configuration
    # Pin to ray 2.44.0 to match live cluster environments
    # TODO: When live clusters upgrade, update this version
    head_group = HeadGroupConfig(
        service_account=geneva_k8s_service_account,
        num_cpus=1,
        memory="3Gi",
        image="rayproject/ray:2.44.0-py310",
        node_selector=head_node_selector,
        labels={},
        tolerations=[],
    )

    worker_group = WorkerGroupConfig(
        service_account=geneva_k8s_service_account,
        num_cpus=2,
        memory="4Gi",
        image="rayproject/ray:2.44.0-py310",
        node_selector=worker_node_selector,
        labels={},
        tolerations=[],
    )

    kuberay_config = KubeRayConfig(
        namespace=k8s_namespace,
        head_group=head_group,
        worker_groups=[worker_group],
        config_method=k8s_config_method,
        use_portforwarding=True,
        aws_region=region if k8s_config_method == K8sConfigMethod.EKS_AUTH else None,
        aws_role_name="geneva-client-role" if k8s_config_method == K8sConfigMethod.EKS_AUTH else None,
    )

    cluster = GenevaCluster(
        cluster_type=GenevaClusterType.KUBE_RAY,
        name=cluster_name,
        kuberay=kuberay_config,
    )

    conn.define_cluster(cluster_name, cluster)
    _LOG.info(f"Cluster '{cluster_name}' defined")

    return cluster_name


@pytest.fixture
def gpu_cluster(
    oxford_pets_table: tuple,
    geneva_k8s_service_account: str,
    k8s_config_method: K8sConfigMethod,
    k8s_namespace: str,
    csp: str,
    region: str,
    head_node_selector: dict,
    k8s_cluster_name: str,
    slug: str,
) -> str:
    """
    Define a GPU Ray cluster for caption and embedding generation.

    Returns the cluster name for use with conn.context(cluster=name, manifest=name).
    """
    conn, _, _ = oxford_pets_table
    cluster_name = "e2e-gpu-cluster"

    _LOG.info(f"Defining GPU cluster '{cluster_name}'")

    # GPU worker node selector
    gpu_worker_node_selector = (
        {"geneva.lancedb.com/ray-worker-gpu": "true"}
        if csp == "aws"
        else {"_PLACEHOLDER": "true"}
    )

    # Define cluster configuration
    # Pin to ray 2.44.0 to match live cluster environments
    # TODO: When live clusters upgrade, update this version
    head_group = HeadGroupConfig(
        service_account=geneva_k8s_service_account,
        num_cpus=1,
        memory="3Gi",
        image="rayproject/ray:2.44.0-py310",
        node_selector=head_node_selector,
        labels={},
        tolerations=[],
    )

    worker_group = WorkerGroupConfig(
        service_account=geneva_k8s_service_account,
        num_cpus=4,
        memory="16Gi",
        image="rayproject/ray:2.44.0-py310",
        node_selector=gpu_worker_node_selector,
        labels={},
        tolerations=[],
        num_gpus=1,
    )

    kuberay_config = KubeRayConfig(
        namespace=k8s_namespace,
        head_group=head_group,
        worker_groups=[worker_group],
        config_method=k8s_config_method,
        use_portforwarding=True,
        aws_region=region if k8s_config_method == K8sConfigMethod.EKS_AUTH else None,
        aws_role_name="geneva-client-role" if k8s_config_method == K8sConfigMethod.EKS_AUTH else None,
    )

    cluster = GenevaCluster(
        cluster_type=GenevaClusterType.KUBE_RAY,
        name=cluster_name,
        kuberay=kuberay_config,
    )

    conn.define_cluster(cluster_name, cluster)
    _LOG.info(f"Cluster '{cluster_name}' defined")

    return cluster_name

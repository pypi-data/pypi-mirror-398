# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
E2E test-specific fixtures for OpenVid suite.

This conftest is fully self-contained and does not depend on src/conftest.py.
All fixtures needed for e2e tests are defined here.
"""

import contextlib
import logging
import os
import random
import subprocess
import sys
import uuid
import warnings
from collections.abc import Generator
from pathlib import Path

import kubernetes
import pyarrow as pa
import pytest

from geneva.cluster import K8sConfigMethod
from geneva.cluster.builder import GenevaClusterBuilder, WorkerGroupBuilder

SYNC_CMD = ["uv", "sync", "--index-strategy", "unsafe-best-match"]

# Add UDF directories to sys.path so UDF modules can be imported during test
# validation. This is needed because tests unpickle UDFs for validation before
# sending to Ray
_udfs_dir = Path(__file__).parent / "udfs"
# Add more UDF packages as they are created
for udf_package in ["simple", "embedding_vjepa2"]:
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

# ============================================================================
# Demo data paths and constants
# ============================================================================

GENEVA_VERSION = "0.x"
# Pre-populated demo table with OpenVid videos and embeddings
GENEVA_DB_PATH = f"gs://jon-geneva-demo/video-{GENEVA_VERSION}"
# Demo data bucket containing source videos and metadata
DEMO_DATA_DB_PATH = "gs://jon-geneva-demo/demo-data"
VID_DATA_PATH = f"{DEMO_DATA_DB_PATH}/openvid/videos/video"
# Pre-existing table name in the demo database
SOURCE_TABLE_NAME = "videos"
DEMO_TABLE_NAME = "videos_100"


def run_test_in_udf_env(
    udf_name: str,
    test_path: str,
    pytest_args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """
    Run a test file in a specific UDF's Python environment.

    This is useful when tests need dependencies that differ from the main
    test environment (e.g., Ray 2.48.0 vs 2.44.0).

    Args:
        udf_name: Name of UDF package (e.g., "embedding_vjepa2")
        test_path: Path to test file relative to e2e/openvid/
                  (e.g., "test_drivers/test_video_embeddings.py")
        pytest_args: Additional pytest arguments (e.g., ["-v", "-s"])
        env: Additional environment variables to pass to the subprocess

    Returns:
        CompletedProcess with returncode, stdout, stderr

    Raises:
        RuntimeError: If dependency sync fails
    """
    udfs_dir = Path(__file__).parent / "udfs"
    udf_dir = udfs_dir / udf_name

    if not udf_dir.exists():
        raise ValueError(f"UDF directory not found: {udf_dir}")

    _LOG.info(f"Running test in '{udf_name}' UDF environment...")

    # Step 1: Sync dependencies to populate .venv with UDF dependencies
    _LOG.info(f"Syncing dependencies for '{udf_name}'...")
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

    # Step 2: Run test from UDF's .venv
    # Construct path to test file relative to UDF directory
    test_file = Path("../../") / test_path
    cmd = ["uv", "run", "python", "-m", "pytest", str(test_file)]
    if pytest_args:
        cmd.extend(pytest_args)

    _LOG.info(f"Running: {' '.join(cmd)}")
    _LOG.info(f"  Working directory: {udf_dir}")

    # Disable uv runtime env for Ray compatibility
    subprocess_env = os.environ.copy()
    subprocess_env["RAY_ENABLE_UV_RUN_RUNTIME_ENV"] = "0"
    # Merge custom env variables if provided
    if env:
        subprocess_env.update(env)

    # Stream output in real-time instead of buffering
    # This is important for long-running tests (GPU backfills) so we can see progress
    _LOG.info(f"  [{udf_name}] Starting test (output will stream in real-time)...")

    process = subprocess.Popen(
        cmd,
        cwd=str(udf_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Merge stderr into stdout
        text=True,
        env=subprocess_env,
        bufsize=1,  # Line-buffered
    )

    # Stream output line by line in real-time AND capture for return value
    captured_lines = []
    for line in iter(process.stdout.readline, ""):
        if line:
            _LOG.info(f"  [{udf_name}] {line.rstrip()}")
            captured_lines.append(line)

    process.stdout.close()
    returncode = process.wait()

    # Create a CompletedProcess-like object with captured output
    captured_output = "".join(captured_lines)
    result = subprocess.CompletedProcess(
        args=cmd,
        returncode=returncode,
        stdout=captured_output,
        stderr="",  # Merged into stdout
    )

    return result


def _upload_all_manifests(bucket_path: str) -> None:
    """
    Upload all UDF manifests and add columns to the table.

    This runs after the table is created but before tests execute.
    Each upload script runs in its own UDF environment via `uv run`.
    """
    _LOG.info("Uploading UDF manifests and adding columns...")

    udfs_dir = Path(__file__).parent / "udfs"
    # Add UDF packages as they are created
    # Note: frame_extractor only uploads its manifest without adding columns
    # (blob columns break regular queries on the shared source table)
    udf_packages = []
    for pkg in ["simple", "embedding_vjepa2", "frame_extractor"]:
        if (udfs_dir / pkg).exists():
            udf_packages.append(pkg)

    for udf_name in udf_packages:
        udf_dir = udfs_dir / udf_name
        upload_script = udf_dir / "upload_manifest.py"

        if not upload_script.exists():
            _LOG.warning(f"Upload script not found for '{udf_name}', skipping...")
            continue

        _LOG.info(f"Uploading manifest for '{udf_name}' UDF package...")

        # Run upload script in UDF's environment
        # Step 1: Sync dependencies to populate .venv with UDF dependencies
        sync_result = subprocess.run(
            SYNC_CMD,
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
        "--num-videos",
        action="store",
        type=int,
        default=20,
        help="Number of videos to process from OpenVid dataset",
    )
    parser.addoption(
        "--batch-size",
        action="store",
        type=int,
        default=4,
        help="Batch size for backfill operations",
    )
    parser.addoption(
        "--skip-gpu",
        action="store_true",
        default=False,
        help="Skip GPU-based tests (video embeddings, captions)",
    )
    parser.addoption(
        "--source-bucket",
        action="store",
        default="gs://jon-geneva-demo/demo-data/openvid/videos",
        help="Source bucket containing OpenVid videos",
    )


# ============================================================================
# Common fixtures
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
            # todo: https://linear.app/lancedb/issue/GEN-257/move-e2e-tests-to-new-stack
            bucket_path = f"gs://geneva-integ-test/{slug}/data"
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
    # todo: https://linear.app/lancedb/issue/GEN-257/move-e2e-tests-to-new-stack
    return "geneva-service-account" if csp == "aws" else "geneva-integ-test"


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

VideoBatchGenerator = Generator[pa.RecordBatch, None, None]


def load_openvid_videos(
    source_bucket: str, num_videos: int = 100, chunk_size: int = 10000
) -> VideoBatchGenerator:
    """
    Load video metadata from OpenVid-1M CSV preserving all columns.

    Downloads the OpenVid-1M.csv from HuggingFace and yields the data in chunks,
    preserving all CSV columns (video, caption, frame, fps, seconds, etc.).
    Lance will infer column names and types from the CSV data.

    Optionally adds a video_path column with full GCS paths if source_bucket
    is provided.

    Args:
        source_bucket: GCS path to OpenVid videos (e.g., gs://bucket/videos)
                      If provided, adds a video_path column combining
                      bucket + video name
        num_videos: Number of videos to load
        chunk_size: Number of videos per chunk (default: 10000)

    Yields:
        PyArrow RecordBatch with all CSV columns (video, caption, frame, fps,
        seconds, etc.) and optionally video_path if source_bucket is provided

    Raises:
        pytest.skip: If CSV cannot be downloaded or parsed
    """
    import io

    import pandas as pd
    import requests

    _LOG.info("Downloading OpenVid-1M metadata from HuggingFace")

    csv_url = "https://huggingface.co/datasets/nkp37/OpenVid-1M/resolve/main/data/train/OpenVid-1M.csv"

    try:
        # Download CSV from HuggingFace
        response = requests.get(csv_url, timeout=60)
        response.raise_for_status()

        # Parse CSV
        df = pd.read_csv(io.StringIO(response.text))
        _LOG.info(f"Downloaded CSV with {len(df)} total videos")
        _LOG.info(f"CSV columns: {list(df.columns)}")

        # Verify expected columns exist
        expected_cols = ["video", "caption", "frame", "fps", "seconds"]
        missing_cols = [col for col in expected_cols if col not in df.columns]
        if missing_cols:
            _LOG.warning(f"Missing expected columns: {missing_cols}")

        # Limit to requested number of videos
        df = df.head(num_videos)
        _LOG.info(f"Processing {len(df)} videos in chunks of {chunk_size}")

        # Process in chunks
        for start in range(0, len(df), chunk_size):
            chunk = df.iloc[start:start + chunk_size].copy()

            # Optionally add video_path column with full GCS paths
            if source_bucket and "video" in chunk.columns:
                chunk["video_path"] = chunk["video"].apply(
                    lambda vid: f"{source_bucket.rstrip('/')}/{vid}"
                )

            _LOG.info(
                f"Chunk {start // chunk_size}: {len(chunk)} rows, "
                f"columns: {list(chunk.columns)}"
            )

            # Convert to PyArrow RecordBatch, preserving all CSV columns
            yield pa.RecordBatch.from_pandas(chunk, preserve_index=False)

    except requests.RequestException as e:
        pytest.skip(
            f"Failed to download OpenVid-1M.csv from HuggingFace. "
            f"This may be due to network issues or API unavailability. Error: {e}"
        )
    except Exception as e:
        pytest.skip(f"Failed to process OpenVid metadata: {e}")


def create_openvid_demo_table(
    num_videos: int = 100,
    source_bucket: str | None = None,
) -> None:
    """
    Create the demo OpenVid table at GENEVA_DB_PATH.

    This function is used to initially populate the demo database with
    OpenVid videos from HuggingFace. It downloads the CSV metadata,
    creates the table, and uploads UDF manifests.

    This is a one-time setup operation. Tests use openvid_table fixture
    which copies from this pre-existing table.

    Args:
        num_videos: Number of videos to include in demo table
        source_bucket: Optional GCS bucket path containing videos
                      (e.g., gs://bucket/videos)
    """
    import geneva

    _LOG.info(
        f"Creating demo OpenVid table at {GENEVA_DB_PATH} "
        f"with {num_videos} videos"
    )

    conn = geneva.connect(GENEVA_DB_PATH)

    # Ensure source table exists (create if needed)
    try:
        src_tbl = conn.create_table(
            SOURCE_TABLE_NAME, batch, mode="create_new"
        )
        _LOG.info(
            f"Source table being created from HuggingFace CSV "
            f"with {num_videos} videos..."
        )
        for batch in load_openvid_videos(source_bucket, num_videos):
            src_tbl.add(batch)
        _LOG.info(
            f"Source table created: name='{SOURCE_TABLE_NAME}', "
            f"rows={len(src_tbl)}"
        )

    except ValueError:
        # assume already exists
        src_tbl = conn.open_table(SOURCE_TABLE_NAME)
        _LOG.info(
            f"Source table exists: name='{SOURCE_TABLE_NAME}', "
            f"rows={len(src_tbl)}"
        )


    # Create demo table by sampling from source table
    sample_df = src_tbl._ltbl.search().where("has_file").limit(num_videos).to_pandas()
    tbl = conn.create_table(DEMO_TABLE_NAME, sample_df, mode="overwrite")

    _LOG.info(
        f"Demo table created: name='{DEMO_TABLE_NAME}', "
        f"rows={len(tbl)}, schema={tbl.schema.names}"
    )

    # Set environment variable for upload scripts
    os.environ["GENEVA_TABLE_NAME"] = DEMO_TABLE_NAME

    # Upload manifests and add columns
    _upload_all_manifests(GENEVA_DB_PATH)

    # Refresh table to pick up newly added columns
    tbl = conn.open_table(DEMO_TABLE_NAME)
    _LOG.info(f"Table schema after manifest uploads: {tbl.schema.names}")

    _LOG.info(f"✓ Demo table ready at {GENEVA_DB_PATH}/{DEMO_TABLE_NAME}")


# ============================================================================
# E2E test-specific fixtures
# ============================================================================


@pytest.fixture(scope="session")
def num_videos(request) -> int:
    """Number of videos to process in e2e tests."""
    return request.config.getoption("--num-videos")


@pytest.fixture(scope="session")
def batch_size(request) -> int:
    """Batch size for backfill operations in e2e tests."""
    return request.config.getoption("--batch-size")


@pytest.fixture(scope="session")
def skip_gpu(request) -> bool:
    """Whether to skip GPU-based tests."""
    return request.config.getoption("--skip-gpu")


@pytest.fixture(scope="session")
def source_bucket(request) -> str:
    """Source bucket containing OpenVid videos."""
    return request.config.getoption("--source-bucket")


@pytest.fixture(scope="session")
def openvid_table(
    geneva_test_bucket: str, num_videos: int
) -> tuple:  # type: ignore[misc]
    """
    Session-scoped fixture that copies a sample from the pre-existing demo table.

    Copies data from GENEVA_DB_PATH to the test bucket for isolated testing.
    This is much faster than creating the table from scratch.

    Also sets GENEVA_TABLE_NAME environment variable for upload scripts.

    Returns:
        tuple: (connection, table, table_name)
    """
    import geneva

    _LOG.info(
        f"Copying {num_videos} videos from demo table at {GENEVA_DB_PATH}"
    )

    # Connect to test bucket
    conn = geneva.connect(geneva_test_bucket)
    table_name = f"openvid_test_{uuid.uuid4().hex}"

    # Drop geneva_clusters table to force schema recreation (in case schema changed)
    try:
        conn._db.drop_table("geneva_clusters")
        _LOG.info("Dropped existing geneva_clusters table to refresh schema")
    except Exception:
        pass  # Table might not exist yet

    # Connect to demo database and copy sample data
    demo_conn = geneva.connect(GENEVA_DB_PATH)
    demo_tbl = demo_conn.open_table(SOURCE_TABLE_NAME)

    _LOG.info(
        f"Demo table has {len(demo_tbl)} rows, schema: {demo_tbl.schema.names}"
    )

    # Copy a sample of the demo table to test bucket
    sample_df = demo_tbl._ltbl.search().where("has_file").limit(num_videos).to_pandas()

    # Drop columns that will be added by manifest uploads to avoid conflicts
    cols_to_drop = ["has_file", "video_embedding_vjepa2"]
    for col in cols_to_drop:
        if col in sample_df.columns:
            sample_df = sample_df.drop(columns=[col])
            _LOG.info(f"Dropped column '{col}' from sample (will be re-added by manifest)")

    tbl = conn.create_table(
        table_name,
        sample_df,
        mode="overwrite",
        storage_options={"new_table_enable_stable_row_ids": "true"},
    )

    _LOG.info(
        f"Test table created: name='{table_name}', rows={len(tbl)}, "
        f"schema={tbl.schema.names}. Copied from demo table."
    )

    # Export table name as environment variable for upload scripts
    os.environ["GENEVA_TABLE_NAME"] = table_name
    _LOG.info(f"Set GENEVA_TABLE_NAME={table_name}")

    # Upload manifests to test bucket (once per session)
    global _MANIFESTS_UPLOADED
    if not _MANIFESTS_UPLOADED:
        _upload_all_manifests(geneva_test_bucket)
        _MANIFESTS_UPLOADED = True

        # Refresh table to pick up newly added columns
        tbl = conn.open_table(table_name)
        _LOG.info(f"Table schema after manifest uploads: {tbl.schema.names}")

    return conn, tbl, table_name


@pytest.fixture
def standard_cluster(
    openvid_table: tuple,
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
    conn, _, _ = openvid_table
    cluster_name = "e2e-openvid-standard-cluster"

    _LOG.info(f"Defining standard cluster '{cluster_name}'")

    # Build cluster using fluent API
    # Pin to ray 2.44.0 to match live cluster environments
    builder = GenevaClusterBuilder.create(cluster_name).namespace(
        k8s_namespace
    ).config_method(k8s_config_method).portforwarding(True).head_group(
        service_account=geneva_k8s_service_account,
        cpus=1,
        memory="3Gi",
        image="rayproject/ray:2.44.0-py310",
        node_selector=head_node_selector,
    ).add_worker_group(
        WorkerGroupBuilder.cpu_worker(cpus=2, memory="4Gi")
        .image("rayproject/ray:2.44.0-py310")
        .service_account(geneva_k8s_service_account)
        .node_selector(worker_node_selector)
    )

    # Add AWS config if needed
    if k8s_config_method == K8sConfigMethod.EKS_AUTH:
        builder.aws_config(region=region, role_name="geneva-client-role")

    cluster = builder.build()

    conn.define_cluster(cluster_name, cluster)
    _LOG.info(f"Cluster '{cluster_name}' defined")

    return cluster_name


@pytest.fixture
def gpu_cluster(
    openvid_table: tuple,
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
    Define a GPU Ray cluster for video embedding and processing.

    Returns the cluster name for use with conn.context(cluster=name, manifest=name).
    """
    conn, _, _ = openvid_table
    cluster_name = "e2e-openvid-gpu-cluster"

    _LOG.info(f"Defining GPU cluster '{cluster_name}'")

    # GPU worker node selector
    gpu_worker_node_selector = (
        {"geneva.lancedb.com/ray-worker-gpu": "true"}
        if csp == "aws"
        else {"_PLACEHOLDER": "true"}
    )

    # Build cluster using fluent API
    # Pin to ray 2.44.0 to match live cluster environments
    builder = GenevaClusterBuilder.create(cluster_name).namespace(
        k8s_namespace
    ).config_method(k8s_config_method).portforwarding(True).head_group(
        service_account=geneva_k8s_service_account,
        cpus=1,
        memory="3Gi",
        image="rayproject/ray:2.44.0-py310",
        node_selector=head_node_selector,
    ).add_worker_group(
        WorkerGroupBuilder.gpu_worker(cpus=4, memory="16Gi", gpus=1)
        .image("rayproject/ray:2.44.0-py310")
        .service_account(geneva_k8s_service_account)
        .node_selector(gpu_worker_node_selector)
    )

    # Add AWS config if needed
    if k8s_config_method == K8sConfigMethod.EKS_AUTH:
        builder.aws_config(region=region, role_name="geneva-client-role")

    cluster = builder.build()

    conn.define_cluster(cluster_name, cluster)
    _LOG.info(f"Cluster '{cluster_name}' defined")

    return cluster_name


@pytest.fixture
def rayml_248_gpu_cluster(
    openvid_table: tuple,
    geneva_k8s_service_account: str,
    k8s_config_method: K8sConfigMethod,
    k8s_namespace: str,
    csp: str,
    region: str,
    head_node_selector: dict,
    worker_node_selector:dict,
    k8s_cluster_name: str,
    slug: str,
) -> str:
    """
    Define a GPU Ray cluster using ray-ml:2.48.0 with custom conda environment.

    This cluster uses ray-ml:2.48.0 images with torch 2.7.1 and includes
    ray_init_kwargs with conda dependencies for:
    - ffmpeg (compatible with torch 2.7.1)
    - torchvision 0.22.1
    - torchcodec 0.5.0
    - transformers 4.57.1
    - And other ML dependencies

    Suitable for video embedding tasks (V-JEPA2, etc.) and other ML workloads
    requiring these dependencies.

    Returns the cluster name for use with conn.context(cluster=name, manifest=name).
    """
    conn, _, _ = openvid_table
    cluster_name = "e2e-openvid-rayml-248-gpu-cluster"

    _LOG.info(
        f"Defining ray-ml:2.48.0 GPU cluster '{cluster_name}' "
        "with conda environment"
    )

    # GPU worker node selector
    gpu_worker_node_selector = (
        {"geneva.lancedb.com/ray-worker-gpu": "true"}
        if csp == "aws"
        else {"_PLACEHOLDER": "true"}
    )

    # Ray init kwargs with conda environment for V-JEPA2
    # torch 2.7.1 included in ray-ml:2.48.0 containers, make torchvision compatible
    ray_init_kwargs = {
        "conda": {
            "channels": ["conda-forge"],
            "dependencies": [
                "python=3.10",  # must match cluster Python
                # brings the ffmpeg binary on PATH. Torch 2.7.1 needs
                # ffmpeg 4-7 (not 8)
                "ffmpeg<8",
                "imageio",
                "moviepy",
                "opencv",  # optional
                "pyarrow=21.0.0",
                # "pytorch", # already in ray-ml image
                "torchvision=0.22.1",
                "pandas",
                "pip",
                {
                    "pip": [
                        # Add fury.io indexes for pylance and lancedb beta versions
                        "--extra-index-url=https://pypi.fury.io/lance-format/",
                        "--extra-index-url=https://pypi.fury.io/lancedb/",
                        "attrs>=23,<25",
                        "cattrs",
                        "pylance>=1.1.0b2",
                        "lancedb>=0.25.4b2",
                        "lance-namespace>=0.2.1",
                        "cloudpickle",
                        "tenacity",
                        "requests",
                        "urllib3>=2,<3",
                        "more-itertools",
                        "toml>=0.10.2",
                        "pyyaml>=6.0.2",
                        "tqdm",
                        "bidict",
                        "emoji",
                        "multiprocess",
                        "aiohttp>=3.12.12",
                        "fsspec",
                        "transformers==4.57.1",
                        "torchcodec==0.5.0",  # goes with torch 2.7.1 from ray-ml image
                        "fsspec[gcs]>=2023.0.0",
                        "gcsfs>=2023.0.0",
                        "numpy>=2.2.6",  # bumped
                        "tomli>=2.0; python_version<'3.11'",
                        "kubernetes",
                        "geneva",  # needed by UDF manifests
                        "google-cloud-storage",  # needed for GCS operations
                    ]
                },
            ],
        },
        "config": {"eager_install": True},  # install env when ray.init() runs
    }

    # Build cluster using fluent API
    # Use ray-ml:2.48.0 image for GPU with pre-installed ML libraries
    builder = GenevaClusterBuilder.create(cluster_name).namespace(
        k8s_namespace
    ).config_method(k8s_config_method).portforwarding(True).head_group(
        service_account=geneva_k8s_service_account,
        cpus=1,
        memory="3Gi",
        image="rayproject/ray-ml:2.48.0.2c63f6-py310-cpu",
        node_selector=head_node_selector,
    ).add_worker_group(
        WorkerGroupBuilder.cpu_worker(cpus=30, memory="120Gi")
        .image("rayproject/ray-ml:2.48.0.2c63f6-py310-cpu")
        .service_account(geneva_k8s_service_account)
        .node_selector(worker_node_selector)
    ).add_worker_group(
        WorkerGroupBuilder.gpu_worker(cpus=4, memory="16Gi", gpus=1)
        .image("rayproject/ray-ml:2.48.0.2c63f6-py310-gpu")
        .service_account(geneva_k8s_service_account)
        .node_selector(gpu_worker_node_selector)
    ).ray_init_kwargs(
        {"runtime_env": ray_init_kwargs}
    )

    # Add AWS config if needed
    if k8s_config_method == K8sConfigMethod.EKS_AUTH:
        builder.aws_config(region=region, role_name="geneva-client-role")

    cluster = builder.build()

    conn.define_cluster(cluster_name, cluster)
    _LOG.info(f"Cluster '{cluster_name}' defined with conda environment")

    return cluster_name


@pytest.fixture
def rayml_248_cpu_cluster(
    openvid_table: tuple,
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
    Define a CPU-only Ray cluster using ray-ml:2.48.0 with conda environment.

    This cluster is similar to rayml_248_gpu_cluster but without GPU workers.
    Suitable for CPU-based video processing (frame extraction with torchcodec).

    Uses the same conda environment with torchcodec, Pillow, ffmpeg, etc.

    Returns the cluster name for use with conn.context(cluster=name, manifest=name).
    """
    conn, _, _ = openvid_table
    cluster_name = "e2e-openvid-rayml-248-cpu-cluster"

    _LOG.info(
        f"Defining ray-ml:2.48.0 CPU cluster '{cluster_name}' "
        "with conda environment"
    )

    # Ray init kwargs with conda environment (same as GPU cluster)
    ray_init_kwargs = {
        "conda": {
            "channels": ["conda-forge"],
            "dependencies": [
                "python=3.10",
                "ffmpeg<8",
                "imageio",
                "Pillow",  # For frame extraction
                "pyarrow=21.0.0",
                "torchvision=0.22.1",
                "pandas",
                "pip",
                {
                    "pip": [
                        "--extra-index-url=https://pypi.fury.io/lance-format/",
                        "--extra-index-url=https://pypi.fury.io/lancedb/",
                        "attrs>=23,<25",
                        "cattrs",
                        "pylance>=1.1.0b2",
                        "lancedb>=0.25.4b2",
                        "lance-namespace>=0.2.1",
                        "cloudpickle",
                        "tenacity",
                        "requests",
                        "urllib3>=2,<3",
                        "more-itertools",
                        "toml>=0.10.2",
                        "pyyaml>=6.0.2",
                        "tqdm",
                        "bidict",
                        "emoji",
                        "multiprocess",
                        "aiohttp>=3.12.12",
                        "fsspec",
                        "torchcodec==0.5.0",
                        "fsspec[gcs]>=2023.0.0",
                        "gcsfs>=2023.0.0",
                        "numpy>=2.2.6",
                        "tomli>=2.0; python_version<'3.11'",
                        "kubernetes",
                        "geneva",
                        "google-cloud-storage",
                    ]
                },
            ],
        },
        "config": {"eager_install": True},
    }

    # Build cluster - CPU only, no GPU workers
    builder = GenevaClusterBuilder.create(cluster_name).namespace(
        k8s_namespace
    ).config_method(k8s_config_method).portforwarding(True).head_group(
        service_account=geneva_k8s_service_account,
        cpus=1,
        memory="3Gi",
        image="rayproject/ray-ml:2.48.0.2c63f6-py310-cpu",
        node_selector=head_node_selector,
    ).add_worker_group(
        WorkerGroupBuilder.cpu_worker(cpus=8, memory="32Gi")
        .image("rayproject/ray-ml:2.48.0.2c63f6-py310-cpu")
        .service_account(geneva_k8s_service_account)
        .node_selector(worker_node_selector)
    ).ray_init_kwargs(
        {"runtime_env": ray_init_kwargs}
    )

    # Add AWS config if needed
    if k8s_config_method == K8sConfigMethod.EKS_AUTH:
        builder.aws_config(region=region, role_name="geneva-client-role")

    cluster = builder.build()

    conn.define_cluster(cluster_name, cluster)
    _LOG.info(f"Cluster '{cluster_name}' defined (CPU-only)")

    return cluster_name

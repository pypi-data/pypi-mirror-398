# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Wrapper tests for materialized view blob handling.

These tests run the actual blob MV tests via subprocess in the
frame_extractor UDF environment which has Ray 2.48.0 dependencies.

This allows the main test suite (Ray 2.44.0) to orchestrate tests that
need different Ray versions. Frame extraction runs on CPU using torchcodec.
"""

import logging
import os

import pytest

from conftest import run_test_in_udf_env

_LOG = logging.getLogger(__name__)


def _get_pytest_args(request, openvid_table, cluster_name=None) -> list[str]:
    """Build pytest arguments for subprocess tests."""
    conn, tbl, table_name = openvid_table

    pytest_args = ["-v", "-s"]

    # Get command-line options from parent pytest session
    if hasattr(request.config, "getoption"):
        csp = request.config.getoption("--csp", default="gcp")
        test_slug = request.config.getoption("--test-slug", default=None)
        bucket_path = request.config.getoption("--bucket-path", default=None)
        num_videos = request.config.getoption("--num-videos", default=20)
        batch_size_arg = request.config.getoption("--batch-size", default=4)

        pytest_args.extend([
            f"--csp={csp}",
            f"--num-videos={num_videos}",
            f"--batch-size={batch_size_arg}",
        ])
        if test_slug:
            pytest_args.append(f"--test-slug={test_slug}")
        if bucket_path:
            pytest_args.append(f"--bucket-path={bucket_path}")

    return pytest_args


def _get_env_vars(
    openvid_table, geneva_test_bucket, cluster_name=None
) -> dict[str, str]:
    """Get environment variables for subprocess tests."""
    conn, tbl, table_name = openvid_table

    env = os.environ.copy()
    env["GENEVA_TEST_BUCKET"] = geneva_test_bucket
    env["GENEVA_TABLE_NAME"] = table_name
    if cluster_name:
        env["GENEVA_CLUSTER_NAME"] = cluster_name

    return env


def test_mv_blob_column_creation(
    openvid_table,
    rayml_248_cpu_cluster,
    geneva_test_bucket,
    request,
) -> None:
    """Run test_mv_with_frame_blob_column in Ray 2.48.0 environment (CPU)."""
    cluster_name = rayml_248_cpu_cluster
    pytest_args = _get_pytest_args(request, openvid_table, cluster_name)

    # Set environment variables for the subprocess
    env = _get_env_vars(openvid_table, geneva_test_bucket, cluster_name)

    result = run_test_in_udf_env(
        udf_name="frame_extractor",
        test_path="test_drivers/_test_mv_blobs_impl.py::test_mv_with_frame_blob_column",
        pytest_args=pytest_args,
        env=env,
    )

    if result.returncode != 0:
        _LOG.error("test_mv_with_frame_blob_column failed in Ray 2.48.0 environment")
        _LOG.error("Return code: %d", result.returncode)
        if result.stdout:
            _LOG.error("=== Last 100 lines of output ===")
            for line in result.stdout.splitlines()[-100:]:
                _LOG.error(line)
        pytest.fail(
            f"test_mv_with_frame_blob_column failed with return code "
            f"{result.returncode}. See logs above for details."
        )
    _LOG.info("test_mv_with_frame_blob_column passed in Ray 2.48.0 environment")


def test_mv_blob_metadata_propagates(
    openvid_table,
    rayml_248_cpu_cluster,
    geneva_test_bucket,
    request,
) -> None:
    """Run test_mv_blob_metadata_propagates in Ray 2.48.0 environment (CPU)."""
    cluster_name = rayml_248_cpu_cluster
    pytest_args = _get_pytest_args(request, openvid_table, cluster_name)
    env = _get_env_vars(openvid_table, geneva_test_bucket, cluster_name)

    result = run_test_in_udf_env(
        udf_name="frame_extractor",
        test_path="test_drivers/_test_mv_blobs_impl.py::test_mv_blob_metadata_propagates",
        pytest_args=pytest_args,
        env=env,
    )

    if result.returncode != 0:
        _LOG.error("test_mv_blob_metadata_propagates failed in Ray 2.48.0 environment")
        _LOG.error("Return code: %d", result.returncode)
        if result.stdout:
            _LOG.error("=== Last 100 lines of output ===")
            for line in result.stdout.splitlines()[-100:]:
                _LOG.error(line)
        pytest.fail(
            f"test_mv_blob_metadata_propagates failed with return code "
            f"{result.returncode}. See logs above for details."
        )
    _LOG.info("test_mv_blob_metadata_propagates passed in Ray 2.48.0 environment")


def test_mv_take_blobs_after_refresh(
    openvid_table,
    rayml_248_cpu_cluster,
    geneva_test_bucket,
    request,
) -> None:
    """Run test_mv_take_blobs_after_refresh in Ray 2.48.0 environment (CPU)."""
    cluster_name = rayml_248_cpu_cluster
    pytest_args = _get_pytest_args(request, openvid_table, cluster_name)
    env = _get_env_vars(openvid_table, geneva_test_bucket, cluster_name)

    result = run_test_in_udf_env(
        udf_name="frame_extractor",
        test_path="test_drivers/_test_mv_blobs_impl.py::test_mv_take_blobs_after_refresh",
        pytest_args=pytest_args,
        env=env,
    )

    if result.returncode != 0:
        _LOG.error("test_mv_take_blobs_after_refresh failed in Ray 2.48.0 environment")
        _LOG.error("Return code: %d", result.returncode)
        if result.stdout:
            _LOG.error("=== Last 100 lines of output ===")
            for line in result.stdout.splitlines()[-100:]:
                _LOG.error(line)
        pytest.fail(
            f"test_mv_take_blobs_after_refresh failed with return code "
            f"{result.returncode}. See logs above for details."
        )
    _LOG.info("test_mv_take_blobs_after_refresh passed in Ray 2.48.0 environment")

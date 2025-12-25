# ruff: noqa: E402
# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

# lance dataset distributed transform job checkpointing + UDF utils

import base64
import fcntl
import json
import logging
import os
import site
import tempfile
import threading
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

_LOG = logging.getLogger(__name__)

_extract_lock = threading.Lock()


def _download_and_extract(args: dict) -> None:
    src_path, download_path, output_dir = (
        args["src_path"],
        args["download_path"],
        args["output_dir"],
    )
    namespace_info = args.get("namespace")

    # Check if this is an uploaded workspace (contains /_uploads/)
    # If so, use LanceFileSession for namespace-aware downloads
    if "/_uploads/" in src_path:
        # Parse the path to extract base_path and remote filename
        # e.g., s3://bucket/path/to/table/_uploads/workspace.zip
        # -> base_path: s3://bucket/path/to/table/_uploads
        # -> remote_path: workspace.zip
        parts = src_path.rsplit("/_uploads/", 1)
        if len(parts) == 2:
            base_path = f"{parts[0]}/_uploads"
            remote_path = parts[1]

            # Create session with namespace credentials if available
            if namespace_info is not None:
                try:
                    # Import lance lazily to avoid issues when dependencies
                    # aren't available yet
                    # (e.g., when they're part of the manifest being loaded via
                    # GENEVA_ZIPS)
                    from lance.file import LanceFileSession
                except ImportError as e:
                    raise RuntimeError(
                        "could not import lance. pylance must be "
                        "provided explicitly in the manifest "
                        "via `pip=...`"
                    ) from e

                from geneva.namespace import get_storage_options_provider

                storage_options_provider, storage_options = (
                    get_storage_options_provider(
                        namespace_info["impl"],
                        namespace_info["properties"],
                        namespace_info["table_id"],
                    )
                )
                session = LanceFileSession(
                    base_path,
                    storage_options=storage_options,
                    storage_options_provider=storage_options_provider,
                )
                session.download_file(remote_path, download_path)
            else:
                _download_with_pyarrow(src_path, download_path)
        else:
            # Fallback if parsing fails
            _download_with_pyarrow(src_path, download_path)
    else:
        # Fallback to PyArrow for paths that aren't in /_uploads/
        _download_with_pyarrow(src_path, download_path)

    with (
        zipfile.ZipFile(download_path) as z,
        _extract_lock,  # ensure only one thread extracts at a time
    ):
        z.extractall(output_dir)
        _LOG.info("extracted workspace to %s", output_dir)


def _download_with_pyarrow(src_path: str, download_path: Path) -> None:
    """Fallback download using PyArrow FileSystem."""
    import pyarrow.fs as fs

    handle, path = fs.FileSystem.from_uri(src_path)
    handle: fs.FileSystem = handle
    path: str = path

    with (
        handle.open_input_file(path) as f,
        open(download_path, "wb") as out,
    ):
        chunk_size = 1024 * 1024 * 8  # 8MiB chunks
        while data := f.read(chunk_size):
            out.write(data)


# MAGIC: if GENEVA_ZIPS is set, we will extract the zips and add them as site-packages
# this is how we acheive "import geneva" == importing workspace from client
#
# NOTE: think of this like booting up a computer. At this point we do not have any
# dependencies installed, so this logic needs to have minimal dependency surface.
# We avoid importing anything from geneva and do everything in the stdlib
if "GENEVA_ZIPS" in os.environ:
    import fcntl

    with (
        open("/tmp/.geneva_zip_setup", "w") as file,  # noqa: S108
        ThreadPoolExecutor(max_workers=8) as executor,
    ):
        # use fcntl to lock the file so we don't have multiple processes
        # trying to extract at the same time and blow up the disk space
        fcntl.lockf(file, fcntl.LOCK_EX)

        payload = json.loads(base64.b64decode(os.environ["GENEVA_ZIPS"]))
        zips = payload.get("zips", [])
        namespace_info = payload.get("namespace")

        for parts in zips:
            if not len(parts):
                # got an empty list, skip
                continue

            _LOG.info("Setting up geneva workspace from zips %s", parts)
            file_name = parts[0].split("/")[-1]
            name = file_name.split(".")[0]
            output_dir = Path(tempfile.gettempdir()) / name
            if output_dir.exists():
                _LOG.info("workspace already extracted to %s", output_dir)
            else:
                # force collect to surface errors
                list(
                    executor.map(
                        _download_and_extract,
                        (
                            {
                                "src_path": z,
                                "download_path": Path(tempfile.gettempdir())
                                / z.split("/")[-1],
                                "output_dir": output_dir,
                                "namespace": namespace_info,
                            }
                            for z in parts
                        ),
                    )
                )

            site.addsitedir(output_dir.as_posix())
            _LOG.info("added %s to sys.path", output_dir)

        fcntl.lockf(file, fcntl.LOCK_UN)


from geneva._context import get_current_context
from geneva.apply import CheckpointingApplier, ReadTask, ScanTask
from geneva.checkpoint import (
    CheckpointStore,
    InMemoryCheckpointStore,
)
from geneva.db import connect
from geneva.transformer import udf

__all__ = [
    "CheckpointStore",
    "connect",
    "InMemoryCheckpointStore",
    "CheckpointingApplier",
    "ReadTask",
    "ScanTask",
    "udf",
    "get_current_context",
]

version = "0.8.0"

__version__ = version

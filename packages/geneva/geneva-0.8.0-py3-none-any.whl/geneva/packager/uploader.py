# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import contextlib
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import attrs
import emoji
import pyarrow.fs as fs
from lance.file import LanceFileSession
from lance_namespace import DescribeTableRequest
from lance_namespace import connect as namespace_connect

from geneva.config import ConfigBase
from geneva.namespace import get_storage_options_provider
from geneva.tqdm import tqdm

_LOG = logging.getLogger(__name__)


@attrs.define
class Uploader(ConfigBase):
    """
    This class is used to upload files to a specified directory.

    Supports uploads via:
    - GCS optimized path (google.cloud.storage SDK) for gs:// URLs
    - LanceFileSession (with automatic multi-part upload) when namespace is available
    - PyArrow FileSystem as fallback

    Upload directories are automatically derived to be table-specific:
    - For namespace tables: {table_location}/_uploads
    - For local tables: {db_uri}/{table_name}.lance/_uploads
    """

    upload_dir: Optional[str] = attrs.field(default=None)
    namespace_impl: Optional[str] = attrs.field(default=None)
    namespace_properties: Optional[dict[str, str]] = attrs.field(default=None)
    table_id: Optional[list[str]] = attrs.field(default=None)
    db_uri: Optional[str] = attrs.field(default=None)

    def __attrs_post_init__(self) -> None:
        # Derive upload_dir to be table-specific
        if self.namespace_impl and self.namespace_properties and self.table_id:
            # Namespace table: get location from namespace
            namespace_client = namespace_connect(
                self.namespace_impl, self.namespace_properties
            )
            response = namespace_client.describe_table(
                DescribeTableRequest(id=self.table_id)
            )
            if response.location is None:
                raise ValueError(f"Table location is None for table {self.table_id}")

            # Set upload_dir to table-specific location
            self.upload_dir = f"{response.location.rstrip('/')}/_uploads"
            _LOG.info(f"Derived namespace table upload_dir: {self.upload_dir}")
        elif self.db_uri and self.table_id:
            # Local table: construct path from db_uri and table_name
            table_name = self.table_id[-1] if self.table_id else ""
            table_path = f"{self.db_uri.rstrip('/')}/{table_name}.lance"
            self.upload_dir = f"{table_path}/_uploads"
            _LOG.info(f"Derived local table upload_dir: {self.upload_dir}")
        elif self.upload_dir:
            # Remove trailing slash if present
            self.upload_dir = self.upload_dir.removesuffix("/")
        else:
            raise ValueError(
                "Either upload_dir must be provided, or table context "
                "(table_id + db_uri or namespace credentials) must be provided"
            )

    @classmethod
    def name(cls) -> str:
        return "uploader"

    @property
    def fs_and_path(self) -> tuple[fs.FileSystem, str]:
        assert self.upload_dir is not None, "upload_dir must be set"
        return fs.FileSystem.from_uri(self.upload_dir)

    def _upload_gcs(self, f: Path) -> str:
        """
        Upload to GCS -- dispatch here when we detect the dir is GCS
        Because the google client is much more performant than pyarrow
        """
        # optional dependency so don't import at the top
        from google.cloud import storage

        # we don't call this frequently so just create client on the fly
        storage_client = storage.Client()

        assert self.upload_dir is not None, "upload_dir must be set"
        path = self.upload_dir.removeprefix("gs://")
        bucket_name, destination_blob_prefix = path.split("/", 1)
        destination_blob_name = f"{destination_blob_prefix}/{f.name}"
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        # determine upload strategy
        # if the file is small enough, we can just upload it directly
        # otherwise we will upload in chunks
        # and then compose the chunks together
        # this lets us maximize upload bandwidth for large files
        if f.stat().st_size < 1024 * 1024 * 1024:  # 1GiB
            blob.upload_from_filename(f.as_posix())
        else:
            # we will upload in 32 chunks, which is the maximum number of
            # chunks allowed for composing blobs
            chunk_size = -(-f.stat().st_size // 32)

            pbar = tqdm(
                total=f.stat().st_size, unit="B", unit_scale=True, unit_divisor=1024
            )
            pbar.set_description(
                emoji.emojize(f":cloud: uploading {f.name:5.5} to {self.upload_dir}")
            )

            def _upload_part(idx: int) -> storage.Blob:
                start = idx * chunk_size
                end = min(start + chunk_size, f.stat().st_size)

                length = end - start
                part = bucket.blob(f"{destination_blob_name}-{idx}")
                with (
                    part.open("wb") as f_out,
                    open(f, "rb") as f_in,
                ):
                    f_in.seek(start)
                    while length:
                        read_size = min(length, 1024 * 64)
                        data = f_in.read(read_size)
                        f_out.write(data)  # type: ignore[arg-type]
                        length -= read_size
                        pbar.update(read_size)
                return part

            # int_divceil
            num_chunks = -(-f.stat().st_size // chunk_size)
            with ThreadPoolExecutor(max_workers=8) as executor:
                parts = executor.map(_upload_part, range(num_chunks))

            pbar.close()
            blob.compose(list(parts))

        return f"gs://{bucket_name}/{destination_blob_name}"

    def _file_exists(self, f: Path) -> bool:
        try:
            # Use GCS SDK for GCS
            if self.upload_dir and self.upload_dir.startswith("gs://"):
                from google.cloud import storage

                storage_client = storage.Client()
                path = self.upload_dir.removeprefix("gs://")
                bucket_name, prefix = path.split("/", 1)
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(f"{prefix}/{f.name}")
                return blob.exists()

            # Use LanceFileSession when namespace is available
            if (
                self.namespace_impl is not None
                and self.namespace_properties is not None
                and self.table_id is not None
            ):
                storage_options_provider, storage_options = (
                    get_storage_options_provider(
                        self.namespace_impl, self.namespace_properties, self.table_id
                    )
                )
                assert self.upload_dir is not None, "upload_dir must be set"
                session = LanceFileSession(
                    self.upload_dir,
                    storage_options=storage_options,
                    storage_options_provider=storage_options_provider,
                )
                return session.contains(f.name)

            # Fallback to PyArrow FileSystem
            handle, prefix = self.fs_and_path
            upload_path = str(Path(prefix) / f.name)
            return handle.get_file_info(upload_path).type == fs.FileType.File
        except Exception:
            _LOG.exception(f"Failed to check if file exists: {f.name}")
            return False

    def _upload_lance_session(self, f: Path) -> str:
        """
        Upload using LanceFileSession (with automatic multi-part upload support).

        This is used for non-GCS uploads when namespace credentials are available.
        """
        # Get storage options from namespace
        assert self.namespace_impl is not None, "namespace_impl must be set"
        assert self.namespace_properties is not None, "namespace_properties must be set"
        assert self.table_id is not None, "table_id must be set"
        assert self.upload_dir is not None, "upload_dir must be set"

        storage_options_provider, storage_options = get_storage_options_provider(
            self.namespace_impl, self.namespace_properties, self.table_id
        )
        # Create session
        session = LanceFileSession(
            self.upload_dir,
            storage_options=storage_options,
            storage_options_provider=storage_options_provider,
        )

        # Upload with progress bar
        with tqdm(
            total=f.stat().st_size, unit="B", unit_scale=True, unit_divisor=1024
        ) as pbar:
            pbar.set_description(
                emoji.emojize(f":cloud: uploading {f.name} to {self.upload_dir}")
            )

            # Upload the file - multi-part upload happens automatically for files > 5MB
            session.upload_file(str(f), f.name)  # type: ignore[attr-defined]
            pbar.update(f.stat().st_size)

        return f"{self.upload_dir}/{f.name}"

    def upload(self, f: Path) -> str:
        """
        Upload a file to the specified directory.

        The name of the object will be in the form of
        <path_to_upload_dir>/<name_of_file>
        """
        if self._file_exists(f):
            _LOG.debug(
                f"File {f.name} already exists in {self.upload_dir}, skipping upload"
            )
            return f"{self.upload_dir}/{f.name}"

        # GCS optimized path using google.cloud.storage SDK
        assert self.upload_dir is not None, "upload_dir must be set"
        if self.upload_dir.startswith("gs://"):
            return self._upload_gcs(f)

        # Use LanceFileSession for non-GCS uploads when namespace is available
        # This provides automatic multi-part upload and better credential management
        if (
            self.namespace_impl is not None
            and self.namespace_properties is not None
            and self.table_id is not None
        ):
            return self._upload_lance_session(f)

        # Fallback to PyArrow FileSystem
        handle, prefix = self.fs_and_path
        upload_path = str(Path(prefix) / f.name)

        # Create upload directory if it doesn't exist
        with contextlib.suppress(Exception):
            handle.create_dir(prefix, recursive=True)

        with (
            handle.open_output_stream(upload_path, buffer_size=1024 * 1024 * 64) as out,
            tqdm(
                total=f.stat().st_size, unit="B", unit_scale=True, unit_divisor=1024
            ) as pbar,
            f.open("rb") as f_in,
        ):
            pbar.set_description(
                emoji.emojize(f":cloud: uploading {f.name} to {self.upload_dir}")
            )
            chunk_size = 1024 * 1024 * 8  # 8MiB chunks

            while data := f_in.read(chunk_size):
                out.write(data)
                pbar.update(len(data))

        return f"{self.upload_dir}/{f.name}"

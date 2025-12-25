# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

# module for packaging workspace and UDFs
# also data spec for persisting the artifacts

import abc
import base64
import hashlib
import json
import logging
from pathlib import Path

import attrs
from lance.file import LanceFileSession
from lance.namespace import LanceNamespaceStorageOptionsProvider
from pyarrow.fs import FileSystem, FileType
from typing_extensions import Self

import geneva.cloudpickle as cloudpickle
from geneva.config import ConfigBase
from geneva.packager.zip import WorkspaceZipper
from geneva.transformer import UDF

_LOG = logging.getLogger(__name__)


class UDFBackend(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def packager(cls) -> "UDFPackager":
        """Return the packager for this backend."""

    def to_bytes(self) -> bytes:
        return json.dumps(attrs.asdict(self)).encode()

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        return cls(**json.loads(data.decode()))


@attrs.define
class UDFSpec:
    """Specification for a user-defined function.

    This is an holder of an arbitrary user-defined function,
    which can use an backend for marshalling.

    The most common is likely Docker + some kind of workspace
    persistence. However, we want to support more than just
    Docker, so we create this "out most" abstraction to allow
    for more flexibility.
    """

    # the name of the udf
    name: str = attrs.field()

    def __attrs_post_init__(self) -> None:
        if not self.name:
            raise ValueError("UDF name must not be empty.")
        if len(self.name) < 1:
            raise ValueError("UDF name must be at least 1 character long.")

        backend_names = [cls.__name__ for cls in UDFBackend.__subclasses__()]
        unique_backend_names = set(backend_names)
        if self.backend not in unique_backend_names:
            raise ValueError(f"Unknown backend: {self.backend}")

    # the packaging backend for the udf
    backend: str = attrs.field()

    udf_payload: bytes = attrs.field()

    # the payload for the runner -- This is a HACK for allowing phalanx knowing
    # how to dispatch the UDF job. Make sure changes here are compatible to
    # parsing in phalanx.
    runner_payload: bytes | None = attrs.field(default=None)

    @classmethod
    def udf_from_spec(cls, data) -> UDF:
        # TODO: load the spec and find the backend,
        # then call the packager to do the next level unmarshalling
        raise NotImplementedError("udf_from_spec not yet implemented")


@attrs.define
class DockerUDFSpecV1(UDFBackend):
    """Specification for a user-defined function that runs in a Docker container.
    -- Version 1

    In this packaging spec, the python interpreter is assumed to be correctly
    setup in the container, and the user-defined function is expected to load
    using cloudpickle. With the option of downloading additional workspace
    files from a remote location (S3, GCS, etc).
    """

    # the image to run the udf in
    image: str = attrs.field()

    # the tag of the image
    tag: str | None = attrs.field()

    # optionally have a zip of the workspace and store it separately
    # this should be the path to the zip file on (S3, GCS, etc)
    workspace_zip: str | None = attrs.field()

    # the checksum of the workspace zip
    workspace_checksum: str | None = attrs.field()

    # the udf pickle to run
    udf_pickle: bytes = attrs.field()

    # the checksum of the udf pickle
    udf_checksum: str = attrs.field(init=False)

    def __attrs_post_init__(self) -> None:
        # Validate tag
        if self.tag is not None:
            if len(self.tag) > 128:
                raise ValueError("Tag must be less than 128 characters.")
            if not all(
                c.isalpha() or c.isnumeric() or c in {"_", ".", "-"} for c in self.tag
            ):
                raise ValueError("Tag must be valid alphanumeric.")

        # Validate workspace checksum
        if self.workspace_zip and not self.workspace_checksum:
            raise ValueError(
                "Workspace checksum must not be empty when a workspace is provided."
            )

        # Validate UDF pickle
        if not self.udf_pickle:
            raise ValueError("UDF pickle must not be empty.")

        # Try to validate the UDF by unpickling, but don't fail if modules are missing
        # This supports distributed workflows where manifests are created in one
        # environment and used in another (e.g., uploaded by CI, used in notebooks)
        try:
            udf = cloudpickle.loads(self.udf_pickle)
            if not isinstance(udf, UDF):
                raise ValueError("UDF pickle must contain a UDF object.")
        except ModuleNotFoundError as e:
            _LOG.warning(
                f"Could not validate UDF pickle during spec loading: {e}. "
                "This is expected if the UDF was created in a different environment. "
                "Validation will happen when the UDF is executed on Ray workers."
            )

        self.udf_checksum = hashlib.sha256(self.udf_pickle).hexdigest()

    @classmethod
    def packager(cls) -> "UDFPackager":
        return DockerUDFPackager()

    def to_bytes(self) -> bytes:
        self_as_dict = attrs.asdict(self)
        self_as_dict["udf_pickle"] = base64.b64encode(
            self_as_dict["udf_pickle"]
        ).decode("utf-8")
        return json.dumps(self_as_dict).encode()

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        self_as_dict = json.loads(data.decode())
        self_as_dict["udf_pickle"] = base64.b64decode(
            self_as_dict["udf_pickle"].encode("utf-8")
        )

        checksum = self_as_dict.pop("udf_checksum")  # not part of the init
        val = cls(**self_as_dict)
        val.udf_checksum = checksum

        return val


class UDFPackager(abc.ABC):
    """Packager for user-defined functions."""

    @abc.abstractmethod
    def marshal(self, udf: UDF, table_ref=None) -> UDFSpec:
        """Marshal a user-defined function."""

    @abc.abstractmethod
    def unmarshal(self, spec: UDFSpec) -> UDF | None:
        """Unmarshal a user-defined function.

        Returns None if the UDF cannot be unpickled due to missing modules.
        """


@attrs.define
class _DockerUDFPackagerConfig(ConfigBase):
    prebuilt_docker_img: str | None = attrs.field(default=None)

    # the backend the image will eventually run on. Gets passed ot the
    # docker workspace packager it can know which base image/dockerfile
    # template to use
    runtime_backend: str | None = attrs.field(default=None)

    workspace_upload_location: str | None = attrs.field(default=None)

    @classmethod
    def name(cls) -> str:
        return "docker"


@attrs.define
class _UDFPackagerConfig(ConfigBase):
    docker: _DockerUDFPackagerConfig = attrs.field(default=_DockerUDFPackagerConfig())

    @classmethod
    def name(cls) -> str:
        return "udf"


@attrs.define
class DockerUDFPackager(UDFPackager):
    # If the user wants to use an prebuilt docker image, they can provide the
    # image name:tag here. This will be used instead of building and pushing a
    # new image.
    prebuilt_docker_img: str | None = attrs.field(default=None)

    # the location to upload the zipped workspace to
    # this should be the path to some directory on object storage (S3, GCS, etc)
    workspace_upload_location: str | None = attrs.field(default=None)

    # provide a zipper implementation with the correct configuration for how to
    # to zip the workspace. If workspace_zip is supplied and this is not, then
    # the packager will use the default WorkspaceZipper.
    zip_workspace_packager: WorkspaceZipper | None = attrs.field(default=None)

    def __attrs_post_init__(self) -> None:
        # Set default prebuilt_docker_img
        if self.prebuilt_docker_img is None:
            config = _UDFPackagerConfig.get()
            if config.docker is not None:
                self.prebuilt_docker_img = config.docker.prebuilt_docker_img

        # Set default workspace_upload_location
        if self.workspace_upload_location is None:
            config = _UDFPackagerConfig.get()
            if config.docker is not None:
                self.workspace_upload_location = config.docker.workspace_upload_location

        # Set default zip_workspace_packager
        if self.zip_workspace_packager is None and self.workspace_upload_location:
            self.zip_workspace_packager = WorkspaceZipper(path=Path("."))

    def marshal(self, udf: UDF, table_ref=None) -> UDFSpec:
        image_name, tag = "test-image", "latest"

        workspace_zip = None
        workspace_checksum = None
        if self.zip_workspace_packager:
            _LOG.info("Packaging zipped workspace")
            zip_path, checksum = self.zip_workspace_packager.zip()
            _LOG.info("Uploading zipped workspace")

            # Determine upload location - prefer table-specific location
            namespace_client = None
            storage_options = None
            if table_ref is not None:
                # Create table-specific upload location
                if namespace_client := table_ref.connect_namespace():
                    from lance_namespace import (
                        DescribeTableRequest,
                    )

                    response = namespace_client.describe_table(
                        DescribeTableRequest(id=table_ref.table_id)
                    )
                    if response.location is None:
                        raise ValueError(
                            f"Table location is None for table {table_ref.table_id}"
                        )
                    upload_location = f"{response.location.rstrip('/')}/_uploads"
                    storage_options = response.storage_options
                else:
                    # Local table - construct from db_uri
                    table_name = table_ref.table_id[-1] if table_ref.table_id else ""
                    table_path = f"{table_ref.db_uri.rstrip('/')}/{table_name}.lance"
                    upload_location = f"{table_path}/_uploads"
                _LOG.info(f"Using table-specific upload location: {upload_location}")
            else:
                # Fallback to packager-level workspace_upload_location
                upload_location = self.workspace_upload_location

            if upload_location is not None and upload_location[-1] != "/":
                upload_location += "/"

            if upload_location is None:
                raise ValueError(
                    "workspace_upload_location cannot be None "
                    "and table_ref was not provided"
                )

            # Check if file already exists and upload if needed
            if isinstance(zip_path, list):
                raise ValueError("zip_path should be a single Path, not a list")

            file_name = f"{checksum}.zip"

            # Use LanceFileSession for namespace tables, PyArrow FileSystem for others
            if namespace_client is not None and table_ref is not None:
                # Only set provider if namespace provides storage_options
                storage_options_provider = None
                if storage_options is not None:
                    storage_options_provider = LanceNamespaceStorageOptionsProvider(
                        namespace_client, table_ref.table_id
                    )
                session = LanceFileSession(
                    upload_location.rstrip("/"),
                    storage_options=storage_options,
                    storage_options_provider=storage_options_provider,
                )

                # Check if file exists
                if not session.contains(file_name):
                    dest = f"{upload_location}{file_name}"
                    _LOG.info(
                        f"Workspace zip does not exist, uploading {zip_path} to {dest}"
                    )
                    session.upload_file(str(zip_path), file_name)  # type: ignore[attr-defined]
                    _LOG.info(f"Uploaded workspace zip to {dest}")
                else:
                    _LOG.info("Workspace zip already exists, skipping upload")
            else:
                # Local table or no namespace - use PyArrow FileSystem
                remote_fs, root_path = FileSystem.from_uri(upload_location)
                out_path = f"{root_path}/{file_name}"
                curr_remote_file_info = remote_fs.get_file_info(out_path)
                if curr_remote_file_info.type == FileType.NotFound:
                    _LOG.info(f"Uploading workspace zip {zip_path} to {out_path}")
                    local_fs, _local_root = FileSystem.from_uri(
                        zip_path.absolute().parent.as_uri()
                    )

                    with (
                        local_fs.open_input_stream(str(zip_path)) as in_file,
                        remote_fs.open_output_stream(out_path) as out_file,
                    ):
                        bath_size = 1024 * 1024
                        while True:
                            buf = in_file.read(bath_size)
                            if buf:
                                out_file.write(buf)
                            else:
                                break

                    _LOG.info(f"Uploaded workspace zip to {out_path}")
                else:
                    _LOG.info("Workspace zip already exists, skipping upload")

            workspace_zip = f"{upload_location}{file_name}"
            workspace_checksum = checksum

        udf_pickle = cloudpickle.dumps(udf)

        return UDFSpec(
            name=udf.name,
            backend=DockerUDFSpecV1.__name__,
            udf_payload=DockerUDFSpecV1(
                image=image_name,
                tag=tag,
                workspace_zip=workspace_zip,
                workspace_checksum=workspace_checksum,
                udf_pickle=udf_pickle,
            ).to_bytes(),
            runner_payload=json.dumps(
                {
                    "image": image_name + ":" + tag,
                }
            ).encode(),
        )

    def unmarshal(self, spec: UDFSpec) -> UDF | None:
        """Unmarshal a UDF from a spec.

        Returns None if the UDF cannot be unpickled due to missing modules.
        This supports distributed workflows where manifests are created in one
        environment and used in another.
        """
        docker_spec = self.backend(spec)
        try:
            udf = cloudpickle.loads(docker_spec.udf_pickle)
            if not isinstance(udf, UDF):
                raise ValueError("UDF pickle must contain a UDF object.")
            return udf
        except ModuleNotFoundError as e:
            _LOG.warning(
                f"Cannot unmarshal UDF for validation: {e}. "
                "This is expected if the UDF was created in a different environment. "
                "Skipping client-side validation. The UDF will be executed on Ray "
                "workers where modules are available via py_modules in the manifest."
            )
            return None

    def backend(self, spec: UDFSpec) -> DockerUDFSpecV1:
        if spec.backend != DockerUDFSpecV1.__name__:
            raise ValueError("Invalid backend for UDF spec.")

        return DockerUDFSpecV1.from_bytes(spec.udf_payload)

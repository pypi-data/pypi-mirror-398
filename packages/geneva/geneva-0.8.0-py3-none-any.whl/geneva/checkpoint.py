# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""Checkpoint Store for Geneva Pipeline"""

import abc
import logging
import tempfile
from collections.abc import Iterator
from enum import Enum
from typing import TYPE_CHECKING, Optional

import attrs
import lance
import pyarrow as pa
from lance.file import LanceFileSession
from lance.namespace import LanceNamespaceStorageOptionsProvider
from lance_namespace import DescribeTableRequest
from packaging.version import Version

from geneva.config import ConfigBase
from geneva.utils import retry_lance

if TYPE_CHECKING:
    from lance_namespace import LanceNamespace

_LOG = logging.getLogger(__name__)


class CheckpointStore(abc.ABC):
    """Abstract class for checkpoint store, which is used to store intermediate results
      of Geneva pipelines.

    It is implemented as a key-value store of :class:`pyarrow.RecordBatch` objects.

    This is a lighter weight version of collections.abc.MutableMapping
    where we don't expose length or deletion operations

    TODO: implementations are not consistently handling keys with '/'.  Please avoid it.
    """

    @abc.abstractmethod
    def __contains__(self, item: str) -> bool:
        pass

    @abc.abstractmethod
    def __getitem__(self, item: str) -> pa.RecordBatch:
        pass

    @abc.abstractmethod
    def __setitem__(self, key: str, value: pa.RecordBatch) -> None:
        pass

    @abc.abstractmethod
    def list_keys(self, prefix: str = "") -> Iterator[str]:
        """List all the available keys for check point."""

    @abc.abstractmethod
    def uri(self) -> str:
        pass

    @classmethod
    def from_uri(cls, uri: str) -> "CheckpointStore":
        """Construct a CheckpointStore from a URI."""
        if uri == "memory":
            return InMemoryCheckpointStore()
        try:
            if Version(lance.__version__) < Version("0.35.0b3"):
                _LOG.warning(
                    f"pylance {lance.__version__} has issues at scale.  "
                    "Upgrade to 0.35.0b3 or higher to avoid this."
                )
            return LanceCheckpointStore(uri)
        except Exception as e:
            raise ValueError(f"Invalid checkpoint store uri: {uri}") from e


class InMemoryCheckpointStore(CheckpointStore):
    """In memory checkpoint store for testing purposes."""

    def __init__(self) -> None:
        self._store = {}

    def __repr__(self) -> str:
        return self._store.__repr__()

    def __contains__(self, item: str) -> bool:
        return item in self._store

    def __getitem__(self, item: str) -> pa.RecordBatch:
        return self._store[item]

    def __setitem__(self, key: str, value: pa.RecordBatch) -> None:
        self._store[key] = value

    def list_keys(self, prefix: str = "") -> Iterator[str]:
        for key in self._store:
            if key.startswith(prefix):
                yield key

    def uri(self) -> str:
        return "memory:///"


class LanceCheckpointStore(CheckpointStore):
    """
    Stores checkpoint data as Lance formatted files

    The API mimics a dictionary.

    NOTE: The dict keys are actual paths in a file system and can be vulnerable to
    filesystem traversal attacks.
    """

    def __init__(
        self,
        root: str,
        namespace_client: Optional["LanceNamespace"] = None,
        table_id: Optional[list[str]] = None,
    ) -> None:
        self.root = root
        self.namespace_client = namespace_client
        self.table_id = table_id

        # Lazy-initialized runtime state (avoid getting this pickled)
        self._session: Optional[LanceFileSession] = None

    def __getstate__(self) -> dict:
        """Exclude unpicklable session from pickle."""
        return {
            "root": self.root,
            "namespace_client": self.namespace_client,
            "table_id": self.table_id,
        }

    def __setstate__(self, state: dict) -> None:
        """Restore state from pickle, leaving session uninitialized."""
        self.root = state["root"]
        self.namespace_client = state.get("namespace_client")
        self.table_id = state.get("table_id")
        self._session = None

    @property
    def session(self) -> "LanceFileSession":
        """Lazily create LanceFileSession on first access."""
        if self._session is None:
            # Get storage options from namespace if available
            storage_options = None
            if self.namespace_client and self.table_id:
                response = self.namespace_client.describe_table(
                    DescribeTableRequest(id=self.table_id)
                )
                storage_options = response.storage_options

            # Only set storage_options_provider if namespace provides storage_options
            storage_options_provider = None
            if self.namespace_client and self.table_id and storage_options is not None:
                storage_options_provider = LanceNamespaceStorageOptionsProvider(
                    self.namespace_client, self.table_id
                )

            self._session = LanceFileSession(
                self.root,
                storage_options=storage_options,
                storage_options_provider=storage_options_provider,
            )
        return self._session

    @retry_lance
    def __contains__(self, key: str) -> bool:
        _LOG.debug("contains: %s", key)
        return self.session.contains(f"{key}.lance")

    @retry_lance
    def __getitem__(self, key: str) -> pa.RecordBatch:
        _LOG.debug("get: %s", key)
        reader = self.session.open_reader(f"{key}.lance")
        return reader.read_all().to_table().combine_chunks().to_batches()[0]

    @retry_lance
    def __setitem__(self, key: str, value: pa.RecordBatch) -> None:
        _LOG.debug("set: %s", key)
        with self.session.open_writer(f"{key}.lance", schema=value.schema) as writer:
            writer.write_batch(value)

    @retry_lance
    def list_keys(self, prefix: str = "") -> Iterator[str]:
        _LOG.debug("list_keys: %s", prefix)
        files = self.session.list(prefix if prefix else None)
        for file_path in files:
            if file_path.endswith(".lance"):
                yield file_path.rstrip(".lance")

    def uri(self) -> str:
        return self.root


class CheckpointMode(Enum):
    OBJECT_STORE = "object_store"

    # Store checkpoints in temporary files, for local development
    # and testing.
    # It can be shared between process, i.e., local ray actors.
    TEMPFILE = "tempfile"

    # for testing only
    IN_MEMORY = "in_memory"

    @staticmethod
    def from_str(s: str) -> "CheckpointMode":
        if isinstance(s, CheckpointMode):
            return s
        return CheckpointMode(s)


@attrs.define
class ObjectStoreCheckpointConfig(ConfigBase):
    path: str

    @classmethod
    def name(cls) -> str:
        return "object_store"

    def make(self) -> CheckpointStore:
        return LanceCheckpointStore(self.path)


@attrs.define
class CheckpointConfig(ConfigBase):
    mode: CheckpointMode = attrs.field(
        default=CheckpointMode.OBJECT_STORE, converter=CheckpointMode.from_str
    )

    object_store: ObjectStoreCheckpointConfig | None = attrs.field(default=None)

    @classmethod
    def name(cls) -> str:
        return "checkpoint"

    def make(self) -> CheckpointStore:
        match self.mode:
            case CheckpointMode.TEMPFILE:
                temp_dir = tempfile.mkdtemp()
                _LOG.info("Create checkpoint store on %s", temp_dir)
                return LanceCheckpointStore(temp_dir)
            case CheckpointMode.OBJECT_STORE:
                if self.object_store is None:
                    raise ValueError("CheckpointConfig::object_store is required")
                return LanceCheckpointStore(self.object_store.path)
            case CheckpointMode.IN_MEMORY:
                return InMemoryCheckpointStore()
            case _:
                raise ValueError(f"Unknown checkpoint mode {self.mode}")

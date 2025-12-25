# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors
import copy
import shutil
import tempfile
from unittest.mock import MagicMock

import lancedb
import pyarrow as pa
import pytest

from geneva.db import connect
from geneva.manifest.mgr import GenevaManifest
from geneva.table import TableReference


class TestNamespaceConnection:
    """Test namespace-based LanceDB connection."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_connect_namespace_dir(self) -> None:
        """Test connecting to Geneva through DirectoryNamespace."""
        # Connect using DirectoryNamespace
        props = {"root": self.temp_dir}
        db = lancedb.connect_namespace("dir", props)

        # Should be a LanceNamespaceDBConnection
        assert isinstance(db, lancedb.LanceNamespaceDBConnection)

        # Initially no tables
        assert len(list(db.table_names())) == 0

        # connect through geneva
        db = connect(namespace_impl="dir", namespace_properties=props)
        assert len(list(db.table_names())) == 0

        assert db.namespace_impl == "dir"
        assert db.namespace_properties == props
        assert len(list(db.table_names())) == 0
        assert isinstance(db._namespace_connection, lancedb.LanceNamespaceDBConnection)

    def test_open_table_through_namespace(self) -> None:
        """Test opening an existing table through namespace."""
        db = connect(namespace_impl="dir", namespace_properties={"root": self.temp_dir})

        # Create a table with schema
        schema = pa.schema(
            [
                pa.field("id", pa.int64()),
                pa.field("vector", pa.list_(pa.float32(), 2)),
            ]
        )
        db.create_table("test_table", schema=schema)

        # Open the table
        table = db.open_table("test_table")
        assert table is not None
        assert table.name == "test_table"

        # Verify empty table with correct schema
        result = table.to_pandas()
        assert len(result) == 0
        assert list(result.columns) == ["id", "vector"]

        assert len(db.list_manifests()) == 0

    def test_table_reference(self) -> None:
        props = {"root": self.temp_dir}
        ref = TableReference(
            table_id=["test_table"],
            version=None,
            db_uri=None,
            namespace_impl="dir",
            namespace_properties=props,
        )

        db = ref.open_db()

        assert db.namespace_impl == "dir"
        assert db.namespace_properties == props
        assert len(list(db.table_names())) == 0
        assert isinstance(db._namespace_connection, lancedb.LanceNamespaceDBConnection)
        assert ref.table_id == ["test_table"]
        assert ref.table_name == "test_table"

    @pytest.mark.slow
    def test_manifest_crud_with_namespace(self) -> None:
        """Test manifest CRUD operations with namespace connection."""
        # Create mock uploader to avoid actual file uploads
        mock_uploader = MagicMock()
        mock_uploader.upload_dir = "/mock/upload/dir"
        mock_uploader._file_exists.return_value = False
        mock_uploader.upload.side_effect = lambda path: f"mock://{path.name}"

        # Connect using namespace
        db = connect(namespace_impl="dir", namespace_properties={"root": self.temp_dir})

        # Verify manifest table will be created in the configured namespace
        assert db.namespace_impl == "dir"
        assert db.system_namespace == ["default"]  # Default system namespace

        # Create a manifest
        manifest_def = GenevaManifest(
            name="test-ns-manifest",
            local_zip_output_dir=self.temp_dir,
            skip_site_packages=False,
            delete_local_zips=False,
            pip=["numpy", "pandas"],
            py_modules=["pyarrow"],
        )

        # Test CREATE: define manifest
        db.define_manifest("test-ns-manifest", manifest_def, uploader=mock_uploader)

        # Verify upload was called
        upload_count = mock_uploader.upload.call_count
        assert upload_count >= 1, "files should have been uploaded"

        # Test READ: list manifests
        manifests = db.list_manifests()
        assert len(manifests) == 1, "should have exactly one manifest"
        m = manifests[0]
        _assert_manifest_eq(m.as_dict(), manifest_def.as_dict())
        assert m.name == "test-ns-manifest"
        assert m.pip == ["numpy", "pandas"]
        assert m.py_modules == ["pyarrow"]

        # Test UPDATE: update manifest and verify checksum changes
        manifest_def.skip_site_packages = True
        db.define_manifest("test-ns-manifest", manifest_def, uploader=mock_uploader)

        manifests = db.list_manifests()
        assert len(manifests) == 1, "should still have exactly one manifest"
        m1 = manifests[0].as_dict()
        m2 = manifest_def.as_dict()
        assert m1["checksum"] != m2["checksum"], "checksum should change after update"
        _assert_manifest_eq(m1, m2)
        assert mock_uploader.upload.call_count >= upload_count, (
            "more files should be uploaded"
        )

        # Test DELETE: delete manifest
        db.delete_manifest("test-ns-manifest")
        assert db.list_manifests() == [], "manifest should be deleted"

    def test_manifest_custom_namespace_config(self) -> None:
        """Test manifest with custom system namespace configuration."""
        mock_uploader = MagicMock()
        mock_uploader.upload_dir = "/mock/upload/dir"
        mock_uploader._file_exists.return_value = False
        mock_uploader.upload.side_effect = lambda path: f"mock://{path.name}"

        # Connect with custom system namespace
        db = connect(
            namespace_impl="dir",
            namespace_properties={"root": self.temp_dir},
            system_namespace=["custom", "namespace"],
        )

        # Verify custom configuration
        assert db.system_namespace == ["custom", "namespace"]

        # Create and verify manifest works with custom config
        manifest_def = GenevaManifest(
            name="custom-manifest",
            local_zip_output_dir=self.temp_dir,
            skip_site_packages=True,
            delete_local_zips=False,
            pip=["requests"],
        )

        db.define_manifest("custom-manifest", manifest_def, uploader=mock_uploader)

        # Verify manifest was created
        manifests = db.list_manifests()
        assert len(manifests) == 1
        assert manifests[0].name == "custom-manifest"
        assert manifests[0].pip == ["requests"]

        # Clean up
        db.delete_manifest("custom-manifest")
        assert db.list_manifests() == []


def _assert_manifest_eq(m1: dict, m2: dict) -> None:
    """Assert two manifest dicts are equal, excluding transient fields."""
    m1 = copy.deepcopy(m1)
    m2 = copy.deepcopy(m2)
    # exclude transient fields from comparison
    for f in {"checksum", "zips", "created_at", "created_by"}:
        if f in m1:
            del m1[f]
        if f in m2:
            del m2[f]
    assert m1 == m2, "manifests should match"

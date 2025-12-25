# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import copy
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from geneva import connect
from geneva.cluster.builder import default_image
from geneva.manifest.builder import GenevaManifestBuilder
from geneva.manifest.mgr import GenevaManifest


@pytest.mark.slow
def test_manifest_upload_location_namespace(tmp_path: Path) -> None:
    """Test manifest zips uploaded to correct location for namespace connections."""
    import pyarrow.fs as pafs
    from lance_namespace import DescribeTableRequest

    # Create a directory namespace connection with a system namespace
    system_ns = "test_system"
    db_root = tmp_path / "db"
    db_root.mkdir()

    # Create zip output directory
    zip_dir = tmp_path / "zips"
    zip_dir.mkdir()

    geneva = connect(
        namespace_impl="dir",
        namespace_properties={"root": str(db_root)},
        system_namespace=[system_ns],
    )

    manifest_def = GenevaManifest(
        name="test-manifest",
        local_zip_output_dir=str(zip_dir),
        skip_site_packages=True,  # Skip to make test faster
        delete_local_zips=False,
        pip=["numpy"],
    )

    # Define the manifest (this should upload zips)
    geneva.define_manifest("test-manifest", manifest_def)

    # Verify the manifest was created and has zips
    manifests = geneva.list_manifests()
    assert len(manifests) == 1
    manifest = manifests[0]
    assert len(manifest.zips) > 0, "Expected manifest to have uploaded zips"

    # Get the manifest table location from namespace
    assert geneva.namespace_client is not None
    from geneva.manifest.mgr import MANIFEST_TABLE_NAME

    table_id = [system_ns, MANIFEST_TABLE_NAME]
    response = geneva.namespace_client.describe_table(DescribeTableRequest(id=table_id))
    manifest_table_location = response.location
    assert manifest_table_location is not None

    # Expected upload directory should be {manifest_table_location}/_uploads
    expected_upload_dir = f"{manifest_table_location.rstrip('/')}/_uploads"

    # Verify that all uploaded zips are in the expected location
    for zip_path_list in manifest.zips:
        for zip_path in zip_path_list:
            # The zip path should start with the expected upload directory
            assert zip_path.startswith(expected_upload_dir), (
                f"Expected zip to be uploaded to {expected_upload_dir}, "
                f"but got {zip_path}"
            )

            # Verify the file actually exists at that location
            filesystem, path = pafs.FileSystem.from_uri(zip_path)
            file_info = filesystem.get_file_info(path)
            assert file_info.type == pafs.FileType.File, (
                f"Expected file to exist at {zip_path}"
            )


@pytest.mark.slow
def test_manifest_upload_location_local(tmp_path: Path) -> None:
    """Test manifest zips uploaded to correct location for local connections."""
    import pyarrow.fs as pafs

    # Create a local connection
    db_path = tmp_path / "db"

    # Create zip output directory
    zip_dir = tmp_path / "zips"
    zip_dir.mkdir()

    geneva = connect(db_path)

    manifest_def = GenevaManifest(
        name="test-manifest",
        local_zip_output_dir=str(tmp_path / "zips"),
        skip_site_packages=True,  # Skip to make test faster
        delete_local_zips=False,
        pip=["numpy"],
    )

    # Define the manifest (this should upload zips)
    geneva.define_manifest("test-manifest", manifest_def)

    # Verify the manifest was created and has zips
    manifests = geneva.list_manifests()
    assert len(manifests) == 1
    manifest = manifests[0]
    assert len(manifest.zips) > 0, "Expected manifest to have uploaded zips"

    # Verify upload directory is within the manifest table
    from geneva.manifest.mgr import MANIFEST_TABLE_NAME

    expected_upload_dir = f"{str(db_path)}/{MANIFEST_TABLE_NAME}.lance/_uploads"

    # Verify that all uploaded zips are in the expected location
    for zip_path_list in manifest.zips:
        for zip_path in zip_path_list:
            # The zip path should start with the expected upload directory
            assert zip_path.startswith(expected_upload_dir), (
                f"Expected zip to be uploaded to {expected_upload_dir}, "
                f"but got {zip_path}"
            )

            # Verify the file actually exists at that location
            filesystem, path = pafs.FileSystem.from_uri(zip_path)
            file_info = filesystem.get_file_info(path)
            assert file_info.type == pafs.FileType.File, (
                f"Expected file to exist at {zip_path}"
            )


@pytest.mark.slow
def test_manifest_crud(tmp_path: Path) -> None:
    mock_uploader = MagicMock()
    mock_uploader.upload_dir = "/mock/upload/dir"
    mock_uploader._file_exists.return_value = False
    mock_uploader.upload.side_effect = lambda path: f"mock://{path.name}"

    geneva = connect(tmp_path)

    manifest_def = GenevaManifest(
        name="test-manifest-1",
        local_zip_output_dir=str(tmp_path),
        skip_site_packages=False,
        delete_local_zips=False,
        pip=["numpy", "pandas"],
        py_modules=["pyarrow"],
    )

    # upload and create
    geneva.define_manifest("test-manifest-1", manifest_def, uploader=mock_uploader)
    m = geneva.list_manifests()[0]
    _assert_manifest_eq(m.as_dict(), manifest_def.as_dict())

    upload_count = mock_uploader.upload.call_count
    assert upload_count >= 1, "files were not uploaded"

    # update - should update metadata and upload new artifacts
    manifest_def.skip_site_packages = True
    geneva.define_manifest("test-manifest-1", manifest_def, uploader=mock_uploader)
    manifests = geneva.list_manifests()
    assert len(manifests) == 1, "expected single manifest"
    m1 = manifests[0].as_dict()
    m2 = manifest_def.as_dict()
    assert m1["checksum"] != m2["checksum"], "checksum should change"
    _assert_manifest_eq(m1, m2)
    assert mock_uploader.upload.call_count >= upload_count, "files were not uploaded"

    # delete
    geneva.delete_manifest("test-manifest-1")
    assert geneva.list_manifests() == []


def _assert_manifest_eq(m1: dict, m2: dict) -> bool:
    m1 = copy.deepcopy(m1)
    m2 = copy.deepcopy(m2)
    # exclude transient fields from comparison
    for f in {"checksum", "zips"}:
        if f in m1:
            del m1[f]
        if f in m2:
            del m2[f]
    assert m1 == m2, "manifests should match"


class TestGenevaManifestBuilder:
    """Test suite for GenevaManifestBuilder."""

    def test_builder_minimal(self) -> None:
        """Test minimal manifest creation with builder."""
        manifest = GenevaManifestBuilder.create("test-manifest").build()

        assert manifest.name == "test-manifest"
        assert manifest.version is None
        assert manifest.pip == []
        assert manifest.py_modules == []
        assert manifest.head_image is None
        assert manifest.skip_site_packages is False
        assert manifest.delete_local_zips is False
        assert manifest.local_zip_output_dir is None

    def test_builder_fluent_api(self) -> None:
        """Test fluent API chaining."""
        manifest = (
            GenevaManifestBuilder()
            .name("test-manifest")
            .version("1.0.0")
            .pip(["numpy", "pandas"])
            .py_modules(["mymodule", "othermodule"])
            .head_image("custom:latest")
            .worker_image("custom:latest2")
            .skip_site_packages(True)
            .delete_local_zips(True)
            .local_zip_output_dir("/foo/tmp/zips")
            .build()
        )

        assert manifest.name == "test-manifest"
        assert manifest.version == "1.0.0"
        assert manifest.pip == ["numpy", "pandas"]
        assert manifest.py_modules == ["mymodule", "othermodule"]
        assert manifest.head_image == "custom:latest"
        assert manifest.worker_image == "custom:latest2"
        assert manifest.skip_site_packages is True
        assert manifest.delete_local_zips is True
        assert manifest.local_zip_output_dir == "/foo/tmp/zips"

    def test_builder_add_methods(self) -> None:
        """Test add_pip and add_py_module methods."""
        manifest = (
            GenevaManifestBuilder.create("test-manifest")
            .add_pip("numpy")
            .add_pip("pandas")
            .add_py_module("mymodule")
            .add_py_module("othermodule")
            .build()
        )

        assert manifest.pip == ["numpy", "pandas"]
        assert manifest.py_modules == ["mymodule", "othermodule"]

    def test_builder_list_immutability(self) -> None:
        """Test that lists are copied and not shared."""
        original_pip = ["numpy", "pandas"]
        original_modules = ["mymodule"]

        manifest1 = (
            GenevaManifestBuilder.create("manifest1")
            .pip(original_pip)
            .py_modules(original_modules)
            .build()
        )

        # Modify original lists
        original_pip.append("scipy")
        original_modules.append("othermodule")

        # Manifest should not be affected
        assert manifest1.pip == ["numpy", "pandas"]
        assert manifest1.py_modules == ["mymodule"]

        # Create another manifest with the same builder pattern
        manifest2 = (
            GenevaManifestBuilder.create("manifest2")
            .pip(original_pip)
            .py_modules(original_modules)
            .build()
        )

        # This manifest should have the modified lists
        assert manifest2.pip == ["numpy", "pandas", "scipy"]
        assert manifest2.py_modules == ["mymodule", "othermodule"]

    def test_builder_requires_name(self) -> None:
        """Test that builder requires a name."""
        with pytest.raises(ValueError, match="Manifest name is required"):
            GenevaManifestBuilder().build()

    def test_builder_class_method_create(self) -> None:
        """Test create class method."""
        manifest = GenevaManifestBuilder.create("created-manifest").build()

        assert manifest.name == "created-manifest"

    def test_builder_with_real_manifest_compatibility(self) -> None:
        """Test that builder creates manifests compatible with existing code."""
        # Create with builder
        built_manifest = (
            GenevaManifestBuilder.create("test-builder")
            .pip(["numpy", "pandas"])
            .py_modules(["pyarrow"])
            .skip_site_packages(True)
            .build()
        )

        # Create traditionally
        traditional_manifest = GenevaManifest(
            name="test-traditional",
            pip=["numpy", "pandas"],
            py_modules=["pyarrow"],
            skip_site_packages=True,
        )

        # Both should have same structure (excluding name and auto-generated fields)
        built_dict = built_manifest.as_dict()
        traditional_dict = traditional_manifest.as_dict()

        # Remove name and other varying fields for comparison
        for d in [built_dict, traditional_dict]:
            del d["name"]
            del d["checksum"]
            del d["created_at"]
            del d["created_by"]

        assert built_dict == traditional_dict

    def test_builder_version_handling(self) -> None:
        """Test version field handling."""
        manifest_with_version = (
            GenevaManifestBuilder.create("versioned").version("2.1.0").build()
        )

        manifest_without_version = GenevaManifestBuilder.create("unversioned").build()

        assert manifest_with_version.version == "2.1.0"
        assert manifest_without_version.version is None

    def test_builder_boolean_flags(self) -> None:
        """Test boolean flag methods."""
        # Test explicit True
        manifest1 = (
            GenevaManifestBuilder.create("test1")
            .skip_site_packages(True)
            .delete_local_zips(True)
            .build()
        )

        # Test explicit False
        manifest2 = (
            GenevaManifestBuilder.create("test2")
            .skip_site_packages(False)
            .delete_local_zips(False)
            .build()
        )

        # Test default (True)
        manifest3 = (
            GenevaManifestBuilder.create("test3")
            .skip_site_packages()
            .delete_local_zips()
            .build()
        )

        assert manifest1.skip_site_packages is True
        assert manifest1.delete_local_zips is True
        assert manifest2.skip_site_packages is False
        assert manifest2.delete_local_zips is False
        assert manifest3.skip_site_packages is True
        assert manifest3.delete_local_zips is True

    def test_default_image(self) -> None:
        m = (
            GenevaManifestBuilder.create("foo")
            .default_head_image()
            .default_worker_image()
            .build()
        )
        assert m.head_image == default_image()
        assert m.worker_image == default_image()

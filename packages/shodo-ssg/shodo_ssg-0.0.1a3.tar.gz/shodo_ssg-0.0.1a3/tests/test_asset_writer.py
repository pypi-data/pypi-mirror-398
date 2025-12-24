"""Tests for the asset_writer module."""

import os
import shutil
from shodo_ssg.asset_writer import (
    BaseAssetWriter,
    FaviconWriter,
    AssetWriter,
    RootFilesWriter,
    ScriptWriter,
    CSSWriter,
)


def test_base_asset_writer_write(settings_dict):
    """Test the write method of the base BaseAssetWriter Class"""
    dest_path = settings_dict["build_dir"] + "/favicon.ico"

    asset_writer = BaseAssetWriter(settings_dict["favicon_path"], dest_path)

    if not os.path.exists(settings_dict["build_dir"]):
        # Make the dist directory if it doesn't exist
        os.makedirs(settings_dict["build_dir"])

    if os.path.exists(dest_path):
        os.remove(dest_path)
        assert not os.path.exists(dest_path)

    asset_writer.write()

    assert os.path.exists(dest_path)
    assert os.path.isfile(dest_path)


def test_favicon_writer_write(settings_dict):
    """Test the write method of the FaviconWriter class."""
    favicon_writer = FaviconWriter(settings_dict)

    dest_path = settings_dict["build_dir"] + "/favicon.ico"

    if not os.path.exists(settings_dict["build_dir"]):
        # Make the dist directory if it doesn't exist
        os.makedirs(settings_dict["build_dir"])

    if os.path.exists(dest_path):
        os.remove(dest_path)
        assert not os.path.exists(dest_path)

    favicon_writer.write()

    assert os.path.exists(dest_path)
    assert os.path.isfile(dest_path)


def test_script_writer_write(settings_dict):
    """Test the write method of the ScriptWriter class."""
    script_writer = ScriptWriter(settings_dict)

    dest_path = settings_dict["build_dir"] + "/static/scripts"

    if not os.path.exists(settings_dict["build_dir"]):
        # Make the dist directory if it doesn't exist
        os.makedirs(settings_dict["build_dir"])

    if os.path.exists(dest_path):
        shutil.rmtree(dest_path)
        assert not os.path.exists(dest_path)

    script_writer.write()

    assert os.path.exists(dest_path)
    assert os.path.isdir(dest_path)


def test_css_writer_write(settings_dict):
    """Test the write method of the CSS writer class"""
    css_writer = CSSWriter(settings_dict)

    dest_path = settings_dict["build_dir"] + "/static/styles"

    if not os.path.exists(settings_dict["build_dir"]):
        # Make the dist directory if it doesn't exist
        os.makedirs(settings_dict["build_dir"])

    if os.path.exists(dest_path):
        shutil.rmtree(dest_path)
        assert not os.path.exists(dest_path)

    css_writer.write()

    assert os.path.exists(dest_path)
    assert os.path.isdir(dest_path)


def test_asset_writer_write(settings_dict):
    """Test the write method of the AssetWriter class"""
    asset_writer = AssetWriter(settings_dict)

    dest_path = settings_dict["build_dir"] + "/static/assets"

    if not os.path.exists(settings_dict["build_dir"]):
        # Make the dist directory if it doesn't exist
        os.makedirs(settings_dict["build_dir"])

    if os.path.exists(dest_path):
        shutil.rmtree(dest_path)
        assert not os.path.exists(dest_path)

    asset_writer.write()

    assert os.path.exists(dest_path)
    assert os.path.isdir(dest_path)


def test_root_files_writer_write(settings_dict):
    """Test the write method of the RootFilesWriter class"""
    root_files_writer = RootFilesWriter(settings_dict)
    dest_path = settings_dict["build_dir"]
    if not os.path.exists(settings_dict["build_dir"]):
        # Make the dist directory if it doesn't exist
        os.makedirs(settings_dict["build_dir"])
    # Create a test file in the source root files path
    test_file_src = os.path.join(settings_dict["root_files_path"], "test_root_file.txt")
    os.makedirs(settings_dict["root_files_path"], exist_ok=True)
    with open(test_file_src, "w", encoding="utf-8") as f:
        f.write("This is a test root file.")
    test_file_dest = os.path.join(dest_path, "test_root_file.txt")
    if os.path.exists(test_file_dest):
        os.remove(test_file_dest)
        assert not os.path.exists(test_file_dest)

    root_files_writer.write()

    assert os.path.exists(test_file_dest)
    assert os.path.isfile(test_file_dest)

"""Tests for the static_site_generator module."""

import os
import shutil
from shodo_ssg.static_site_generator import StaticSiteGenerator
from tests.build_validation import (
    css_exist_in_build_dir,
    favicon_exists_in_build_dir,
    images_exist_in_build_dir,
    linked_template_pages_exist_in_build_dir,
    markdown_pages_exist_in_build_dir,
    scripts_exist_in_build_dir,
)


def test_static_site_generator_init(
    static_site_generator_deps,
):  # pylint: disable=redefined-outer-name
    """Test the initialization of the StaticSiteGenerator class."""
    template_handler, asset_handler = static_site_generator_deps
    static_site_generator = StaticSiteGenerator(template_handler, asset_handler)
    assert static_site_generator.template_handler == template_handler
    assert static_site_generator.asset_handler == asset_handler
    assert static_site_generator.build_dir == template_handler.build_dir
    assert static_site_generator.root_path == template_handler.root_path


def test_static_site_generator_get_build_dir_path(
    static_site_generator_deps,
):  # pylint: disable=redefined-outer-name
    """Test the get_build_dir_path method of the StaticSiteGenerator class."""
    template_handler, asset_handler = static_site_generator_deps
    static_site_generator = StaticSiteGenerator(template_handler, asset_handler)
    assert static_site_generator.get_build_dir_path().startswith(
        template_handler.root_path
    )
    assert static_site_generator.get_build_dir_path() == os.path.abspath(
        template_handler.build_dir
    )


def test_static_site_generator_get_build_dir_relative_path(
    static_site_generator_deps,
):  # pylint: disable=redefined-outer-name
    """Test the get_build_dir_path method of the StaticSiteGenerator class with a relative path."""
    template_handler, asset_handler = static_site_generator_deps
    static_site_generator = StaticSiteGenerator(template_handler, asset_handler)
    static_site_generator.build_dir = "dist"
    assert static_site_generator.get_build_dir_path().startswith(
        template_handler.root_path
    )
    assert static_site_generator.get_build_dir_path() == os.path.abspath(
        os.path.join(template_handler.root_path, "dist")
    )


def test_static_site_generator_get_build_dir_absolute_path(
    static_site_generator_deps,
):  # pylint: disable=redefined-outer-name
    """Test the get_build_dir_path method of the StaticSiteGenerator class with an absolute path."""
    template_handler, asset_handler = static_site_generator_deps
    static_site_generator = StaticSiteGenerator(template_handler, asset_handler)
    static_site_generator.build_dir = os.path.join(template_handler.root_path, "dist")
    assert static_site_generator.get_build_dir_path().startswith(
        template_handler.root_path
    )
    assert static_site_generator.get_build_dir_path() == os.path.abspath(
        os.path.join(template_handler.root_path, "dist")
    )


def test_static_site_generator_clear_build_dir(
    static_site_generator_deps,
):  # pylint: disable=redefined-outer-name
    """Test the clear_build_dir method of the StaticSiteGenerator class."""
    template_handler, asset_handler = static_site_generator_deps
    static_site_generator = StaticSiteGenerator(template_handler, asset_handler)
    build_path = static_site_generator.get_build_dir_path()
    if not os.path.exists(build_path):
        os.makedirs(build_path)
    assert os.path.exists(build_path)
    static_site_generator.clear_build_dir()
    assert not os.path.exists(static_site_generator.get_build_dir_path())


def test_static_site_generator_clear_build_dir_no_dir(
    static_site_generator_deps,
):  # pylint: disable=redefined-outer-name
    """Test the clear_build_dir method of the StaticSiteGenerator class with no directory."""
    template_handler, asset_handler = static_site_generator_deps
    static_site_generator = StaticSiteGenerator(template_handler, asset_handler)
    build_path = static_site_generator.get_build_dir_path()
    if os.path.exists(build_path):
        shutil.rmtree(build_path)
    assert not os.path.exists(build_path)
    static_site_generator.clear_build_dir()
    assert not os.path.exists(build_path)


def test_static_site_generator_refresh_and_create_new_build_dir(
    static_site_generator_deps,
):  # pylint: disable=redefined-outer-name
    """Test the refresh_and_create_new_build_dir method of the StaticSiteGenerator class."""
    template_handler, asset_handler = static_site_generator_deps
    static_site_generator = StaticSiteGenerator(template_handler, asset_handler)
    build_path = static_site_generator.get_build_dir_path()
    test_file = os.path.join(build_path, "test.txt")
    static_site_generator.refresh_and_create_new_build_dir()
    assert os.path.exists(build_path)
    assert not os.listdir(build_path)
    assert os.path.isdir(build_path)
    assert not os.path.exists(test_file)
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("test")
    assert os.path.exists(test_file)
    static_site_generator.refresh_and_create_new_build_dir()
    assert not os.path.exists(test_file)
    assert os.path.exists(build_path)
    assert not os.listdir(build_path)
    assert os.path.isdir(build_path)


def test_static_site_generator_build(
    static_site_generator_deps,
    settings_dict,
):  # pylint: disable=redefined-outer-name
    """Test the build method of the StaticSiteGenerator class."""
    template_handler, asset_handler = static_site_generator_deps
    static_site_generator = StaticSiteGenerator(template_handler, asset_handler)
    build_path = static_site_generator.get_build_dir_path()
    test_file = os.path.join(build_path, "test.txt")
    if not os.path.exists(build_path):
        os.makedirs(build_path)
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("test")
    assert os.path.exists(test_file)
    static_site_generator.build()
    assert os.path.exists(build_path)
    assert os.listdir(build_path)
    assert os.path.isdir(build_path)
    assert not os.path.exists(test_file)
    assert os.path.exists(os.path.join(build_path, "index.html"))
    assert linked_template_pages_exist_in_build_dir(
        build_path, settings_dict["template_paths"]
    )
    assert markdown_pages_exist_in_build_dir(
        build_path, template_handler.context.md_pages
    )
    assert scripts_exist_in_build_dir(build_path)
    assert css_exist_in_build_dir(build_path)
    assert images_exist_in_build_dir(build_path)
    assert favicon_exists_in_build_dir(build_path)

"""Tests for the assembler module."""

import os
import shutil
from shodo_ssg.assembler import (
    load_settings,
    initialize_components,
    generate_site,
    build_static_site,
)
from shodo_ssg.template_handler import TemplateHandler
from shodo_ssg.asset_writer import AssetHandler
from tests.build_validation import (
    css_exist_in_build_dir,
    favicon_exists_in_build_dir,
    images_exist_in_build_dir,
    linked_template_pages_exist_in_build_dir,
    markdown_pages_exist_in_build_dir,
    scripts_exist_in_build_dir,
)


def test_load_settings(temp_project_path, settings_dict):
    """Test the load_settings function."""
    temp_abs_path = os.path.abspath(temp_project_path)
    data = load_settings(temp_abs_path)

    assert isinstance(data, dict)
    assert os.path.abspath(data["build_dir"]) == os.path.abspath(
        settings_dict["build_dir"]
    )
    assert data["markdown_path"] == settings_dict["markdown_path"]
    assert data["json_config_path"] == settings_dict["json_config_path"]
    assert data["favicon_path"] == settings_dict["favicon_path"]
    assert data["scripts_path"] == settings_dict["scripts_path"]
    assert data["assets_path"] == settings_dict["assets_path"]
    assert data["styles_path"] == settings_dict["styles_path"]
    assert set(data["template_paths"]) == set(settings_dict["template_paths"])


def test_initialize_components(settings_dict, static_site_generator_deps):
    """Test the initialize_components function."""
    template_handler = static_site_generator_deps[0]
    components = initialize_components(settings_dict)

    assert isinstance(components, tuple)
    assert isinstance(components[0], TemplateHandler)
    assert isinstance(components[1], AssetHandler)

    assert components[0].build_dir == template_handler.build_dir
    assert components[0].root_path == template_handler.root_path
    assert len(components[0].context.md_pages) == len(template_handler.context.md_pages)
    assert set(components[0].context.render_args.keys()) == set(
        template_handler.context.render_args.keys()
    )
    assert components[0].context.markdown_loader
    assert components[0].context.json_loader
    assert components[1].favicon
    assert components[1].scripts
    assert components[1].assets
    assert components[1].styles


def test_generate_site(static_site_generator_deps, settings_dict):
    """Test the generate_site function"""
    template_handler, asset_handler = static_site_generator_deps
    build_path = os.path.abspath(settings_dict["build_dir"])

    if os.path.exists(build_path):
        shutil.rmtree(build_path)
    assert not os.path.exists(build_path)

    generate_site(template_handler, asset_handler)

    assert os.path.exists(build_path)
    assert os.listdir(build_path)
    assert os.path.isdir(build_path)
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


def test_build_static_site(temp_project_path, template_handler_dependencies):
    """Test the build_static_site function"""
    tmp_proj_root = os.path.abspath(temp_project_path)
    settings, root_layout_builder, pagination_handler, api = (
        template_handler_dependencies
    )
    template_handler = TemplateHandler(
        settings, root_layout_builder, pagination_handler, api
    )
    build_path = os.path.abspath(settings["build_dir"])

    if os.path.exists(build_path):
        shutil.rmtree(build_path)
    assert not os.path.exists(build_path)

    build_static_site(tmp_proj_root)

    assert os.path.exists(build_path)
    assert os.listdir(build_path)
    assert os.path.isdir(build_path)
    assert os.path.exists(os.path.join(build_path, "index.html"))
    assert linked_template_pages_exist_in_build_dir(
        build_path, settings["template_paths"]
    )
    assert markdown_pages_exist_in_build_dir(
        build_path, template_handler.context.md_pages
    )
    assert scripts_exist_in_build_dir(build_path)
    assert css_exist_in_build_dir(build_path)
    assert images_exist_in_build_dir(build_path)
    assert favicon_exists_in_build_dir(build_path)


def test_build_static_site_paginates_articles(
    temp_project_path, template_handler_dependencies
):
    """Test that build_static_site paginates articles correctly."""
    tmp_proj_root = os.path.abspath(temp_project_path)
    settings, _root_layout_builder, _pagination_handler, _api = (
        template_handler_dependencies
    )

    build_path = os.path.abspath(settings["build_dir"])

    if os.path.exists(build_path):
        shutil.rmtree(build_path)
    assert not os.path.exists(build_path)

    build_static_site(tmp_proj_root)

    # Check that paginated article pages exist
    articles_page_1 = os.path.join(build_path, "blog", "index.html")
    articles_page_2 = os.path.join(build_path, "blog", "page", "2", "index.html")

    assert os.path.exists(articles_page_1)
    assert os.path.exists(articles_page_2)
    assert os.path.isdir(os.path.join(build_path, "blog", "page", "2"))
    assert os.path.isfile(articles_page_1)
    assert os.path.isfile(articles_page_2)


def test_build_static_site_paginates_items_from_json_store(
    temp_project_path, template_handler_dependencies
):
    """Test that build_static_site paginates json data correctly."""
    tmp_proj_root = os.path.abspath(temp_project_path)
    settings, _root_layout_builder, _pagination_handler, _api = (
        template_handler_dependencies
    )

    build_path = os.path.abspath(settings["build_dir"])

    if os.path.exists(build_path):
        shutil.rmtree(build_path)
    assert not os.path.exists(build_path)

    build_static_site(tmp_proj_root)

    # Check that paginated article pages exist
    items_page_1 = os.path.join(build_path, "items", "index.html")
    items_page_2 = os.path.join(build_path, "items", "page", "2", "index.html")
    items_page_3 = os.path.join(build_path, "items", "page", "3", "index.html")

    assert os.path.exists(items_page_1)
    assert os.path.exists(items_page_2)
    assert os.path.exists(items_page_3)
    assert os.path.isdir(os.path.join(build_path, "items", "page", "2"))
    assert os.path.isdir(os.path.join(build_path, "items", "page", "3"))
    assert os.path.isfile(items_page_1)
    assert os.path.isfile(items_page_2)
    assert os.path.isfile(items_page_3)


def test_abs_urls_in_rss_final_build(
    temp_project_path,
    template_handler_dependencies,
):
    """Test that all URLs in the RSS feed are absolute in the final build."""
    tmp_proj_root = os.path.abspath(temp_project_path)
    settings, _root_layout_builder, _pagination_handler, _api = (
        template_handler_dependencies
    )

    build_path = os.path.abspath(settings["build_dir"])

    if os.path.exists(build_path):
        shutil.rmtree(build_path)
    assert not os.path.exists(build_path)

    build_static_site(tmp_proj_root)

    rss_feed_path = os.path.join(build_path, "feed.xml")
    assert os.path.exists(rss_feed_path)

    with open(rss_feed_path, "r", encoding="utf-8") as f:
        rss_content = f.read()

    # Check that all URLs in the RSS feed are absolute
    assert '<a href="https://shodo.dev/' in rss_content
    assert '<a href="/' not in rss_content
    assert 'src="/' not in rss_content


def test_root_files_writer_write_merges_data_when_directory_exists_in_final_build(
    temp_project_path, template_handler_dependencies
):
    """Test the write method of the RootFilesWriter class when directory exists in destination."""
    tmp_proj_root = os.path.abspath(temp_project_path)
    settings, _root_layout_builder, _pagination_handler, _api = (
        template_handler_dependencies
    )

    build_path = os.path.abspath(settings["build_dir"])

    if os.path.exists(build_path):
        shutil.rmtree(build_path)
    assert not os.path.exists(build_path)

    build_static_site(tmp_proj_root)

    # There should be two files in the fonts directory after merging
    fonts_dir = os.path.join(build_path, "static", "assets", "fonts")
    assert os.path.exists(fonts_dir)
    assert os.path.isdir(fonts_dir)
    merged_files = os.listdir(fonts_dir)
    assert "pretend-font.txt" in merged_files
    assert "another-font.txt" in merged_files

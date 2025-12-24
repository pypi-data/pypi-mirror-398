"""Tests for the template_handler module."""

import os
from shodo_ssg.template_handler import TemplateHandler
from tests.build_validation import get_linked_page_relative_build_paths


def test_template_handler_init(
    template_handler_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the __init__ method of the TemplateHandler class."""
    settings, root_layout_builder, pagination_handler, api = (
        template_handler_dependencies
    )
    template_handler = TemplateHandler(
        settings, root_layout_builder, pagination_handler, api
    )

    assert template_handler.template_env
    assert template_handler.build_dir
    assert template_handler.root_path
    assert template_handler.context
    assert template_handler.api


def test_template_handler_get_template(
    template_handler_dependencies,
    temp_project_path,
    settings_dict,
):  # pylint: disable=redefined-outer-name
    """Test the get_template method of the TemplateHandler class."""
    settings, root_layout_builder, pagination_handler, api = (
        template_handler_dependencies
    )
    template_handler = TemplateHandler(
        settings, root_layout_builder, pagination_handler, api
    )

    view_path = os.path.join(temp_project_path, settings_dict["root_template_paths"][0])

    template_name = "hello_world.jinja"
    template_contents = "<div>Hello, World!</div>"
    template_path = os.path.join(view_path, template_name)

    with open(template_path, "w", encoding="utf-8") as template_file:
        template_file.write(template_contents)

    assert template_handler.get_template(template_name)
    assert template_handler.get_template(template_name).name == template_name
    assert hasattr(template_handler.get_template(template_name), "render")
    rendered_template = template_handler.get_template(template_name).render()
    assert isinstance(rendered_template, str)
    assert rendered_template == template_contents


def test_template_handler_write_home_template(
    template_handler_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the write_home_template method of the TemplateHandler class."""
    settings, root_layout_builder, pagination_handler, api = (
        template_handler_dependencies
    )
    template_handler = TemplateHandler(
        settings, root_layout_builder, pagination_handler, api
    )

    if not os.path.exists(template_handler.build_dir):
        os.makedirs(template_handler.build_dir)

    template_handler.write_home_template()

    assert os.path.exists(f"{template_handler.build_dir}/index.html")
    with open(
        f"{template_handler.build_dir}/index.html", "r", encoding="utf-8"
    ) as index_file:
        index_contents = index_file.read()
    assert index_contents
    assert "<!DOCTYPE html>" in index_contents


def test_template_handler_write_linked_template_pages(
    template_handler_dependencies,
    settings_dict,
):  # pylint: disable=redefined-outer-name
    """Test the write_linked_template_pages method of the TemplateHandler class."""
    settings, root_layout_builder, pagination_handler, api = (
        template_handler_dependencies
    )
    template_handler = TemplateHandler(
        settings, root_layout_builder, pagination_handler, api
    )

    # Get the source paths for the linked page directories
    linked_page_paths = get_linked_page_relative_build_paths(
        settings_dict["template_paths"]
    )

    # Make sure the build directory exists
    if not os.path.exists(template_handler.build_dir):
        os.makedirs(template_handler.build_dir)

    # Ensure the template functions are defined
    # pylint: disable=protected-access
    template_handler._pass_global_template_functions(
        [
            template_handler.api.shodo_get_articles,
            template_handler.api.shodo_query_store,
            template_handler.api.shodo_get_excerpt,
            template_handler.api.get_rfc822,
            template_handler.api.rel_to_abs,
            template_handler.api.current_dt,
        ]
    )

    template_handler.write_linked_template_pages()

    for path in linked_page_paths:
        if not path.endswith(".xml"):
            assert os.path.exists(f"{template_handler.build_dir}/{path}/index.html")
            with open(
                f"{template_handler.build_dir}/{path}/index.html", "r", encoding="utf-8"
            ) as page_file:
                page_contents = page_file.read()
            assert page_contents
            assert "<!DOCTYPE html>" in page_contents
        else:
            # Feed was marked with <file_type: "xml">, just check that the xml file exists
            assert os.path.exists(f"{template_handler.build_dir}/{path}")


def test_template_handler_get_front_matter_returns_front_matter_from_file(
    template_handler_dependencies, temp_project_path, settings_dict
):  # pylint: disable=redefined-outer-name
    """Test the get_front_matter method of the TemplateHandler class."""
    settings, root_layout_builder, pagination_handler, api = (
        template_handler_dependencies
    )
    template_handler = TemplateHandler(
        settings, root_layout_builder, pagination_handler, api
    )

    test_article_path = os.path.join(
        temp_project_path, settings_dict["markdown_path"], "articles/test_dir/"
    )
    test_article_name = "test_article.md"

    content = "@frontmatter\n"
    content += '{"title": "Test Article",\n"description": "This is a test article."}\n'
    content += "@endfrontmatter\n"
    content += "This is the content of the test article.\n"

    # Create a test article md file with front matter
    os.mkdir(test_article_path)
    with open(
        os.path.join(test_article_path, test_article_name), "w", encoding="utf-8"
    ) as article_file:
        article_file.write(content)

    front_matter = template_handler.get_front_matter(
        os.path.join(test_article_path, test_article_name)
    )

    assert front_matter
    assert isinstance(front_matter, dict)
    assert "title" in front_matter
    assert "description" in front_matter
    assert front_matter["title"] == "Test Article"
    assert front_matter["description"] == "This is a test article."
    for key in front_matter:
        assert front_matter[key] != "This is the content of the test article."


def test_template_handler_write_article_pages(
    template_handler_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the write_article_pages method of the TemplateHandler class."""
    settings, root_layout_builder, pagination_handler, api = (
        template_handler_dependencies
    )
    template_handler = TemplateHandler(
        settings, root_layout_builder, pagination_handler, api
    )

    if not os.path.exists(template_handler.build_dir):
        os.makedirs(template_handler.build_dir)

    template_handler.write_article_pages()

    for md_page in template_handler.context.md_pages:
        build_path = os.path.join(
            template_handler.build_dir,
            md_page["url_segment"].strip("/"),
            md_page["name"].strip("/"),
        )
        assert os.path.exists(build_path)
        assert os.path.exists(f"{build_path}/index.html")
        with open(f"{build_path}/index.html", "r", encoding="utf-8") as page_file:
            page_contents = page_file.read()
        assert page_contents
        assert "<!DOCTYPE html>" in page_contents
        assert (
            template_handler.context.front_matter_processor.clear_front_matter(
                file_path=None, content=md_page["html"]
            )
            in page_contents
        )


def test_template_handler_get_md_layout_template_defaults_to_root_layout(
    template_handler_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the get_md_layout_template method of the TemplateHandler class."""
    settings, root_layout_builder, pagination_handler, api = (
        template_handler_dependencies
    )
    template_handler = TemplateHandler(
        settings, root_layout_builder, pagination_handler, api
    )

    url_segment = "test_url_segment"

    assert template_handler.get_md_layout_template(url_segment)
    assert (
        template_handler.get_md_layout_template(url_segment) == "articles/layout.jinja"
    )


def test_template_handler_get_md_layout_template_returns_matching_layout(
    template_handler_dependencies, settings_dict
):  # pylint: disable=redefined-outer-name
    """Test the get_md_layout_template method of the TemplateHandler class."""
    settings, root_layout_builder, pagination_handler, api = (
        template_handler_dependencies
    )
    template_handler = TemplateHandler(
        settings, root_layout_builder, pagination_handler, api
    )

    test_article_path = os.path.join(
        template_handler.root_path, settings_dict["markdown_path"], "articles/test_dir/"
    )
    test_layout_path = os.path.join(
        template_handler.root_path,
        settings_dict["root_template_paths"][0],
        "articles/test_dir/",
    )
    test_article_name = "test_article.md"

    # Create a test article md and layout template that should be matched to the article md
    os.mkdir(test_article_path)
    with open(
        os.path.join(test_article_path, test_article_name), "w", encoding="utf-8"
    ) as article_file:
        article_file.write("Test article content")
    os.mkdir(test_layout_path)
    with open(
        os.path.join(test_layout_path, "layout.jinja"), "w", encoding="utf-8"
    ) as layout_file:
        layout_file.write(r"<div>Test layout content: {{ article }}</div>")

    url_segment = "test_dir"
    layout = "articles/test_dir/layout.jinja"

    assert template_handler.get_md_layout_template(url_segment)
    assert template_handler.get_md_layout_template(url_segment) == layout


def test_template_handler_write(
    template_handler_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the write method of the TemplateHandler class."""
    settings, root_layout_builder, pagination_handler, api = (
        template_handler_dependencies
    )
    template_handler = TemplateHandler(
        settings, root_layout_builder, pagination_handler, api
    )

    if not os.path.exists(template_handler.build_dir):
        os.makedirs(template_handler.build_dir)

    template_handler.write()

    # Check that the home page was written
    assert os.path.exists(f"{template_handler.build_dir}/index.html")
    with open(
        f"{template_handler.build_dir}/index.html", "r", encoding="utf-8"
    ) as index_file:
        index_contents = index_file.read()
    assert index_contents
    assert "<!DOCTYPE html>" in index_contents
    # Check that the linked pages were written
    linked_page_paths = get_linked_page_relative_build_paths(settings["template_paths"])
    for path in linked_page_paths:
        if not path.endswith(".xml"):
            assert os.path.exists(f"{template_handler.build_dir}/{path}/index.html")
            with open(
                f"{template_handler.build_dir}/{path}/index.html", "r", encoding="utf-8"
            ) as page_file:
                page_contents = page_file.read()
            assert page_contents
            assert "<!DOCTYPE html>" in page_contents
        else:
            # Feed was marked with <file_type: "xml">, just check that the xml file exists
            assert os.path.exists(f"{template_handler.build_dir}/{path}")
    # Check that the article pages were written
    for md_page in template_handler.context.md_pages:
        build_path = os.path.join(
            template_handler.build_dir,
            md_page["url_segment"].strip("/"),
            md_page["name"].strip("/"),
        )
        assert os.path.exists(build_path)
        assert os.path.exists(f"{build_path}/index.html")
        with open(f"{build_path}/index.html", "r", encoding="utf-8") as page_file:
            page_contents = page_file.read()
        assert page_contents
        assert "<!DOCTYPE html>" in page_contents
        assert (
            template_handler.context.front_matter_processor.clear_front_matter(
                file_path=None, content=md_page["html"]
            )
            in page_contents
        )


def test_template_handler_write_outputs_frontmatter_with_correct_heirarchy(
    template_handler_dependencies,
):  # pylint: disable=redefined-outer-name
    """
    Test that the write method output of the TemplateHandler class overwrites the
    global config with the homepage frontmatter.
    """
    settings, root_layout_builder, pagination_handler, api = (
        template_handler_dependencies
    )
    template_handler = TemplateHandler(
        settings, root_layout_builder, pagination_handler, api
    )

    if not os.path.exists(template_handler.build_dir):
        os.makedirs(template_handler.build_dir)

    template_handler.write()

    # Check that the home page was written
    assert os.path.exists(f"{template_handler.build_dir}/index.html")
    with open(
        f"{template_handler.build_dir}/index.html", "r", encoding="utf-8"
    ) as index_file:
        index_contents = index_file.read()
    assert index_contents
    assert (
        "<title>Shodo - A Static Site Generator - Home</title>" in index_contents
    ), "Metadata should be pulled from the homepage frontmatter"
    assert (
        '<meta name="description" content="Home page of the site">' in index_contents
    ), "Metadata should be pulled from the homepage frontmatter"


def test_template_handler_write_outputs_article_layout_frontmatter_with_correct_heirarchy(
    template_handler_dependencies,
):  # pylint: disable=redefined-outer-name
    """
    Test that the write method output of the TemplateHandler class overwrites the
    global config with the article layout frontmatter.
    """
    settings, root_layout_builder, pagination_handler, api = (
        template_handler_dependencies
    )
    template_handler = TemplateHandler(
        settings, root_layout_builder, pagination_handler, api
    )

    if not os.path.exists(template_handler.build_dir):
        os.makedirs(template_handler.build_dir)

    template_handler.write()

    build_path = os.path.join(
        template_handler.build_dir,
        "blog",
        "subject",
        "second-blog",
    )

    assert os.path.exists(build_path)
    assert os.path.exists(f"{build_path}/index.html")
    with open(f"{build_path}/index.html", "r", encoding="utf-8") as page_file:
        page_contents = page_file.read()
    assert page_contents
    assert "<!DOCTYPE html>" in page_contents
    assert (
        'id="blog-subject-page-container"' in page_contents
    ), "Body attributes should be pulled from the nested article layout frontmatter"

    assert '<meta name="author" content="Shodo SSG Nested Layout">' in page_contents

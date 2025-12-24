"""Tests for the template_context module."""

from datetime import datetime
from zoneinfo import ZoneInfo
from shodo_ssg.template_context import TemplateContext


def test_template_context_init(
    template_context_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the __init__ method of the TemplateHandler class."""
    markdown_loader, json_loader, front_matter_processor = template_context_dependencies
    template_context = TemplateContext(
        markdown_loader, json_loader, front_matter_processor
    )

    assert template_context.markdown_loader
    assert template_context.json_loader
    assert template_context.front_matter_processor


def test_template_context_render_args(
    template_context_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the render_args property of the TemplateHandler class."""
    markdown_loader, json_loader, front_matter_processor = template_context_dependencies
    template_context = TemplateContext(
        markdown_loader, json_loader, front_matter_processor
    )

    assert template_context.render_args
    assert isinstance(template_context.render_args, dict)
    assert "config" in template_context.render_args
    assert "metadata" in template_context.render_args["config"]
    assert "title" in template_context.render_args["config"]["metadata"]
    assert "description" in template_context.render_args["config"]["metadata"]
    assert "author" in template_context.render_args["config"]["metadata"]
    assert "url_origin" in template_context.render_args["config"]
    assert "timezone" in template_context.render_args["config"]
    assert "short" in template_context.render_args
    assert "collections" in template_context.render_args
    assert "another_short" in template_context.render_args["collections"]
    assert "list_of_words" in template_context.render_args
    assert "home_page_title" in template_context.render_args


def test_template_context_md_pages(
    template_context_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the md_pages property of the TemplateHandler class."""
    markdown_loader, json_loader, front_matter_processor = template_context_dependencies
    template_context = TemplateContext(
        markdown_loader, json_loader, front_matter_processor
    )

    assert template_context.md_pages
    assert isinstance(template_context.md_pages, list)
    assert template_context.md_pages[0]
    assert isinstance(template_context.md_pages[0], dict)
    assert "html" in template_context.md_pages[0]
    assert "url_segment" in template_context.md_pages[0]
    assert "name" in template_context.md_pages[0]


def test_template_context_update_render_arg(
    template_context_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the update_render_arg method of the TemplateHandler class."""
    markdown_loader, json_loader, front_matter_processor = template_context_dependencies
    template_context = TemplateContext(
        markdown_loader, json_loader, front_matter_processor
    )

    key = "test_key"
    value = "test_value"

    assert key not in template_context.render_args

    template_context.update_render_arg(key, value)

    assert key in template_context.render_args
    assert template_context.render_args[key] == value


# Tests for _format_md_page_data
def test_format_md_page_data_complete(
    template_context_dependencies,
):
    """Test _format_md_page_data with complete front matter"""
    markdown_loader, json_loader, front_matter_processor = template_context_dependencies
    template_context = TemplateContext(
        markdown_loader, json_loader, front_matter_processor
    )

    md_page = {
        "name": "first-post",
        "url_segment": "/blog/",
        "html": "<p>First post content</p>",
        "front_matter": {
            "title": "First Post",
            "description": "First post description",
            "summary": "First post summary",
            "keywords": ["python", "ssg"],
            "author": "John Doe",
            "category": "technology",
            "tags": ["python", "web"],
            "date": "2025-01-15",
            "draft": False,
            "image": "/images/first.jpg",
            "image_alt": "First post image",
            "published_datetime": "2025-01-15T10:00:00Z",
        },
    }

    # pylint: disable=protected-access
    result = template_context.format_md_page_data(md_page)

    assert result["file_name"] == "first-post"
    assert result["directory"] == "/blog/"
    assert result["path"] == "/blog/first-post"
    assert result["title"] == "First Post"
    assert result["description"] == "First post description"
    assert result["summary"] == "First post summary"
    assert result["keywords"] == ["python", "ssg"]
    assert result["author"] == "John Doe"
    assert result["category"] == "technology"
    assert result["tags"] == ["python", "web"]
    assert result["date"].strftime("%Y-%m-%d") == "2025-01-15"
    assert result["draft"] is False
    assert result["image"] == "/images/first.jpg"
    assert result["image_alt"] == "First post image"
    assert result["content"] == "<p>First post content</p>"
    assert result["published_datetime"] == datetime.strptime(
        "2025-01-15T10:00:00Z", "%Y-%m-%dT%H:%M:%SZ"
    )
    assert result["published_dt_local"].strftime(
        "%Y-%m-%d %H:%M:%S %Z%z"
    ) == datetime.strptime("2025-01-15T10:00:00Z", "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=ZoneInfo("UTC")
    ).astimezone(
        ZoneInfo("America/Chicago")
    ).strftime(
        "%Y-%m-%d %H:%M:%S %Z%z"
    )


def test_format_md_page_data_minimal(
    template_context_dependencies,
):
    """Test _format_md_page_data with minimal front matter"""
    markdown_loader, json_loader, front_matter_processor = template_context_dependencies
    template_context = TemplateContext(
        markdown_loader, json_loader, front_matter_processor
    )

    md_page = {
        "name": "minimal-post",
        "url_segment": "/posts/",
        "html": "<p>Minimal content</p>",
        "front_matter": {},
    }

    # pylint: disable=protected-access
    result = template_context.format_md_page_data(md_page)

    assert result["file_name"] == "minimal-post"
    assert result["directory"] == "/posts/"
    assert result["path"] == "/posts/minimal-post"
    assert result["title"] == ""
    assert result["description"] == ""
    assert result["summary"] == ""
    assert result["keywords"] == []
    assert result["author"] == ""
    assert result["category"] == ""
    assert result["tags"] == []
    assert result["date"] is None
    assert result["published_datetime"] is None
    assert result["published_dt_local"] is None
    assert result["draft"] is False
    assert result["image"] == ""
    assert result["image_alt"] == ""
    assert result["content"] == "<p>Minimal content</p>"


def test_format_md_page_data_no_front_matter(
    template_context_dependencies,
):
    """Test _format_md_page_data when front_matter is None"""
    markdown_loader, json_loader, front_matter_processor = template_context_dependencies
    template_context = TemplateContext(
        markdown_loader, json_loader, front_matter_processor
    )

    md_page = {
        "name": "no-front-matter",
        "url_segment": "/posts/",
        "html": "<p>Content</p>",
        "front_matter": None,
    }
    # pylint: disable=protected-access
    result = template_context.format_md_page_data(md_page)

    assert result["title"] == ""
    assert result["draft"] is False

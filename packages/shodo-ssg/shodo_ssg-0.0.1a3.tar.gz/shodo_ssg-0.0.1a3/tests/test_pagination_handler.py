"""
Tests for the PaginationHandler class
"""

import os
from typing import cast
from unittest.mock import Mock, mock_open, patch
import pytest
from jinja2 import Template
from shodo_ssg.data_loader import JSONLoader
from shodo_ssg.front_matter_processor import FrontMatterProcessor
from shodo_ssg.pagination_handler import PaginationHandler
from shodo_ssg.api import API
from shodo_ssg.html_root_layout_builder import HTMLRootLayoutBuilder
from shodo_ssg.template_context import TemplateContext


# pylint: disable=too-many-public-methods
class TestPaginationHandler:
    """Test suite for PaginationHandler class"""

    @pytest.fixture
    def mock_context(self, settings_dict):
        """Fixture to provide a mock TemplateContext"""
        context = cast(TemplateContext, Mock(spec=TemplateContext))
        # pylint: disable=protected-access
        context._render_args = {
            "users": [
                {"id": 1, "name": "Alice", "role": "admin"},
                {"id": 2, "name": "Bob", "role": "user"},
                {"id": 3, "name": "Charlie", "role": "user"},
            ],
            "products": [
                {"id": 101, "name": "Widget", "price": 9.99},
                {"id": 102, "name": "Gadget", "price": 19.99},
            ],
            "single_item": {"id": 201, "name": "Solo", "price": 29.99},
            "empty_collection": [],
        }

        # Make render_args a property that always returns _render_args
        type(context).render_args = property(lambda self: self._render_args.copy())

        context._md_pages = []  # pylint: disable=protected-access
        type(context).md_pages = property(lambda self: self._md_pages.copy())

        # Mock json_loader
        mock_json_loader = Mock()
        json_loader = JSONLoader(settings_dict)

        def mock_format_string_for_json_compatibility(x):
            result = json_loader.format_string_for_json_compatibility(x)
            return result

        def mock_json_to_dict(content: str):
            result = json_loader.json_to_dict(content)
            return result

        mock_json_loader.format_string_for_json_compatibility = Mock(
            side_effect=mock_format_string_for_json_compatibility
        )

        mock_json_loader.json_to_dict = Mock(side_effect=mock_json_to_dict)
        context.json_loader = mock_json_loader

        # Mock front_matter_processor
        context.front_matter_processor = cast(FrontMatterProcessor, Mock())
        context.front_matter_processor.clear_front_matter = Mock()

        context.update_render_arg = Mock(
            # pylint: disable=protected-access
            side_effect=lambda key, value: context._render_args.update({key: value})
        )

        return context

    @pytest.fixture
    def mock_html_root_layout_builder(self):
        """Fixture to provide a mock HTMLRootLayoutBuilder"""
        builder = cast(HTMLRootLayoutBuilder, Mock(spec=HTMLRootLayoutBuilder))
        builder.get_doc_head = Mock(return_value="<html><head></head><body>")
        builder.get_doc_tail = Mock(return_value="</body></html>")
        return builder

    @pytest.fixture
    def mock_api(self):
        """Fixture to provide a mock API"""
        api = cast(API, Mock(spec=API))
        # Default: return 25 articles for pagination testing
        api.shodo_get_articles = Mock(
            return_value=[{"title": f"Article {i}"} for i in range(1, 26)]
        )
        api.shodo_query_store = Mock(
            return_value=[{"name": f"Item {i}"} for i in range(1, 26)]
        )
        return api

    @pytest.fixture
    def pagination_handler(
        self,
        mock_context: TemplateContext,
        mock_html_root_layout_builder: HTMLRootLayoutBuilder,
        mock_api: API,
    ):
        """Fixture to provide a PaginationHandler instance"""
        return PaginationHandler(mock_context, mock_html_root_layout_builder, mock_api)

    @pytest.fixture
    def mock_template(self):
        """Fixture to provide a mock Jinja2 template"""
        template = cast(Template, Mock(spec=Template))
        template.filename = "/path/to/template.jinja"
        template.render = Mock(return_value="<div>Rendered content</div>")

        return template

    # Tests for handle_pagination
    def test_handle_pagination_invalid_pagination_type(
        self, pagination_handler: PaginationHandler, mock_template: Template
    ):
        """Test that invalid pagination type raises ValueError"""
        front_matter = {"paginate": "invalid_type", "per_page": 10}

        with pytest.raises(ValueError, match="not supported"):
            pagination_handler.handle_pagination(
                "/path/to/template.jinja",
                mock_template,
                "dist/blog/index.html",
                front_matter,
            )

    def test_handle_pagination_missing_per_page(
        self, pagination_handler: PaginationHandler, mock_template: Template
    ):
        """Test that missing per_page raises ValueError"""
        front_matter = {"paginate": "shodo_get_articles"}

        with pytest.raises(ValueError, match="per_page"):
            pagination_handler.handle_pagination(
                "/path/to/template.jinja",
                mock_template,
                "dist/blog/index.html",
                front_matter,
            )

    def test_handle_pagination_invalid_per_page(
        self, pagination_handler: PaginationHandler, mock_template: Template
    ):
        """Test that invalid per_page value raises ValueError"""
        front_matter = {"paginate": "shodo_get_articles", "per_page": "invalid"}

        with pytest.raises(ValueError, match="per_page"):
            pagination_handler.handle_pagination(
                "/path/to/template.jinja",
                mock_template,
                "dist/blog/index.html",
                front_matter,
            )

    def test_handle_pagination_per_page_as_string(
        self, pagination_handler: PaginationHandler, mock_template: Template
    ):
        """Test that per_page can be provided as a string number"""
        front_matter = {"paginate": "shodo_get_articles", "per_page": "10"}

        template_content = """
        {% for post in shodo_get_articles(filters={'where': {'category': 'blog'}}) %}
        {% endfor %}
        """

        with patch("builtins.open", mock_open(read_data=template_content)) as m:
            with patch("os.makedirs"):
                # with patch("builtins.open", mock_open()) as m:
                pagination_handler.handle_pagination(
                    "/path/to/template.jinja",
                    mock_template,
                    "dist/blog/index.html",
                    front_matter,
                )

                # Should create 3 pages (25 items / 10 per page)
                assert m.call_count == 3 + 1  # +1 for reading template file

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_handle_pagination_creates_multiple_pages(
        self,
        _mock_file,
        mock_makedirs,
        pagination_handler: PaginationHandler,
        mock_template,
    ):
        """Test that pagination creates the correct number of pages"""
        front_matter = {"paginate": "shodo_get_articles", "per_page": 10}

        template_content = """
        {% for post in shodo_get_articles({}) %}
        {% endfor %}
        """

        with patch("builtins.open", mock_open(read_data=template_content)) as m:
            pagination_handler.handle_pagination(
                "/path/to/template.jinja",
                mock_template,
                "dist/blog/index.html",
                front_matter,
            )

            assert m.call_count == 3 + 1  # +1 for reading template file

        # Should create 3 pages (25 items / 10 per page = 2.5 -> 3 pages)
        assert mock_makedirs.call_count == 3 - 1  # No dir for first page

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_handle_pagination_extracts_filters(
        self,
        _mock_file,
        _mock_makedirs,
        pagination_handler: PaginationHandler,
        mock_template: Template,
        mock_api: API,
        front_matter_processor_dependencies,
    ):
        """Test that pagination extracts filters from template"""
        front_matter = {"paginate": "shodo_get_articles", "per_page": 10}

        template_content = r"""
        {% for post in shodo_get_articles(filters={
            "where": {"category": "technology", "tags": { "contains": ["python"]}},
        }) %}
        {% endfor %}
        """

        json_loader = front_matter_processor_dependencies
        mock_json_to_dict = pagination_handler.context.json_loader.json_to_dict
        pagination_handler.context.json_loader.json_to_dict = json_loader.json_to_dict

        with patch("builtins.open", mock_open(read_data=template_content)):
            pagination_handler.handle_pagination(
                "/path/to/template.jinja",
                mock_template,
                "dist/blog/index.html",
                front_matter,
            )

        # Verify API was called with correct filters
        mock_api.shodo_get_articles.assert_called_once()
        call_args = mock_api.shodo_get_articles.call_args
        filters = call_args.kwargs.get("filters", {})

        assert filters.get("where").get("category") == "technology"
        assert filters.get("where").get("tags").get("contains") == ["python"]

        pagination_handler.context.json_loader.json_to_dict = mock_json_to_dict

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_handle_pagination_removes_offset_and_limit_when_extracting_filters(
        self,
        _mock_file,
        _mock_makedirs,
        pagination_handler: PaginationHandler,
        mock_template: Template,
        mock_api: API,
        front_matter_processor_dependencies,
    ):
        """Test that pagination extracts filters from template"""
        front_matter = {"paginate": "shodo_get_articles", "per_page": 10}

        template_content = r"""
        {% for post in shodo_get_articles(filters={
            "where": {"category": "technology", "tags": { "contains": ["python"]}},
            "limit": pagination.per_page,
            "offset": pagination.per_page * (pagination.current_page - 1)
        }) %}
        {% endfor %}
        """

        json_loader = front_matter_processor_dependencies
        mock_json_to_dict = pagination_handler.context.json_loader.json_to_dict
        pagination_handler.context.json_loader.json_to_dict = json_loader.json_to_dict

        with patch("builtins.open", mock_open(read_data=template_content)):
            pagination_handler.handle_pagination(
                "/path/to/template.jinja",
                mock_template,
                "dist/blog/index.html",
                front_matter,
            )

        # Verify API was called with correct filters
        mock_api.shodo_get_articles.assert_called_once()
        call_args = mock_api.shodo_get_articles.call_args
        filters = call_args.kwargs.get("filters", {})

        assert filters.get("where").get("category") == "technology"
        assert filters.get("where").get("tags").get("contains") == ["python"]
        # offset and limit should be removed
        assert "offset" not in filters
        assert "limit" not in filters

        pagination_handler.context.json_loader.json_to_dict = mock_json_to_dict

    # Tests for _write_pagination_page_html_from_template
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_write_pagination_page_first_page(
        self,
        mock_file,
        _mock_makedirs,
        pagination_handler: PaginationHandler,
        mock_template,
    ):
        """Test writing the first pagination page"""
        front_matter = {}
        pagination_context = {
            "root_page_path": "blog",
            "page_num": 1,
            "total_pages": 3,
            "items_per_page": 10,
            "total_items": 25,
        }

        # pylint: disable=protected-access
        pagination_handler._write_pagination_page_html_from_template(
            mock_template,
            front_matter,
            "dist/blog/index.html",
            pagination_context,
        )

        # First page should write to the original destination
        mock_file.assert_called_with("dist/blog/index.html", "w", encoding="utf-8")

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_write_pagination_page_subsequent_pages(
        self,
        mock_file,
        _mock_makedirs,
        pagination_handler: PaginationHandler,
        mock_template,
    ):
        """Test writing subsequent pagination pages"""
        front_matter = {}
        pagination_context = {
            "root_page_path": "blog",
            "page_num": 2,
            "total_pages": 3,
            "items_per_page": 10,
            "total_items": 25,
        }

        # pylint: disable=protected-access
        pagination_handler._write_pagination_page_html_from_template(
            mock_template,
            front_matter,
            "dist/blog/index.html",
            pagination_context,
        )

        # Subsequent pages should write to page/{num}/index.html
        expected_path = os.path.join("dist", "blog", "page", "2", "index.html")
        mock_file.assert_called_with(expected_path, "w", encoding="utf-8")

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_write_pagination_page_updates_context(
        self,
        _mock_file,
        _mock_makedirs,
        pagination_handler: PaginationHandler,
        mock_template: Template,
        mock_context: TemplateContext,
    ):
        """Test that pagination context is updated with correct values"""
        front_matter = {}
        pagination_context = {
            "root_page_path": "blog",
            "page_num": 2,
            "total_pages": 3,
            "items_per_page": 10,
            "total_items": 25,
        }

        # pylint: disable=protected-access
        pagination_handler._write_pagination_page_html_from_template(
            mock_template,
            front_matter,
            "dist/blog/index.html",
            pagination_context,
        )

        # Assert that context's update_render_arg was called with correct
        # pagination data the first time, and None the second time
        assert mock_context.update_render_arg.call_count == 2
        first_call_args = mock_context.update_render_arg.call_args_list[0][0]
        second_call_args = mock_context.update_render_arg.call_args_list[1][0]
        assert first_call_args[0] == "pagination"
        assert second_call_args[0] == "pagination"
        assert first_call_args[1] is not None
        assert second_call_args[1] is None

        # Get the arguments that template.render was called with
        render_call_args = mock_template.render.call_args[0][0]

        assert "pagination" in render_call_args
        pagination = render_call_args.get("pagination", {})

        assert pagination["total_items"] == 25
        assert pagination["current_page"] == 2
        assert pagination["per_page"] == 10
        assert pagination["total_pages"] == 3
        assert pagination["has_previous"] is True
        assert pagination["has_next"] is True
        assert pagination["previous_page"] == 1
        assert pagination["next_page"] == 3

    # Tests for get_pagination_link_markup
    def test_get_pagination_link_markup_single_page(
        self, pagination_handler: PaginationHandler
    ):
        """Test pagination markup with only one page returns empty string"""
        result = pagination_handler.get_pagination_link_markup("blog", 1, 1)
        assert result == ""

    def test_get_pagination_link_markup_first_page(
        self, pagination_handler: PaginationHandler
    ):
        """Test pagination markup for first page"""
        result = pagination_handler.get_pagination_link_markup("blog", 1, 5)

        assert "<nav class='pagination'>" in result
        assert "pagination-previous" not in result  # No previous on first page
        assert "pagination-next" in result
        assert "/blog/page/2/" in result

    def test_get_pagination_link_markup_middle_page(
        self, pagination_handler: PaginationHandler
    ):
        """Test pagination markup for middle page"""
        result = pagination_handler.get_pagination_link_markup("blog", 3, 5)

        assert "pagination-previous" in result
        assert "pagination-next" in result
        assert "/blog/page/2/" in result  # Previous page
        assert "/blog/page/4/" in result  # Next page

    def test_get_pagination_link_markup_last_page(
        self, pagination_handler: PaginationHandler
    ):
        """Test pagination markup for last page"""
        result = pagination_handler.get_pagination_link_markup("blog", 5, 5)

        assert "pagination-previous" in result
        assert "pagination-next" not in result  # No next on last page
        assert "/blog/page/4/" in result

    def test_get_pagination_link_markup_many_pages(
        self, pagination_handler: PaginationHandler
    ):
        """Test pagination markup with more than 10 pages shows ellipsis"""
        result = pagination_handler.get_pagination_link_markup("blog", 6, 15)

        assert "pagination-ellipsis" in result
        assert "…" in result

    def test_get_pagination_link_markup_current_page_highlighted(
        self, pagination_handler: PaginationHandler
    ):
        """Test that current page is marked as active"""
        result = pagination_handler.get_pagination_link_markup("blog", 3, 5)

        assert "class='pagination-item active'>3</li>" in result

    # Tests for _generate_numbered_page_links
    def test_generate_numbered_page_links_few_pages(
        self, pagination_handler: PaginationHandler
    ):
        """Test numbered links when total pages <= 10"""
        # pylint: disable=protected-access
        result = pagination_handler._generate_numbered_page_links("blog", 5, 3)

        # Should show all pages
        assert "/blog/'>1</a>" in result
        assert "/blog/page/2/'>2</a>" in result
        assert "active'>3</li>" in result
        assert "/blog/page/4/'>4</a>" in result
        assert "/blog/page/5/'>5</a>" in result

    def test_generate_numbered_page_links_many_pages_beginning(
        self, pagination_handler: PaginationHandler
    ):
        """Test numbered links for current page near beginning"""
        # pylint: disable=protected-access
        result = pagination_handler._generate_numbered_page_links("blog", 15, 2)

        assert "/blog/'>1</a>" in result
        assert "active'>2</li>" in result
        assert "pagination-ellipsis" in result
        assert "/blog/page/15/'>15</a>" in result

    def test_generate_numbered_page_links_many_pages_end(
        self, pagination_handler: PaginationHandler
    ):
        """Test numbered links for current page near end"""
        # pylint: disable=protected-access
        result = pagination_handler._generate_numbered_page_links("blog", 15, 14)

        assert "/blog/'>1</a>" in result
        assert "pagination-ellipsis" in result
        assert "active'>14</li>" in result
        assert "/blog/page/15/'>15</a>" in result

    def test_generate_numbered_page_links_many_pages_middle(
        self, pagination_handler: PaginationHandler
    ):
        """Test numbered links for current page in middle"""
        # pylint: disable=protected-access
        result = pagination_handler._generate_numbered_page_links("blog", 15, 8)

        assert "/blog/'>1</a>" in result
        assert result.count("pagination-ellipsis") == 2  # Before and after
        assert "active'>8</li>" in result
        assert "/blog/page/15/'>15</a>" in result

    # Tests for _generate_page_link
    def test_generate_page_link_first_page(self, pagination_handler: PaginationHandler):
        """Test generating link for first page"""
        # pylint: disable=protected-access
        result = pagination_handler._generate_page_link("blog", 1, 3)

        assert "pagination-item" in result
        assert "/blog/'>1</a>" in result
        assert "active" not in result

    def test_generate_page_link_current_page(
        self, pagination_handler: PaginationHandler
    ):
        """Test generating link for current page"""
        # pylint: disable=protected-access
        result = pagination_handler._generate_page_link("blog", 3, 3)

        assert "pagination-item active'>3</li>" in result
        assert "<a" not in result  # Current page is not a link

    def test_generate_page_link_other_page(self, pagination_handler: PaginationHandler):
        """Test generating link for other pages"""
        # pylint: disable=protected-access
        result = pagination_handler._generate_page_link("blog", 5, 3)

        assert "pagination-item" in result
        assert "/blog/page/5/'>5</a>" in result

    # Tests for set_default_pagination_variables
    def test_set_default_pagination_variables(
        self, pagination_handler: PaginationHandler, mock_context: TemplateContext
    ):
        """Test setting default pagination variables"""
        pagination_handler.set_default_pagination_variables()

        assert "pagination" in mock_context.render_args
        pagination = mock_context.render_args["pagination"]

        assert pagination["total_items"] == 0
        assert pagination["current_page"] == 1
        assert pagination["per_page"] == 10
        assert pagination["total_pages"] == 0
        assert pagination["has_previous"] is False
        assert pagination["has_next"] is False
        assert pagination["previous_page"] is None
        assert pagination["next_page"] is None
        assert pagination["page_links"] == ""

    def test_set_default_pagination_variables_already_set(
        self, pagination_handler: PaginationHandler, mock_context: TemplateContext
    ):
        """Test that existing pagination variables are not overwritten"""
        # pylint: disable=protected-access
        mock_context._render_args["pagination"] = {"custom": "value"}

        pagination_handler.set_default_pagination_variables()

        # Should not overwrite existing pagination
        assert mock_context.render_args["pagination"] == {"custom": "value"}

    # Tests for _extract_pagination_filters
    def test_extract_pagination_filters_shodo_get_articles(
        self, pagination_handler: PaginationHandler
    ):
        """Test extracting filters from shodo_get_articles call"""
        template_content = r"""
        {% for post in shodo_get_articles(filters={'where': {'category': 'tech'}, 'limit': 5}) %}
        {% endfor %}
        """

        with patch("builtins.open", mock_open(read_data=template_content)):
            # pylint: disable=protected-access
            result = pagination_handler._extract_pagination_filters(
                "/path/to/template.jinja", "shodo_get_articles"
            )

        assert result is not None
        assert result["where"]["category"] == "tech"
        assert result["limit"] == 5

    def test_extract_pagination_filters_unsupported_query(
        self, pagination_handler: PaginationHandler
    ):
        """Test extracting filters for unsupported query type"""

        template_content = r"""
        {% for item in unsupported_query() %}
        {% endfor %}
        """

        with patch("builtins.open", mock_open(read_data=template_content)):
            # pylint: disable=protected-access
            result = pagination_handler._extract_pagination_filters(
                "/path/to/template.jinja", "unsupported_query"
            )

        assert result is None

    # Tests for _extract_article_query_filters
    def test_extract_article_query_filters_simple(
        self, pagination_handler: PaginationHandler
    ):
        """Test extracting simple filters from template"""
        content = (
            r"{% for post in shodo_get_articles({'where': {'category': 'tech'}}) %}"
        )

        # pylint: disable=protected-access
        result = pagination_handler._extract_article_query_filters(content)

        assert result is not None
        assert result["where"]["category"] == "tech"

    def test_extract_article_query_filters_multiple_keys(
        self, pagination_handler: PaginationHandler
    ):
        """Test extracting multiple filter keys"""
        content = r"""
        {% for post in shodo_get_articles(filters={
            'where': {'category': 'tech', 'tags': {'contains': ['python', 'web']}},
            'limit': 10
        }) %}
        """

        # pylint: disable=protected-access
        result = pagination_handler._extract_article_query_filters(content)

        assert result is not None
        assert result["where"]["category"] == "tech"
        assert result["where"]["tags"] == {"contains": ["python", "web"]}
        assert result["limit"] == 10

    def test_extract_article_query_filters_single_quotes(
        self, pagination_handler: PaginationHandler
    ):
        """Test extracting filters with single quotes"""
        content = r"{% for post in shodo_get_articles({'category': 'tech'}) %}"

        # pylint: disable=protected-access
        result = pagination_handler._extract_article_query_filters(content)

        assert result is not None
        assert result["category"] == "tech"

    def test_extract_article_query_filters_no_match(
        self, pagination_handler: PaginationHandler
    ):
        """Test when no shodo_get_articles call is found"""
        content = r"{% for post in some_other_function() %}"

        with pytest.raises(ValueError, match="Could not find 'shodo_get_articles'"):
            # pylint: disable=protected-access
            pagination_handler._extract_article_query_filters(content)

    def test_extract_article_query_filters_invalid_json(
        self, pagination_handler: PaginationHandler, mock_context: TemplateContext
    ):
        """Test handling of invalid JSON in filters"""
        content = r"{% for post in shodo_get_articles({invalid json}) %}"

        # Make json_to_dict raise ValueError
        mock_context.json_loader.json_to_dict.side_effect = ValueError("Invalid JSON")

        # pylint: disable=protected-access
        result = pagination_handler._extract_article_query_filters(content)

        assert result is None

    def test_extract_article_query_filters_with_trailing_comma(
        self, pagination_handler: PaginationHandler
    ):
        """Test extracting filters with trailing comma in last item"""
        content = r"""
        {% for post in shodo_get_articles({
            'where': {'category': 'tech'},
            'limit': 10,
        }) %}
        """

        # pylint: disable=protected-access
        result = pagination_handler._extract_article_query_filters(content)

        assert result is not None
        assert result["where"]["category"] == "tech"
        assert result["limit"] == 10

    def test_extract_article_query_filters_wraps_dynamic_variables_and_expressions_in_quotes(
        self, pagination_handler: PaginationHandler
    ):
        """Test extracting filters when variables are used in arguments. Values provided for keys
        like 'limit' and 'offset' should be wrapped in quotes so they can be parsed as strings. This
        is because they will be removed from the query when retrieving pagination data, and the
        actual values will be set dynamically during pagination rendering. During build, we just
        need to parse the relevant user provided filters as valid JSON without raising errors.
        """
        content = r"""
        {% for post in shodo_get_articles({
            "limit": pagination.per_page,
            "offset": pagination.per_page * (pagination.current_page - 1)
        }) %}
        {% endfor %}
        """

        # pylint: disable=protected-access
        result = pagination_handler._extract_article_query_filters(content)

        assert result is not None
        assert result["limit"] == "pagination.per_page"  # Variable name as string
        assert (
            result["offset"] == "pagination.per_page * (pagination.current_page - 1)"
        )  # Expression as string

    def test_extract_article_query_filters_handles_nested_structures(
        self, pagination_handler: PaginationHandler
    ):
        """Test extracting filters with nested structures"""
        content = r"""
        {% for post in shodo_get_articles({
        'where': {
            'category': 'tech',
            'tags': {'contains': ['python', 'web', {'framework': 'django'}]},
            'metadata': {
                'equals': {
                    'author': 'John Doe',
                    'published': true
                }
            }
        }
        }) %}
        """

        # pylint: disable=protected-access
        result = pagination_handler._extract_article_query_filters(content)

        assert result is not None
        assert result["where"]["category"] == "tech"
        assert result["where"]["tags"] == {
            "contains": ["python", "web", {"framework": "django"}]
        }
        assert result["where"]["metadata"]["equals"] == {
            "author": "John Doe",
            "published": True,
        }

    def test_extract_article_query_filters_handles_trailing_commas_in_nested_structures(
        self, pagination_handler: PaginationHandler
    ):
        """Test extracting filters with trailing commas in nested structures"""
        content = r"""
        {% for post in shodo_get_articles({
        'where': {
            'category': 'tech',
            'tags': {'contains': ['python', 'web', {'framework': 'django'}]},
            'metadata': {
                'equals': {
                    'author': 'John Doe',
                    'published': true,
                }
            },
        }
        }) %}
        """

        # pylint: disable=protected-access
        result = pagination_handler._extract_article_query_filters(content)

        assert result is not None
        assert result["where"]["category"] == "tech"
        assert result["where"]["tags"] == {
            "contains": ["python", "web", {"framework": "django"}]
        }
        assert result["where"]["metadata"]["equals"] == {
            "author": "John Doe",
            "published": True,
        }

    def test_extract_article_query_filters_handles_trailing_commas_in_complex_nested_structures(
        self, pagination_handler: PaginationHandler
    ):
        """Test extracting filters with trailing commas in complex nested structures"""
        content = r"""
        {% for post in shodo_get_articles({
            'category': 'tech',
            'tags': ['python', 'web', {'framework': 'django',}],
            'metadata': {
                'author': 'John Doe',
                'published': True,
                'stats': {
                    'views': 100,
                    'likes': 10,
                },
            },
        }) %}
        """

        # pylint: disable=protected-access
        result = pagination_handler._extract_article_query_filters(content)

        assert result is not None
        assert result["category"] == "tech"
        assert result["tags"] == ["python", "web", {"framework": "django"}]
        assert result["metadata"] == {
            "author": "John Doe",
            "published": True,
            "stats": {
                "views": 100,
                "likes": 10,
            },
        }

    def test_extract_article_query_filters_handles_sentences_containing_numbers_and_bools(
        self, pagination_handler: PaginationHandler
    ):
        """Test extracting filters when sentences contain numbers and boolean values"""
        content = r"""
        {% for post in shodo_get_articles({
            'category': 'tech',
            'sentence': 'This article has 1000 views and is featured. True story!',
            'is_featured': True,
        }) %}
        """

        # pylint: disable=protected-access
        result = pagination_handler._extract_article_query_filters(content)

        assert result is not None
        assert result["category"] == "tech"
        assert (
            result["sentence"]
            == "This article has 1000 views and is featured. True story!"
        )
        assert result["is_featured"] is True

    def test_extract_article_query_filters_handles_sentences_containing_quotes(
        self, pagination_handler: PaginationHandler
    ):
        """Test extracting filters when sentences contain quotes"""
        content = r"""
        {% for post in shodo_get_articles({
            "where": {
                "category": "tech",
                "quote": "She said, 'This is a great article!' and smiled.",
                "another_quote": 'He replied, "Indeed, it is!"',
                "third_quote": "She said, 'Let's test quotes!'",
                "fourth_quote": 'He responded, "Let\'s do it!"'
            }
        }) %}
        """

        # pylint: disable=protected-access
        result = pagination_handler._extract_article_query_filters(content)

        assert result is not None
        assert result["where"]["category"] == "tech"
        assert (
            result["where"]["quote"]
            == "She said, 'This is a great article!' and smiled."
        )
        assert result["where"]["another_quote"] == 'He replied, "Indeed, it is!"'
        assert result["where"]["third_quote"] == "She said, 'Let's test quotes!'"
        assert result["where"]["fourth_quote"] == 'He responded, "Let\'s do it!"'

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_handle_pagination_creates_multiple_pages_for_store_query(
        self,
        _mock_file,
        mock_makedirs,
        pagination_handler: PaginationHandler,
        mock_template,
    ):
        """Test that pagination creates the correct number of pages"""
        front_matter = {"paginate": "shodo_query_store", "per_page": 10}

        template_content = """
        {% for post in shodo_query_store({"collection": "products"}) %}
        {% endfor %}
        """

        with patch("builtins.open", mock_open(read_data=template_content)) as m:
            pagination_handler.handle_pagination(
                "/path/to/template.jinja",
                mock_template,
                "dist/blog/index.html",
                front_matter,
            )

            assert m.call_count == 3 + 1  # +1 for reading template file

        # Should create 3 pages (25 items / 10 per page = 2.5 -> 3 pages)
        assert mock_makedirs.call_count == 3 - 1  # No dir for first page

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_handle_pagination_extracts_filters_from_store_query(
        self,
        _mock_file,
        _mock_makedirs,
        pagination_handler: PaginationHandler,
        mock_template: Template,
        mock_api: API,
        front_matter_processor_dependencies,
    ):
        """Test that pagination extracts filters from template"""
        front_matter = {"paginate": "shodo_query_store", "per_page": 10}

        template_content = r"""
        {% for post in shodo_query_store(filters={
            "where": {"collection": "products", "name": { "in": ["Widget", "Gadget"]}},
        }) %}
        {% endfor %}
        """

        json_loader = front_matter_processor_dependencies
        mock_json_to_dict = pagination_handler.context.json_loader.json_to_dict
        pagination_handler.context.json_loader.json_to_dict = json_loader.json_to_dict

        with patch("builtins.open", mock_open(read_data=template_content)):
            pagination_handler.handle_pagination(
                "/path/to/template.jinja",
                mock_template,
                "dist/blog/index.html",
                front_matter,
            )

        # Verify API was called with correct filters
        mock_api.shodo_query_store.assert_called_once()
        call_args = mock_api.shodo_query_store.call_args
        filters = call_args.kwargs.get("filters", {})

        assert filters.get("where").get("collection") == "products"
        assert filters.get("where").get("name").get("in") == ["Widget", "Gadget"]

        pagination_handler.context.json_loader.json_to_dict = mock_json_to_dict

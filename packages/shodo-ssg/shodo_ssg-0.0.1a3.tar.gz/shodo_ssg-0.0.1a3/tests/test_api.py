"""
Tests for the API class
"""

from datetime import datetime, timezone
from unittest.mock import Mock
import pytest
from shodo_ssg.api import API
from shodo_ssg.template_context import TemplateContext
from shodo_ssg.front_matter_processor import FrontMatterProcessor


# pylint: disable=too-many-public-methods
class TestAPI:
    """Test suite for API class"""

    @pytest.fixture
    def front_matter_processor(self, front_matter_processor_dependencies):
        """Fixture to provide a FrontMatterProcessor instance"""
        json_loader = front_matter_processor_dependencies
        return FrontMatterProcessor(json_loader)

    @pytest.fixture
    def template_context(self, template_context_dependencies):
        """Fixture to provide a TemplateContext instance with sample data"""
        context_mock = Mock()

        markdown_loader, json_loader, front_matter_processor = (
            template_context_dependencies
        )

        context = TemplateContext(markdown_loader, json_loader, front_matter_processor)

        context_mock.format_md_page_data = context.format_md_page_data

        # Add sample markdown pages
        context_mock.md_pages = [
            {
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
                },
            },
            {
                "name": "second-post",
                "url_segment": "/blog/tutorials/",
                "html": "<p>Second post content</p>",
                "front_matter": {
                    "title": "Second Post",
                    "description": "Second post description",
                    "summary": "Second post summary",
                    "keywords": ["tutorial"],
                    "author": "Jane Smith",
                    "category": "tutorials",
                    "tags": ["tutorial", "web"],
                    "date": "2025-02-20",
                    "draft": False,
                },
            },
            {
                "name": "draft-post",
                "url_segment": "/blog/",
                "html": "<p>Draft content</p>",
                "front_matter": {
                    "title": "Draft Post",
                    "draft": True,
                    "date": "2025-03-01",
                },
            },
            {
                "name": "newsletter-post",
                "url_segment": "/newsletter/",
                "html": "<p>Newsletter content</p>",
                "front_matter": {
                    "title": "Newsletter Issue 1",
                    "category": "newsletter",
                    "tags": ["news"],
                    "date": "2025-01-01",
                    "draft": False,
                },
            },
        ]

        # Add sample store data
        context_mock.render_args = {
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

        return context_mock

    @pytest.fixture
    def api(self, template_context: TemplateContext, front_matter_processor):
        """Fixture to provide an API instance"""
        return API(template_context, front_matter_processor)

    # Tests for shodo_get_articles
    def test_shodo_get_articles_no_filters(self, api: API):
        """Test shodo_get_articles returns all non-draft articles"""
        result = api.shodo_get_articles()

        assert len(result) == 3  # Should exclude the draft
        assert all(not post["draft"] for post in result)
        assert any(post["title"] == "First Post" for post in result)
        assert any(post["title"] == "Second Post" for post in result)
        assert any(post["title"] == "Newsletter Issue 1" for post in result)
        assert not any(post["title"] == "Draft Post" for post in result)

    def test_shodo_get_articles_filter_by_directory_starts_with(self, api: API):
        """Test filtering articles by directory_starts_with"""
        filters = {"where": {"directory": {"starts_with": "/blog"}}}

        result = api.shodo_get_articles(filters)

        assert len(result) == 2
        assert all(post["directory"].startswith("/blog") for post in result)
        assert any(post["title"] == "First Post" for post in result)
        assert any(post["title"] == "Second Post" for post in result)

    def test_shodo_get_articles_filter_by_directory_equals(self, api: API):
        """Test filtering articles by directory_equals"""
        filters = {"where": {"directory": {"equals": "/blog/"}}}
        result = api.shodo_get_articles(filters)

        assert len(result) == 1
        assert result[0]["title"] == "First Post"
        assert result[0]["directory"] == "/blog/"

    def test_shodo_get_articles_filter_by_category_string(self, api: API):
        """Test filtering articles by category as string"""
        filters = {"where": {"category": {"equals": "technology"}}}
        result = api.shodo_get_articles(filters)

        assert len(result) == 1
        assert result[0]["title"] == "First Post"
        assert result[0]["category"] == "technology"

    def test_shodo_get_articles_filter_by_category_list(self, api: API):
        """Test filtering articles by category as list"""
        filters = {"where": {"category": {"in": ["technology", "tutorials"]}}}
        result = api.shodo_get_articles(filters)

        assert len(result) == 2
        categories = [post["category"] for post in result]
        assert "technology" in categories
        assert "tutorials" in categories

    def test_shodo_get_articles_filter_by_tags(self, api: API):
        """Test filtering articles by tags"""
        filters = {"where": {"tags": {"contains": "web"}}}
        result = api.shodo_get_articles(filters)

        assert len(result) == 2
        assert all(any(tag in post["tags"] for tag in ["web"]) for post in result)

    def test_shodo_get_articles_filter_by_date(self, api: API):
        """Test filtering articles by date"""
        filters = {"where": {"date": {"gte": "2025-02-01"}}}
        result = api.shodo_get_articles(filters)

        assert len(result) == 1
        assert result[0]["title"] == "Second Post"
        assert result[0]["date"] >= datetime.strptime("2025-02-01", "%Y-%m-%d")

    def test_shodo_get_articles_order_by_date(self, api: API):
        """Test ordering articles by date (descending)"""
        filters = {"order_by": {"desc": "date"}}
        result = api.shodo_get_articles(filters)

        assert len(result) == 3
        assert (
            result[0]["date"].strftime("%Y-%m-%d") == "2025-02-20"
        )  # Most recent first
        assert result[1]["date"].strftime("%Y-%m-%d") == "2025-01-15"
        assert result[2]["date"].strftime("%Y-%m-%d") == "2025-01-01"

    def test_shodo_get_articles_order_by_title(self, api: API):
        """Test ordering articles by title (ascending)"""
        filters = {"order_by": {"asc": "title"}}
        result = api.shodo_get_articles(filters)

        assert len(result) == 3
        titles = [post["title"] for post in result]
        assert titles == sorted(titles)

    def test_shodo_get_articles_with_limit(self, api: API):
        """Test limiting number of returned articles"""
        filters = {"limit": 2, "order_by": {"desc": "date"}}
        result = api.shodo_get_articles(filters)

        assert len(result) == 2
        assert result[0]["date"].strftime("%Y-%m-%d") == "2025-02-20"
        assert result[1]["date"].strftime("%Y-%m-%d") == "2025-01-15"

    def test_shodo_get_articles_with_offset(self, api: API):
        """Test offsetting returned articles"""
        filters = {"offset": 1, "order_by": {"desc": "date"}}
        result = api.shodo_get_articles(filters)

        assert len(result) == 2
        assert result[0]["date"].strftime("%Y-%m-%d") == "2025-01-15"
        assert result[1]["date"].strftime("%Y-%m-%d") == "2025-01-01"

    def test_shodo_get_articles_with_offset_and_limit(self, api: API):
        """Test combining offset and limit"""
        filters = {"offset": 1, "limit": 1, "order_by": {"desc": "date"}}
        result = api.shodo_get_articles(filters)

        assert len(result) == 1
        assert result[0]["date"].strftime("%Y-%m-%d") == "2025-01-15"

    def test_shodo_get_articles_multiple_filters(self, api: API):
        """Test combining multiple filters"""
        filters = {
            "where": {
                "directory": {"starts_with": "/blog"},
                "tags": {"contains": "web"},
            },
            "order_by": {"desc": "date"},
            "limit": 1,
        }
        result = api.shodo_get_articles(filters)

        assert len(result) == 1
        assert result[0]["title"] == "Second Post"

    def test_shodo_get_articles_no_matches(self, api: API):
        """Test when filters match no articles"""
        filters = {"where": {"category": {"equals": "nonexistent"}}}
        result = api.shodo_get_articles(filters)

        assert len(result) == 0

    # Tests for shodo_query_store
    def test_shodo_query_store_no_filters(self, api: API):
        """Test shodo_query_store raises ValueError for missing 'collection' key"""
        with pytest.raises(ValueError):
            api.shodo_query_store({})

    def test_shodo_query_store_filter_by_role(self, api: API):
        """Test filtering store data by role"""
        filters = {"collection": "users", "where": {"role": {"equals": "user"}}}
        result = api.shodo_query_store(filters)

        assert len(result) == 2
        assert all(user["role"] == "user" for user in result)

    def test_shodo_query_store_order_by_name(self, api: API):
        """Test ordering store data by name (ascending)"""
        filters = {"collection": "users", "order_by": {"asc": "name"}}
        result = api.shodo_query_store(filters)

        assert len(result) == 3
        names = [user["name"] for user in result]
        assert names == sorted(names)

    def test_shodo_query_store_with_limit(self, api: API):
        """Test limiting number of returned store items"""
        filters = {"collection": "products", "limit": 1}
        result = api.shodo_query_store(filters)

        assert len(result) == 1
        assert result[0]["name"] == "Widget"

    def test_shodo_query_store_with_offset(self, api: API):
        """Test offsetting returned store items"""
        filters = {"collection": "products", "offset": 1}
        result = api.shodo_query_store(filters)

        assert len(result) == 1
        assert result[0]["name"] == "Gadget"

    def test_shodo_query_store_no_matches(self, api: API):
        """Test when filters match no store items"""
        filters = {"collection": "users", "where": {"name": {"equals": "Nonexistent"}}}
        result = api.shodo_query_store(filters)

        assert len(result) == 0

    def test_shodo_query_store_invalid_collection(self, api: API):
        """Test shodo_query_store with invalid collection name"""
        filters = {"collection": "invalid_collection"}
        with pytest.raises(ValueError):
            api.shodo_query_store(filters)

    def test_shodo_query_store_single_item_collection(self, api: API):
        """Test shodo_query_store with a collection that is a single dictionary item"""
        filters = {"collection": "single_item"}
        result = api.shodo_query_store(filters)

        assert len(result) == 1
        assert result[0]["name"] == "Solo"

    def test_shodo_query_store_empty_collection(self, api: API):
        """Test shodo_query_store with an empty collection"""
        api.context.render_args["empty_collection"] = []
        filters = {"collection": "empty_collection"}
        result = api.shodo_query_store(filters)

        assert len(result) == 0

    # Tests for shodo_get_excerpt
    def test_shodo_get_excerpt_single_paragraph(self, api: API):
        """Test getting excerpt from single paragraph"""
        content = "<p>This is a test paragraph with some content.</p>"
        result = api.shodo_get_excerpt(content, length=20)

        assert result == "This is a test..."

    def test_shodo_get_excerpt_multiple_paragraphs(self, api: API):
        """Test getting excerpt from multiple paragraphs"""
        content = """
        <p>First paragraph with some text.</p>
        <p>Second paragraph with more text.</p>
        <p>Third paragraph.</p>
        """
        result = api.shodo_get_excerpt(content, length=50)

        assert "First paragraph" in result
        assert "Second paragraph" in result
        assert result.endswith("...")

    def test_shodo_get_excerpt_with_html_tags(self, api: API):
        """Test that HTML tags are removed from excerpt"""
        content = "<p>This has <strong>bold</strong> and <em>italic</em> text.</p>"
        result = api.shodo_get_excerpt(content, length=50)

        assert "<strong>" not in result
        assert "<em>" not in result
        assert "bold" in result
        assert "italic" in result

    def test_shodo_get_excerpt_no_paragraph_tags(self, api: API):
        """Test excerpt from content without paragraph tags"""
        content = "<div>This is content in a div tag.</div>"
        result = api.shodo_get_excerpt(content, length=16)

        assert result == "This is content..."

    def test_shodo_get_excerpt_exact_length(self, api: API):
        """Test excerpt when content is exactly at length limit"""
        content = "<p>Exactly twenty chars</p>"
        result = api.shodo_get_excerpt(content, length=23)

        assert result == "Exactly twenty chars"
        assert not result.endswith("...")

    def test_shodo_get_excerpt_shorter_than_limit(self, api: API):
        """Test excerpt when content is shorter than limit"""
        content = "<p>Short text</p>"
        result = api.shodo_get_excerpt(content, length=100)

        assert result == "Short text"
        assert not result.endswith("...")

    def test_shodo_get_excerpt_default_length(self, api: API):
        """Test excerpt with default length parameter"""
        content = "<p>" + "x" * 150 + "</p>"
        result = api.shodo_get_excerpt(content)

        assert len(result) <= 103  # 100 + "..."
        assert result.endswith("...")

    def test_shodo_get_excerpt_truncate_at_word_boundary(self, api: API):
        """Test that excerpt truncates at word boundaries"""
        content = "<p>This is a longer sentence that should be truncated properly.</p>"
        result = api.shodo_get_excerpt(content, length=25)

        assert result.endswith("...")
        assert not result.endswith(" ...")  # Should not have trailing space

    def test_shodo_get_excerpt_with_front_matter(self, api: API):
        """Test that front matter is removed from excerpt"""
        content = """
        @frontmatter
        {
            "head_extra": "<p>This should not be included in the excerpt!</p>"
        }
        @endfrontmatter
        <p>This is the actual content.</p>
        """
        result = api.shodo_get_excerpt(content, length=50)

        assert "title:" not in result
        assert "Test Post" not in result
        assert "This is the actual content." in result

    def test_shodo_get_excerpt_empty_content(self, api: API):
        """Test excerpt from empty content"""
        content = ""
        result = api.shodo_get_excerpt(content, length=100)

        assert result == ""

    def test_shodo_get_excerpt_whitespace_only(self, api: API):
        """Test excerpt from whitespace-only content"""
        content = "   \n\n   "
        result = api.shodo_get_excerpt(content, length=100)

        assert result == ""

    def test_shodo_get_excerpt_nested_html(self, api: API):
        """Test excerpt with nested HTML structures"""
        content = """
        <div>
            <p>First paragraph in div.</p>
            <section>
                <p>Second paragraph in section.</p>
            </section>
        </div>
        """
        result = api.shodo_get_excerpt(content, length=50)

        assert "<div>" not in result
        assert "<section>" not in result
        assert "First paragraph" in result
        assert "Second paragraph" in result

    # Tests for get_rfc822
    def test_get_rfc822_with_valid_datetime(self, api: API):
        """Test get_rfc822 with a valid datetime object"""
        dt = datetime(2025, 1, 15, 14, 30, 0)
        result = api.get_rfc822(dt)

        assert result == "Wed, 15 Jan 2025 14:30:00 +0000"

    def test_get_rfc822_with_string_input(self, api: API, caplog):
        """Test get_rfc822 with string input returns minimal date and logs warning"""
        result = api.get_rfc822("2025-01-15")

        assert "1000" in result  # Year should be 1000 (minimal date)
        assert "[warn] get_rfc822 received a string instead of datetime" in caplog.text

    def test_get_rfc822_with_none_input(self, api: API, caplog):
        """Test get_rfc822 with None input returns minimal date and logs warning"""
        result = api.get_rfc822(None)

        assert "1000" in result  # Year should be 1000 (minimal date)
        assert "[warn] get_rfc822 received None instead of datetime" in caplog.text

    def test_get_rfc822_format_correctness(self, api: API):
        """Test that get_rfc822 produces correct RFC 822 format"""
        dt = datetime(2025, 12, 25, 23, 59, 59)
        result = api.get_rfc822(dt)

        # Check format: Day, DD Mon YYYY HH:MM:SS +0000
        assert result == "Thu, 25 Dec 2025 23:59:59 +0000"
        assert result.endswith("+0000")  # Should always be UTC

    def test_get_rfc822_with_leap_year(self, api: API):
        """Test get_rfc822 with leap year date"""
        dt = datetime(2024, 2, 29, 12, 0, 0)
        result = api.get_rfc822(dt)

        assert result == "Thu, 29 Feb 2024 12:00:00 +0000"

    # Tests for rel_to_abs
    def test_rel_to_abs_with_href_links(self, api: API):
        """Test converting relative href URLs to absolute"""
        html = '<a href="/blog/post">Link</a><a href="/about">About</a>'
        result = api.rel_to_abs(html, "https://example.com")

        assert 'href="https://example.com/blog/post"' in result
        assert 'href="https://example.com/about"' in result

    def test_rel_to_abs_with_src_attributes(self, api: API):
        """Test converting relative src URLs to absolute"""
        html = '<img src="/images/photo.jpg"><script src="/js/main.js"></script>'
        result = api.rel_to_abs(html, "https://example.com")

        assert 'src="https://example.com/images/photo.jpg"' in result
        assert 'src="https://example.com/js/main.js"' in result

    def test_rel_to_abs_preserves_absolute_urls(self, api: API):
        """Test that absolute URLs are not modified"""
        html = '<a href="https://other.com/page">External</a>'
        result = api.rel_to_abs(html, "https://example.com")

        assert 'href="https://other.com/page"' in result

    def test_rel_to_abs_preserves_anchor_links(self, api: API):
        """Test that anchor links (#section) are not modified"""
        html = '<a href="#section">Jump</a>'
        result = api.rel_to_abs(html, "https://example.com")

        assert 'href="#section"' in result

    def test_rel_to_abs_with_no_base_url(self, api: API):
        """Test rel_to_abs with no base URL returns original content"""
        html = '<a href="/blog">Link</a>'
        result = api.rel_to_abs(html, None)

        assert result == html

    def test_rel_to_abs_with_empty_base_url(self, api: API):
        """Test rel_to_abs with empty base URL returns original content"""
        html = '<a href="/blog">Link</a>'
        result = api.rel_to_abs(html, "")

        assert result == html

    def test_rel_to_abs_uses_context_url_origin(self, api: API):
        """Test rel_to_abs uses url_origin from context when base_url not provided"""
        api.context.render_args["config"] = {}
        api.context.render_args["config"]["url_origin"] = "https://mysite.com"
        html = '<a href="/page">Link</a>'
        result = api.rel_to_abs(html)

        assert 'href="https://mysite.com/page"' in result

    def test_rel_to_abs_preserves_code_blocks(self, api: API):
        """Test that URLs in code blocks are not modified"""
        html = """
        <p>Check out <a href="/api">our API</a></p>
        <code>fetch('/api/data')</code>
        <pre>curl https://example.com/api</pre>
        """
        result = api.rel_to_abs(html, "https://example.com")

        assert 'href="https://example.com/api"' in result
        assert "fetch('/api/data')" in result  # Should not be modified
        assert "curl https://example.com/api" in result  # Should not be modified

    def test_rel_to_abs_with_single_and_double_quotes(self, api: API):
        """Test rel_to_abs handles both single and double quoted attributes"""
        html = "<a href='/blog'>Link1</a><a href=\"/about\">Link2</a>"
        result = api.rel_to_abs(html, "https://example.com")

        assert 'href="https://example.com/blog"' in result
        assert 'href="https://example.com/about"' in result

    def test_rel_to_abs_with_query_parameters(self, api: API):
        """Test rel_to_abs preserves query parameters"""
        html = '<a href="/search?q=test&page=2">Search</a>'
        result = api.rel_to_abs(html, "https://example.com")

        assert 'href="https://example.com/search?q=test&page=2"' in result

    def test_rel_to_abs_with_fragments(self, api: API):
        """Test rel_to_abs preserves URL fragments"""
        html = '<a href="/page#section">Link</a>'
        result = api.rel_to_abs(html, "https://example.com")

        assert 'href="https://example.com/page#section"' in result

    def test_rel_to_abs_complex_html(self, api: API):
        """Test rel_to_abs with complex nested HTML"""
        html = """
        <article>
            <h1><a href="/blog/post-1">Post Title</a></h1>
            <img src="/images/hero.jpg" alt="Hero">
            <p>Read more at <a href="/blog">our blog</a>.</p>
            <code>const url = '/api/data';</code>
        </article>
        """
        result = api.rel_to_abs(html, "https://example.com")

        assert 'href="https://example.com/blog/post-1"' in result
        assert 'src="https://example.com/images/hero.jpg"' in result
        assert 'href="https://example.com/blog"' in result
        assert "const url = '/api/data';" in result  # Code should not be modified

    def test_rel_to_abs_with_nested_code_and_pre(self, api: API):
        """Test that nested code and pre blocks are preserved"""
        html = """
        <pre><code>
        <a href="/test">Don't modify this</a>
        <img src="/image.jpg">
        </code></pre>
        <a href="/real-link">But modify this</a>
        """
        result = api.rel_to_abs(html, "https://example.com")

        assert '<a href="/test">Don\'t modify this</a>' in result
        assert '<img src="/image.jpg">' in result
        assert 'href="https://example.com/real-link"' in result

    # Tests for current_dt
    def test_current_dt_returns_datetime(self, api: API):
        """Test current_dt returns a datetime object"""
        result = api.current_dt()

        assert isinstance(result, datetime)

    def test_current_dt_is_utc(self, api: API):
        """Test current_dt returns UTC timezone"""
        result = api.current_dt()

        assert result.tzinfo == timezone.utc

"""
Tests for the HTMLRootLayoutBuilder class
"""

import pytest
from shodo_ssg.html_root_layout_builder import HTMLRootLayoutBuilder


# pylint: disable=too-many-public-methods
class TestHTMLRootLayoutBuilder:
    """Test suite for HTMLRootLayoutBuilder"""

    @pytest.fixture
    def builder(self):
        """Fixture to provide a fresh HTMLRootLayoutBuilder instance"""
        return HTMLRootLayoutBuilder()

    @pytest.fixture
    def minimal_render_args(self):
        """Fixture providing minimal render arguments"""
        return {
            "config": {
                "metadata": {
                    "title": "Test Site",
                    "charset": "UTF-8",
                    "lang": "en",
                }
            }
        }

    @pytest.fixture
    def full_render_args(self):
        """Fixture providing complete render arguments with all metadata"""
        return {
            "config": {
                "metadata": {
                    "title": "Test Site",
                    "charset": "UTF-8",
                    "lang": "en",
                    "description": "A test site description",
                    "keywords": ["test", "ssg", "python"],
                    "author": "Test Author",
                    "theme_color": "#ffffff",
                    "og_image": "https://example.com/image.jpg",
                    "og_image_alt": "Test image",
                    "og_title": "Test OG Title",
                    "og_description": "Test OG Description",
                    "og_url": "https://example.com",
                    "og_type": "website",
                    "og_site_name": "Test Site",
                    "og_locale": "en_US",
                    "canonical": "https://example.com/canonical",
                    "google_font_link": "https://fonts.googleapis.com/css2?family=Roboto",
                    "preconnects": ["https://example.com", "https://cdn.example.com"],
                    "stylesheets": ["/styles/custom.css", "/styles/theme.css"],
                    "robots": "index, follow",
                    "head_extra": ['<meta name="custom" content="value">'],
                    "body_id": "main-page",
                    "body_class": "home-page active",
                }
            }
        }

    def test_get_doc_head_minimal(
        self, builder: HTMLRootLayoutBuilder, minimal_render_args
    ):
        """Test get_doc_head with minimal metadata"""
        result = builder.get_doc_head(minimal_render_args)
        # Strip all newlines and extra spaces for easier assertions
        result = " ".join(result.split())

        assert "<!DOCTYPE html>" in result
        assert '<html lang="en">' in result
        assert '<meta charset="UTF-8">' in result
        assert "<title>Test Site</title>" in result
        assert '<link rel="icon" type="image/x-icon" href="/favicon.ico">' in result
        assert '<link href="/static/styles/main.css" rel="stylesheet" />' in result
        assert "<body" in result

    def test_get_doc_head_with_front_matter_override(
        self, builder: HTMLRootLayoutBuilder, minimal_render_args
    ):
        """Test that front matter overrides global metadata"""
        front_matter = {
            "title": "Page Title",
            "description": "Page description",
            "lang": "fr",
        }
        result = builder.get_doc_head(minimal_render_args, front_matter=front_matter)
        # Strip all newlines and extra spaces for easier assertions
        result = " ".join(result.split())

        assert "<title>Page Title</title>" in result
        assert '<meta name="description" content="Page description">' in result
        assert '<html lang="fr">' in result

    def test_get_doc_head_applies_global_metadata_defaults(
        self, builder: HTMLRootLayoutBuilder
    ):
        """Test that global metadata defaults are applied when missing"""
        render_args = {
            "config": {
                "metadata": {
                    "title": "Test Site",
                    "description": "A test site description",
                }
            }
        }
        result = builder.get_doc_head(render_args)
        # Strip all newlines and extra spaces for easier assertions
        result = " ".join(result.split())

        assert "<title>Test Site</title>" in result
        assert '<meta name="description" content="A test site description">' in result

    def test_get_doc_head_with_body_attributes(
        self, builder: HTMLRootLayoutBuilder, minimal_render_args
    ):
        """Test that body_id and body_class are properly added to body tag"""
        front_matter = {
            "body_id": "custom-id",
            "body_class": "page-class another-class",
        }
        result = builder.get_doc_head(minimal_render_args, front_matter=front_matter)
        # Strip all newlines and extra spaces for easier assertions
        result = " ".join(result.split())

        assert '<body id="custom-id" class="page-class another-class">' in result

    def test_get_doc_head_full_metadata(
        self, builder: HTMLRootLayoutBuilder, full_render_args
    ):
        """Test get_doc_head with complete metadata"""
        result = builder.get_doc_head(full_render_args)
        # Strip all newlines and extra spaces for easier assertions
        result = " ".join(result.split())

        # Basic tags
        assert "<title>Test Site</title>" in result
        assert '<meta name="description" content="A test site description">' in result
        assert '<meta name="keywords" content="test,ssg,python">' in result
        assert '<meta name="author" content="Test Author">' in result

        # Theme and color
        assert '<meta name="theme-color" content="#ffffff">' in result

        # Open Graph tags
        assert (
            '<meta property="og:image" content="https://example.com/image.jpg">'
            in result
        )
        assert '<meta property="og:image:alt" content="Test image">' in result
        assert '<meta property="og:title" content="Test OG Title">' in result
        assert (
            '<meta property="og:description" content="Test OG Description">' in result
        )
        assert '<meta property="og:url" content="https://example.com">' in result
        assert '<meta property="og:type" content="website">' in result
        assert '<meta property="og:site_name" content="Test Site">' in result
        assert '<meta property="og:locale" content="en_US">' in result

        # SEO tags
        assert '<link rel="canonical" href="https://example.com/canonical">' in result
        assert '<meta name="robots" content="index, follow">' in result

        # Custom resources
        assert "https://fonts.googleapis.com/css2?family=Roboto" in result
        assert '<link rel="preconnect" href="https://example.com">' in result
        assert '<link rel="preconnect" href="https://cdn.example.com">' in result
        assert '<link rel="stylesheet" href="/styles/custom.css">' in result
        assert '<link rel="stylesheet" href="/styles/theme.css">' in result

        # Custom head extra
        assert '<meta name="custom" content="value">' in result

        # Body attributes
        assert '<body id="main-page" class="home-page active">' in result

    def test_get_doc_head_custom_styles_and_favicon(
        self, builder: HTMLRootLayoutBuilder, minimal_render_args
    ):
        """Test custom stylesheet and favicon links"""
        result = builder.get_doc_head(
            minimal_render_args,
            styles_link="/custom/styles.css",
            favicon_link='<link rel="icon" type="image/png" href="/custom-favicon.png">',
        )
        # Strip all newlines and extra spaces for easier assertions
        result = " ".join(result.split())

        assert '<link href="/custom/styles.css" rel="stylesheet" />' in result
        assert '<link rel="icon" type="image/png" href="/custom-favicon.png">' in result

    def test_get_doc_head_empty_optional_fields(self, builder: HTMLRootLayoutBuilder):
        """Test that empty optional fields don't produce empty tags"""
        render_args = {
            "metadata": {
                "title": "Test",
                "charset": "UTF-8",
                "description": "",
                "keywords": "",
                "author": "",
                "theme_color": "",
                "og_image": "",
            }
        }
        result = builder.get_doc_head(render_args)
        # Strip all newlines and extra spaces for easier assertions
        result = " ".join(result.split())

        # Should not contain empty meta tags
        assert 'content=""' not in result

    def test_get_doc_head_keywords_as_string(
        self, builder: HTMLRootLayoutBuilder, minimal_render_args
    ):
        """Test that keywords can be provided as a string"""
        front_matter = {"keywords": "single,keyword,string"}
        result = builder.get_doc_head(minimal_render_args, front_matter=front_matter)

        assert '<meta name="keywords" content="single,keyword,string">' in result

    def test_get_doc_head_google_font_link(
        self, builder: HTMLRootLayoutBuilder, minimal_render_args
    ):
        """Test Google Font link inclusion"""
        front_matter = {
            "google_font_link": "https://fonts.googleapis.com/css2?family=Open+Sans"
        }
        result = builder.get_doc_head(minimal_render_args, front_matter=front_matter)

        assert "https://fonts.googleapis.com" in result
        assert "https://fonts.gstatic.com" in result
        assert "family=Open+Sans" in result

    def test_get_doc_head_preconnects_as_string(
        self, builder: HTMLRootLayoutBuilder, minimal_render_args
    ):
        """Test that preconnects can be provided as a single string"""
        front_matter = {"preconnects": "https://single-preconnect.com"}
        result = builder.get_doc_head(minimal_render_args, front_matter=front_matter)

        assert '<link rel="preconnect" href="https://single-preconnect.com">' in result

    def test_get_doc_head_stylesheets_as_string(
        self, builder: HTMLRootLayoutBuilder, minimal_render_args
    ):
        """Test that stylesheets can be provided as a single string"""
        front_matter = {"stylesheets": "/single/stylesheet.css"}
        result = builder.get_doc_head(minimal_render_args, front_matter=front_matter)

        assert '<link rel="stylesheet" href="/single/stylesheet.css">' in result

    def test_get_doc_head_head_extra_as_string(
        self, builder: HTMLRootLayoutBuilder, minimal_render_args
    ):
        """Test that head_extra can be provided as a single string"""
        front_matter = {"head_extra": '<meta name="test" content="value">'}
        result = builder.get_doc_head(minimal_render_args, front_matter=front_matter)

        assert '<meta name="test" content="value">' in result

    def test_get_doc_tail_default(self, builder: HTMLRootLayoutBuilder):
        """Test get_doc_tail with default script link"""
        result = builder.get_doc_tail()

        assert '<script type="module" src="/static/scripts/main.js"></script>' in result
        assert "</body>" in result
        assert "</html>" in result

    def test_get_doc_tail_custom_script(self, builder: HTMLRootLayoutBuilder):
        """Test get_doc_tail with custom script link"""
        result = builder.get_doc_tail(script_link="/custom/script.js")

        assert '<script type="module" src="/custom/script.js"></script>' in result
        assert "</body>" in result
        assert "</html>" in result

    def test_merge_head_data(self, builder: HTMLRootLayoutBuilder):
        """Test _merge_head_data properly merges front matter and global metadata"""
        global_metadata = {
            "title": "Global Title",
            "description": "Global Description",
            "author": "Global Author",
        }
        front_matter = {
            "title": "Page Title",
            "description": "Page Description",
        }

        # pylint: disable=protected-access
        result = builder._merge_head_data(front_matter, global_metadata)

        assert result["title"] == "Page Title"  # Front matter overrides
        assert result["description"] == "Page Description"  # Front matter overrides
        assert result["author"] == "Global Author"  # Falls back to global

    def test_merge_head_data_defaults(self, builder: HTMLRootLayoutBuilder):
        """Test _merge_head_data provides defaults when no metadata present"""
        result = builder._merge_head_data({}, {})  # pylint: disable=protected-access

        assert result["title"] == "Shodo SSG"
        assert result["lang"] == "en"
        assert result["charset"] == "UTF-8"
        assert result["description"] == ""
        assert result["keywords"] == ""

    def test_format_head_data_as_html(self, builder: HTMLRootLayoutBuilder):
        """Test _format_head_data_as_html creates proper HTML tags"""
        head_content = {
            "charset": "UTF-8",
            "title": "Test Title",
            "description": "Test Description",
            "keywords": ["test", "keywords"],
            "author": "Test Author",
            "theme_color": "#000000",
            "og_image": "https://example.com/image.jpg",
            "og_image_alt": "Alt text",
            "og_title": "OG Title",
            "og_description": "OG Description",
            "og_url": "https://example.com",
            "og_type": "website",
            "og_site_name": "Site Name",
            "og_locale": "en_US",
            "canonical": "https://example.com/canonical",
            "google_font_link": "https://fonts.googleapis.com/css2?family=Roboto",
            "preconnects": ["https://example.com"],
            "stylesheets": ["/styles/main.css"],
            "robots": "index, follow",
            "head_extra": ['<meta name="custom" content="value">'],
        }

        # pylint: disable=protected-access
        result = builder._format_head_data_as_html(head_content)

        assert result["charset"] == '<meta charset="UTF-8">'
        assert result["title"] == "<title>Test Title</title>"
        assert (
            result["description"]
            == '<meta name="description" content="Test Description">'
        )
        assert result["keywords"] == '<meta name="keywords" content="test,keywords">'
        assert result["author"] == '<meta name="author" content="Test Author">'
        assert (
            result["canonical"]
            == '<link rel="canonical" href="https://example.com/canonical">'
        )

    def test_format_head_data_empty_values(self, builder: HTMLRootLayoutBuilder):
        """Test _format_head_data_as_html handles empty values correctly"""
        head_content = {
            "charset": "UTF-8",
            "title": "Test",
            "description": "",
            "keywords": "",
            "author": "",
            "theme_color": "",
            "og_image": "",
            "og_image_alt": "",
            "og_title": "",
            "og_description": "",
            "og_url": "",
            "og_type": "",
            "og_site_name": "",
            "og_locale": "",
            "canonical": "",
            "google_font_link": "",
            "preconnects": "",
            "stylesheets": "",
            "robots": "",
            "head_extra": "",
        }

        # pylint: disable=protected-access
        result = builder._format_head_data_as_html(head_content)

        # Required fields should have values
        assert result["charset"] != ""
        assert result["title"] != ""
        assert result["viewport"] != ""

        # Optional empty fields should be empty strings
        assert result["description"] == ""
        assert result["keywords"] == ""
        assert result["author"] == ""
        assert result["canonical"] == ""

    def test_no_metadata_in_render_args(self, builder: HTMLRootLayoutBuilder):
        """Test get_doc_head when render_args has no metadata key"""
        render_args = {}
        result = builder.get_doc_head(render_args)

        # Should use defaults
        assert "<title>Shodo SSG</title>" in result
        assert '<html lang="en">' in result
        assert '<meta charset="UTF-8">' in result

"""Tests for the front_matter_processor module."""

from shodo_ssg.front_matter_processor import FrontMatterProcessor


def test_front_matter_processor_init(
    front_matter_processor_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the __init__ method of the TemplateHandler class."""
    json_loader = front_matter_processor_dependencies
    front_matter_processor = FrontMatterProcessor(json_loader)

    assert front_matter_processor.json_loader


def test_front_matter_processor_get_front_matter_returns_front_matter_from_file(
    front_matter_processor_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the get_front_matter method of the TemplateHandler class."""
    json_loader = front_matter_processor_dependencies
    front_matter_processor = FrontMatterProcessor(json_loader)

    content = "@frontmatter\n"
    content += '{"title": "Test Article",\n"description": "This is a test article."}\n'
    content += "@endfrontmatter\n"
    content += "This is the content of the test article.\n"

    front_matter = front_matter_processor.get_front_matter(content)

    assert front_matter
    assert isinstance(front_matter, dict)
    assert "title" in front_matter
    assert "description" in front_matter
    assert front_matter["title"] == "Test Article"
    assert front_matter["description"] == "This is a test article."
    for key in front_matter:
        assert front_matter[key] != "This is the content of the test article."


def test_front_matter_processor_get_front_matter_returns_none_when_no_front_matter(
    front_matter_processor_dependencies,
):  # pylint: disable=redefined-outer-name
    """
    Test the get_front_matter method of the TemplateHandler class when
    no front matter is present.
    """
    json_loader = front_matter_processor_dependencies
    front_matter_processor = FrontMatterProcessor(json_loader)

    content = "This is the content of the test article without front matter.\n"

    front_matter = front_matter_processor.get_front_matter(content)

    assert front_matter is None


def test_front_matter_processor_get_front_matter_handles_complex_head_extra_tags(
    front_matter_processor_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the get_front_matter method with complex front matter content."""
    json_loader = front_matter_processor_dependencies
    front_matter_processor = FrontMatterProcessor(json_loader)

    content = r"""@frontmatter
    {
        "title": "Complex Article",
        "description": "This article has complex front matter.",
        "head_extra": [
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
            "<link rel=\"stylesheet\" href=\"/styles/main.css\">"
        ]
    }
    @endfrontmatter
    This is the content of the complex article.
    """
    front_matter = front_matter_processor.get_front_matter(content)
    assert front_matter
    assert isinstance(front_matter, dict)
    assert "title" in front_matter
    assert "description" in front_matter
    assert "head_extra" in front_matter
    assert front_matter["title"] == "Complex Article"
    assert front_matter["description"] == "This article has complex front matter."
    assert isinstance(front_matter["head_extra"], list)
    assert len(front_matter["head_extra"]) == 2
    assert (
        front_matter["head_extra"][0]
        == '<meta name="viewport" content="width=device-width, initial-scale=1">'
    )
    assert (
        front_matter["head_extra"][1]
        == '<link rel="stylesheet" href="/styles/main.css">'
    )


def test_front_matter_processor_get_front_matter_handles_single_quotes_in_head_extra_tags(
    front_matter_processor_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the get_front_matter method with single quotes in head_extra tags."""
    json_loader = front_matter_processor_dependencies
    front_matter_processor = FrontMatterProcessor(json_loader)

    content = r"""@frontmatter
    {
        "title": "Single Quote Article",
        "description": "This article has single quotes in head extra.",
        "head_extra": [
            "<meta name='viewport' content='width=device-width, initial-scale=1'>",
            "<link rel='stylesheet' href='/styles/main.css'>",
            '<script src="/scripts/custom.js"></script>'
        ]
    }
    @endfrontmatter
    This is the content of the single quote article.
    """
    front_matter = front_matter_processor.get_front_matter(content)
    assert front_matter
    assert isinstance(front_matter, dict)
    assert "title" in front_matter
    assert "description" in front_matter
    assert "head_extra" in front_matter
    assert front_matter["title"] == "Single Quote Article"
    assert (
        front_matter["description"] == "This article has single quotes in head extra."
    )
    assert isinstance(front_matter["head_extra"], list)
    assert len(front_matter["head_extra"]) == 3
    assert (
        front_matter["head_extra"][0]
        == '<meta name="viewport" content="width=device-width, initial-scale=1">'
    )
    assert (
        front_matter["head_extra"][1]
        == '<link rel="stylesheet" href="/styles/main.css">'
    )
    assert front_matter["head_extra"][2] == '<script src="/scripts/custom.js"></script>'


def test_front_matter_processor_get_front_matter_handles_ld_json_in_head_extra_tags(
    front_matter_processor_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the get_front_matter method with ld+json script in head_extra tags."""
    json_loader = front_matter_processor_dependencies
    front_matter_processor = FrontMatterProcessor(json_loader)

    content = r"""@frontmatter
    {
        "title": "LD+JSON Article",
        "description": "This article has ld+json in head extra.",
        "head_extra": [
            "<script type='application/ld+json'>{ \"@context\": \"https://schema.org\", \"@type\": \"Article\", \"headline\": \"LD+JSON Article\", \"description\": \"This article has ld+json in head extra.\" }</script>",
            "<script type='application/ld+json'>{ '@context': 'https://schema.org', '@type': 'Article', 'headline': 'LD+JSON Article', 'description': 'This article has ld+json in head extra.' }</script>",
            '<script type="application/ld+json">{ "@context": "https://schema.org", "@type": "Article", "headline": "LD+JSON Article", "description": "This article has ld+json in head extra." }</script>',
            "<script type='application/ld+json'>{\n \"@context\": \"https://schema.org\",\n \"@type\": \"Article\",\n \"headline\": \"LD+JSON Article\",\n \"description\": \"This article has ld+json in head extra.\"\n }</script>"
        ]
    }
    @endfrontmatter
    This is the content of the ld+json article.
    """
    front_matter = front_matter_processor.get_front_matter(content)
    assert front_matter
    assert isinstance(front_matter, dict)
    assert "title" in front_matter
    assert "description" in front_matter
    assert "head_extra" in front_matter
    assert front_matter["title"] == "LD+JSON Article"
    assert front_matter["description"] == "This article has ld+json in head extra."
    assert isinstance(front_matter["head_extra"], list)
    assert len(front_matter["head_extra"]) == 4
    assert " ".join(
        front_matter["head_extra"][0]
        .strip()
        .replace("\n", "")
        .replace("\t", "")
        .split()
    ) == " ".join(
        '<script type="application/ld+json">{\n'
        '                "@context": "https://schema.org",\n'
        '                "@type": "Article",\n'
        '                "headline": "LD+JSON Article",\n'
        '                "description": "This article has ld+json in head extra."\n'
        "            }</script>".strip().replace("\n", "").replace("\t", "").split()
    )
    assert " ".join(
        front_matter["head_extra"][1]
        .strip()
        .replace("\n", "")
        .replace("\t", "")
        .split()
    ) == " ".join(
        '<script type="application/ld+json">{\n'
        '                "@context": "https://schema.org",\n'
        '                "@type": "Article",\n'
        '                "headline": "LD+JSON Article",\n'
        '                "description": "This article has ld+json in head extra."\n'
        "            }</script>".strip().replace("\n", "").replace("\t", "").split()
    )
    assert " ".join(
        front_matter["head_extra"][2]
        .strip()
        .replace("\n", "")
        .replace("\t", "")
        .split()
    ) == " ".join(
        '<script type="application/ld+json">{\n'
        '                "@context": "https://schema.org",\n'
        '                "@type": "Article",\n'
        '                "headline": "LD+JSON Article",\n'
        '                "description": "This article has ld+json in head extra."\n'
        "            }</script>".strip().replace("\n", "").replace("\t", "").split()
    )
    assert " ".join(
        front_matter["head_extra"][3]
        .strip()
        .replace("\n", "")
        .replace("\t", "")
        .split()
    ) == " ".join(
        '<script type="application/ld+json">{\n'
        '                "@context": "https://schema.org",\n'
        '                "@type": "Article",\n'
        '                "headline": "LD+JSON Article",\n'
        '                "description": "This article has ld+json in head extra."\n'
        "            }</script>".strip().replace("\n", "").replace("\t", "").split()
    )


def test_front_matter_processor_clear_front_matter_returns_content_without_front_matter(
    front_matter_processor_dependencies,
):  # pylint: disable=redefined-outer-name
    """Test the clear_front_matter method of the TemplateHandler class."""
    json_loader = front_matter_processor_dependencies
    front_matter_processor = FrontMatterProcessor(json_loader)

    content = """
    @frontmatter
    {"title": "Test Article", "description": "This is a test article."}
    @endfrontmatter
    This is the content of the test article.
    <p>@frontmatter
    {"title": "Another Article", "description": "This is another test article."}
    @endfrontmatter</p>
    This is the content of another test article.
    """

    expected_content = """
    This is the content of the test article.
    This is the content of another test article.
    """

    result = front_matter_processor.clear_front_matter(file_path=None, content=content)

    # Remove all whitespace
    result = "".join(result.split())
    expected_content = "".join(expected_content.split())

    assert result == expected_content

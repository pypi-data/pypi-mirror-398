"""Tests for the data_loader module."""

import json
import os

from shodo_ssg.data_loader import (
    MarkdownLoader,
    JSONLoader,
    SettingsLoader,
)


def test_markdown_loader_list_files(
    settings_dict,
):  # pylint: disable=redefined-outer-name
    """Test the list_files method of the MarkdownLoader class."""
    loader = MarkdownLoader(settings_dict)
    files = loader.list_files()
    assert isinstance(files, list)
    assert isinstance(files[0], tuple)
    md_path, md_file_name = files[0]
    assert settings_dict["markdown_path"] in md_path
    assert md_file_name.endswith(".md")


def test_markdown_loader_load_args(
    settings_dict,
):  # pylint: disable=redefined-outer-name
    """Test the load_args method of the MarkdownLoader class."""
    loader = MarkdownLoader(settings_dict)
    args = loader.load_args()
    assert isinstance(args, dict)


def test_markdown_loader_load_pages(
    settings_dict,
):  # pylint: disable=redefined-outer-name
    """Test the load_pages method of the MarkdownLoader class."""
    loader = MarkdownLoader(settings_dict)
    pages = loader.load_pages()
    assert isinstance(pages, list)


def test_json_loader_list_files(
    settings_dict,
):  # pylint: disable=redefined-outer-name
    """Test the list_files method of the JSONLoader class."""
    loader = JSONLoader(settings_dict)
    files = loader.list_files()
    json_path, json_file_name = files[0]
    assert isinstance(files, list)
    assert isinstance(files[0], tuple)
    assert "src/store/" in json_path
    assert json_file_name.endswith(".json")


def test_json_loader_load_args(
    settings_dict,
):  # pylint: disable=redefined-outer-name
    """Test the load_args method of the JSONLoader class."""
    loader = JSONLoader(settings_dict)
    args = loader.load_args()
    assert isinstance(args, dict)


def test_json_loader_load_args_handles_head_extra_metadata(
    settings_dict,
):  # pylint: disable=redefined-outer-name
    """Test that JSONLoader correctly loads head_extra metadata."""
    loader = JSONLoader(settings_dict)
    args = loader.load_args()
    config = args.get("config", {})
    metadata = config.get("metadata", {})
    assert isinstance(metadata, dict)
    assert "head_extra" in metadata
    head_extra = metadata["head_extra"]
    assert isinstance(head_extra, list)
    assert len(head_extra) == 8  # There are 8 elements in the head_extra list

    assert " ".join(
        head_extra[0].strip().replace("\n", "").replace("\t", "").split()
    ) == " ".join(
        '<script type="application/ld+json">{\n'
        '                "@context": "https://schema.org",\n'
        '                "@type": "Article",\n'
        '                "headline": "LD+JSON Article",\n'
        '                "description": "This article has ld+json in head extra."\n'
        "            }</script>".strip().replace("\n", "").replace("\t", "").split()
    )
    assert " ".join(
        head_extra[1].strip().replace("\n", "").replace("\t", "").split()
    ) == " ".join(
        '<script type="application/ld+json">{\n'
        '                "@context": "https://schema.org",\n'
        '                "@type": "Article",\n'
        '                "headline": "LD+JSON Article",\n'
        '                "description": "This article has ld+json in head extra."\n'
        "            }</script>".strip().replace("\n", "").replace("\t", "").split()
    )
    assert " ".join(
        head_extra[2].strip().replace("\n", "").replace("\t", "").split()
    ) == " ".join(
        '<script type="application/ld+json">{\n'
        '                "@context": "https://schema.org",\n'
        '                "@type": "Article",\n'
        '                "headline": "LD+JSON Article",\n'
        '                "description": "This article has ld+json in head extra."\n'
        "            }</script>".strip().replace("\n", "").replace("\t", "").split()
    )

    # Also assert the remaining elements are rendered correctly in double quotes
    assert " ".join(
        head_extra[3].strip().replace("\n", "").replace("\t", "").split()
    ) == " ".join(
        (
            '<link rel="icon" href="/static/images/favicons/site-favicon-light.ico"'
            + ' type="image/x-icon" media="(prefers-color-scheme: light)">'
        )
        .strip()
        .replace("\n", "")
        .replace("\t", "")
        .split()
    )
    assert " ".join(
        head_extra[4].strip().replace("\n", "").replace("\t", "").split()
    ) == " ".join(
        (
            '<link rel="icon" href="/static/images/favicons/site-favicon-dark.ico"'
            + ' type="image/x-icon" media="(prefers-color-scheme: dark)">'
        )
        .strip()
        .replace("\n", "")
        .replace("\t", "")
        .split()
    )
    assert " ".join(
        head_extra[5].strip().replace("\n", "").replace("\t", "").split()
    ) == " ".join(
        '<link rel="apple-touch-icon" href="/static/images/favicons/site-favicon-dark.png">'.strip()
        .replace("\n", "")
        .replace("\t", "")
        .split()
    )
    assert " ".join(
        head_extra[6].strip().replace("\n", "").replace("\t", "").split()
    ) == " ".join(
        '<script type="text/javascript" src="/static/scripts/theme-loader.js"></script>'.strip()
        .replace("\n", "")
        .replace("\t", "")
        .split()
    )
    assert " ".join(
        head_extra[7].strip().replace("\n", "").replace("\t", "").split()
    ) == " ".join(
        '<link rel="stylesheet" href="/static/styles/extra-styles.css">'.strip()
        .replace("\n", "")
        .replace("\t", "")
        .split()
    )


def test_json_loader_load_args_handles_quotes_in_values(
    settings_dict,
):  # pylint: disable=redefined-outer-name
    """Test that JSONLoader correctly loads JSON with quotes in values."""
    loader = JSONLoader(settings_dict)
    args = loader.load_args()
    quotes = args.get("quotes", {})
    assert isinstance(quotes, dict)
    assert "quote" in quotes
    assert quotes["quote"] == "She said, 'This is a great article!' and smiled."
    assert "another_quote" in quotes
    assert quotes["another_quote"] == 'He replied, "Indeed, it is!"'
    assert "third_quote" in quotes
    assert quotes["third_quote"] == 'She said, "Let\'s test quotes!"'
    assert "fourth_quote" in quotes
    assert quotes["fourth_quote"] == 'He responded, "Let\'s do it!"'


def test_settings_loader_data(
    temp_project_path,
    settings_dict,
):  # pylint: disable=redefined-outer-name
    """Test the data attribute of the SettingsLoader class."""
    temp_abs_path = os.path.abspath(temp_project_path)
    loader = SettingsLoader(temp_abs_path)
    data = loader.data

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


def test_settings_loader_load_args(
    temp_project_path,
):  # pylint: disable=redefined-outer-name
    """Test the load_args method of the SettingsLoader class."""
    temp_abs_path = os.path.abspath(temp_project_path)
    loader = SettingsLoader(temp_abs_path)
    args = loader.load_args()
    settings_path = os.path.join(temp_project_path, "build_settings.json")
    with open(settings_path, "r", encoding="utf-8") as settings_file:
        test_settings = json.load(settings_file)

    assert isinstance(args, dict)
    assert args["build_dir"] == test_settings["build_dir"]
    assert args["markdown_path"] == test_settings["markdown_path"]
    assert args["json_config_path"] == test_settings["json_config_path"]
    assert args["favicon_path"] == test_settings["favicon_path"]
    assert args["scripts_path"] == test_settings["scripts_path"]
    assert args["assets_path"] == test_settings["assets_path"]
    assert args["styles_path"] == test_settings["styles_path"]


def test_json_loader_format_string_converts_single_quotes_to_double(
    settings_dict,
):
    """Test that single quotes are converted to double quotes"""
    loader = JSONLoader(settings_dict)
    input_str = "{'key': 'value'}"
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"key": "value"}'


def test_json_loader_format_string_removes_trailing_commas(
    settings_dict,
):
    """Test that trailing commas are removed"""
    loader = JSONLoader(settings_dict)
    input_str = '{"key": "value",}'
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"key": "value"}'


def test_json_loader_format_string_removes_newlines(
    settings_dict,
):
    """Test that newlines are removed"""
    loader = JSONLoader(settings_dict)
    input_str = '{\n"key": "value"\n}'
    result = loader.format_string_for_json_compatibility(input_str)

    assert "\n" not in result


def test_json_loader_format_string_quotes_unquoted_values(
    settings_dict,
):
    """Test that unquoted values are wrapped in quotes"""
    loader = JSONLoader(settings_dict)
    input_str = '{"key": value}'
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"key": "value"}'


def test_json_loader_format_string_preserves_numbers(
    settings_dict,
):
    """Test that numeric values remain unquoted"""
    loader = JSONLoader(settings_dict)
    input_str = '{"count": 42, "price": 19.99, "negative": -5}'
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"count": 42, "price": 19.99, "negative": -5}'


def test_json_loader_format_string_handles_booleans(
    settings_dict,
):
    """Test that boolean values are converted to lowercase"""
    loader = JSONLoader(settings_dict)
    input_str = '{"active": True, "disabled": False}'
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"active": true, "disabled": false}'


def test_json_loader_format_string_preserves_arrays(
    settings_dict,
):
    """Test that arrays are preserved correctly"""
    loader = JSONLoader(settings_dict)
    input_str = '{"tags": ["python", "web", "django"]}'
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"tags": ["python", "web", "django"]}'


def test_json_loader_format_string_handles_nested_objects(
    settings_dict,
):
    """Test that nested objects are handled correctly"""
    loader = JSONLoader(settings_dict)
    input_str = '{"user": {"name": "John", "age": 30}}'
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"user": {"name": "John", "age": 30}}'


def test_json_loader_format_string_handles_single_quotes_in_double_quoted_strings(
    settings_dict,
):
    """Test that single quotes inside double-quoted strings are preserved"""
    loader = JSONLoader(settings_dict)
    input_str = '{"quote": "She said, \'Hello!\'"}'
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"quote": "She said, \'Hello!\'"}'


def test_json_loader_format_string_handles_double_quotes_in_single_quoted_strings(
    settings_dict,
):
    """Test that double quotes inside single-quoted strings are escaped"""
    loader = JSONLoader(settings_dict)
    input_str = """{'quote': 'He said, "Hello!"'}"""
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"quote": "He said, \\"Hello!\\""}'


def test_json_loader_format_string_handles_escaped_single_quotes(
    settings_dict,
):
    """Test that escaped single quotes (apostrophes) are preserved"""
    loader = JSONLoader(settings_dict)
    input_str = """{'text': 'It\\'s a great day!'}"""
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"text": "It\'s a great day!"}'


def test_json_loader_format_string_handles_complex_quotes(
    settings_dict,
):
    """Test handling of complex quote scenarios"""
    loader = JSONLoader(settings_dict)
    input_str = """{
        "quote1": "She said, 'This is great!' and smiled.",
        "quote2": 'He replied, "Indeed, it is!"',
        "quote3": "She said, 'Let's test quotes!'",
        "quote4": 'He responded, "Let\\'s do it!"'
    }"""
    result = loader.format_string_for_json_compatibility(input_str)

    # Parse the result to verify it's valid JSON
    parsed = json.loads(result)
    assert parsed["quote1"] == "She said, 'This is great!' and smiled."
    assert parsed["quote2"] == 'He replied, "Indeed, it is!"'
    assert parsed["quote3"] == "She said, 'Let's test quotes!'"
    assert parsed["quote4"] == 'He responded, "Let\'s do it!"'


def test_json_loader_format_string_handles_trailing_commas_in_arrays(
    settings_dict,
):
    """Test that trailing commas in arrays are removed"""
    loader = JSONLoader(settings_dict)
    input_str = '{"tags": ["python", "web",]}'
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"tags": ["python", "web"]}'


def test_json_loader_format_string_handles_trailing_commas_in_nested_objects(
    settings_dict,
):
    """Test that trailing commas in nested objects are removed"""
    loader = JSONLoader(settings_dict)
    input_str = '{"user": {"name": "John", "age": 30,}, "active": true,}'
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"user": {"name": "John", "age": 30}, "active": true}'


def test_json_loader_format_string_handles_mixed_quotes_and_numbers(
    settings_dict,
):
    """Test handling of mixed quotes and numeric values"""
    loader = JSONLoader(settings_dict)
    input_str = """{
        'title': 'Article with 100 views',
        'views': 100,
        'featured': True,
        'quote': "It's rated 5/5 stars!"
    }"""
    result = loader.format_string_for_json_compatibility(input_str)

    parsed = json.loads(result)
    assert parsed["title"] == "Article with 100 views"
    assert parsed["views"] == 100
    assert parsed["featured"] is True
    assert parsed["quote"] == "It's rated 5/5 stars!"


def test_json_loader_format_string_handles_empty_strings(
    settings_dict,
):
    """Test that empty strings are preserved"""
    loader = JSONLoader(settings_dict)
    input_str = '{"empty": ""}'
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"empty": ""}'


def test_json_loader_format_string_handles_whitespace_in_values(
    settings_dict,
):
    """Test that whitespace in string values is preserved"""
    loader = JSONLoader(settings_dict)
    input_str = '{"text": "  multiple   spaces  "}'
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"text": "  multiple   spaces  "}'


def test_json_loader_format_string_handles_special_characters(
    settings_dict,
):
    """Test that special characters in strings are preserved"""
    loader = JSONLoader(settings_dict)
    input_str = '{"url": "https://example.com/page?query=test&page=2"}'
    result = loader.format_string_for_json_compatibility(input_str)

    assert result == '{"url": "https://example.com/page?query=test&page=2"}'


def test_json_loader_format_string_produces_valid_json(
    settings_dict,
):
    """Test that the output is valid JSON that can be parsed"""
    loader = JSONLoader(settings_dict)
    input_str = """{
        'name': 'Test',
        'age': 25,
        'active': True,
        'tags': ['python', 'web'],
        'metadata': {
            'created': '2025-01-01',
            'author': 'John Doe'
        }
    }"""
    result = loader.format_string_for_json_compatibility(input_str)

    # Should not raise an exception
    parsed = json.loads(result)
    assert parsed["name"] == "Test"
    assert parsed["age"] == 25
    assert parsed["active"] is True
    assert parsed["tags"] == ["python", "web"]
    assert parsed["metadata"]["created"] == "2025-01-01"


def test_json_loader_format_string_handles_ld_json_script(
    settings_dict,
):
    """Test handling of LD+JSON script tags (real-world use case)"""
    loader = JSONLoader(settings_dict)
    input_str = r"""<script type='application/ld+json'>{
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': 'Test Article',
        'description': "This article has quotes: 'single' and \"double\""
    }</script>"""

    # Extract just the JSON part for testing
    json_part = "{" + input_str.split("{", 1)[1].rsplit("}", 1)[0] + "}"
    result = loader.format_string_for_json_compatibility(json_part)

    # Should produce valid JSON
    parsed = json.loads(result)
    assert parsed["@context"] == "https://schema.org"
    assert parsed["@type"] == "Article"


def test_json_loader_format_string_handles_complex_nested_structure_with_quotes(
    settings_dict,
):
    """Test complex nested structure with various quote scenarios"""
    loader = JSONLoader(settings_dict)
    input_str = r"""{
        'articles': [
            {
                'title': "She said, 'Hello!'",
                'content': 'He replied, "Hi there!"',
                'metadata': {
                    'author': 'John O\'Brien',
                    'tags': ['python', 'web']
                }
            }
        ]
    }"""
    result = loader.format_string_for_json_compatibility(input_str)

    parsed = json.loads(result)
    assert parsed["articles"][0]["title"] == "She said, 'Hello!'"
    assert parsed["articles"][0]["content"] == 'He replied, "Hi there!"'
    assert parsed["articles"][0]["metadata"]["author"] == "John O'Brien"

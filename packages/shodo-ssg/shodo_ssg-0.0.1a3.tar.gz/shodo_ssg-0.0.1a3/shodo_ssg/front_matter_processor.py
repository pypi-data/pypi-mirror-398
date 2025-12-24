"""
Handles front matter extraction and processing from templates
"""

import re
from typing import Optional
from shodo_ssg.data_loader import JSONLoader


class FrontMatterProcessor:
    """Extracts and processes front matter from templates"""

    def __init__(self, json_loader: JSONLoader):
        self.json_loader = json_loader

    def get_front_matter(self, content: str):
        """
        Retrieves the front matter from content that has been parsed from either a markdown or
        jinja file. The front matter is the metadata that is used to populate the render arguments.
        It is a JSON object that is enclosed by `@frontmatter` at the beginning of the object and
        `@endfrontmatter` at the end of the front matter.
        """
        pattern = r"@frontmatter\s*(.*?)\s*@endfrontmatter"
        pattern = re.compile(pattern, re.DOTALL)
        front_matters = pattern.findall(content)
        if front_matters:
            # If the front matter is a list, merge them into a single dict,
            # with the last one taking precedence
            if isinstance(front_matters, list) and len(front_matters) >= 1:
                combined_front_matter = {}
                for fm in front_matters:
                    parsed_fm = self._parse_front_matter(fm)
                    if parsed_fm and isinstance(parsed_fm, dict):
                        combined_front_matter.update(parsed_fm)
                # If the front matter is a dictionary, return it
                if isinstance(combined_front_matter, dict):
                    return combined_front_matter

        return None

    def clear_front_matter(
        self, file_path: Optional[str] = None, content: Optional[str] = None
    ):
        """
        Strips the front matter from the rendered html file. The front matter is a JSON object
        that is enclosed by the tags `@frontmatter` and `@endfrontmatter`. In the html files
        that were generated from markdown files, the front matter tags are also enclosed in
        '<p>' tags. This function removes the front matter and the enclosing '<p>' tags if they
        exist. If a file path is provided, the function will write the content back to the file
        after removing the front matter. If no content is provided instead of a file path, the
        function will return the content with the front matter removed.
        """
        front_matters = None

        if content is None and file_path is not None:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

        if "<p>@frontmatter" in content:
            pattern = r"(<p>@frontmatter\s*.*?\s*@endfrontmatter</p>)"
            pattern = re.compile(pattern, re.DOTALL)
            front_matters = pattern.findall(content)
            if front_matters:
                for fm in front_matters:
                    fm = fm.strip()
                    content = content.replace(fm, "")

        if "@frontmatter" in content:
            pattern = r"(@frontmatter\s*.*?\s*@endfrontmatter)"
            pattern = re.compile(pattern, re.DOTALL)
            front_matters = pattern.findall(content)
            if front_matters:
                for fm in front_matters:
                    fm = fm.strip()
                    content = content.replace(fm, "")
        if front_matters and file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)

        return content

    def _parse_front_matter(self, fm: str):
        """
        Parses front matter string into a dictionary.
        """
        fm = fm.replace("@frontmatter", "").replace("@endfrontmatter", "")
        fm = fm.strip()
        # If parsable json, return as dict
        if fm.startswith("{") and fm.endswith("}"):
            fm = self.json_loader.format_string_for_json_compatibility(fm)
            fm = self.json_loader.json_to_dict(fm)
            if isinstance(fm, dict):
                head_extra = fm.get("head_extra", None)
                if head_extra and isinstance(head_extra, list):
                    formatted_head_extra = []
                    for item in head_extra:
                        # Allow single quotes to be used in tags
                        # instead of escaped double quotes, as well
                        # as ensuring proper formatting for ld+json scripts
                        formatted_item = item.replace("'", '"')
                        formatted_head_extra.append(formatted_item)
                    fm["head_extra"] = formatted_head_extra
                return fm
        return None

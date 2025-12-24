"""
Template context management for static site generation.
"""

from datetime import datetime
import logging
import os
from zoneinfo import ZoneInfo
from shodo_ssg.data_loader import JSONLoader, MarkdownLoader
from shodo_ssg.front_matter_processor import FrontMatterProcessor


class TemplateContext:
    """Holds context data for template rendering"""

    def __init__(
        self,
        markdown_loader: MarkdownLoader,
        json_loader: JSONLoader,
        front_matter_processor: FrontMatterProcessor,
    ):
        self._render_args = None
        self._md_pages = None
        self.markdown_loader = markdown_loader
        self.json_loader = json_loader
        self.front_matter_processor = front_matter_processor

    @property
    def render_args(self):
        """
        Getter for the render arguments
        """
        if self._render_args is None:
            # Set the render arguments upon class instantiation
            self._render_args = self.markdown_loader.load_args()
            self._render_args.update(self.json_loader.load_args())

        return self._render_args.copy()

    @property
    def md_pages(self):
        """
        Getter for the markdown pages
        """
        if self._md_pages is None:
            # Set the markdown pages upon class instantiation
            self._md_pages = self.markdown_loader.load_pages()

            for md_page in self._md_pages:
                front_matter = self._get_front_matter_from_md(
                    os.path.abspath(md_page["path"])
                )
                if not front_matter:
                    front_matter = {}
                # Add the front matter to the md_page
                md_page["front_matter"] = front_matter

        return self._md_pages.copy()

    def update_render_arg(self, key, value):
        """
        Update a render argument with the provided key-value pair. Used for
        setting and updating render arguments that are reused for dynamic content,
        such as article pages.
        """
        if self._render_args is None:
            self._render_args = self.render_args
        self._render_args[key] = value

    def _get_front_matter_from_md(self, file_path: str):
        """
        Retrieves the front matter from a markdown file. The front matter is
        the metadata that is used to populate the render arguments. It is a JSON object that
        is enclosed by `@frontmatter` at the beginning of the object and `@endfrontmatter` at
        the end of the front matter.
        """
        content = ""
        if file_path.endswith(".md"):
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                content = content.lstrip()

        front_matter = self.front_matter_processor.get_front_matter(content)
        return front_matter

    def format_md_page_data(self, md_page: dict) -> dict:
        """
        Format the markdown page data for rendering. This includes extracting
        the front matter and content from the markdown page. Used for rendering
        a list of articles/posts in a template with the shodo_get_articles function.
        """
        post = {}
        post["file_name"] = md_page["name"]
        post["directory"] = md_page["url_segment"]
        post["path"] = os.path.join(md_page["url_segment"], md_page["name"])

        front_matter = md_page["front_matter"]

        if not isinstance(front_matter, dict):
            front_matter = {}

        url_origin = self.render_args.get("config", {}).get("url_origin", "")
        tz = self.render_args.get("config", {}).get("timezone", None)

        link = ""
        if url_origin:
            link = os.path.join(url_origin, post["path"].lstrip("/"))

        post["title"] = front_matter.get("title", "")
        post["description"] = front_matter.get("description", "")
        post["summary"] = front_matter.get("summary", "")
        post["keywords"] = front_matter.get("keywords", [])
        post["author"] = front_matter.get("author", "")
        post["category"] = front_matter.get("category", "")
        post["tags"] = front_matter.get("tags", [])
        post["date"] = front_matter.get("date", None)
        post["published_datetime"] = front_matter.get("published_datetime", None)
        post["published_dt_local"] = None
        post["draft"] = front_matter.get("draft", False)
        post["image"] = front_matter.get("image", "")
        post["image_alt"] = front_matter.get("image_alt", "")
        post["content"] = md_page["html"]
        post["modified_datetime"] = front_matter.get("modified_datetime", None)
        post["modified_dt_local"] = None
        post["extra"] = front_matter.get("extra", {})
        post["link"] = link

        utc_pub_datetime = front_matter.get("published_datetime", None)
        if utc_pub_datetime:
            post["published_datetime"] = self._get_date_object_from_utc(
                utc_pub_datetime, post["path"]
            )
            if tz:
                post["published_dt_local"] = self._get_local_datetime_from_utc(
                    post["published_datetime"], tz, post["path"]
                )
        utc_mod_datetime = front_matter.get("modified_datetime", None)

        if utc_mod_datetime:
            post["modified_datetime"] = self._get_date_object_from_utc(
                utc_mod_datetime, post["path"]
            )
            if tz:
                post["modified_dt_local"] = self._get_local_datetime_from_utc(
                    post["modified_datetime"], tz, post["path"]
                )
        date = front_matter.get("date", None)
        if date:
            post["date"] = self._get_date_object_from_string(date, post["path"])

        return post

    def _get_date_object_from_utc(self, utc_date_str: str, file_path: str):
        """
        Convert a date string to a datetime object.
        """
        try:
            dt_object = datetime.strptime(utc_date_str, "%Y-%m-%dT%H:%M:%SZ")
            return dt_object
        except ValueError as e:
            logging.error(
                "Invalid date format in %s: %s. Expected format: 'YYYY-MM-DDTHH:MM:SSZ'",
                file_path,
                utc_date_str,
            )
            raise SystemExit from e

    def _get_date_object_from_string(self, date_str: str, file_path: str):
        """
        Convert a date string YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ to a datetime object.
        """
        try:
            dt_object = datetime.strptime(date_str, "%Y-%m-%d")
            return dt_object
        except ValueError:
            try:
                # Try parsing as ISO format first
                dt_object = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                return dt_object
            except ValueError as ex:
                logging.error(
                    "Invalid date format in %s: %s. Expected format: 'YYYY-MM-DD' "
                    + "or 'YYYY-MM-DDTHH:MM:SSZ'",
                    file_path,
                    date_str,
                )
                raise SystemExit from ex

    def _get_local_datetime_from_utc(
        self, utc_datetime: datetime, tz: str, file_path: str
    ):
        """
        Convert a UTC date string to a local datetime object.
        """
        try:
            utc_datetime = utc_datetime.replace(tzinfo=ZoneInfo("UTC"))
            local_timezone = ZoneInfo(tz)
            local_datetime = utc_datetime.astimezone(local_timezone)
            return local_datetime
        except Exception as e:
            logging.error(
                "Error converting UTC to local datetime in %s: %s",
                file_path,
                str(e),
            )
            raise SystemExit from e

"""
This module is responsible for handling the template environment as well as
rendering the Jinja2 templates as html
"""

import logging
import os
from typing import Optional
from jinja2 import (
    Environment,
    FileSystemLoader,
    Template,
)

from shodo_ssg.api import API
from shodo_ssg.data_loader import SettingsDict
from shodo_ssg.html_root_layout_builder import HTMLRootLayoutBuilder
from shodo_ssg.pagination_handler import PaginationHandler


class TemplateHandler:
    """
    Handles the loading and rendering of templates using Jinja2.
    """

    def __init__(
        self,
        settings: SettingsDict,
        html_root_layout_builder: HTMLRootLayoutBuilder,
        pagination_handler: PaginationHandler,
        api: API,
    ):
        """
        Initialize the TemplateHandler with the paths to the template directories.
        """
        self.template_env = Environment(
            loader=FileSystemLoader(searchpath=settings["template_paths"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.build_dir = settings["build_dir"]
        self.root_path = settings["root_path"]
        self.root_layout_builder = html_root_layout_builder
        self.pagination_handler = pagination_handler
        self.api = api
        self.context = api.context

    def get_template(self, template_name):
        """
        Retrieves a template by name
        """
        return self.template_env.get_template(template_name)

    def _log_info(self, page_name, destination):
        """
        Prints a status update of the writing operation
        """
        logging.info(
            "\033[94mWriting html from %s to %s...\033[0m", page_name, destination
        )

    def _process_template(
        self, template_name, destination_dir: str, front_matter: Optional[dict] = None
    ):
        """
        Prepares and writes a template to the specified destination
        """
        template = self.get_template(template_name)
        template_path = os.path.abspath(template.filename)
        if front_matter is None:
            front_matter = self.get_front_matter(
                file_path=template_path, template_name=template_name
            )

        is_draft = front_matter.get("draft", False) in [True, "true", "1", "True", 1]

        if is_draft:
            return

        file_type = front_matter.get("file_type", "html")
        suffix = "/index.html"
        if file_type == "xml":
            suffix = ".xml"
        else:
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)

        destination_path = f"{destination_dir.rstrip('/')}{suffix}"
        self._log_info(template_name, destination_path)

        if front_matter and front_matter.get("paginate", False):
            self.pagination_handler.handle_pagination(
                template_path, template, destination_path, front_matter=front_matter
            )
            return

        if file_type == "xml":
            self._write_xml_file(template, destination_path, front_matter)
        else:
            self._write_html_file(template, destination_path, front_matter)

        self.context.front_matter_processor.clear_front_matter(destination_path)

    def _write_html_file(
        self, template: Template, destination_path, front_matter: dict
    ):
        """
        Render a template as HTML and write it to a file.
        """
        doc_head = ""
        doc_tail = ""
        if not front_matter.get("no_wrapper", False):
            doc_head = self.root_layout_builder.get_doc_head(
                render_args=self.context.render_args, front_matter=front_matter
            )
            doc_tail = self.root_layout_builder.get_doc_tail()
        with open(destination_path, "w", encoding="utf-8") as output_file:
            output_file.write(
                doc_head + template.render(self.context.render_args) + "\n" + doc_tail
            )

    def _write_xml_file(self, template: Template, destination_path, front_matter: dict):
        """
        Render a template as XML and write it to a file.
        """
        declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        if front_matter.get("no_wrapper", False):
            declaration = ""
        with open(destination_path, "w", encoding="utf-8") as output_file:
            output_file.write(
                declaration + template.render(self.context.render_args).strip()
            )

    def write_home_template(self):
        """
        Write the index.html file using the provided render arguments.
        """
        return self._process_template("home.jinja", f"{self.build_dir}")

    def write_linked_template_pages(self, nested_dirs=""):
        """
        Write HTML pages linked from the index page using the provided render arguments.
        """
        primary_root_template_path = self.context.json_loader.settings[
            "root_template_paths"
        ][0]
        src_path = os.path.join(self.root_path, primary_root_template_path, "pages")

        pages_src_dir = "/" + os.path.join(src_path, nested_dirs).strip("/") + "/"
        if os.path.exists(pages_src_dir) and os.listdir(pages_src_dir):
            for path in os.listdir(pages_src_dir):
                if (
                    path.endswith(".jinja")
                    or path.endswith(".j2")
                    or path.endswith(".jinja2")
                ):
                    template_name = os.path.join(nested_dirs, path)
                    page_name = nested_dirs + os.path.splitext(path)[0]
                    self._process_template(
                        template_name, f"{self.build_dir}/{page_name}"
                    )
                path_from_root = os.path.join(self.root_path, pages_src_dir + path)
                # If directory, recursively create a nested route
                if os.path.isdir(path_from_root):
                    nested_path = nested_dirs + path + "/"
                    self.write_linked_template_pages(nested_path)

    def write_article_pages(self):
        """
        Writes html pages for each markdown file in the `articles` directory
        """
        for md_page in self.context.md_pages:
            # Get the layout for this template
            layout_template = self.get_md_layout_template(md_page["url_segment"])
            # Get the path
            build_path = os.path.join(
                self.build_dir,
                md_page["url_segment"].strip("/"),
                md_page["name"].strip("/"),
            )

            article_data = self.context.format_md_page_data(md_page)
            self.context.update_render_arg("article", article_data)

            front_matter = md_page["front_matter"]

            if front_matter:
                # Don't write the template if 'draft' is set in front matter
                is_draft = front_matter.get("draft", False)
                if isinstance(is_draft, bool) and is_draft:
                    continue
                if isinstance(is_draft, str) and (
                    is_draft.lower() == "true" or is_draft == "1"
                ):
                    continue

            if not os.path.exists(build_path):
                os.makedirs(build_path)

            self._process_template(layout_template, f"{build_path}")
            self.context.update_render_arg("article", {})

    def get_md_layout_template(self, url_segment: str):
        """
        Retrieves the layout template that maps to the specified
        article path. If no layout is defined in the template directory
        with the same name, the layout template closest in the tree will
        be used.
        """
        if not url_segment:
            return "articles/layout.jinja"
        template_path = os.path.join("articles", url_segment.strip("/"), "layout.jinja")

        primary_root_template_path = self.context.json_loader.settings[
            "root_template_paths"
        ][0]

        src_view_path = "/" + os.path.join(
            self.root_path, primary_root_template_path
        ).strip("/")

        if os.path.exists(f"{src_view_path}/{template_path}"):
            return template_path
        segments = url_segment.strip("/").split("/")
        segments.pop()
        return self.get_md_layout_template("/".join(segments))

    def get_front_matter(self, file_path="", template_name=""):
        """
        Retrieves the front matter from either a markdown or jinja file. The front matter is
        the metadata that is used to populate the render arguments. It is a JSON object that
        is enclosed by `@frontmatter` at the beginning of the object and `@endfrontmatter` at
        the end of the front matter.
        """
        content = ""
        if template_name and (
            file_path.endswith(".jinja")
            or file_path.endswith(".j2")
            or file_path.endswith(".jinja2")
        ):
            # If the file is a jinja template, we need to render it so
            # that front matter from included templates is also included
            # in the front matter
            template = self.get_template(template_name)
            # Temporarily suppress missing variable errors
            self.pagination_handler.set_default_pagination_variables()
            content = template.render(self.context.render_args)
            self.context.update_render_arg("pagination", None)
        else:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                content = content.lstrip()

        front_matter = self.context.front_matter_processor.get_front_matter(content)
        return front_matter

    def _pass_global_template_functions(self, funcs: list[callable]):
        """
        Passes the provided functions to the template environment as global functions.
        """
        for func in funcs:
            self.template_env.globals[func.__name__] = func

    def write(self):
        """
        Writes the root index.html and any linked html pages using the provided render arguments.
        """

        self._pass_global_template_functions(
            [
                self.api.shodo_get_articles,
                self.api.shodo_query_store,
                self.api.shodo_get_excerpt,
                self.api.get_rfc822,
                self.api.rel_to_abs,
                self.api.current_dt,
            ]
        )
        self.write_article_pages()
        self.write_home_template()
        self.write_linked_template_pages()

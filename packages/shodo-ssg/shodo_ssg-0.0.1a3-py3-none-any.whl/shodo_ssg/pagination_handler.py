"""
Handles pagination logic for article listings
"""

import os
import re
import logging
from typing import Optional
from jinja2 import Template

from shodo_ssg.api import API
from shodo_ssg.html_root_layout_builder import HTMLRootLayoutBuilder
from shodo_ssg.template_context import TemplateContext


class PaginationHandler:
    """Manages pagination for article listings"""

    def __init__(
        self,
        context: TemplateContext,
        html_root_layout_builder: HTMLRootLayoutBuilder,
        api: API,
    ):
        self.context = context
        self.root_layout_builder = html_root_layout_builder
        self.api = api

    def handle_pagination(
        self,
        template_path: str,
        template: Template,
        destination_dir,
        front_matter: dict,
    ):
        """
        Handle pagination for a template that requires it.
        """
        supported_pagination_types = ["shodo_get_articles", "shodo_query_store"]
        if front_matter.get("paginate") not in supported_pagination_types:
            raise ValueError(
                f"Pagination requested in {template.filename} but 'paginate' value is not "
                + f"supported. Supported types are: {', '.join(supported_pagination_types)}"
            )

        items_per_page = front_matter.get("per_page", None)
        # Try to convert items_per_page to int if it's a string
        if isinstance(items_per_page, str):
            try:
                items_per_page = int(items_per_page)
            except ValueError:
                items_per_page = None
        if items_per_page is None or not isinstance(items_per_page, int):
            raise ValueError(
                f"Pagination requested in {template.filename} but 'per_page' not "
                + "set or invalid in front matter."
            )

        # Get the pagination filters directly from the specified 'paginate' function
        # in the template by parsing the template source file
        pagination_filters = self._extract_pagination_filters(
            template_path, front_matter.get("paginate")
        )

        # Remove 'offset' and 'limit' from the filters if they exist
        if pagination_filters:
            pagination_filters.pop("offset", None)
            pagination_filters.pop("limit", None)

        all_items = []
        if front_matter.get("paginate") == "shodo_get_articles":
            all_items = self.api.shodo_get_articles(filters=pagination_filters)
        elif front_matter.get("paginate") == "shodo_query_store":
            all_items = self.api.shodo_query_store(filters=pagination_filters)

        total_items = len(all_items)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        total_pages = max(total_pages, 1)

        # Get everything from os.path.dirname(destination_dir) after 'dist/'
        root_page_path = os.path.relpath(os.path.dirname(destination_dir), start="dist")

        for page_num in range(1, total_pages + 1):
            pagination_context = {
                "root_page_path": root_page_path,
                "page_num": page_num,
                "total_pages": total_pages,
                "items_per_page": items_per_page,
                "total_items": total_items,
            }
            self._write_pagination_page_html_from_template(
                template=template,
                front_matter=front_matter,
                destination_dir=destination_dir,
                pagination_context=pagination_context,
            )

    def _write_pagination_page_html_from_template(
        self,
        template: Template,
        front_matter: dict,
        destination_dir: str,
        pagination_context: dict,
    ) -> None:
        """
        Write a paginated HTML page from a template to the specified output path.
        """
        root_page_path = pagination_context.get("root_page_path")
        page_num = pagination_context.get("page_num")
        total_pages = pagination_context.get("total_pages")
        items_per_page = pagination_context.get("items_per_page")
        total_items = pagination_context.get("total_items")

        pagination_link_markup = self.get_pagination_link_markup(
            root_page_path, page_num, total_pages
        )

        # Update render arguments with paginated items and pagination info
        self.context.update_render_arg(
            "pagination",
            {
                "total_items": total_items,
                "current_page": page_num,
                "per_page": items_per_page,
                "total_pages": total_pages,
                "has_previous": page_num > 1,
                "has_next": page_num < total_pages,
                "previous_page": page_num - 1 if page_num > 1 else None,
                "next_page": page_num + 1 if page_num < total_pages else None,
                "next_page_url": (
                    f"/{root_page_path.strip('/')}/page/{page_num + 1}/"
                    if page_num + 1 > 1
                    else f"/{root_page_path.strip('/')}/"
                ),
                "previous_page_url": (
                    f"/{root_page_path.strip('/')}/page/{page_num - 1}/"
                    if page_num - 1 > 1
                    else f"/{root_page_path.strip('/')}/"
                ),
                "page_links": pagination_link_markup,
            },
        )

        # Determine the output file path
        if page_num == 1:
            output_path = destination_dir
        else:
            output_path = os.path.join(
                os.path.dirname(destination_dir),
                "page",
                f"{page_num}",
                "index.html",
            )
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(
                self.root_layout_builder.get_doc_head(
                    render_args=self.context.render_args,
                    front_matter=front_matter,
                )
                + template.render(self.context.render_args)
                + "\n"
                + self.root_layout_builder.get_doc_tail()
            )

        self.context.front_matter_processor.clear_front_matter(output_path)
        self.context.update_render_arg("pagination", None)

    def get_pagination_link_markup(
        self, root_page_path: str, current_page_num: int, total_pages: int
    ) -> str:
        """
        Generate the pagination link HTML markup for a given page number.
        """
        if total_pages <= 1:
            return ""

        html = "<nav class='pagination'>\n<ul class='pagination-list'>\n"

        if current_page_num > 1:
            prev_page_url = (
                f"/{root_page_path.strip('/')}/page/{current_page_num - 1}/"
                if current_page_num - 1 > 1
                else f"/{root_page_path.strip('/')}/"
            )
            html += f"""
            <li class='pagination-previous'><a href='{prev_page_url}'><span>Previous</span></a></li>\n
            """

        # Generate numbered page links
        html += self._generate_numbered_page_links(
            root_page_path, total_pages, current_page_num
        )

        if current_page_num < total_pages:
            next_page_url = f"/{root_page_path.strip('/')}/page/{current_page_num + 1}/"
            html += f"""
            <li class='pagination-next'><a href='{next_page_url}'><span>Next</span></a></li>\n
            """

        html += "</ul>\n</nav>\n"
        return html

    def _generate_numbered_page_links(
        self, root_page_path: str, total_pages: int, current_page_num: int
    ) -> str:
        """
        Generate numbered HTML pagination links for all pages.
        """
        html = ""
        # If there are less than 10 pages, display all page links
        if total_pages <= 10:
            for i in range(1, total_pages + 1):
                html += self._generate_page_link(root_page_path, i, current_page_num)
            return html
        # If there are more than 10 pages, display a truncated set of page links
        # Always show the first 2 pages, last 2 pages, current page, and 2 pages
        # before and after the current page
        start_page = max(1, current_page_num - 2)
        end_page = min(total_pages, current_page_num + 2)

        # Show the first 2 pages
        if start_page > 1:
            html += self._generate_page_link(root_page_path, 1, current_page_num)
            if start_page > 2:
                html += "<li class='pagination-ellipsis'>…</li>\n"

        # Show the current page and surrounding pages
        for i in range(start_page, end_page + 1):
            html += self._generate_page_link(root_page_path, i, current_page_num)

        # Show the last 2 pages
        if end_page < total_pages:
            if end_page < total_pages - 1:
                html += "<li class='pagination-ellipsis'>…</li>\n"
            html += self._generate_page_link(
                root_page_path, total_pages, current_page_num
            )

        return html

    def _generate_page_link(
        self, root_page_path: str, page_num: int, current_page_num: int
    ) -> str:
        """
        Generate the numbered HTML pagination link for a given page number.
        """
        if page_num == current_page_num:
            return f"<li class='pagination-item active'>{page_num}</li>\n"
        if page_num == 1:
            return f"""
            <li class='pagination-item'>
            <a href='/{root_page_path.strip('/')}/'>{page_num}</a></li>\n
            """

        return f"""
        <li class='pagination-item'>
        <a href='/{root_page_path.strip('/')}/page/{page_num}/'>{page_num}</a></li>\n
        """

    def set_default_pagination_variables(self):
        """
        Sets default pagination variables in the render arguments if they are not already set.
        """
        if (
            "pagination" not in self.context.render_args
            or self.context.render_args["pagination"] is None
        ):
            self.context.update_render_arg(
                "pagination",
                {
                    "total_items": 0,
                    "current_page": 1,
                    "per_page": 10,
                    "total_pages": 0,
                    "has_previous": False,
                    "has_next": False,
                    "previous_page": None,
                    "next_page": None,
                    "next_page_url": None,
                    "previous_page_url": None,
                    "page_links": "",
                },
            )

    def _extract_pagination_filters(
        self, template_path: str, query_to_paginate: str
    ) -> Optional[dict]:
        """
        Extract pagination filters from the template source file by parsing
        the 'query_to_paginate' function call.
        """
        with open(template_path, "r", encoding="utf-8") as file:
            content = file.read()

        if query_to_paginate == "shodo_get_articles":
            return self._extract_article_query_filters(content)
        if query_to_paginate == "shodo_query_store":
            return self._extract_store_query_filters(content)
        return None

    def _extract_article_query_filters(self, content) -> Optional[dict]:
        """
        Extract pagination filters from the template source file by parsing
        the 'shodo_get_articles' function call arguments.
        """
        return self._extract_query_filters(content, "shodo_get_articles")

    def _extract_store_query_filters(self, content) -> Optional[dict]:
        """
        Extract pagination filters from the template source file by parsing
        the 'shodo_query_store' function call arguments.
        """
        return self._extract_query_filters(content, "shodo_query_store")

    def _extract_query_filters(self, content, function_name) -> Optional[dict]:
        """
        Extract pagination filters from the template source file by parsing
        the specified function call arguments.
        """
        pattern = rf"{function_name}\s*\(\s*(?:filters\s*=\s*)?(\{{.*?\}})\s*\)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            filters_str = match.group(1)
            try:
                # if only whitespace inside braces, return empty dict
                if re.match(r"^\s*\{\s*\}\s*$", filters_str):
                    return {}

                formatted_json = (
                    self.context.json_loader.format_string_for_json_compatibility(
                        filters_str
                    )
                )
                filters_dict = self.context.json_loader.json_to_dict(formatted_json)

                if not isinstance(filters_dict, dict):
                    raise ValueError(f"Failed to parse filters in {function_name}.")
                return filters_dict
            except ValueError as e:
                logging.error("Error parsing pagination filters from template: %s", e)
                return None
        else:
            raise ValueError(
                f"Could not find '{function_name}' function call in template for pagination."
            )

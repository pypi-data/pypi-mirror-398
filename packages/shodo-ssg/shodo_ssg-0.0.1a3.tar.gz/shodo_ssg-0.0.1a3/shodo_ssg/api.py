"""API functions to expose to templates."""

import logging
import re
from datetime import datetime, timezone
from typing import Optional, Union
from shodo_ssg.front_matter_processor import FrontMatterProcessor
from shodo_ssg.template_context import TemplateContext


class API:
    """Exposes API functions to templates"""

    def __init__(
        self, context: TemplateContext, front_matter_processor: FrontMatterProcessor
    ):
        self.context = context
        self.front_matter_processor = front_matter_processor

    def shodo_get_articles(self, filters: Optional[dict] = None):
        """
        Returns a list of articles that are not marked as drafts to expose to the
        template. The articles are filtered based on the provided filters. The filters
        can include "category", "tags", "date", and "limit".
        """
        formatted_data = [
            self.context.format_md_page_data(md_page)
            for md_page in self.context.md_pages
        ]

        filtered_data = [post for post in formatted_data if not post["draft"]]
        if filters is None:
            filters = {}

        filtered_data = self._apply_query_filters(filtered_data, filters)

        return filtered_data if filtered_data else []

    def shodo_query_store(self, filters: Optional[dict] = None):
        """
        Queries the json data loaded in render_args with the provided filters.
        The filters can include key-value pairs to match against the collection items.
        """

        collection = filters.get("collection", None)
        if collection is None:
            raise ValueError(
                "'collection' must be specified in filters. This will be a top-level key "
                "in the json data specified in the 'store' directory."
            )

        data = self.context.render_args.get(collection, None)
        if data is None:
            raise ValueError(f"Collection '{collection}' not found in the store data.")

        # If dictionary, wrap in a list for uniform processing
        if isinstance(data, dict):
            data = [data]

        filtered_data = self._apply_query_filters(data, filters)

        return filtered_data if filtered_data else []

    def shodo_get_excerpt(self, content: str, length: int = 100):
        """
        Returns an excerpt from html content. Only content within the <p> tags
        is considered. The excerpt is truncated to the specified length.
        """
        # Extract the content within <p> tags
        content = self.front_matter_processor.clear_front_matter(
            file_path=None, content=content
        )
        pattern = r"<p>(.*?)</p>"
        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            # Join the matches and truncate to the specified length
            excerpt = " ".join(matches)
        else:
            # If no <p> tags are found, attempt to truncate a plain text string
            excerpt = re.sub(r"<.*?>", "", content)

        if excerpt:
            # Remove HTML tags
            excerpt = re.sub(r"<.*?>", "", excerpt)

        if len(excerpt) > length:
            # Find the last space before the length limit
            last_space = excerpt.rfind(" ", 0, length)
            if last_space != -1:
                excerpt = excerpt[:last_space] + "..."
            else:
                excerpt = excerpt[:length] + "..."

        return excerpt.strip()

    def _apply_query_filters(self, data: list, filters: Optional[dict] = None):
        """
        Applies query filters to the provided data list.
        """
        if not data or filters is None:
            return data

        filtered_data = data

        # Extract where conditions
        and_conditions, or_conditions = self._extract_where_conditions(filters)

        # Apply AND conditions
        filtered_data = self._apply_and_conditions(filtered_data, and_conditions)

        # Apply OR conditions
        if or_conditions:
            filtered_data = self._apply_or_conditions(filtered_data, or_conditions)

        # Apply ordering, offset, and limit
        filtered_data = self._apply_ordering(filtered_data, filters)
        filtered_data = self._apply_offset_and_limit(filtered_data, filters)

        return filtered_data

    def _extract_where_conditions(self, filters: dict) -> tuple[list, list]:
        """Extract AND and OR conditions from filters."""
        and_conditions = []
        or_conditions = []

        where = filters.get("where", {})
        for key, value in where.items():
            if key == "or":
                for or_condition in value:
                    for or_key, or_value in or_condition.items():
                        or_conditions.append((or_key, or_value))
            elif key == "and":
                for and_condition in value:
                    for and_key, and_value in and_condition.items():
                        and_conditions.append((and_key, and_value))
            else:
                and_conditions.append((key, value))

        return and_conditions, or_conditions

    def _apply_and_conditions(self, data: list, conditions: list) -> list:
        """Apply AND conditions to filter data."""
        filtered_data = data

        for key, condition in conditions:
            if not condition:
                continue
            filtered_data = self._apply_single_condition(filtered_data, key, condition)

        return filtered_data

    def _apply_or_conditions(self, data: list, conditions: list) -> list:
        """Apply OR conditions to filter data."""
        or_filtered_data = []

        for key, condition in conditions:
            if not condition:
                continue

            temp_filtered = self._apply_single_condition(data, key, condition)

            # Merge temp_filtered into or_filtered_data (union)
            for item in temp_filtered:
                if item not in or_filtered_data:
                    or_filtered_data.append(item)

        return or_filtered_data

    def _apply_single_condition(self, data: list, key: str, condition) -> list:
        """Apply a single condition to filter data."""
        # Simple equality check if condition is not a dict
        if not isinstance(condition, dict):
            return [item for item in data if item.get(key) == condition]

        def dt_parse(val):
            # If val is already a datetime, or not in ISO format or MM-DD-YYYY, return as is
            if isinstance(val, datetime):
                return val
            # Check if string starts with YYYY-MM-DD pattern
            is_date = re.match(r"^\d{4}-\d{2}-\d{2}", str(val))
            if is_date:
                try:
                    # Try parsing as ISO format first
                    return datetime.strptime(val, "%Y-%m-%dT%H:%M:%SZ")
                except (ValueError, TypeError):
                    try:
                        # Try parsing as YYYY-MM-DD format
                        return datetime.strptime(val, "%Y-%m-%d")
                    except ValueError:
                        return val
            return val

        # Map condition operators to filter functions
        condition_handlers = {
            "equals": lambda item: item.get(key) == dt_parse(condition["equals"]),
            "contains": lambda item: condition["contains"] in item.get(key, []),
            "starts_with": lambda item: isinstance(item.get(key), str)
            and item.get(key, "").startswith(condition["starts_with"]),
            "ends_with": lambda item: isinstance(item.get(key), str)
            and item.get(key, "").endswith(condition["ends_with"]),
            "gt": lambda item: item.get(key, None) is not None
            and item.get(key) > dt_parse(condition["gt"]),
            "gte": lambda item: item.get(key, None) is not None
            and item.get(key) >= dt_parse(condition["gte"]),
            "lt": lambda item: item.get(key, None) is not None
            and item.get(key) < dt_parse(condition["lt"]),
            "lte": lambda item: item.get(key, None) is not None
            and item.get(key) <= dt_parse(condition["lte"]),
            "in": lambda item: item.get(key) in condition["in"],
            "not_in": lambda item: item.get(key) not in condition["not_in"],
            "not_equals": lambda item: item.get(key)
            != dt_parse(condition["not_equals"]),
            "not_contains": lambda item: condition["not_contains"]
            not in item.get(key, []),
            "regex": lambda item: isinstance(item.get(key), str)
            and re.compile(condition["regex"]).search(item.get(key, "")),
        }

        # Find and apply the first matching condition
        for operator, handler in condition_handlers.items():
            if condition.get(operator) is not None:
                return [item for item in data if handler(item)]

        return data

    def _apply_ordering(self, data: list, filters: dict) -> list:
        """Apply ordering to filtered data."""
        if "order_by" not in filters:
            return data

        order_by = filters["order_by"]

        def dt_normalize(key, val, file_path):
            """Normalize datetime values for sorting."""
            date_fields = ["published_datetime", "modified_datetime", "date"]
            if key in date_fields and not isinstance(val, datetime):
                if val is None:
                    logging.warning(
                        "[warn] Sorting by date field '%s' received a None value. "
                        + "No '%s' set in '%s'. "
                        + "Returning minimal date.",
                        key,
                        key,
                        file_path,
                    )
                    return datetime.min
                if isinstance(val, str):
                    if val.strip() == "":
                        logging.warning(
                            "[warn] Sorting by date field '%s' received a string instead of "
                            + "datetime. Check date formatting in '%s'. Returning minimal date.",
                            key,
                            file_path,
                        )
                        # Return minimal datetime for empty strings
                        return datetime.min
                    try:
                        return datetime.strptime(val, "%Y-%m-%dT%H:%M:%SZ")
                    except (ValueError, TypeError):
                        try:
                            return datetime.strptime(val, "%Y-%m-%d")
                        except ValueError:
                            return val
            return val

        if order_by.get("asc") is not None:
            order_key = order_by["asc"]
            return sorted(
                data,
                key=lambda x: dt_normalize(
                    order_key, x.get(order_key, None), x.get("path")
                ),
            )

        if order_by.get("desc") is not None:
            order_key = order_by["desc"]
            return sorted(
                data,
                key=lambda x: dt_normalize(
                    order_key, x.get(order_key, None), x.get("path")
                ),
                reverse=True,
            )

        return data

    def _apply_offset_and_limit(self, data: list, filters: dict) -> list:
        """Apply offset and limit to filtered data."""
        result = data

        if "offset" in filters:
            offset = filters["offset"]
            result = result[offset:]

        if "limit" in filters:
            limit = filters["limit"]
            result = result[:limit]

        return result

    def get_rfc822(self, dt: Union[datetime, str, None]) -> str:
        """Returns a datetime formatted as an RFC 822 date string."""
        if isinstance(dt, str):
            dt = datetime.min
            # Set year to 1900 to avoid issues with strftime
            dt = dt.replace(year=1000)
            logging.warning(
                "[warn] get_rfc822 received a string instead of datetime. Returning minimal date."
            )
        if dt is None:
            dt = datetime.min
            logging.warning(
                "[warn] get_rfc822 received None instead of datetime. Returning minimal date."
            )
            # Set year to 1900 to avoid issues with strftime
            dt = dt.replace(year=1000)
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

    def rel_to_abs(
        self, html_content: str, base_url_origin: Optional[str] = None
    ) -> str:
        """
        Converts relative URLs in the provided HTML content to absolute URLs
        based on the given base URL origin.
        """
        if base_url_origin is None:
            base_url_origin = self.context.render_args.get("config", {}).get(
                "url_origin", ""
            )

        if not base_url_origin:
            return html_content

        # Temporarily replace anything in <code> or <pre> tags to avoid modifying them
        pre_code_patterns = re.findall(
            r"(<(code|pre)[^>]*>.*?<\/\2>)", html_content, re.DOTALL
        )
        placeholders = {}
        for i, (full_match, _) in enumerate(pre_code_patterns):
            placeholder = f"__PLACEHOLDER_{i}__"
            placeholders[placeholder] = full_match
            html_content = html_content.replace(full_match, placeholder)

        # Regex patterns to find relative URLs in href and src attributes
        href_pattern = r'href=["\'](\/[^"\']*)["\']'
        src_pattern = r'src=["\'](\/[^"\']*)["\']'

        # Replace relative URLs with absolute URLs
        html_content = re.sub(
            href_pattern,
            lambda match: f'href="{base_url_origin}{match.group(1)}"',
            html_content,
        )
        html_content = re.sub(
            src_pattern,
            lambda match: f'src="{base_url_origin}{match.group(1)}"',
            html_content,
        )

        # Restore the original <code> and <pre> content
        for placeholder, original in placeholders.items():
            html_content = html_content.replace(placeholder, original)

        return html_content

    def current_dt(self) -> datetime:
        """Returns the current UTC datetime during build."""
        return datetime.now(timezone.utc)

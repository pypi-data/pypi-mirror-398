"""
Handles generation of HTML head sections with metadata
"""

from typing import Optional


class HTMLRootLayoutBuilder:
    """Builds HTML head sections with metadata and front matter"""

    def get_doc_head(
        self,
        render_args: dict,
        styles_link="/static/styles/main.css",
        favicon_link='<link rel="icon" type="image/x-icon" href="/favicon.ico">',
        front_matter: Optional[dict] = None,
    ):
        """
        Generate the HTML head section for a document, including opening body tag.
        """
        global_metadata: dict = render_args.get("config", {}).get("metadata", {})
        if front_matter is None:
            front_matter = {}

        # Merge global metadata with front matter, with front_matter taking precedence
        head_content = self._merge_head_data(front_matter, global_metadata)

        # Extract the "lang", "body_id", and "body_class" properties and
        # remove them from the dictionary
        lang = head_content.pop("lang", "en")
        body_id = head_content.pop("body_id", None)
        body_class = head_content.pop("body_class", None)

        # Format the properties of the head content as HTML tags
        head_content_tags = self._format_head_data_as_html(head_content)

        # Remove empty tags "" from the dictionary
        head_content_tags = {k: v for k, v in head_content_tags.items() if v != ""}
        # Join the tags into a single string
        head_content_html = "\n".join(head_content_tags.values())

        head_html = f"""
        <!DOCTYPE html>
        <html lang="{lang}">
        <head>
            {head_content_html}
            {favicon_link}
            <link href="{styles_link}" rel="stylesheet" />
        </head>
        <body
        """
        if body_id:
            head_html += f' id="{body_id}"'
        if body_class:
            head_html += f' class="{body_class}"'
        head_html += ">"
        head_html = head_html.strip() + "\n"

        return head_html

    def get_doc_tail(self, script_link="/static/scripts/main.js"):
        """
        Generate the HTML end section for a document, including script tag
        for main.js and a closing body tag.
        """
        return f"""
                <script type="module" src="{script_link}"></script>
            </body>
        </html>
        """.strip()

    def _format_head_data_as_html(self, head_content: dict) -> dict:
        """
        Format the properties of the head content as HTML tags.
        """
        # Format the properties of the head content as HTML tags
        formatted_head_content = {
            "charset": f'<meta charset="{head_content["charset"]}">',
            "viewport": '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "title": f'<title>{head_content["title"]}</title>',
            "description": (
                f'<meta name="description" content="{head_content["description"]}">'
                if head_content["description"]
                else ""
            ),
            "keywords": (
                f'<meta name="keywords" content="{",".join(head_content["keywords"])}">'
                if isinstance(head_content["keywords"], list)
                else (
                    f'<meta name="keywords" content="{head_content["keywords"]}">'
                    if head_content["keywords"]
                    else ""
                )
            ),
            "author": (
                f'<meta name="author" content="{head_content["author"]}">'
                if head_content["author"]
                else ""
            ),
            "theme_color": (
                f'<meta name="theme-color" content="{head_content["theme_color"]}">'
                if head_content["theme_color"]
                else ""
            ),
            "og_image": (
                f'<meta property="og:image" content="{head_content["og_image"]}">'
                if head_content["og_image"]
                else ""
            ),
            "og_image_alt": (
                f'<meta property="og:image:alt" content="{head_content["og_image_alt"]}">'
                if head_content["og_image_alt"]
                else ""
            ),
            "og_title": (
                f'<meta property="og:title" content="{head_content["og_title"]}">'
                if head_content["og_title"]
                else ""
            ),
            "og_description": (
                f'<meta property="og:description" content="{head_content["og_description"]}">'
                if head_content["og_description"]
                else ""
            ),
            "og_url": (
                f'<meta property="og:url" content="{head_content["og_url"]}">'
                if head_content["og_url"]
                else ""
            ),
            "og_type": (
                f'<meta property="og:type" content="{head_content["og_type"]}">'
                if head_content["og_type"]
                else ""
            ),
            "og_site_name": (
                f'<meta property="og:site_name" content="{head_content["og_site_name"]}">'
                if head_content["og_site_name"]
                else ""
            ),
            "og_locale": (
                f'<meta property="og:locale" content="{head_content["og_locale"]}">'
                if head_content["og_locale"]
                else ""
            ),
            "canonical": (
                f'<link rel="canonical" href="{head_content["canonical"]}">'
                if head_content["canonical"]
                else ""
            ),
            "google_font_link": (
                f"""
                <link rel="preconnect" href="https://fonts.googleapis.com">
                <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                <link href="{head_content["google_font_link"]}" rel="stylesheet">
                """
                if head_content["google_font_link"]
                else ""
            ),
            "preconnects": (
                "\n".join(
                    [
                        f'<link rel="preconnect" href="{link}">'
                        for link in head_content["preconnects"]
                    ]
                )
                if isinstance(head_content["preconnects"], list)
                else (
                    f'<link rel="preconnect" href="{head_content["preconnects"]}">'
                    if head_content["preconnects"]
                    else ""
                )
            ),
            "stylesheets": (
                "\n".join(
                    [
                        f'<link rel="stylesheet" href="{sheet}">'
                        for sheet in head_content["stylesheets"]
                    ]
                )
                if isinstance(head_content["stylesheets"], list)
                else (
                    f'<link rel="stylesheet" href="{head_content["stylesheets"]}">'
                    if head_content["stylesheets"]
                    else ""
                )
            ),
            "robots": (
                f'<meta name="robots" content="{head_content["robots"]}">'
                if head_content["robots"]
                else ""
            ),
            "head_extra": (
                "\n".join(head_content["head_extra"])
                if isinstance(head_content["head_extra"], list)
                else (
                    f'{head_content["head_extra"]}'
                    if head_content["head_extra"]
                    else ""
                )
            ),
        }
        return formatted_head_content

    def _merge_head_data(self, front_matter: dict, global_metadata: dict):
        """
        Format the head data for the HTML document. This includes merging
        global metadata with front matter and generating the HTML head section.
        """
        # Merge global metadata with front matter, with front_matter taking precedence
        metadata = {
            "title": front_matter.get(
                "title", global_metadata.get("title", "Shodo SSG")
            ),
            "lang": front_matter.get("lang", global_metadata.get("lang", "en")),
            "charset": front_matter.get(
                "charset", global_metadata.get("charset", "UTF-8")
            ),
            "description": front_matter.get(
                "description", global_metadata.get("description", "")
            ),
            "keywords": front_matter.get(
                "keywords", global_metadata.get("keywords", "")
            ),
            "author": front_matter.get("author", global_metadata.get("author", "")),
            "theme_color": front_matter.get(
                "theme_color", global_metadata.get("theme_color", "")
            ),
            "og_image": front_matter.get(
                "og_image", global_metadata.get("og_image", "")
            ),
            "og_image_alt": front_matter.get(
                "og_image_alt", global_metadata.get("og_image_alt", "")
            ),
            "og_title": front_matter.get(
                "og_title", global_metadata.get("og_title", "")
            ),
            "og_description": front_matter.get(
                "og_description", global_metadata.get("og_description", "")
            ),
            "og_url": front_matter.get("og_url", global_metadata.get("og_url", "")),
            "og_type": front_matter.get("og_type", global_metadata.get("og_type", "")),
            "og_site_name": front_matter.get(
                "og_site_name", global_metadata.get("og_site_name", "")
            ),
            "og_locale": front_matter.get(
                "og_locale", global_metadata.get("og_locale", "")
            ),
            "canonical": front_matter.get(
                "canonical", global_metadata.get("canonical", "")
            ),
            "google_font_link": front_matter.get(
                "google_font_link", global_metadata.get("google_font_link", "")
            ),
            "preconnects": front_matter.get(
                "preconnects", global_metadata.get("preconnects", [])
            ),
            "stylesheets": front_matter.get(
                "stylesheets", global_metadata.get("stylesheets", [])
            ),
            "robots": front_matter.get("robots", global_metadata.get("robots", "")),
            "head_extra": front_matter.get(
                "head_extra", global_metadata.get("head_extra", "")
            ),
            "body_id": front_matter.get("body_id", global_metadata.get("body_id", "")),
            "body_class": front_matter.get(
                "body_class", global_metadata.get("body_class", "")
            ),
        }
        return metadata

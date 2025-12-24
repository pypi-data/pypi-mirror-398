"""
This module loads settings and initializes components for building a static site
"""

import logging
from shodo_ssg.api import API
from shodo_ssg.asset_writer import (
    AssetHandler,
    CSSWriter,
    FaviconWriter,
    AssetWriter,
    ScriptWriter,
    RootFilesWriter,
)
from shodo_ssg.data_loader import JSONLoader, MarkdownLoader, SettingsLoader
from shodo_ssg.front_matter_processor import FrontMatterProcessor
from shodo_ssg.html_root_layout_builder import HTMLRootLayoutBuilder
from shodo_ssg.pagination_handler import PaginationHandler
from shodo_ssg.static_site_generator import StaticSiteGenerator
from shodo_ssg.template_context import TemplateContext
from shodo_ssg.template_handler import TemplateHandler


def load_settings(root_path: str):
    """
    Loads the settings from the settings.json file in the root directory.

    Returns:
        dict: The settings data loaded from the settings.json file
    """
    settings_loader = SettingsLoader(root_path)
    return settings_loader.data


def initialize_components(settings: dict):
    """
    Initializes the components necessary for building the static site.

    Args:
        settings (dict): The settings data loaded from the settings.json file

    Returns:
        Tuple[TemplateHandler, AssetHandler]: A tuple containing the initialized components
    """
    md_loader = MarkdownLoader(settings)
    json_loader = JSONLoader(settings)
    root_layout_builder = HTMLRootLayoutBuilder()
    front_matter_processor = FrontMatterProcessor(json_loader)
    template_context = TemplateContext(md_loader, json_loader, front_matter_processor)
    api = API(template_context, front_matter_processor)
    pagination_handler = PaginationHandler(template_context, root_layout_builder, api)
    template_handler = TemplateHandler(
        settings,
        root_layout_builder,
        pagination_handler,
        api,
    )
    favicon_writer = FaviconWriter(settings)
    script_writer = ScriptWriter(settings)
    asset_writer = AssetWriter(settings)
    css_writer = CSSWriter(settings)
    root_files_writer = RootFilesWriter(settings)

    asset_handler = AssetHandler(
        favicon_writer, script_writer, asset_writer, css_writer, root_files_writer
    )

    return (template_handler, asset_handler)


def generate_site(template_handler: TemplateHandler, asset_handler: AssetHandler):
    """
    Generates the static site by calling the build method of the StaticSiteGenerator.

    Args:
        template_handler (TemplateHandler): The initialized TemplateHandler
        asset_handler (AssetHandler): The initialized AssetHandler
    """
    site_generator = StaticSiteGenerator(template_handler, asset_handler)
    site_generator.build()


def build_static_site(root_path: str):
    """
    Builds a static site by initializing the necessary components and calling the build method.

    This function sets up the TemplateHandler with the MarkdownLoader and JSONLoader, as well as
    various writers for favicon, scripts, images, and CSS. It then creates a StaticSiteGenerator
    instance and calls its build method to generate the static site.
    """
    # Set up logging configuration
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Load settings
    settings = load_settings(root_path)

    # Initialize components
    template_handler, asset_handler = initialize_components(settings)

    # Build the static site
    generate_site(template_handler, asset_handler)

"""
This package is part of the Shodo Static Site Generator.
It provides the necessary classes and functions for building a static site.

Classes:
- `TemplateHandler`: Handles the rendering of templates.
- `DataLoader`, `MarkdownLoader`, `JSONLoader`, `SettingsLoader` : These
   classes are responsible for loading data from various sources.
- `FaviconWriter`, `ScriptWriter`, `ImageWriter`, `CSSWriter`: These classes handle
   copying, combining, and writing of various assets.
- `AssetHandler`: Dataclass for holding multiple instances of AssetWriter.
- `StaticSiteGenerator`: This class orchestrates the generation of the static site.

This package is used in the `site_builder.py` script to build the static site.

"""

from .template_handler import TemplateHandler
from .html_root_layout_builder import HTMLRootLayoutBuilder
from .pagination_handler import PaginationHandler
from .template_context import TemplateContext
from .api import API
from .data_loader import DataLoader, MarkdownLoader, JSONLoader, SettingsLoader
from .asset_writer import (
    FaviconWriter,
    ScriptWriter,
    AssetWriter,
    CSSWriter,
    AssetHandler,
    RootFilesWriter,
)
from .static_site_generator import StaticSiteGenerator
from .assembler import (
    load_settings,
    initialize_components,
    generate_site,
    build_static_site,
)
from .start_shodo_project import start_shodo_project
from .server import start_server
from .cli import cli

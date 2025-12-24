"""
This module builds a static site in the destination directory from jinja2
templates and all static assets
"""

import os
from shodo_ssg import build_static_site

if __name__ == "__main__":
    # Set the ROOT_PATH variable to the directory of this file
    root_path = os.path.dirname(os.path.abspath(__file__))
    build_static_site(root_path)

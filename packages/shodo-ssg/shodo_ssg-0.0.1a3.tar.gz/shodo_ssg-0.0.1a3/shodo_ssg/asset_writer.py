"""
This module is responsible for writing static assets, including
styles, scripts, and images to the destination build directory
"""

from dataclasses import dataclass
import logging
import os
import shutil

from shodo_ssg.data_loader import SettingsDict


class BaseAssetWriter:
    """
    Base class for writing and compiling static assets that are to be included in the final build
    """

    def __init__(self, src_path: str, destination_path: str):
        self.src_path = src_path
        self.destination_path = destination_path

    def log_info(self):
        """
        Prints a status message that the file writing operation is taking place
        """
        logging.info(
            "\033[94mCopying contents from %s to %s...\033[0m",
            self.src_path,
            self.destination_path,
        )

    def write(self):
        """
        Copies contents of either a single file OR an entire directory from the
        provided source path to the destination path.
        """
        self.log_info()
        if os.path.isfile(self.src_path):
            shutil.copyfile(self.src_path, self.destination_path)
        if os.path.isdir(self.src_path):
            shutil.copytree(self.src_path, self.destination_path)


class FaviconWriter(BaseAssetWriter):
    """
    Handles writing the favicon file to the destination directory
    """

    def __init__(self, settings: SettingsDict):
        """
        Initializes the FaviconWriter with the source and destination paths for the favicon
        """
        super().__init__(
            settings["favicon_path"], f"{settings['build_dir']}/favicon.ico"
        )


class ScriptWriter(BaseAssetWriter):
    """
    Handles writing all script files to the destination directory
    """

    def __init__(self, settings: SettingsDict):
        """
        Initializes the ScriptWriter with the source and destination paths for the scripts
        """
        super().__init__(
            settings["scripts_path"], f"{settings['build_dir']}/static/scripts"
        )


class AssetWriter(BaseAssetWriter):
    """
    Handles writing all image files to the destination directory
    """

    def __init__(self, settings: SettingsDict):
        """
        Initializes the AssetWriter with the source and destination paths for the images,
        fonts, and any other static assets
        """
        super().__init__(
            settings["assets_path"], f"{settings['build_dir']}/static/assets"
        )


class CSSWriter(BaseAssetWriter):
    """
    Handles writing all CSS files to the destination directory as a single CSS file
    """

    def __init__(self, settings: SettingsDict):
        """
        Initializes the CSSWriter with the source and destination paths for the stylesheets
        """
        super().__init__(
            settings["styles_path"], f"{settings['build_dir']}/static/styles"
        )

    def log_info(self):
        """
        Prints a status message that the css file writing operation is taking place
        """
        logging.info(
            "\033[94mCombining all stylesheets from %s to %s/main.css...\033[0m",
            self.src_path,
            self.destination_path.rstrip("/"),
        )

    def write(self):
        """
        Combines all CSS files and writes to the destination directory
        """
        self.log_info()
        destination_path = self.destination_path.rstrip("/") + "/"
        os.makedirs(destination_path)
        css_files = []

        for file in os.listdir(self.src_path):
            if file.endswith(".css"):
                css_files.append(file)

        with open(f"{destination_path}main.css", "w", encoding="utf-8") as outfile:
            for index, css_file in enumerate(css_files):
                css_file_path = os.path.join(self.src_path, css_file)
                with open(css_file_path, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())
                # Add a newline character after each file's content, skipping last iteration
                if index < len(css_files) - 1:
                    outfile.write("\n\n")


class RootFilesWriter(BaseAssetWriter):
    """
    Handles writing root-level files (like robots.txt, various config files, sitemap.xml)
    to the destination directory
    """

    def __init__(self, settings: SettingsDict):
        """
        Initializes the RootFilesWriter with the source and destination paths for the root files
        """
        super().__init__(settings["root_files_path"], settings["build_dir"])

    def log_info(self):
        """
        Prints a status message that the root files writing operation is taking place
        """
        logging.info(
            "\033[94mCopying root-level files from %s to %s...\033[0m",
            self.src_path,
            self.destination_path,
        )

    def write(self):
        """
        Copies contents of self.src_path to self.destination_path, but not the self.src_path
        directory itself. If one of the files already exists in the destination, it will be
        overwritten and a warning will be logged. If one of the directories already exists in
        the destination, its contents will be merged with the source directory's contents.
        """
        if not os.path.exists(self.src_path):
            return
        self.log_info()
        for item in os.listdir(self.src_path):
            s = os.path.join(self.src_path, item)
            d = os.path.join(self.destination_path, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    logging.info(
                        "\033[94m- Directory %s already exists in destination."
                        + " Merging contents.\033[0m",
                        d,
                    )
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copytree(s, d)
            else:
                if os.path.exists(d):
                    logging.warning(
                        "\033[93mFile %s already exists in destination. Overwriting.\033[0m",
                        d,
                    )
                shutil.copyfile(s, d)


@dataclass
class AssetHandler:
    """
    Data class that holds logic for writing static site files to the build directory,
    including favicon, scripts, styles, and miscellaneous assets
    """

    favicon: FaviconWriter
    scripts: ScriptWriter
    assets: AssetWriter
    styles: CSSWriter
    root_files: RootFilesWriter

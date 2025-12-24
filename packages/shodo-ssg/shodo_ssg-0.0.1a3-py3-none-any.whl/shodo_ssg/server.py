""" 
This module contains the code to start a development server using Python's http.server module. 
It serves the static files from the build output directory of the project. 
"""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import logging
import sys
from shodo_ssg import SettingsLoader


def start_server(path_from_root: str, port=3000):
    """
    Starts a development web server using Python's http.server
    """

    settings = SettingsLoader(path_from_root)
    directory_to_serve = settings.data["build_dir"]

    # Set up logging configuration
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    class Handler(SimpleHTTPRequestHandler):
        """
        Extends Python's SimpleHTTPRequestHandler to overide the default directory
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory_to_serve, **kwargs)

    handler = Handler

    # Create the server
    with ThreadingHTTPServer(("", port), handler) as httpd:
        logging.info(
            "\033[96mServing HTTP on 127.0.0.1 port %s ( http://127.0.0.1:%s/ )...\033[95m",
            port,
            port,
        )
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:  # ^C to stop server, triggering __exit__ method
            print("\n" + "\033[96m" + "Gracefully shutting down..." + "\033[0m")
            sys.exit(0)  # Exit the program with a successful status code

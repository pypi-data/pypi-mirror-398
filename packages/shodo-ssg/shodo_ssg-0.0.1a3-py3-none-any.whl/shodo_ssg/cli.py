"""
Command-line interface for Shodo Static Site Generator.
"""

import argparse
import logging
from datetime import datetime, timezone


def get_utc_timestamp():
    """
    Generate current UTC timestamp in ISO 8601 format.
    Equivalent to: date -u +%Y-%m-%dT%H:%M:%SZ
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def timestamp_command():
    """
    CLI command to print current UTC timestamp.
    """
    print(get_utc_timestamp())


def cli():
    """
    Main entry point for the Shodo CLI.
    """
    parser = argparse.ArgumentParser(
        description="Shodo Static Site Generator CLI",
        prog="shodo",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add 'now' datetime subcommand
    subparsers.add_parser(
        "now",
        help="Generate current UTC datetime in ISO 8601 format",
    )

    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    args = parser.parse_args()

    if args.command == "now":
        timestamp_command()
    else:
        parser.print_help()


if __name__ == "__main__":
    cli()

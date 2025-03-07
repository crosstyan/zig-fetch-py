"""
Command-line interface for the ZON parser.
"""

import json
import sys
from pathlib import Path

import click
from loguru import logger

from zig_fetch_py.parser import parse_zon_file


@click.command()
@click.argument("file", type=click.Path(exists=True, readable=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(writable=True),
    help="Output JSON file path (default: stdout)",
)
@click.option("-p", "--pretty", is_flag=True, help="Pretty print JSON output")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
def main(file, output, pretty, verbose):
    """Parse ZON files and convert to JSON.

    This tool parses Zig Object Notation (ZON) files and converts them to JSON format.
    """
    # Configure logging
    log_level = "DEBUG" if verbose else "INFO"
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, level=log_level)

    logger.info(f"Processing file: {file}")

    try:
        result = parse_zon_file(file)

        indent = 4 if pretty else None
        json_str = json.dumps(result, indent=indent)

        if output:
            logger.info(f"Writing output to: {output}")
            with open(output, "w") as f:
                f.write(json_str)
        else:
            logger.debug("Writing output to stdout")
            click.echo(json_str)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


# This is only executed when the module is run directly
if __name__ == "__main__":
    # When imported as a module, click will handle the function call
    # When run directly, we need to call it explicitly
    main()

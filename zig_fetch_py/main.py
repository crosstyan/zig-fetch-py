"""
Command-line interface for zon2json.
"""

import sys
from pathlib import Path

import click
from loguru import logger

from zig_fetch_py.parser import zon_to_json


def setup_logger(verbose: bool = False):
    """
    Set up the logger.

    Args:
        verbose: Whether to enable verbose logging
    """
    logger.remove()
    log_level = "DEBUG" if verbose else "INFO"
    logger.add(sys.stderr, level=log_level)


@click.command()
@click.argument("zon_file", type=click.Path(exists=True, readable=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(writable=True, path_type=Path),
    help="Output file (default: stdout)",
)
@click.option(
    "-i", "--indent", type=int, default=2, help="Indentation for the JSON output"
)
@click.option(
    "--empty-tuple-as-dict",
    is_flag=True,
    help="Parse empty tuples as empty dictionaries",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
def main(zon_file, output, indent, empty_tuple_as_dict, verbose):
    """
    Convert a ZON file to JSON.

    ZON_FILE: Path to the ZON file to convert
    """
    # Set up logging
    setup_logger(verbose)

    try:
        # Read the ZON file
        with open(zon_file, "r") as f:
            zon_content = f.read()

        # Convert to JSON
        json_content = zon_to_json(
            zon_content, indent=indent, empty_tuple_as_dict=empty_tuple_as_dict
        )

        # Output the JSON
        if output:
            with open(output, "w") as f:
                f.write(json_content)
            logger.info(f"JSON written to {output}")
        else:
            click.echo(json_content)

    except FileNotFoundError:
        logger.error(f"File not found: {zon_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

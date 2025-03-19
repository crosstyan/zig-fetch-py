"""
Command-line interface for zig-fetch-py.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from loguru import logger

from zig_fetch_py.downloader import process_dependencies
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


def convert_zon_to_json(
    zon_file: Path,
    output: Optional[Path] = None,
    indent: int = 2,
    empty_tuple_as_dict: bool = False,
    verbose: bool = False,
):
    """
    Convert a ZON file to JSON.

    Args:
        zon_file: Path to the ZON file
        output: Output file (default: stdout)
        indent: Indentation for the JSON output
        empty_tuple_as_dict: Parse empty tuples as empty dictionaries
        verbose: Enable verbose logging
    """
    # Set up logging
    setup_logger(verbose)

    try:
        # Read the ZON file
        with open(zon_file, "r", encoding="utf-8") as f:
            zon_content = f.read()

        # Convert to JSON
        json_content = zon_to_json(
            zon_content, indent=indent, empty_tuple_as_dict=empty_tuple_as_dict
        )

        # Output the JSON
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(json_content)
            logger.info(f"JSON written to {output}")
            return json_content
        else:
            click.echo(json_content)
            return json_content

    except FileNotFoundError:
        logger.error(f"File not found: {zon_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool):
    """Zig package manager utilities."""
    # Set up logging
    setup_logger(verbose)

    # Ensure we have a context object
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose


@cli.command()
@click.argument("zon_file", type=click.Path(exists=True, readable=True, path_type=Path))
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="Recursively process dependencies from downloaded artifacts or scan directories",
)
@click.pass_context
def download(ctx: click.Context, zon_file: Path, recursive: bool):
    """
    Download dependencies from a ZON file or directory.

    If ZON_FILE is a directory, all build.zig.zon files will be processed.
    If --recursive is specified, all dependencies of dependencies will also be processed.

    ZON_FILE: Path to the ZON file or directory to process
    """
    logger.info(f"Processing dependencies from {zon_file}")

    if zon_file.is_dir():
        logger.info(f"{zon_file} is a directory, searching for build.zig.zon files")

    dependencies = process_dependencies(str(zon_file), recursive=recursive)

    if dependencies:
        logger.info(f"Successfully processed {len(dependencies)} dependencies:")
        for name, path in dependencies.items():
            logger.info(f"  - {name}: {path}")
    else:
        logger.warning("No dependencies were processed")


@cli.command()
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
@click.pass_context
def convert(
    ctx: click.Context,
    zon_file: Path,
    output: Optional[Path],
    indent: int,
    empty_tuple_as_dict: bool,
):
    """
    Convert a ZON file to JSON.

    ZON_FILE: Path to the ZON file to convert
    """
    # Use the shared convert function
    convert_zon_to_json(
        zon_file=zon_file,
        output=output,
        indent=indent,
        empty_tuple_as_dict=empty_tuple_as_dict,
        verbose=ctx.obj.get("VERBOSE", False),
    )


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
def zon2json(zon_file, output, indent, empty_tuple_as_dict, verbose):
    """
    Convert a ZON file to JSON.

    ZON_FILE: Path to the ZON file to convert
    """
    # Use the shared convert function
    convert_zon_to_json(
        zon_file=zon_file,
        output=output,
        indent=indent,
        empty_tuple_as_dict=empty_tuple_as_dict,
        verbose=verbose,
    )


def main():
    """Entry point for the zig-fetch CLI."""
    cli()  # pylint: disable=no-value-for-parameter


if __name__ == "__main__":
    main()

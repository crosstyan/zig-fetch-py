"""
Dependency downloader for Zig packages.

This module handles downloading and extracting dependencies specified in ZON files.
"""

import shutil
import click
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Set, List

import httpx
from loguru import logger

from zig_fetch_py.parser import parse_zon_file


def get_cache_dir() -> Path:
    """
    Get the Zig cache directory for packages.

    Returns:
        Path to the Zig cache directory (~/.cache/zig/p)
    """
    cache_dir = Path.home() / ".cache" / "zig" / "p"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def download_file(url: str, target_path: Path) -> None:
    """
    Download a file from a URL to a target path.

    Args:
        url: URL to download from
        target_path: Path to save the downloaded file
    """
    logger.info(f"Downloading {url} to {target_path}")

    # Create client with environment proxies
    with httpx.Client(follow_redirects=True) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()

            # Create parent directories if they don't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file
            with open(target_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)


def extract_tarball(tarball_path: Path, extract_dir: Path) -> Path:
    """
    Extract a tarball to a directory.

    Args:
        tarball_path: Path to the tarball
        extract_dir: Directory to extract to

    Returns:
        Path to the extracted directory
    """
    logger.info(f"Extracting {tarball_path} to {extract_dir}")

    # Create extraction directory if it doesn't exist
    extract_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(tarball_path, "r:*") as tar:
        # Get the common prefix of all files in the tarball
        members = tar.getmembers()
        common_prefix = Path(Path(members[0].name).parts[0]) if members else None

        # Extract all files
        tar.extractall(path=extract_dir)

        # Return the path to the extracted directory
        return extract_dir / common_prefix if common_prefix else extract_dir


def process_dependency(
    name: str, dep_info: Dict[str, Any], cache_dir: Path
) -> Optional[Path]:
    """
    Process a single dependency from a ZON file.

    Args:
        name: Name of the dependency
        dep_info: Dependency information from the ZON file
        cache_dir: Cache directory to store the dependency

    Returns:
        Path to the extracted dependency directory, or None if the dependency is already cached
    """
    url = dep_info.get("url")
    hash_value = dep_info.get("hash")

    if not url or not hash_value:
        logger.warning(f"Dependency {name} is missing url or hash, skipping")
        return None

    # Check if the dependency is already cached
    target_dir = cache_dir / hash_value
    if target_dir.exists():
        logger.info(
            f"Dependency {name} ({hash_value}) is already cached at {target_dir}"
        )
        return target_dir

    # Create a temporary directory for downloading and extracting
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Download the tarball
        tarball_path = temp_dir_path / f"{name}.tar.gz"
        download_file(url, tarball_path)

        # Extract the tarball to a temporary directory
        extract_path = extract_tarball(tarball_path, temp_dir_path / "extract")

        # Move the extracted directory to the cache directory with the hash as the name
        if extract_path and extract_path.exists():
            if not target_dir.parent.exists():
                target_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(extract_path), str(target_dir))

            logger.info(f"Dependency {name} ({hash_value}) cached at {target_dir}")
            return target_dir
        else:
            logger.error(f"Failed to extract {name} from {tarball_path}")
            return None


def find_build_zig_zon_files(directory: Path) -> List[Path]:
    """
    Find all build.zig.zon files in a directory and its subdirectories.

    Args:
        directory: Directory to search in

    Returns:
        List of paths to build.zig.zon files
    """
    logger.debug(f"Searching for build.zig.zon files in {directory}")

    zon_files = []
    for zon_file in directory.glob("**/build.zig.zon"):
        logger.debug(f"Found build.zig.zon file: {zon_file}")
        zon_files.append(zon_file)

    return zon_files


def process_dependencies(
    zon_file_path: str, recursive: bool = False
) -> Dict[str, Path]:
    """
    Process all dependencies from a ZON file.

    Args:
        zon_file_path: Path to the ZON file or directory
        recursive: Whether to process dependencies recursively

    Returns:
        Dictionary mapping dependency names to their extracted paths
    """
    # Convert to Path object
    zon_file = Path(zon_file_path)

    # If the path is a directory, find all build.zig.zon files
    if zon_file.is_dir():
        logger.info(f"Processing directory: {zon_file}")
        all_zon_files = find_build_zig_zon_files(zon_file)

        if not all_zon_files:
            logger.warning(f"No build.zig.zon files found in {zon_file}")
            return {}

        # Process all found ZON files
        result = {}
        for zon_path in all_zon_files:
            logger.info(f"Processing {zon_path}")
            deps = process_dependencies_from_file(str(zon_path), recursive)
            result.update(deps)

        return result

    # Otherwise, process the single ZON file
    return process_dependencies_from_file(zon_file_path, recursive)


def process_dependencies_from_file(
    zon_file_path: str, recursive: bool = False
) -> Dict[str, Path]:
    """
    Process all dependencies from a single ZON file.

    Args:
        zon_file_path: Path to the ZON file
        recursive: Whether to process dependencies recursively

    Returns:
        Dictionary mapping dependency names to their extracted paths
    """
    logger.info(f"Processing dependencies from file: {zon_file_path}")

    # Parse the ZON file
    try:
        zon_data = parse_zon_file(zon_file_path)
    except Exception as e:
        logger.error(f"Error parsing {zon_file_path}: {e}")
        return {}

    # Get the dependencies section
    dependencies = zon_data.get("dependencies", {})
    if not dependencies:
        logger.warning(f"No dependencies found in {zon_file_path}")
        return {}

    # Get the cache directory
    cache_dir = get_cache_dir()

    # Process each dependency
    result = {}
    processed_paths = set()

    for name, dep_info in dependencies.items():
        path = process_dependency(name, dep_info, cache_dir)
        if path:
            result[name] = path
            processed_paths.add(path)

            # Recursively process dependencies if requested
            if recursive and path.exists():
                process_nested_dependencies(path, result, processed_paths)

    return result


def process_nested_dependencies(
    dep_path: Path, result: Dict[str, Path], processed_paths: Set[Path]
) -> None:
    """
    Process nested dependencies from a dependency directory.

    Args:
        dep_path: Path to the dependency directory
        result: Dictionary to update with new dependencies
        processed_paths: Set of paths that have already been processed
    """
    # Find all build.zig.zon files in the dependency directory
    zon_files = find_build_zig_zon_files(dep_path)

    if not zon_files:
        logger.debug(f"No nested build.zig.zon files found in {dep_path}")
        return

    for zon_file in zon_files:
        logger.info(f"Processing nested dependency file: {zon_file}")

        # Parse the ZON file
        try:
            zon_data = parse_zon_file(str(zon_file))
        except Exception as e:
            logger.error(f"Error parsing {zon_file}: {e}")
            continue

        # Get the dependencies section
        dependencies = zon_data.get("dependencies", {})
        if not dependencies:
            logger.debug(f"No dependencies found in {zon_file}")
            continue

        # Get the cache directory
        cache_dir = get_cache_dir()

        # Process each dependency
        for name, dep_info in dependencies.items():
            path = process_dependency(name, dep_info, cache_dir)
            if path and path not in processed_paths:
                result[name] = path
                processed_paths.add(path)

                # Recursively process this dependency's dependencies
                process_nested_dependencies(path, result, processed_paths)


def main(zon_file_path: str, recursive: bool = False) -> None:
    """
    Main entry point for the dependency downloader.

    Args:
        zon_file_path: Path to the ZON file or directory
        recursive: Whether to process dependencies recursively
    """
    logger.info(f"Processing dependencies from {zon_file_path}")
    dependencies = process_dependencies(zon_file_path, recursive=recursive)

    if dependencies:
        logger.info(f"Successfully processed {len(dependencies)} dependencies:")
        for name, path in dependencies.items():
            logger.info(f"  - {name}: {path}")
    else:
        logger.warning("No dependencies were processed")


@click.command()
@click.argument("zon_file", type=click.Path(exists=True, readable=True))
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="Recursively process dependencies from downloaded artifacts",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(zon_file, recursive, verbose):
    """Download dependencies from a ZON file."""
    # Set up logging
    log_level = "DEBUG" if verbose else "INFO"
    logger.remove()
    logger.add(sys.stderr, level=log_level)

    # Run the main function
    main(zon_file, recursive=recursive)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

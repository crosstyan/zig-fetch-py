"""
Dependency downloader for Zig packages.

This module handles downloading and extracting dependencies specified in ZON files.
"""

import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

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


def process_dependencies(zon_file_path: str) -> Dict[str, Path]:
    """
    Process all dependencies from a ZON file.

    Args:
        zon_file_path: Path to the ZON file

    Returns:
        Dictionary mapping dependency names to their extracted paths
    """
    # Parse the ZON file
    zon_data = parse_zon_file(zon_file_path)

    # Get the dependencies section
    dependencies = zon_data.get("dependencies", {})
    if not dependencies:
        logger.warning(f"No dependencies found in {zon_file_path}")
        return {}

    # Get the cache directory
    cache_dir = get_cache_dir()

    # Process each dependency
    result = {}
    for name, dep_info in dependencies.items():
        path = process_dependency(name, dep_info, cache_dir)
        if path:
            result[name] = path

    return result


def main(zon_file_path: str) -> None:
    """
    Main entry point for the dependency downloader.

    Args:
        zon_file_path: Path to the ZON file
    """
    logger.info(f"Processing dependencies from {zon_file_path}")
    dependencies = process_dependencies(zon_file_path)

    if dependencies:
        logger.info(f"Successfully processed {len(dependencies)} dependencies:")
        for name, path in dependencies.items():
            logger.info(f"  - {name}: {path}")
    else:
        logger.warning("No dependencies were processed")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <zon_file_path>")
        sys.exit(1)

    main(sys.argv[1])

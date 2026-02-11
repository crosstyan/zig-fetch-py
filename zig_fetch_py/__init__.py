"""
zig-fetch-py - A tool to parse Zig Object Notation (ZON) files and convert them to JSON.
"""

__version__ = "0.1.0"

from zig_fetch_py.parser import dump_zon, parse_zon_file, zon_to_json
from zig_fetch_py.downloader import process_dependencies, get_cache_dir

__all__ = [
    "parse_zon_file",
    "zon_to_json",
    "dump_zon",
    "process_dependencies",
    "get_cache_dir",
]

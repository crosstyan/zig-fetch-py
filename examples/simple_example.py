#!/usr/bin/env python3
"""
Simple example demonstrating how to use the zig-fetch-py library.
"""

import json
import sys
from pathlib import Path

from loguru import logger
from zig_fetch_py.parser import parse_zon_file, zon_to_json

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Example ZON content
ZON_CONTENT = """.{
    .name = "example",
    .version = "1.0.0",
    .dependencies = .{
        .lib1 = .{
            .url = "https://example.com/lib1.tar.gz",
            .hash = "abcdef123456",
        },
    },
    .tags = .["tag1", "tag2"],
}"""


def main():
    # Create a temporary ZON file
    example_dir = Path(__file__).parent
    zon_file = example_dir / "example.zon"
    zon_file.write_text(ZON_CONTENT)

    logger.info(f"Created example ZON file: {zon_file}")

    # Parse the ZON file
    result = parse_zon_file(str(zon_file))
    logger.info("Parsed ZON file to Python dictionary:")
    logger.info(result)

    # Convert to JSON
    json_str = zon_to_json(ZON_CONTENT, indent=2)
    logger.info("Converted ZON to JSON:")
    logger.info(json_str)

    # Save JSON to file
    json_file = example_dir / "example.json"
    with open(json_file, "w") as f:
        f.write(json_str)

    logger.info(f"Saved JSON to file: {json_file}")

    # Access specific values from the parsed data
    logger.info(f"Package name: {result['name']}")
    logger.info(f"Package version: {result['version']}")
    logger.info(f"Dependencies: {list(result['dependencies'].keys())}")
    logger.info(f"Tags: {result['tags']}")


if __name__ == "__main__":
    main()

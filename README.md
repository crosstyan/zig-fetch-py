# zig-fetch-py

A Python utility for working with Zig package manager files and Zig Object Notation (ZON).

## Features

- Parse ZON files into Python dictionaries
- Convert ZON files to JSON
- Download and extract dependencies from ZON files

## Installation

### Using uv (recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

```bash
# Install uv if you don't have it
curl -sSf https://astral.sh/uv/install.sh | bash

# Clone the repository
git clone https://github.com/yourusername/zig-fetch-py.git
cd zig-fetch-py

# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in development mode
uv pip install -e .

# Install development dependencies
uv pip install -e ".[dev]"
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/zig-fetch-py.git
cd zig-fetch-py

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Usage

### Command Line Interface

The package provides a command-line interface with the following commands:

#### Download Dependencies

Download and extract dependencies from a ZON file:

```bash
zig-fetch download examples/test.zon
```

This will download all dependencies specified in the ZON file to `~/.cache/zig/p` and extract them to directories named after their hash values.

#### Convert ZON to JSON

Convert a ZON file to JSON:

```bash
zig-fetch convert examples/test.zon
```

Or use the dedicated command:

```bash
zon2json examples/test.zon
```

Options:
- `--indent N`, `-i N`: Set the indentation level for the JSON output (default: 2)
- `--output PATH`, `-o PATH`: Output file (default: stdout)
- `--empty-tuple-as-dict`: Parse empty tuples (`.{}`) as empty dictionaries (`{}`) instead of empty lists (`[]`)
- `--verbose`, `-v`: Enable verbose logging

### Python API

You can also use the package as a Python library:

```python
from zig_fetch_py.parser import parse_zon_file, zon_to_json
from zig_fetch_py.downloader import process_dependencies

# Parse a ZON file
zon_data = parse_zon_file("examples/test.zon")

# Convert ZON to JSON
json_str = zon_to_json(zon_content, indent=2)

# Download dependencies
dependencies = process_dependencies("examples/test.zon")
```

## ZON Parser Options

The ZON parser supports the following options:

- `empty_tuple_as_dict`: If True, empty tuples (`.{}`) will be parsed as empty dictionaries (`{}`) instead of empty lists (`[]`)

## Trivia

Cursor (powered by Claude 3.7) help me do almost all of the heavy lifting. I
can't even write a proper parser by my own.

The motivation of it is this issue ([add http/socks5 proxy support for package manager](https://github.com/ziglang/zig/issues/15048)).
Until proper proxy support is added to zig, I'll maintain this repo. (The Zon parser might be useful for other projects though)

## License

```
            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                    Version 2, December 2004

 Copyright (C) 2024 <crosstyan@outlook.com>

 Everyone is permitted to copy and distribute verbatim or modified
 copies of this license document, and changing it is allowed as long
 as the name is changed.

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. You just DO WHAT THE FUCK YOU WANT TO.
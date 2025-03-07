# zig-fetch-py

A Python tool to parse Zig Object Notation (ZON) files and convert them to JSON.

## Installation

### Using uv (recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver. To install zig-fetch-py using uv:

```bash
# Install uv if you don't have it
curl -sSf https://astral.sh/uv/install.sh | bash

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
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Usage

### Command Line

```bash
# Basic usage
zon2json path/to/file.zon

# Output to a file
zon2json path/to/file.zon -o output.json

# Pretty print the JSON
zon2json path/to/file.zon -p

# Enable verbose logging
zon2json path/to/file.zon -v
```

### Python API

```python
from zig_fetch_py.parser import parse_zon_file, zon_to_json

# Parse a ZON file
result = parse_zon_file("path/to/file.zon")
print(result)  # Python dictionary

# Convert ZON content to JSON
zon_content = """.{
    .name = "test",
    .version = "1.0.0",
}"""
json_str = zon_to_json(zon_content, indent=4)
print(json_str)
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=zig_fetch_py

# Generate coverage report
pytest --cov=zig_fetch_py --cov-report=html
```

## ZON Format

Zig Object Notation (ZON) is a data format used by the Zig programming language. It's similar to JSON but with some differences in syntax:

- Objects (anonymous structs) are defined with `.{ .key = value, ... }`
- Keys are prefixed with a dot: `.key = value`
- Tuples are defined with `.{value1, value2, ...}` and are parsed as arrays in JSON
- Special identifiers can be quoted with `@`: `.@"special-name" = value`
- Comments use `//` syntax

Note: ZON doesn't have a dedicated array syntax like JSON's `[]`. Instead, tuples (`.{value1, value2, ...}`) serve a similar purpose and are converted to arrays in JSON.

Example:

```zon
.{
    .name = "example",
    .version = "1.0.0",
    .dependencies = .{
        .lib1 = .{
            .url = "https://example.com/lib1.tar.gz",
            .hash = "abcdef123456",
        },
    },
    .tags = .{1, 2, 3},     // Tuple (parsed as array in JSON)
    .paths = .{""},         // Single-item tuple
}
```

## License

MIT
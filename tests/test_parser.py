"""
Unit tests for the ZON parser.
"""

import json
import pytest
from pathlib import Path

from zig_fetch_py.parser import ZonParser, parse_zon_file, zon_to_json


class TestZonParser:
    """Test cases for the ZonParser class."""

    def test_parse_empty_object(self):
        """Test parsing an empty object."""
        parser = ZonParser(".{}")
        result = parser.parse()
        assert result == {}

    def test_parse_simple_object(self):
        """Test parsing a simple object with string values."""
        parser = ZonParser(
            """.{
            .name = "test",
            .version = "1.0.0",
        }"""
        )
        result = parser.parse()
        assert result == {"name": "test", "version": "1.0.0"}

    def test_parse_nested_object(self):
        """Test parsing a nested object."""
        parser = ZonParser(
            """.{
            .metadata = .{
                .name = "test",
                .version = "1.0.0",
            },
        }"""
        )
        result = parser.parse()
        assert result == {"metadata": {"name": "test", "version": "1.0.0"}}

    def test_parse_array(self):
        """Test parsing an array."""
        parser = ZonParser(
            """.{
            .tags = .["tag1", "tag2", "tag3"],
        }"""
        )
        result = parser.parse()
        assert result == {"tags": ["tag1", "tag2", "tag3"]}

    def test_parse_numbers(self):
        """Test parsing different number formats."""
        parser = ZonParser(
            """.{
            .integer = 42,
            .negative = -10,
            .float = 3.14,
            .hex = 0xDEADBEEF,
        }"""
        )
        result = parser.parse()
        assert result == {
            "integer": 42,
            "negative": -10,
            "float": 3.14,
            "hex": 0xDEADBEEF,
        }

    def test_parse_boolean(self):
        """Test parsing boolean values."""
        parser = ZonParser(
            """.{
            .is_true = true,
            .is_false = false,
        }"""
        )
        result = parser.parse()
        assert result == {"is_true": True, "is_false": False}

    def test_parse_null(self):
        """Test parsing null values."""
        parser = ZonParser(
            """.{
            .nothing = null,
        }"""
        )
        result = parser.parse()
        assert result == {"nothing": None}

    def test_parse_comments(self):
        """Test parsing with comments."""
        parser = ZonParser(
            """.{
            // This is a comment
            .name = "test", // Inline comment
            // Another comment
            .version = "1.0.0",
        }"""
        )
        result = parser.parse()
        assert result == {"name": "test", "version": "1.0.0"}

    def test_parse_special_identifiers(self):
        """Test parsing special identifiers with @ symbol."""
        parser = ZonParser(
            """.{
            .@"special-name" = "value",
        }"""
        )
        result = parser.parse()
        assert result == {"special-name": "value"}

    def test_parse_shorthand_notation(self):
        """Test parsing shorthand notation where key is the same as value."""
        parser = ZonParser(
            """.{
            .name,
            .version,
        }"""
        )
        result = parser.parse()
        assert result == {"name": "name", "version": "version"}

    def test_parse_escaped_strings(self):
        """Test parsing strings with escape sequences."""
        parser = ZonParser(
            """.{
            .escaped = "Line 1\\nLine 2\\tTabbed\\r\\n",
        }"""
        )
        result = parser.parse()
        assert result == {"escaped": "Line 1\nLine 2\tTabbed\r\n"}

    def test_parse_error_invalid_syntax(self):
        """Test that parser raises an error for invalid syntax."""
        with pytest.raises(ValueError):
            parser = ZonParser(".{,}")
            parser.parse()

    def test_parse_error_unterminated_string(self):
        """Test that parser raises an error for unterminated strings."""
        with pytest.raises(ValueError):
            parser = ZonParser(
                """.{
                .name = "unterminated,
            }"""
            )
            parser.parse()


class TestZonFileParser:
    """Test cases for the file parsing functions."""

    def test_zon_to_json(self, tmp_path):
        """Test converting ZON to JSON."""
        zon_content = """.{
            .name = "test",
            .version = "1.0.0",
        }"""

        # Test without indentation
        json_str = zon_to_json(zon_content)
        parsed_json = json.loads(json_str)
        assert parsed_json == {"name": "test", "version": "1.0.0"}

        # Test with indentation
        json_str_pretty = zon_to_json(zon_content, indent=2)
        assert "  " in json_str_pretty  # Should have indentation
        parsed_json = json.loads(json_str_pretty)
        assert parsed_json == {"name": "test", "version": "1.0.0"}

    def test_parse_zon_file(self, tmp_path):
        """Test parsing a ZON file."""
        # Create a temporary ZON file
        zon_file = tmp_path / "test.zon"
        zon_file.write_text(
            """.{
            .name = "test",
            .version = "1.0.0",
        }"""
        )

        # Parse the file
        result = parse_zon_file(str(zon_file))
        assert result == {"name": "test", "version": "1.0.0"}

"""
ZON parser module - Parses Zig Object Notation (ZON) files.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union, Tuple, Optional

from loguru import logger


class ZonParser:
    """
    A parser for Zig Object Notation (ZON) files.
    """

    def __init__(self, content: str):
        """
        Initialize the parser with ZON content.

        Args:
            content: The ZON content to parse
        """
        self.content = content
        self.pos = 0
        self.line = 1
        self.col = 1

    def parse(self) -> Dict[str, Any]:
        """Parse ZON content and return a Python dictionary."""
        result = self._parse_value()
        return result

    def _current_char(self) -> str:
        if self.pos >= len(self.content):
            return ""
        return self.content[self.pos]

    def _next_char(self) -> str:
        self.pos += 1
        if self.pos - 1 < len(self.content):
            char = self.content[self.pos - 1]
            if char == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            return char
        return ""

    def _skip_whitespace_and_comments(self):
        while self.pos < len(self.content):
            char = self._current_char()

            # Skip whitespace
            if char.isspace():
                self._next_char()
                continue

            # Skip comments
            if (
                char == "/"
                and self.pos + 1 < len(self.content)
                and self.content[self.pos + 1] == "/"
            ):
                # Skip to end of line
                while self.pos < len(self.content) and self._current_char() != "\n":
                    self._next_char()
                continue

            break

    def _parse_value(self) -> Any:
        self._skip_whitespace_and_comments()

        char = self._current_char()

        if char == ".":
            self._next_char()  # Skip the dot

            # Check if it's an object
            if self._current_char() == "{":
                return self._parse_object()

            # Check if it's an array
            if self._current_char() == "[":
                return self._parse_array()

            # It's a field name or a special value
            return self._parse_identifier()

        elif char == '"':
            return self._parse_string()
        elif char.isdigit() or char == "-":
            return self._parse_number()
        elif char == "t" or char == "f":
            return self._parse_boolean()
        elif char == "n" and self.content[self.pos : self.pos + 4] == "null":
            self.pos += 4
            return None
        else:
            raise ValueError(
                f"Unexpected character '{char}' at line {self.line}, column {self.col}"
            )

    def _parse_object(self) -> Dict[str, Any]:
        result = {}

        # Skip the opening brace
        self._next_char()

        while True:
            self._skip_whitespace_and_comments()

            # Check for closing brace
            if self._current_char() == "}":
                self._next_char()
                break

            # Parse key
            if self._current_char() == ".":
                self._next_char()  # Skip the dot
                key = self._parse_identifier()
            else:
                raise ValueError(
                    f"Expected '.' before key at line {self.line}, column {self.col}"
                )

            self._skip_whitespace_and_comments()

            # Parse equals sign or check if it's a shorthand notation
            if self._current_char() == "=":
                self._next_char()
                self._skip_whitespace_and_comments()
                value = self._parse_value()
            else:
                # Shorthand notation where key is the same as value
                value = key

            result[key] = value

            self._skip_whitespace_and_comments()

            # Check for comma
            if self._current_char() == ",":
                self._next_char()
            elif self._current_char() != "}":
                raise ValueError(
                    f"Expected ',' or '}}' at line {self.line}, column {self.col}"
                )

        return result

    def _parse_array(self) -> List[Any]:
        result = []

        # Skip the opening bracket
        self._next_char()

        while True:
            self._skip_whitespace_and_comments()

            # Check for closing bracket
            if self._current_char() == "]":
                self._next_char()
                break

            # Parse value
            value = self._parse_value()
            result.append(value)

            self._skip_whitespace_and_comments()

            # Check for comma
            if self._current_char() == ",":
                self._next_char()
            elif self._current_char() != "]":
                raise ValueError(
                    f"Expected ',' or ']' at line {self.line}, column {self.col}"
                )

        return result

    def _parse_identifier(self) -> str:
        start = self.pos

        # Handle quoted identifiers (like .@"lsp-codegen")
        if (
            self._current_char() == "@"
            and self.pos + 1 < len(self.content)
            and self.content[self.pos + 1] == '"'
        ):
            self._next_char()  # Skip @
            return self._parse_string()

        # Regular identifier
        while self.pos < len(self.content):
            char = self._current_char()
            if char.isalnum() or char == "_" or char == "-":
                self._next_char()
            else:
                break

        if start == self.pos:
            raise ValueError(f"Empty identifier at line {self.line}, column {self.col}")

        return self.content[start : self.pos]

    def _parse_string(self) -> str:
        result = ""

        # Skip the opening quote
        self._next_char()

        while self.pos < len(self.content) and self._current_char() != '"':
            if self._current_char() == "\\":
                self._next_char()
                if self._current_char() == "n":
                    result += "\n"
                elif self._current_char() == "t":
                    result += "\t"
                elif self._current_char() == "r":
                    result += "\r"
                elif self._current_char() == '"':
                    result += '"'
                elif self._current_char() == "\\":
                    result += "\\"
                else:
                    result += "\\" + self._current_char()
            else:
                result += self._current_char()
            self._next_char()

        if self._current_char() != '"':
            raise ValueError(
                f"Unterminated string at line {self.line}, column {self.col}"
            )

        self._next_char()  # Skip the closing quote
        return result

    def _parse_number(self) -> Union[int, float]:
        start = self.pos

        # Handle hex numbers
        if (
            self._current_char() == "0"
            and self.pos + 1 < len(self.content)
            and self.content[self.pos + 1].lower() == "x"
        ):
            self._next_char()  # Skip 0
            self._next_char()  # Skip x

            hex_start = self.pos
            while self.pos < len(self.content) and (
                self._current_char().isdigit()
                or self._current_char().lower() in "abcdef"
            ):
                self._next_char()

            hex_str = self.content[hex_start : self.pos]
            return int(hex_str, 16)

        # Regular number
        is_float = False

        # Handle sign
        if self._current_char() == "-":
            self._next_char()

        # Handle digits before decimal point
        while self.pos < len(self.content) and self._current_char().isdigit():
            self._next_char()

        # Handle decimal point
        if self._current_char() == ".":
            is_float = True
            self._next_char()

            # Handle digits after decimal point
            while self.pos < len(self.content) and self._current_char().isdigit():
                self._next_char()

        # Handle exponent
        if self._current_char().lower() == "e":
            is_float = True
            self._next_char()

            # Handle exponent sign
            if self._current_char() in "+-":
                self._next_char()

            # Handle exponent digits
            while self.pos < len(self.content) and self._current_char().isdigit():
                self._next_char()

        num_str = self.content[start : self.pos]

        if is_float:
            return float(num_str)
        else:
            return int(num_str)

    def _parse_boolean(self) -> bool:
        if self.content[self.pos : self.pos + 4] == "true":
            self.pos += 4
            return True
        elif self.content[self.pos : self.pos + 5] == "false":
            self.pos += 5
            return False
        else:
            raise ValueError(
                f"Expected 'true' or 'false' at line {self.line}, column {self.col}"
            )


def parse_zon_file(file_path: str) -> Dict[str, Any]:
    """
    Parse a ZON file and return a Python dictionary.

    Args:
        file_path: Path to the ZON file

    Returns:
        Dictionary representation of the ZON file
    """
    logger.debug(f"Parsing ZON file: {file_path}")
    with open(file_path, "r") as f:
        content = f.read()

    parser = ZonParser(content)
    result = parser.parse()
    logger.debug(f"Successfully parsed ZON file")
    return result


def zon_to_json(zon_content: str, indent: Optional[int] = None) -> str:
    """
    Convert ZON content to JSON string.

    Args:
        zon_content: ZON content as string
        indent: Number of spaces for indentation (None for compact JSON)

    Returns:
        JSON string
    """
    parser = ZonParser(zon_content)
    result = parser.parse()
    return json.dumps(result, indent=indent)

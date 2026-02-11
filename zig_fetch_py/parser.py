"""
ZON parser module - Parses Zig Object Notation (ZON) files.
"""

import json
from typing import Any, Dict, List, Union, Optional

from loguru import logger


class ZonParser:
    """
    A parser for Zig Object Notation (ZON) files.
    """

    _content: str
    _pos: int
    _line: int
    _col: int
    empty_tuple_as_dict: bool = False

    def __init__(self, content: str, empty_tuple_as_dict: bool = False):
        """
        Initialize the parser with ZON content.

        Args:
            content: The ZON content to parse
            empty_tuple_as_dict: If True, empty tuples (.{}) will be parsed as empty dictionaries ({})
                               If False, empty tuples will be parsed as empty lists ([])
        """
        self._content = content
        self._pos = 0
        self._line = 1
        self._col = 1
        self.empty_tuple_as_dict = empty_tuple_as_dict

    def parse(self) -> Dict[str, Any]:
        """Parse ZON content and return a Python dictionary."""
        result = self._parse_value()
        return result

    def _current_char(self) -> str:
        if self._pos >= len(self._content):
            return ""
        return self._content[self._pos]

    def _next_char(self) -> str:
        self._pos += 1
        if self._pos - 1 < len(self._content):
            char = self._content[self._pos - 1]
            if char == "\n":
                self._line += 1
                self._col = 1
            else:
                self._col += 1
            return char
        return ""

    def _peek_char(self, offset: int = 1) -> str:
        pos = self._pos + offset
        if pos >= len(self._content):
            return ""
        return self._content[pos]

    def _skip_whitespace_and_comments(self):
        while self._pos < len(self._content):
            char = self._current_char()

            # Skip whitespace
            if char.isspace():
                self._next_char()
                continue

            # Skip comments
            if (
                char == "/"
                and self._pos + 1 < len(self._content)
                and self._content[self._pos + 1] == "/"
            ):
                # Skip to end of line
                while self._pos < len(self._content) and self._current_char() != "\n":
                    self._next_char()
                continue

            break

    def _parse_value(self) -> Any:
        """Parse a ZON value."""
        self._skip_whitespace_and_comments()

        char = self._current_char()

        if char == ".":
            self._next_char()  # Skip the dot

            # Check if it's an object or tuple
            if self._current_char() == "{":
                return self._parse_object()

            # It's a field name or a special value
            return self._parse_identifier()

        elif char == '"':
            return self._parse_string()
        elif char == "\\" and self._peek_char() == "\\":
            return self._parse_multiline_string()
        elif char.isdigit() or char == "-":
            return self._parse_number()
        elif char == "t" or char == "f":
            return self._parse_boolean()
        elif char == "n" and self._content[self._pos : self._pos + 4] == "null":
            self._pos += 4
            return None
        else:
            raise ValueError(
                f"Unexpected character '{char}' at line {self._line}, column {self._col}"
            )

    def _parse_object(self) -> Union[Dict[str, Any], List[Any]]:
        """Parse a ZON object or tuple."""
        # Skip the opening brace
        self._next_char()

        # Look ahead to see if this is a tuple or an object
        pos_before = self._pos
        line_before = self._line
        col_before = self._col

        self._skip_whitespace_and_comments()

        # Check if it's empty
        if self._current_char() == "}":
            # Need to determine if it should be an empty object or empty tuple
            # Use the configuration option to decide
            self._next_char()  # Skip the closing brace
            return (
                {} if self.empty_tuple_as_dict else []
            )  # Empty dict or list based on config

        # Look at the first character to determine if it's a tuple or object
        is_tuple = True
        if self._current_char() == ".":
            # Look ahead one more character
            self._next_char()
            # If the next character is an object, it could be a nested tuple
            if self._current_char() == "{":
                # This is potentially a nested tuple starting with .{
                # Go back to the dot and let the normal parsing decide
                self._pos -= 1
            elif (
                self._current_char() == "@"
                or self._current_char().isalnum()
                or self._current_char() == "_"
            ):
                # This looks like a field name, so it's probably an object
                is_tuple = False
            else:
                # Unexpected character after dot, could be a syntax error
                is_tuple = False

        # Reset position
        self._pos = pos_before
        self._line = line_before
        self._col = col_before

        if is_tuple:
            return self._parse_tuple()
        else:
            return self._parse_struct()

    def _parse_struct(self) -> Dict[str, Any]:
        """Parse a ZON struct/object with key-value pairs."""
        result = {}

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
                    f"Expected '.' before key at line {self._line}, column {self._col}"
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
                    f"Expected ',' or '}}' at line {self._line}, column {self._col}"
                )

        return result

    def _parse_tuple(self) -> Union[Dict[str, Any], List[Any]]:
        """
        Parse a ZON tuple as a list of values or empty dict based on configuration.

        Returns:
            List[Any] for non-empty tuples, or Dict[str, Any] if empty and empty_tuple_as_dict=True
        """
        result = []

        # Skip the opening brace (already done in _parse_object)
        self._skip_whitespace_and_comments()

        # Check for empty tuple
        if self._current_char() == "}":
            self._next_char()
            return (
                {} if self.empty_tuple_as_dict else []
            )  # Empty dict or list based on config

        while True:
            self._skip_whitespace_and_comments()

            # Check for closing brace
            if self._current_char() == "}":
                self._next_char()
                break

            # Handle the special case of nested tuple/object with dot prefix
            if self._current_char() == ".":
                # Save position before the dot
                pos_before = self._pos
                line_before = self._line
                col_before = self._col

                self._next_char()  # Skip the dot

                # If we have a nested object/tuple
                if self._current_char() == "{":
                    # Parse the nested object/tuple
                    value = self._parse_object()
                    result.append(value)
                else:
                    # Not a nested tuple/object, reset position and parse normally
                    self._pos = pos_before
                    self._line = line_before
                    self._col = col_before

                    # Parse as normal value
                    value = self._parse_value()
                    result.append(value)
            else:
                # Regular value
                value = self._parse_value()
                result.append(value)

            self._skip_whitespace_and_comments()

            # Check for comma
            if self._current_char() == ",":
                self._next_char()
            elif self._current_char() != "}":
                raise ValueError(
                    f"Expected ',' or '}}' at line {self._line}, column {self._col}"
                )

        return result

    def _parse_identifier(self) -> str:
        start = self._pos

        # Handle quoted identifiers (like .@"lsp-codegen")
        if (
            self._current_char() == "@"
            and self._pos + 1 < len(self._content)
            and self._content[self._pos + 1] == '"'
        ):
            self._next_char()  # Skip @
            return self._parse_string()

        # Regular identifier
        while self._pos < len(self._content):
            char = self._current_char()
            if char.isalnum() or char == "_" or char == "-":
                self._next_char()
            else:
                break

        if start == self._pos:
            raise ValueError(
                f"Empty identifier at line {self._line}, column {self._col}"
            )

        return self._content[start : self._pos]

    def _parse_string(self) -> str:
        result = ""

        # Skip the opening quote
        self._next_char()

        while self._pos < len(self._content) and self._current_char() != '"':
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
                f"Unterminated string at line {self._line}, column {self._col}"
            )

        self._next_char()  # Skip the closing quote
        return result

    def _parse_multiline_string(self) -> str:
        lines: List[str] = []

        while self._current_char() == "\\" and self._peek_char() == "\\":
            self._next_char()  # Skip first backslash
            self._next_char()  # Skip second backslash

            start = self._pos
            while self._pos < len(self._content) and self._current_char() != "\n":
                self._next_char()

            lines.append(self._content[start : self._pos])

            if self._current_char() == "\n":
                self._next_char()

            self._skip_whitespace_and_comments()

        return "\n".join(lines)

    def _parse_number(self) -> Union[int, float]:
        start = self._pos

        # Handle hex numbers
        if (
            self._current_char() == "0"
            and self._pos + 1 < len(self._content)
            and self._content[self._pos + 1].lower() == "x"
        ):
            self._next_char()  # Skip 0
            self._next_char()  # Skip x

            hex_start = self._pos
            while self._pos < len(self._content) and (
                self._current_char().isdigit()
                or self._current_char().lower() in "abcdef"
            ):
                self._next_char()

            hex_str = self._content[hex_start : self._pos]
            return int(hex_str, 16)

        # Regular number
        is_float = False

        # Handle sign
        if self._current_char() == "-":
            self._next_char()

        # Handle digits before decimal point
        while self._pos < len(self._content) and self._current_char().isdigit():
            self._next_char()

        # Handle decimal point
        if self._current_char() == ".":
            is_float = True
            self._next_char()

            # Handle digits after decimal point
            while self._pos < len(self._content) and self._current_char().isdigit():
                self._next_char()

        # Handle exponent
        if self._current_char().lower() == "e":
            is_float = True
            self._next_char()

            # Handle exponent sign
            if self._current_char() in "+-":
                self._next_char()

            # Handle exponent digits
            while self._pos < len(self._content) and self._current_char().isdigit():
                self._next_char()

        num_str = self._content[start : self._pos]

        if is_float:
            return float(num_str)
        else:
            return int(num_str)

    def _parse_boolean(self) -> bool:
        if self._content[self._pos : self._pos + 4] == "true":
            self._pos += 4
            return True
        elif self._content[self._pos : self._pos + 5] == "false":
            self._pos += 5
            return False
        else:
            raise ValueError(
                f"Expected 'true' or 'false' at line {self._line}, column {self._col}"
            )


def _dump_value(value: Any, indent: int = 0) -> str:
    indent_str = " " * indent
    next_indent = indent + 4
    next_indent_str = " " * next_indent

    if isinstance(value, dict):
        if not value:
            return ".{}"

        lines = [".{"]
        for key, item in value.items():
            if isinstance(item, str) and "\n" in item:
                lines.append(f"{next_indent_str}.{key} =")
                for part in item.split("\n"):
                    lines.append(f"{next_indent_str}\\\\{part}")
                lines.append(f"{next_indent_str},")
            else:
                dumped = _dump_value(item, next_indent)
                lines.append(f"{next_indent_str}.{key} = {dumped},")
        lines.append(f"{indent_str}}}")
        return "\n".join(lines)

    if isinstance(value, list):
        if not value:
            return ".{}"
        items = ", ".join(_dump_value(item, indent) for item in value)
        return f".{{{items}}}"

    if isinstance(value, str):
        escaped = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\t", "\\t")
            .replace("\r", "\\r")
        )
        return f'"{escaped}"'

    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"

    return str(value)


def dump_zon(value: Any) -> str:
    return _dump_value(value)


def parse_zon_file(file_path: str, empty_tuple_as_dict: bool = False) -> Dict[str, Any]:
    """
    Parse a ZON file and return a Python dictionary.

    Args:
        file_path: Path to the ZON file
        empty_tuple_as_dict: If True, empty tuples (.{}) will be parsed as empty dictionaries ({})
                           If False, empty tuples will be parsed as empty lists ([])

    Returns:
        Dictionary representation of the ZON file
    """
    logger.debug(f"Parsing ZON file: {file_path}")
    with open(file_path, "r") as f:
        content = f.read()

    parser = ZonParser(content, empty_tuple_as_dict=empty_tuple_as_dict)
    result = parser.parse()
    logger.debug("Successfully parsed ZON file")
    return result


def zon_to_json(
    zon_content: str, indent: Optional[int] = None, empty_tuple_as_dict: bool = False
) -> str:
    """
    Convert ZON content to JSON string.

    Args:
        zon_content: ZON content as string
        indent: Number of spaces for indentation (None for compact JSON)
        empty_tuple_as_dict: If True, empty tuples (.{}) will be parsed as empty dictionaries ({})
                           If False, empty tuples will be parsed as empty lists ([])

    Returns:
        JSON string
    """
    parser = ZonParser(zon_content, empty_tuple_as_dict=empty_tuple_as_dict)
    result = parser.parse()
    return json.dumps(result, indent=indent)

"""Main parsing functions for sloppy_json."""

from __future__ import annotations

import re
from typing import Any

from .exceptions import ErrorInfo, SloppyJSONDecodeError
from .options import RecoveryOptions

# Regex patterns
TRIPLE_DOUBLE_QUOTE = re.compile(r'"""(?:json)?\s*([\s\S]*?)"""', re.IGNORECASE)
TRIPLE_SINGLE_QUOTE = re.compile(r"'''(?:json)?\s*([\s\S]*?)'''", re.IGNORECASE)
CODE_BLOCK = re.compile(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", re.IGNORECASE)
SINGLE_LINE_COMMENT = re.compile(r"//[^\n]*")
BLOCK_COMMENT = re.compile(r"/\*[\s\S]*?\*/")
JS_IDENTIFIER = re.compile(r"^[a-zA-Z_$][a-zA-Z0-9_$]*$")
BOM = "\ufeff"


class Parser:
    """JSON parser with recovery options."""

    def __init__(self, text: str, options: RecoveryOptions) -> None:
        self.original_text = text
        self.text = text
        self.options = options
        self.pos = 0
        self.errors: list[ErrorInfo] = []

    def parse(self) -> str | tuple[str, list[ErrorInfo]]:
        """Parse the JSON and return normalized output."""
        # Preprocessing
        self._strip_bom()
        self._extract_json()
        self._strip_comments()

        # Parse the value
        self._skip_whitespace()

        if self.pos >= len(self.text):
            self._error("Empty input")

        result = self._parse_value()

        self._skip_whitespace()

        # Check for trailing content (only in strict mode)
        if self.pos < len(self.text) and not self.options.extract_json_from_text:
            remaining = self.text[self.pos :].strip()
            if remaining:
                self._error(f"Unexpected content after JSON: {remaining[:20]}...")

        output = self._serialize(result)

        if self.options.partial_recovery:
            return output, self.errors
        return output

    def _strip_bom(self) -> None:
        """Remove UTF-8 BOM if present."""
        if self.text.startswith(BOM):
            self.text = self.text[1:]

    def _extract_json(self) -> None:
        """Extract JSON from code blocks, triple quotes, or surrounding text."""
        # Priority: code blocks > triple quotes > text extraction
        if self.options.extract_from_code_blocks:
            match = CODE_BLOCK.search(self.text)
            if match:
                self.text = match.group(1).strip()
                return

        if self.options.extract_from_triple_quotes:
            # Try double quotes first
            match = TRIPLE_DOUBLE_QUOTE.search(self.text)
            if match:
                self.text = match.group(1).strip()
                return
            # Try single quotes
            match = TRIPLE_SINGLE_QUOTE.search(self.text)
            if match:
                self.text = match.group(1).strip()
                return

        if self.options.extract_json_from_text:
            # Find the first { or [ and try to match balanced brackets
            extracted = self._extract_json_from_text()
            if extracted:
                self.text = extracted

    def _extract_json_from_text(self) -> str | None:
        """Extract JSON object or array from surrounding text."""
        # Find first { or [
        obj_start = self.text.find("{")
        arr_start = self.text.find("[")

        if obj_start == -1 and arr_start == -1:
            return None

        # Use whichever comes first
        if obj_start == -1:
            start = arr_start
            open_char, close_char = "[", "]"
        elif arr_start == -1 or obj_start < arr_start:
            start = obj_start
            open_char, close_char = "{", "}"
        else:
            start = arr_start
            open_char, close_char = "[", "]"

        # Find matching close bracket, accounting for nested structures and strings
        depth = 0
        in_string = False
        escape_next = False
        i = start

        while i < len(self.text):
            char = self.text[i]

            if escape_next:
                escape_next = False
                i += 1
                continue

            if char == "\\":
                escape_next = True
                i += 1
                continue

            if char == '"' and not in_string:
                in_string = True
            elif char == '"' and in_string:
                in_string = False
            elif not in_string:
                if char == open_char:
                    depth += 1
                elif char == close_char:
                    depth -= 1
                    if depth == 0:
                        return self.text[start : i + 1]

            i += 1

        # If we didn't find a complete match, return from start to end
        # (auto_close options will handle it)
        if self.options.auto_close_objects or self.options.auto_close_arrays:
            return self.text[start:]

        return None

    def _strip_comments(self) -> None:
        """Remove JavaScript-style comments."""
        if not self.options.allow_comments:
            return

        # We need to be careful not to remove comment-like content inside strings
        result: list[str] = []
        i = 0
        in_string = False
        escape_next = False

        while i < len(self.text):
            char = self.text[i]

            if escape_next:
                result.append(char)
                escape_next = False
                i += 1
                continue

            if char == "\\":
                result.append(char)
                escape_next = True
                i += 1
                continue

            if char == '"' and not in_string:
                in_string = True
                result.append(char)
                i += 1
                continue
            elif char == '"' and in_string:
                in_string = False
                result.append(char)
                i += 1
                continue

            if in_string:
                result.append(char)
                i += 1
                continue

            # Check for single-line comment
            if char == "/" and i + 1 < len(self.text) and self.text[i + 1] == "/":
                # Skip to end of line
                while i < len(self.text) and self.text[i] != "\n":
                    i += 1
                continue

            # Check for block comment
            if char == "/" and i + 1 < len(self.text) and self.text[i + 1] == "*":
                # Find end of block comment
                end = self.text.find("*/", i + 2)
                if end == -1:
                    self._error("Unclosed block comment")
                i = end + 2
                continue

            result.append(char)
            i += 1

        self.text = "".join(result)

    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.pos < len(self.text) and self.text[self.pos] in " \t\n\r":
            self.pos += 1

    def _peek(self, offset: int = 0) -> str | None:
        """Peek at character at current position + offset."""
        pos = self.pos + offset
        if pos < len(self.text):
            return self.text[pos]
        return None

    def _advance(self) -> str:
        """Advance position and return current character."""
        char = self.text[self.pos]
        self.pos += 1
        return char

    def _error(self, message: str) -> None:
        """Record or raise an error."""
        # Calculate line and column
        line = 1
        col = 1
        for _i, char in enumerate(self.text[: self.pos]):
            if char == "\n":
                line += 1
                col = 1
            else:
                col += 1

        error = ErrorInfo(message=message, position=self.pos, line=line, column=col)
        self.errors.append(error)

        if not self.options.partial_recovery:
            raise SloppyJSONDecodeError(message, self.pos, line, col)

    def _warn(self, message: str) -> None:
        """Record a warning (recoverable issue). Does not raise."""
        # Calculate line and column
        line = 1
        col = 1
        for _i, char in enumerate(self.text[: self.pos]):
            if char == "\n":
                line += 1
                col = 1
            else:
                col += 1

        error = ErrorInfo(message=message, position=self.pos, line=line, column=col)
        self.errors.append(error)

    def _parse_value(self) -> Any:
        """Parse a JSON value."""
        self._skip_whitespace()

        if self.pos >= len(self.text):
            if self.options.partial_recovery:
                return None
            self._error("Unexpected end of input")

        char = self._peek()

        if char == "{":
            return self._parse_object()
        elif char == "[":
            return self._parse_array()
        elif char == '"':
            return self._parse_string('"')
        elif char == "'" and self.options.allow_single_quotes:
            return self._parse_string("'")
        elif char == "-":
            # Could be negative number or -Infinity
            if (
                self.pos + 1 < len(self.text)
                and self.text[self.pos + 1 : self.pos + 9] == "Infinity"
            ):
                self._advance()  # consume '-'
                return self._parse_keyword_or_identifier(is_negative_infinity=True)
            return self._parse_number()
        elif char and char.isdigit():
            return self._parse_number()
        else:
            return self._parse_keyword_or_identifier()

    def _parse_object(self) -> _Object:
        """Parse a JSON object."""
        self._advance()  # consume '{'
        result = _Object()

        self._skip_whitespace()

        # Check for immediate end of input
        if self.pos >= len(self.text):
            if self.options.auto_close_objects:
                self._warn("Auto-closed unclosed object")
                return result
            self._error("Unexpected end of input in object")
            return result

        # Handle empty object
        if self._peek() == "}":
            self._advance()
            return result

        while True:
            self._skip_whitespace()

            # Check for end or auto-close
            if self.pos >= len(self.text):
                if self.options.auto_close_objects:
                    self._warn("Auto-closed unclosed object")
                    break
                self._error("Unexpected end of input in object")
                break

            char = self._peek()

            # Handle trailing comma
            if char == "}":
                self._advance()
                break

            # Parse key
            key = self._parse_key()

            self._skip_whitespace()

            # Expect colon
            if self._peek() == ":":
                self._advance()
            else:
                if self.pos >= len(self.text) and self.options.auto_close_objects:
                    self._warn("Auto-closed object with incomplete key-value")
                    result.add(key, None)
                    break
                self._error(f"Expected ':' after key, got {self._peek()!r}")

            self._skip_whitespace()

            # Handle missing value
            if self.pos >= len(self.text):
                if self.options.auto_close_objects:
                    result.add(key, None)
                    break
                self._error("Unexpected end of input after ':'")

            # Parse value
            value = self._parse_value()
            result.add(key, value)

            self._skip_whitespace()

            # Check for end of input
            if self.pos >= len(self.text):
                if self.options.auto_close_objects:
                    self._warn("Auto-closed unclosed object")
                    break
                self._error("Unexpected end of input in object")
                break

            char = self._peek()

            if char == ",":
                self._advance()
                self._skip_whitespace()
                # Check for trailing comma
                if self._peek() == "}":
                    if not self.options.allow_trailing_commas:
                        self._error("Trailing comma in object")
                    self._advance()
                    break
            elif char == "}":
                self._advance()
                break
            else:
                # Missing comma - check if next looks like a key
                looks_like_key = (
                    char == '"' or char == "'" or (char and (char.isalpha() or char in "_$"))
                )
                if self.options.allow_missing_commas and looks_like_key:
                    continue  # Implicit comma
                self._error(f"Expected ',' or '}}', got {char!r}")

        return result

    def _parse_array(self) -> list[Any]:
        """Parse a JSON array."""
        self._advance()  # consume '['
        result: list[Any] = []

        self._skip_whitespace()

        # Check for immediate end of input
        if self.pos >= len(self.text):
            if self.options.auto_close_arrays:
                self._warn("Auto-closed unclosed array")
                return result
            self._error("Unexpected end of input in array")
            return result

        # Handle empty array
        if self._peek() == "]":
            self._advance()
            return result

        while True:
            self._skip_whitespace()

            # Check for end or auto-close
            if self.pos >= len(self.text):
                if self.options.auto_close_arrays:
                    self._warn("Auto-closed unclosed array")
                    break
                self._error("Unexpected end of input in array")
                break

            char = self._peek()

            # Handle trailing comma case
            if char == "]":
                self._advance()
                break

            # Parse value
            value = self._parse_value()
            result.append(value)

            self._skip_whitespace()

            # Check for end of input
            if self.pos >= len(self.text):
                if self.options.auto_close_arrays:
                    self._warn("Auto-closed unclosed array")
                    break
                self._error("Unexpected end of input in array")
                break

            char = self._peek()

            if char == ",":
                self._advance()
                self._skip_whitespace()
                # Check for trailing comma or end of input
                if self._peek() == "]":
                    if not self.options.allow_trailing_commas:
                        self._error("Trailing comma in array")
                    self._advance()
                    break
                # Check for end of input after comma
                if self.pos >= len(self.text):
                    if self.options.auto_close_arrays:
                        self._warn("Auto-closed unclosed array")
                        break
                    self._error("Unexpected end of input after comma")
                    break
            elif char == "]":
                self._advance()
                break
            else:
                # Missing comma
                if self.options.allow_missing_commas:
                    continue  # Implicit comma
                self._error(f"Expected ',' or ']', got {char!r}")

        return result

    def _parse_key(self) -> str:
        """Parse an object key."""
        char = self._peek()

        if char == '"':
            return self._parse_string('"')
        elif char == "'" and self.options.allow_single_quotes:
            return self._parse_string("'")
        elif self.options.allow_unquoted_keys:
            return self._parse_unquoted_key()
        else:
            self._error(f"Expected string key, got {char!r}")
            return ""

    def _parse_unquoted_key(self) -> str:
        """Parse an unquoted object key (JavaScript identifier)."""
        start = self.pos
        char = self._peek()

        # First char must be letter, underscore, or $
        if not char or not (char.isalpha() or char in "_$"):
            self._error(f"Invalid unquoted key start: {char!r}")
            return ""

        self._advance()

        # Rest can include digits
        while self.pos < len(self.text):
            char = self._peek()
            if char and (char.isalnum() or char in "_$"):
                self._advance()
            else:
                break

        return self.text[start : self.pos]

    def _parse_string(self, quote: str) -> str:
        """Parse a quoted string."""
        self._advance()  # consume opening quote
        result: list[str] = []

        while True:
            if self.pos >= len(self.text):
                if self.options.auto_close_strings:
                    self._warn("Auto-closed unclosed string")
                    break
                self._error("Unexpected end of input in string")
                break

            char = self._advance()

            if char == quote:
                break
            elif char == "\\":
                if self.pos >= len(self.text):
                    if self.options.auto_close_strings:
                        self._warn("Auto-closed unclosed string")
                        result.append("\\")
                        break
                    self._error("Unexpected end of input after backslash")
                    break
                escaped = self._advance()
                # Handle escape sequences - preserve them in output
                if escaped == quote:
                    # Escaped quote - just add the quote character itself
                    result.append(escaped)
                elif escaped == "\\":
                    # Double backslash - preserve both
                    result.append("\\\\")
                elif escaped in "nrtbf/":
                    # Standard escape - preserve
                    result.append("\\")
                    result.append(escaped)
                elif escaped == "u":
                    # Unicode escape - preserve as-is
                    if self.pos + 4 <= len(self.text):
                        hex_chars = self.text[self.pos : self.pos + 4]
                        result.append("\\u")
                        result.append(hex_chars)
                        self.pos += 4
                    else:
                        result.append("\\u")
                else:
                    # Unknown escape, keep the escaped char only
                    result.append(escaped)
            elif char in "\n\r" and self.options.escape_newlines_in_strings:
                # Keep literal newlines
                result.append(char)
            elif char in "\n\r\t" and not self.options.escape_newlines_in_strings:
                # Unescaped control character - error but continue
                self._error("Unescaped control character in string")
                result.append(char)
            else:
                result.append(char)

        return "".join(result)

    def _parse_number(self) -> _Number:
        """Parse a JSON number."""
        start = self.pos

        # Optional minus
        if self._peek() == "-":
            self._advance()

        # Integer part
        if self._peek() == "0":
            self._advance()
        elif self._peek() and self._peek().isdigit():  # type: ignore[union-attr]
            while self._peek() and self._peek().isdigit():  # type: ignore[union-attr]
                self._advance()
        else:
            self._error("Invalid number")

        # Fractional part
        if self._peek() == ".":
            self._advance()
            if not self._peek() or not self._peek().isdigit():  # type: ignore[union-attr]
                self._error("Invalid number: expected digit after '.'")
            while self._peek() and self._peek().isdigit():  # type: ignore[union-attr]
                self._advance()

        # Exponent
        if self._peek() and self._peek().lower() == "e":  # type: ignore[union-attr]
            self._advance()
            peek = self._peek()
            if peek is not None and peek in "+-":
                self._advance()
            if not self._peek() or not self._peek().isdigit():  # type: ignore[union-attr]
                self._error("Invalid number: expected digit in exponent")
            while self._peek() and self._peek().isdigit():  # type: ignore[union-attr]
                self._advance()

        num_str = self.text[start : self.pos]
        # Return a wrapper that preserves the original string representation
        return _Number(num_str)

    def _parse_keyword_or_identifier(self, is_negative_infinity: bool = False) -> Any:
        """Parse a keyword (true, false, null, etc.) or identifier."""
        start = self.pos

        # Read word
        while self.pos < len(self.text):
            char = self._peek()
            if char and (char.isalnum() or char in "_$"):
                self._advance()
            else:
                break

        word = self.text[start : self.pos]

        # Handle -Infinity case (minus was already consumed)
        if is_negative_infinity and word == "Infinity":
            word = "-Infinity"

        if not word:
            self._error("Expected value")
            return None

        # Check for keywords
        if word == "true":
            return True
        elif word == "false":
            return False
        elif word == "null":
            return None
        elif word == "True" and self.options.convert_python_literals:
            return True
        elif word == "False" and self.options.convert_python_literals:
            return False
        elif word == "None" and self.options.convert_python_literals:
            return None
        elif word == "undefined":
            if self.options.handle_undefined == "null":
                return None
            elif self.options.handle_undefined == "remove":
                return _Undefined()
            else:
                self._error("undefined is not valid JSON")
                return None
        elif word == "NaN":
            if self.options.handle_nan == "null":
                return None
            elif self.options.handle_nan == "string":
                return "NaN"
            else:
                self._error("NaN is not valid JSON")
                return None
        elif word == "Infinity" or word == "-Infinity":
            if self.options.handle_infinity == "null":
                return None
            elif self.options.handle_infinity == "string":
                return word
            else:
                self._error(f"{word} is not valid JSON")
                return None
        elif self.options.allow_unquoted_identifiers and JS_IDENTIFIER.match(word):
            return _Identifier(word)
        else:
            self._error(f"Unknown keyword: {word}")
            return None

    def _serialize(self, value: Any) -> str:
        """Serialize a value back to JSON string."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, _Number):
            return value.normalized
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, float):
            # Handle special float values
            if value != value or value == float("inf") or value == float("-inf"):  # NaN
                return "null"
            else:
                s = repr(value)
                # Python uses 'e' for scientific notation, JSON allows both
                return s
        elif isinstance(value, str):
            return self._serialize_string(value)
        elif isinstance(value, _Identifier):
            return f'"{value.name}"'
        elif isinstance(value, _Undefined):
            return ""  # Will be handled specially in object serialization
        elif isinstance(value, list):
            items = []
            for item in value:
                if isinstance(item, _Undefined):
                    # In arrays, undefined becomes null (can't remove elements)
                    items.append("null")
                else:
                    items.append(self._serialize(item))
            return "[" + ", ".join(items) + "]"
        elif isinstance(value, _Object):
            items = []
            for k, v in value.items:
                if isinstance(v, _Undefined):
                    continue  # Skip undefined values (remove mode)
                items.append(f"{self._serialize_string(k)}: {self._serialize(v)}")
            return "{" + ", ".join(items) + "}"
        elif isinstance(value, dict):
            items = []
            for k, v in value.items():
                if isinstance(v, _Undefined):
                    continue  # Skip undefined values (remove mode)
                items.append(f"{self._serialize_string(k)}: {self._serialize(v)}")
            return "{" + ", ".join(items) + "}"
        else:
            return str(value)

    def _serialize_string(self, s: str) -> str:
        """Serialize a string value with proper escaping.

        The string may already contain escape sequences from parsing,
        so we need to be careful not to double-escape.
        """
        result = ['"']
        i = 0
        while i < len(s):
            char = s[i]
            if char == '"':
                result.append('\\"')
            elif char == "\\":
                # Already an escape sequence - copy as-is
                if i + 1 < len(s):
                    next_char = s[i + 1]
                    if next_char in 'nrtbf"\\/':
                        result.append("\\")
                        result.append(next_char)
                        i += 2
                        continue
                    elif next_char == "u" and i + 5 < len(s):
                        # Unicode escape
                        result.append(s[i : i + 6])
                        i += 6
                        continue
                    elif next_char == "\\":
                        # Double backslash
                        result.append("\\\\")
                        i += 2
                        continue
                result.append("\\\\")
            elif char == "\n":
                result.append("\\n")
            elif char == "\r":
                result.append("\\r")
            elif char == "\t":
                result.append("\\t")
            elif ord(char) < 32:
                result.append(f"\\u{ord(char):04x}")
            else:
                result.append(char)
            i += 1
        result.append('"')
        return "".join(result)


class _Undefined:
    """Sentinel for undefined values."""

    pass


class _Identifier:
    """Wrapper for unquoted identifier values."""

    def __init__(self, name: str) -> None:
        self.name = name


class _Number:
    """Wrapper for numbers that preserves original string representation."""

    def __init__(self, raw: str) -> None:
        self.raw = raw
        # Normalize: lowercase 'e', keep original format
        self.normalized = raw.lower()


class _Object:
    """Object that preserves duplicate keys."""

    def __init__(self) -> None:
        self.items: list[tuple[str, Any]] = []

    def add(self, key: str, value: Any) -> None:
        self.items.append((key, value))


def _permissive_options() -> RecoveryOptions:
    """Return options for maximum recovery (all options enabled)."""
    return RecoveryOptions(
        allow_unquoted_keys=True,
        allow_single_quotes=True,
        allow_unquoted_identifiers=True,
        allow_trailing_commas=True,
        allow_missing_commas=True,
        auto_close_objects=True,
        auto_close_arrays=True,
        auto_close_strings=True,
        extract_json_from_text=True,
        extract_from_code_blocks=True,
        extract_from_triple_quotes=True,
        convert_python_literals=True,
        handle_undefined="null",
        handle_nan="string",
        handle_infinity="string",
        allow_comments=True,
        escape_newlines_in_strings=True,
    )


def parse(
    json_string: str,
    options: RecoveryOptions | None = None,
) -> str | tuple[str, list[ErrorInfo]]:
    """Parse a JSON string with optional recovery.

    Args:
        json_string: The JSON string to parse.
        options: Recovery options.
            - None (default): Permissive mode - all recovery enabled
            - RecoveryOptions(strict=True): Strict JSON parsing
            - RecoveryOptions(...): Custom options

    Returns:
        The parsed JSON as a normalized string.
        If options.partial_recovery is True, returns (result, errors) tuple.

    Raises:
        SloppyJSONDecodeError: If parsing fails and partial_recovery is False.

    Examples:
        # Default permissive parsing
        >>> parse("{'name': 'test', active: True,}")
        '{"name": "test", "active": true}'

        # Strict JSON parsing
        >>> parse('{"name": "test"}', RecoveryOptions(strict=True))
        '{"name": "test"}'

        # Custom options
        >>> parse("{'name': 'test'}", RecoveryOptions(allow_single_quotes=True))
        '{"name": "test"}'
    """
    if options is None:
        # Default: permissive mode
        options = _permissive_options()
    elif options.strict:
        # Strict mode: ignore all other flags
        options = RecoveryOptions(strict=True)

    parser = Parser(json_string, options)
    return parser.parse()

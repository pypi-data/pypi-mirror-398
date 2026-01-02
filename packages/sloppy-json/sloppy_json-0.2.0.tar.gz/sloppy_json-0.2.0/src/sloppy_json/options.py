"""Recovery options configuration for sloppy_json."""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from typing import Literal

# Detection patterns (moved from detector.py)
_UNQUOTED_KEY_PATTERN = re.compile(r"{\s*[a-zA-Z_$][a-zA-Z0-9_$]*\s*:")
_SINGLE_QUOTE_PATTERN = re.compile(r"['\[\{,]\s*'|':\s*'|:\s*'")
_TRAILING_COMMA_OBJECT = re.compile(r",\s*}")
_TRAILING_COMMA_ARRAY = re.compile(r",\s*\]")
_MISSING_COMMA_PATTERN = re.compile(r'"\s+"|\d\s+"|\}\s+\{|\]\s+\[|"\s+\{|"\s+\[')
_PYTHON_TRUE = re.compile(r"[:\[\s,]True[,\s\]\}]|^True[,\s\]\}]")
_PYTHON_FALSE = re.compile(r"[:\[\s,]False[,\s\]\}]|^False[,\s\]\}]")
_PYTHON_NONE = re.compile(r"[:\[\s,]None[,\s\]\}]|^None[,\s\]\}]")
_UNDEFINED_PATTERN = re.compile(r"[:\[\s,]undefined[,\s\]\}]")
_NAN_PATTERN = re.compile(r"[:\[\s,]NaN[,\s\]\}]")
_INFINITY_PATTERN = re.compile(r"[:\[\s,]-?Infinity[,\s\]\}]")
_SINGLE_LINE_COMMENT = re.compile(r"//")
_BLOCK_COMMENT = re.compile(r"/\*")
_CODE_BLOCK_PATTERN = re.compile(r"```")
_TRIPLE_QUOTE_PATTERN = re.compile(r'"""|\'\'\'')


def _is_in_string(text: str, position: int) -> bool:
    """Check if a position is inside a JSON string."""
    quote_count = 0
    in_escape = False

    for char in text[:position]:
        if in_escape:
            in_escape = False
            continue
        if char == "\\":
            in_escape = True
            continue
        if char == '"':
            quote_count += 1

    return quote_count % 2 == 1


@dataclass
class RecoveryOptions:
    """Configuration options for JSON recovery.

    Each option controls a specific type of recovery behavior.
    Options default to False/error to maintain strict parsing by default.

    Usage:
        # Permissive (default when no options passed to parse())
        parse(text)

        # Strict JSON parsing
        parse(text, RecoveryOptions(strict=True))

        # Custom options
        parse(text, RecoveryOptions(allow_single_quotes=True))

        # Auto-detect from samples
        parse(text, RecoveryOptions.detect_from(samples))
    """

    # Strict mode - when True, all other options are ignored
    strict: bool = False
    """When True, parse as standard JSON (all recovery disabled)."""

    # Quoting options
    allow_unquoted_keys: bool = False
    """Allow object keys without quotes: {name: "value"}"""

    allow_single_quotes: bool = False
    """Allow single-quoted strings: {'key': 'value'}"""

    allow_unquoted_identifiers: bool = False
    """Allow unquoted identifier values (JS identifier rules): {"key": value}"""

    # Comma handling
    allow_trailing_commas: bool = False
    """Allow trailing commas in objects and arrays: {"a": 1,}"""

    allow_missing_commas: bool = False
    """Allow missing commas between elements: {"a": 1 "b": 2}"""

    # Incomplete JSON handling
    auto_close_objects: bool = False
    """Automatically close unclosed objects: {"key": "value" -> {"key": "value"}"""

    auto_close_arrays: bool = False
    """Automatically close unclosed arrays: [1, 2, 3 -> [1, 2, 3]"""

    auto_close_strings: bool = False
    """Automatically close unclosed strings: {"key": "value -> {"key": "value"}"""

    # Extra content handling
    extract_json_from_text: bool = False
    """Extract JSON from surrounding text: 'Here is: {"a": 1} done' -> {"a": 1}"""

    extract_from_code_blocks: bool = False
    """Extract JSON from markdown code blocks: ```json\\n{"a": 1}\\n```"""

    extract_from_triple_quotes: bool = False
    '''Extract JSON from Python triple-quoted strings: """{"a": 1}"""'''

    # Value normalization
    convert_python_literals: bool = False
    """Convert Python literals to JSON: True/False/None -> true/false/null"""

    handle_undefined: Literal["null", "remove", "error"] = "null"
    """How to handle JavaScript undefined values."""

    handle_nan: Literal["null", "string", "error"] = "string"
    """How to handle NaN values."""

    handle_infinity: Literal["null", "string", "error"] = "string"
    """How to handle Infinity/-Infinity values."""

    # Comments
    allow_comments: bool = False
    """Allow JavaScript-style comments: // and /* */"""

    # Escape handling
    escape_newlines_in_strings: bool = False
    """Handle unescaped newlines/tabs in strings."""

    # Error handling
    partial_recovery: bool = False
    """When True, parse() returns tuple of (partial_result, list[ErrorInfo])."""

    def __post_init__(self) -> None:
        """Validate option values."""
        valid_undefined = ("null", "remove", "error")
        valid_nan = ("null", "string", "error")
        valid_infinity = ("null", "string", "error")

        if self.handle_undefined not in valid_undefined:
            raise ValueError(f"handle_undefined must be one of {valid_undefined}")
        if self.handle_nan not in valid_nan:
            raise ValueError(f"handle_nan must be one of {valid_nan}")
        if self.handle_infinity not in valid_infinity:
            raise ValueError(f"handle_infinity must be one of {valid_infinity}")

    def __repr__(self) -> str:
        """Return a clean repr showing only non-default values."""
        # Get default values
        defaults = {
            "strict": False,
            "allow_unquoted_keys": False,
            "allow_single_quotes": False,
            "allow_unquoted_identifiers": False,
            "allow_trailing_commas": False,
            "allow_missing_commas": False,
            "auto_close_objects": False,
            "auto_close_arrays": False,
            "auto_close_strings": False,
            "extract_json_from_text": False,
            "extract_from_code_blocks": False,
            "extract_from_triple_quotes": False,
            "convert_python_literals": False,
            "handle_undefined": "null",
            "handle_nan": "string",
            "handle_infinity": "string",
            "allow_comments": False,
            "escape_newlines_in_strings": False,
            "partial_recovery": False,
        }

        non_default = []
        for field in fields(self):
            value = getattr(self, field.name)
            default = defaults.get(field.name)
            if value != default:
                if isinstance(value, str):
                    non_default.append(f"{field.name}={value!r}")
                else:
                    non_default.append(f"{field.name}={value}")

        if not non_default:
            return "RecoveryOptions()"

        if len(non_default) <= 3:
            return f"RecoveryOptions({', '.join(non_default)})"

        # Multi-line for many options
        inner = ",\n    ".join(non_default)
        return f"RecoveryOptions(\n    {inner}\n)"

    @classmethod
    def detect_from(cls, samples: list[str]) -> RecoveryOptions:
        """Analyze JSON samples and detect minimum required recovery options.

        This method examines a list of JSON strings and determines which
        recovery options are needed to parse them successfully.

        Args:
            samples: List of JSON strings to analyze.

        Returns:
            RecoveryOptions with minimum required options enabled.

        Example:
            >>> samples = ["{'key': 'value',}", "{name: True}"]
            >>> opts = RecoveryOptions.detect_from(samples)
            >>> opts
            RecoveryOptions(
                allow_single_quotes=True,
                allow_trailing_commas=True,
                allow_unquoted_keys=True,
                convert_python_literals=True
            )
        """
        if not samples:
            return cls()

        # Initialize all detection flags
        needs_unquoted_keys = False
        needs_single_quotes = False
        needs_trailing_commas = False
        needs_missing_commas = False
        needs_auto_close_objects = False
        needs_auto_close_arrays = False
        needs_auto_close_strings = False
        needs_python_literals = False
        needs_handle_undefined = False
        needs_handle_nan = False
        needs_handle_infinity = False
        needs_comments = False
        needs_code_blocks = False
        needs_triple_quotes = False
        needs_text_extraction = False

        for sample in samples:
            if not sample.strip():
                continue

            # Check for unquoted keys
            match = _UNQUOTED_KEY_PATTERN.search(sample)
            if match and not _is_in_string(sample, match.start()):
                needs_unquoted_keys = True

            # Check for single quotes
            if _SINGLE_QUOTE_PATTERN.search(sample):
                needs_single_quotes = True

            # Check for trailing commas
            if _TRAILING_COMMA_OBJECT.search(sample) or _TRAILING_COMMA_ARRAY.search(sample):
                needs_trailing_commas = True

            # Check for missing commas
            if _MISSING_COMMA_PATTERN.search(sample):
                needs_missing_commas = True

            # Check for unclosed structures
            open_braces = sample.count("{") - sample.count("}")
            open_brackets = sample.count("[") - sample.count("]")

            if open_braces > 0:
                needs_auto_close_objects = True
            if open_brackets > 0:
                needs_auto_close_arrays = True

            # Check for unclosed strings
            quote_count = 0
            in_escape = False
            for char in sample:
                if in_escape:
                    in_escape = False
                    continue
                if char == "\\":
                    in_escape = True
                    continue
                if char == '"':
                    quote_count += 1

            if quote_count % 2 != 0:
                needs_auto_close_strings = True

            # Check for Python literals
            for pattern in [_PYTHON_TRUE, _PYTHON_FALSE, _PYTHON_NONE]:
                match = pattern.search(sample)
                if match and not _is_in_string(sample, match.start()):
                    needs_python_literals = True
                    break

            # Check for special values
            match = _UNDEFINED_PATTERN.search(sample)
            if match and not _is_in_string(sample, match.start()):
                needs_handle_undefined = True

            match = _NAN_PATTERN.search(sample)
            if match and not _is_in_string(sample, match.start()):
                needs_handle_nan = True

            match = _INFINITY_PATTERN.search(sample)
            if match and not _is_in_string(sample, match.start()):
                needs_handle_infinity = True

            # Check for comments
            for pattern in [_SINGLE_LINE_COMMENT, _BLOCK_COMMENT]:
                match = pattern.search(sample)
                if match and not _is_in_string(sample, match.start()):
                    needs_comments = True
                    break

            # Check for code blocks
            if _CODE_BLOCK_PATTERN.search(sample):
                needs_code_blocks = True

            # Check for triple quotes
            if _TRIPLE_QUOTE_PATTERN.search(sample):
                needs_triple_quotes = True

            # Check for extra text around JSON
            stripped = sample.strip()
            has_prefix = stripped and not stripped.startswith(("{", "[", '"'))
            has_suffix = stripped and not stripped.endswith(("}", "]", '"'))
            has_json = "{" in stripped or "[" in stripped
            if (has_prefix or has_suffix) and has_json:
                needs_text_extraction = True

        return cls(
            allow_unquoted_keys=needs_unquoted_keys,
            allow_single_quotes=needs_single_quotes,
            allow_trailing_commas=needs_trailing_commas,
            allow_missing_commas=needs_missing_commas,
            auto_close_objects=needs_auto_close_objects,
            auto_close_arrays=needs_auto_close_arrays,
            auto_close_strings=needs_auto_close_strings,
            convert_python_literals=needs_python_literals,
            handle_undefined="null" if needs_handle_undefined else "error",
            handle_nan="string" if needs_handle_nan else "error",
            handle_infinity="string" if needs_handle_infinity else "error",
            allow_comments=needs_comments,
            extract_from_code_blocks=needs_code_blocks,
            extract_from_triple_quotes=needs_triple_quotes,
            extract_json_from_text=needs_text_extraction,
        )

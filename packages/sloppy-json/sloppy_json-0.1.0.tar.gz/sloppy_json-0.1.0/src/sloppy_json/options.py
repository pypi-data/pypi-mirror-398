"""Recovery options configuration for sloppy_json."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class RecoveryOptions:
    """Configuration options for JSON recovery.

    Each option controls a specific type of recovery behavior.
    Options default to False/error to maintain strict parsing by default.
    """

    # Quoting options
    allow_unquoted_keys: bool = False
    """Allow object keys without quotes: {name: "value"}"""

    allow_single_quotes: bool = False
    """Allow single-quoted strings: {'key': 'value'}"""

    allow_unquoted_identifiers: bool = False
    """Allow unquoted identifier values (JS identifier rules): {"key": value}

    Only matches valid JS identifiers: [a-zA-Z_$][a-zA-Z0-9_$]*
    Examples: ok, success, not_found, $value
    """

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
    '''Extract JSON from Python triple-quoted strings: """{"a": 1}""" or \'\'\'{"a": 1}\'\'\''''

    # Value normalization
    convert_python_literals: bool = False
    """Convert Python literals to JSON: True/False/None -> true/false/null"""

    handle_undefined: Literal["null", "remove", "error"] = "null"
    """How to handle JavaScript undefined values. Default: null"""

    handle_nan: Literal["null", "string", "error"] = "string"
    """How to handle NaN values. Default: string ("NaN")"""

    handle_infinity: Literal["null", "string", "error"] = "string"
    """How to handle Infinity/-Infinity values. Default: string ("Infinity"/"-Infinity")"""

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

    @classmethod
    def strict(cls) -> "RecoveryOptions":
        """Return options for strict JSON parsing (no recovery)."""
        return cls()

    @classmethod
    def lenient(cls) -> "RecoveryOptions":
        """Return options for lenient parsing (common LLM issues)."""
        return cls(
            allow_single_quotes=True,
            allow_trailing_commas=True,
            convert_python_literals=True,
            extract_from_code_blocks=True,
            extract_from_triple_quotes=True,
            allow_comments=True,
        )

    @classmethod
    def permissive(cls) -> "RecoveryOptions":
        """Return options for maximum recovery (all options enabled)."""
        return cls(
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

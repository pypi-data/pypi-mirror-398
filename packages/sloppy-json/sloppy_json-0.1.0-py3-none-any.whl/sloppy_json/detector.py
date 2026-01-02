"""Auto-detection of required recovery options."""

from __future__ import annotations

import re

from .options import RecoveryOptions

# Detection patterns
UNQUOTED_KEY_PATTERN = re.compile(r"{\s*[a-zA-Z_$][a-zA-Z0-9_$]*\s*:")
SINGLE_QUOTE_PATTERN = re.compile(r"['\[\{,]\s*'|':\s*'|:\s*'")
TRAILING_COMMA_OBJECT = re.compile(r",\s*}")
TRAILING_COMMA_ARRAY = re.compile(r",\s*\]")
MISSING_COMMA_PATTERN = re.compile(r'"\s+"|\d\s+"|\}\s+\{|\]\s+\[|"\s+\{|"\s+\[')
UNCLOSED_OBJECT = re.compile(r"\{[^}]*$")
UNCLOSED_ARRAY = re.compile(r"\[[^\]]*$")
UNCLOSED_STRING = re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*$')
PYTHON_TRUE = re.compile(r"[:\[\s,]True[,\s\]\}]|^True[,\s\]\}]")
PYTHON_FALSE = re.compile(r"[:\[\s,]False[,\s\]\}]|^False[,\s\]\}]")
PYTHON_NONE = re.compile(r"[:\[\s,]None[,\s\]\}]|^None[,\s\]\}]")
UNDEFINED_PATTERN = re.compile(r"[:\[\s,]undefined[,\s\]\}]")
NAN_PATTERN = re.compile(r"[:\[\s,]NaN[,\s\]\}]")
INFINITY_PATTERN = re.compile(r"[:\[\s,]-?Infinity[,\s\]\}]")
SINGLE_LINE_COMMENT = re.compile(r"//")
BLOCK_COMMENT = re.compile(r"/\*")
CODE_BLOCK_PATTERN = re.compile(r"```")
TRIPLE_QUOTE_PATTERN = re.compile(r'"""|\'\'\'')
EXTRA_TEXT_PATTERN = re.compile(r"^[^{\[]+[{\[]|[}\]][^}\]]+$")


def detect_required_options(samples: list[str]) -> RecoveryOptions:
    """Analyze broken JSON samples and detect minimum required options.

    This function examines a list of JSON strings and determines which
    recovery options are needed to parse them successfully.

    Args:
        samples: List of broken JSON strings to analyze.

    Returns:
        RecoveryOptions with minimum required options enabled.
    """
    if not samples:
        return RecoveryOptions()

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
        # Skip empty samples
        if not sample.strip():
            continue

        # Check for unquoted keys
        match = UNQUOTED_KEY_PATTERN.search(sample)
        if match and not _is_in_string(sample, match.start()):
            needs_unquoted_keys = True

        # Check for single quotes
        if SINGLE_QUOTE_PATTERN.search(sample):
            needs_single_quotes = True

        # Check for trailing commas
        if TRAILING_COMMA_OBJECT.search(sample) or TRAILING_COMMA_ARRAY.search(sample):
            needs_trailing_commas = True

        # Check for missing commas
        if MISSING_COMMA_PATTERN.search(sample):
            needs_missing_commas = True

        # Check for unclosed structures
        # Count brackets to detect unclosed
        open_braces = sample.count("{") - sample.count("}")
        open_brackets = sample.count("[") - sample.count("]")

        if open_braces > 0:
            needs_auto_close_objects = True
        if open_brackets > 0:
            needs_auto_close_arrays = True

        # Check for unclosed strings (rough heuristic)
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

        # Check for Python literals (outside of strings)
        if PYTHON_TRUE.search(sample) or PYTHON_FALSE.search(sample) or PYTHON_NONE.search(sample):
            # Verify not in string
            for pattern in [PYTHON_TRUE, PYTHON_FALSE, PYTHON_NONE]:
                match = pattern.search(sample)
                if match and not _is_in_string(sample, match.start()):
                    needs_python_literals = True
                    break

        # Check for special values
        if UNDEFINED_PATTERN.search(sample):
            match = UNDEFINED_PATTERN.search(sample)
            if match and not _is_in_string(sample, match.start()):
                needs_handle_undefined = True

        if NAN_PATTERN.search(sample):
            match = NAN_PATTERN.search(sample)
            if match and not _is_in_string(sample, match.start()):
                needs_handle_nan = True

        if INFINITY_PATTERN.search(sample):
            match = INFINITY_PATTERN.search(sample)
            if match and not _is_in_string(sample, match.start()):
                needs_handle_infinity = True

        # Check for comments
        if SINGLE_LINE_COMMENT.search(sample) or BLOCK_COMMENT.search(sample):
            # Check if // or /* is not inside a string
            for pattern in [SINGLE_LINE_COMMENT, BLOCK_COMMENT]:
                match = pattern.search(sample)
                if match and not _is_in_string(sample, match.start()):
                    needs_comments = True
                    break

        # Check for code blocks
        if CODE_BLOCK_PATTERN.search(sample):
            needs_code_blocks = True

        # Check for triple quotes
        if TRIPLE_QUOTE_PATTERN.search(sample):
            needs_triple_quotes = True

        # Check for extra text around JSON
        stripped = sample.strip()
        has_prefix = stripped and not stripped.startswith(("{", "[", '"'))
        has_suffix = stripped and not stripped.endswith(("}", "]", '"'))
        has_json = "{" in stripped or "[" in stripped
        if (has_prefix or has_suffix) and has_json:
            needs_text_extraction = True

    # Build options with detected requirements
    return RecoveryOptions(
        allow_unquoted_keys=needs_unquoted_keys,
        allow_single_quotes=needs_single_quotes,
        allow_trailing_commas=needs_trailing_commas,
        allow_missing_commas=needs_missing_commas,
        auto_close_objects=needs_auto_close_objects,
        auto_close_arrays=needs_auto_close_arrays,
        auto_close_strings=needs_auto_close_strings,
        convert_python_literals=needs_python_literals,
        handle_undefined="null" if needs_handle_undefined else "error",
        handle_nan="null" if needs_handle_nan else "error",
        handle_infinity="null" if needs_handle_infinity else "error",
        allow_comments=needs_comments,
        extract_from_code_blocks=needs_code_blocks,
        extract_from_triple_quotes=needs_triple_quotes,
        extract_json_from_text=needs_text_extraction,
    )


def _is_in_string(text: str, position: int) -> bool:
    """Check if a position is inside a JSON string.

    This is a rough heuristic - it counts quotes before the position.
    """
    quote_count = 0
    in_escape = False

    for _i, char in enumerate(text[:position]):
        if in_escape:
            in_escape = False
            continue
        if char == "\\":
            in_escape = True
            continue
        if char == '"':
            quote_count += 1

    # If odd number of quotes, we're inside a string
    return quote_count % 2 == 1

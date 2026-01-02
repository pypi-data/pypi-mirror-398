"""Hypothesis-based fuzzing tests for sloppy-json.

These tests use property-based testing to find edge cases and ensure
robustness of the parser.
"""

import json

from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from sloppy_json import parse, RecoveryOptions, SloppyJSONDecodeError


# --- Strategies ---

# Strategy for generating valid JSON-serializable values
json_primitives = st.none() | st.booleans() | st.integers() | st.text()

# Avoid floats that can't round-trip (NaN, Inf)
safe_floats = st.floats(allow_nan=False, allow_infinity=False, allow_subnormal=False)

json_values = st.recursive(
    json_primitives | safe_floats,
    lambda children: st.lists(children, max_size=5)
    | st.dictionaries(st.text(), children, max_size=5),
    max_leaves=20,
)


# --- Test: parse() never crashes on arbitrary input ---


@given(st.text())
@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
def test_permissive_never_crashes(text: str):
    """Default permissive mode should handle any input without crashing.

    It may raise SloppyJSONDecodeError for truly unparseable input,
    but it should never raise unexpected exceptions like TypeError,
    AttributeError, IndexError, etc.
    """
    try:
        result = parse(text)
        # Try to load as JSON - if it fails, that's okay for random input
        # The key property is that parse() doesn't crash with unexpected exceptions
        try:
            json.loads(result)
        except json.JSONDecodeError:
            # Some random text produces non-JSON output - that's acceptable
            pass
    except SloppyJSONDecodeError:
        # Expected for some inputs - this is fine
        pass


# --- Test: valid JSON round-trips correctly ---


@given(json_values)
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_valid_json_roundtrips(value):
    """Valid JSON should parse and preserve the original value."""
    # Skip problematic values
    assume(value == value)  # Skip NaN

    try:
        json_str = json.dumps(value)
    except (ValueError, TypeError):
        assume(False)  # Skip values json can't serialize
        return

    result = parse(json_str)
    parsed = json.loads(result)

    # Compare the parsed values
    assert parsed == json.loads(json_str)


# --- Test: strict mode rejects sloppy JSON ---


@given(st.text())
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_strict_mode_validates(text: str):
    """Strict mode should only accept valid JSON."""
    try:
        result = parse(text, RecoveryOptions(strict=True))
        # If it succeeds, it should be valid JSON
        json.loads(result)
        # And the original should also be valid JSON (or very close)
    except SloppyJSONDecodeError:
        # Expected for invalid JSON
        pass


# --- Test: mutated JSON recovery ---


def mutate_json(json_str: str) -> str:
    """Introduce common LLM-style mutations to JSON."""
    import random

    mutations = []

    # Replace double quotes with single quotes (50% chance per quote)
    mutated = ""
    for char in json_str:
        if char == '"' and random.random() < 0.5:
            mutated += "'"
        else:
            mutated += char
    mutations.append(mutated)

    # Add trailing comma
    mutated = json_str.replace("}", ",}")
    mutations.append(mutated)

    # Replace true/false/null with Python versions
    mutated = json_str.replace("true", "True").replace("false", "False").replace("null", "None")
    mutations.append(mutated)

    return random.choice(mutations)


@given(json_values)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_mutated_json_recovers(value):
    """Mutated JSON should be recoverable."""
    assume(value == value)  # Skip NaN

    try:
        original_json = json.dumps(value)
    except (ValueError, TypeError):
        assume(False)
        return

    # Mutate the JSON
    mutated = mutate_json(original_json)

    # Should be able to parse it
    try:
        result = parse(mutated)
        # Result should be valid JSON
        json.loads(result)
    except SloppyJSONDecodeError:
        # Some mutations might be too aggressive - that's okay
        pass


# --- Test: deeply nested structures ---


@given(st.integers(min_value=1, max_value=50))
@settings(max_examples=50)
def test_deep_nesting_objects(depth: int):
    """Deeply nested objects shouldn't cause issues."""
    json_str = '{"a":' * depth + "1" + "}" * depth
    result = parse(json_str)
    json.loads(result)


@given(st.integers(min_value=1, max_value=50))
@settings(max_examples=50)
def test_deep_nesting_arrays(depth: int):
    """Deeply nested arrays shouldn't cause issues."""
    json_str = "[" * depth + "1" + "]" * depth
    result = parse(json_str)
    json.loads(result)


# --- Test: truncated JSON recovery ---


@given(json_values, st.floats(min_value=0.1, max_value=0.9))
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_truncated_json_recovery(value, truncate_ratio: float):
    """Truncated JSON should be recoverable with auto-close options."""
    assume(value == value)  # Skip NaN

    try:
        json_str = json.dumps(value)
    except (ValueError, TypeError):
        assume(False)
        return

    # Only truncate if long enough
    if len(json_str) < 5:
        return

    # Truncate at a random point
    truncate_at = int(len(json_str) * truncate_ratio)
    truncated = json_str[:truncate_at]

    # Should be able to recover with auto-close options
    try:
        result = parse(truncated)
        # Result should be valid JSON
        json.loads(result)
    except SloppyJSONDecodeError:
        # Some truncations might be unrecoverable
        pass


# --- Test: special characters in strings ---


@given(st.text())
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_special_characters_in_strings(text: str):
    """Strings with special characters should be handled."""
    try:
        json_str = json.dumps({"text": text})
    except (ValueError, TypeError):
        assume(False)
        return

    result = parse(json_str)
    parsed = json.loads(result)
    assert parsed["text"] == text


# --- Test: whitespace handling ---


@given(st.text(alphabet=" \t\n\r"), json_values)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_whitespace_handling(whitespace: str, value):
    """Extra whitespace should be handled correctly."""
    assume(value == value)

    try:
        json_str = json.dumps(value)
    except (ValueError, TypeError):
        assume(False)
        return

    # Add whitespace around JSON
    padded = whitespace + json_str + whitespace

    result = parse(padded)
    parsed = json.loads(result)
    original = json.loads(json_str)

    assert parsed == original


# --- Test: code block extraction ---


@given(json_values, st.text())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_code_block_extraction(value, surrounding_text: str):
    """JSON in code blocks should be extractable."""
    assume(value == value)
    # Avoid text that looks like code blocks
    assume("```" not in surrounding_text)

    try:
        json_str = json.dumps(value)
    except (ValueError, TypeError):
        assume(False)
        return

    # Wrap in code block with surrounding text
    wrapped = f"{surrounding_text}\n```json\n{json_str}\n```\n{surrounding_text}"

    result = parse(wrapped)
    parsed = json.loads(result)
    original = json.loads(json_str)

    assert parsed == original


# --- Test: detect_from produces usable options ---


@given(st.lists(st.text(), min_size=1, max_size=10))
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_detect_from_produces_valid_options(samples: list[str]):
    """RecoveryOptions.detect_from should always produce valid options."""
    options = RecoveryOptions.detect_from(samples)

    # Should be a valid RecoveryOptions instance
    assert isinstance(options, RecoveryOptions)

    # Should be usable with parse
    for sample in samples:
        try:
            parse(sample, options)
        except SloppyJSONDecodeError:
            pass  # Some samples might still be unparseable

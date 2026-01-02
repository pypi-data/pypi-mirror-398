"""Tests for allow_unquoted_keys option."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse


class TestUnquotedKeys:
    """Tests for parsing objects with unquoted keys."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Simple cases
            ('{name: "John"}', '{"name": "John"}'),
            ("{age: 30}", '{"age": 30}'),
            ("{active: true}", '{"active": true}'),
            ("{value: null}", '{"value": null}'),
            ("{pi: 3.14}", '{"pi": 3.14}'),
            ("{negative: -42}", '{"negative": -42}'),
            # Multiple keys
            ('{first: "John", last: "Doe"}', '{"first": "John", "last": "Doe"}'),
            ("{a: 1, b: 2, c: 3}", '{"a": 1, "b": 2, "c": 3}'),
            # Special valid key characters
            ("{_private: 1}", '{"_private": 1}'),
            ("{$special: 2}", '{"$special": 2}'),
            ("{camelCase: 3}", '{"camelCase": 3}'),
            ("{snake_case: 4}", '{"snake_case": 4}'),
            ("{PascalCase: 5}", '{"PascalCase": 5}'),
            ("{key123: 6}", '{"key123": 6}'),
            ("{_123: 7}", '{"_123": 7}'),
            ("{__proto: 8}", '{"__proto": 8}'),
            # Nested objects
            ("{outer: {inner: 1}}", '{"outer": {"inner": 1}}'),
            ("{a: {b: {c: 1}}}", '{"a": {"b": {"c": 1}}}'),
            (
                '{level1: {level2: {level3: {level4: "deep"}}}}',
                '{"level1": {"level2": {"level3": {"level4": "deep"}}}}',
            ),
            # Mixed quoted and unquoted
            ('{unquoted: 1, "quoted": 2}', '{"unquoted": 1, "quoted": 2}'),
            ('{"quoted": 1, unquoted: 2}', '{"quoted": 1, "unquoted": 2}'),
            ('{a: 1, "b": 2, c: 3, "d": 4}', '{"a": 1, "b": 2, "c": 3, "d": 4}'),
            # With arrays
            ("{items: [1, 2, 3]}", '{"items": [1, 2, 3]}'),
            ("{data: [{id: 1}, {id: 2}]}", '{"data": [{"id": 1}, {"id": 2}]}'),
            ("{matrix: [[1, 2], [3, 4]]}", '{"matrix": [[1, 2], [3, 4]]}'),
            # With various value types
            (
                '{str: "hello", num: 42, bool: true, nil: null}',
                '{"str": "hello", "num": 42, "bool": true, "nil": null}',
            ),
            # Whitespace variations
            ('{ name : "value" }', '{"name": "value"}'),
            ('{name:"value"}', '{"name": "value"}'),
            ('{\n  name: "value"\n}', '{"name": "value"}'),
            ('{name\t:\t"value"}', '{"name": "value"}'),
        ],
    )
    def test_valid_unquoted_keys(self, input_json: str, expected: str):
        """Test that unquoted keys are parsed correctly when option is enabled."""
        opts = RecoveryOptions(allow_unquoted_keys=True)
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json",
        [
            '{name: "John"}',
            "{a: 1, b: 2}",
            '{_key: "value"}',
            "{outer: {inner: 1}}",
        ],
    )
    def test_fails_without_option(self, input_json: str):
        """Test that unquoted keys fail without the option enabled."""
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, RecoveryOptions())

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Standard JSON should still work
            ('{"name": "John"}', '{"name": "John"}'),
            ('{"a": 1, "b": 2}', '{"a": 1, "b": 2}'),
            ("{}", "{}"),
            ('{"nested": {"key": "value"}}', '{"nested": {"key": "value"}}'),
        ],
    )
    def test_valid_json_still_works(self, input_json: str, expected: str):
        """Test that valid JSON still works with option enabled."""
        opts = RecoveryOptions(allow_unquoted_keys=True)
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json",
        [
            # Keys starting with numbers (invalid identifier)
            '{123key: "value"}',
            '{1: "value"}',
            # Keys with spaces
            '{key name: "value"}',
            # Keys with special chars (not valid JS identifiers)
            '{key-name: "value"}',
            '{key.name: "value"}',
        ],
    )
    def test_invalid_unquoted_keys(self, input_json: str):
        """Test that invalid unquoted keys still fail."""
        opts = RecoveryOptions(allow_unquoted_keys=True)
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, opts)

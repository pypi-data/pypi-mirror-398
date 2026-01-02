"""Tests for allow_single_quotes option."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse


class TestSingleQuotes:
    """Tests for parsing JSON with single-quoted strings."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Simple cases
            ("{'key': 'value'}", '{"key": "value"}'),
            ("{'num': 123}", '{"num": 123}'),
            ("{'bool': true}", '{"bool": true}'),
            ("{'nil': null}", '{"nil": null}'),
            # Mixed quotes
            ("{'single': \"double\"}", '{"single": "double"}'),
            ("{\"double\": 'single'}", '{"double": "single"}'),
            ("{'a': 'single', \"b\": \"double\"}", '{"a": "single", "b": "double"}'),
            # Nested structures
            ("{'outer': {'inner': 'val'}}", '{"outer": {"inner": "val"}}'),
            ("{'a': {'b': {'c': 'deep'}}}", '{"a": {"b": {"c": "deep"}}}'),
            # Arrays
            ("['a', 'b', 'c']", '["a", "b", "c"]'),
            ("{'arr': ['x', 'y']}", '{"arr": ["x", "y"]}'),
            ("[{'id': 1}, {'id': 2}]", '[{"id": 1}, {"id": 2}]'),
            # Escaped quotes inside single-quoted strings
            ("{'key': 'it\\'s fine'}", '{"key": "it\'s fine"}'),
            ("{'key': 'say \"hello\"'}", '{"key": "say \\"hello\\""}'),
            ("{'key': 'nested \\'quotes\\''}", '{"key": "nested \'quotes\'"}'),
            # Empty strings
            ("{'empty': ''}", '{"empty": ""}'),
            ("['', '', '']", '["", "", ""]'),
            # Whitespace in values
            ("{'key': '  spaces  '}", '{"key": "  spaces  "}'),
            # Only keys single-quoted
            ("{'key': 123}", '{"key": 123}'),
            ("{'key': true}", '{"key": true}'),
            # Complex mixed
            (
                "{'users': [{'name': 'Alice', \"age\": 30}, {'name': 'Bob', \"age\": 25}]}",
                '{"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}',
            ),
        ],
    )
    def test_valid_single_quotes(self, input_json: str, expected: str):
        """Test that single-quoted strings are parsed correctly when option is enabled."""
        opts = RecoveryOptions(allow_single_quotes=True)
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json",
        [
            "{'key': 'value'}",
            "['a', 'b']",
            "{'nested': {'inner': 'val'}}",
        ],
    )
    def test_fails_without_option(self, input_json: str):
        """Test that single-quoted strings fail without the option enabled."""
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, RecoveryOptions())

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Standard JSON should still work
            ('{"key": "value"}', '{"key": "value"}'),
            ('["a", "b", "c"]', '["a", "b", "c"]'),
            ('{"nested": {"inner": "val"}}', '{"nested": {"inner": "val"}}'),
        ],
    )
    def test_valid_json_still_works(self, input_json: str, expected: str):
        """Test that valid JSON still works with option enabled."""
        opts = RecoveryOptions(allow_single_quotes=True)
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json",
        [
            # Unclosed single quotes
            "{'key': 'value}",
            "{'key: 'value'}",
            "['a', 'b]",
        ],
    )
    def test_unclosed_single_quotes_fail(self, input_json: str):
        """Test that unclosed single-quoted strings fail (without auto_close_strings)."""
        opts = RecoveryOptions(allow_single_quotes=True)
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, opts)

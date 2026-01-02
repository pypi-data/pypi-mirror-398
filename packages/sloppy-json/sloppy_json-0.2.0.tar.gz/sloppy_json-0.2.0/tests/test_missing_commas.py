"""Tests for allow_missing_commas option."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse


class TestMissingCommas:
    """Tests for parsing JSON with missing commas."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Object missing commas
            ('{"a": 1 "b": 2}', '{"a": 1, "b": 2}'),
            ('{"a": 1 "b": 2 "c": 3}', '{"a": 1, "b": 2, "c": 3}'),
            # Array missing commas
            ("[1 2 3]", "[1, 2, 3]"),
            ('["a" "b" "c"]', '["a", "b", "c"]'),
            ("[true false null]", "[true, false, null]"),
            # Newline as separator
            ('{"a": 1\n"b": 2}', '{"a": 1, "b": 2}'),
            ("[1\n2\n3]", "[1, 2, 3]"),
            ('{\n"a": 1\n"b": 2\n}', '{"a": 1, "b": 2}'),
            # Mixed - some commas present, some missing
            ('{"a": 1, "b": 2 "c": 3}', '{"a": 1, "b": 2, "c": 3}'),
            ("[1, 2 3, 4]", "[1, 2, 3, 4]"),
            ('{"a": 1 "b": 2, "c": 3 "d": 4}', '{"a": 1, "b": 2, "c": 3, "d": 4}'),
            # Nested structures
            ('{"a": {"x": 1 "y": 2} "b": 3}', '{"a": {"x": 1, "y": 2}, "b": 3}'),
            ("[[1 2] [3 4]]", "[[1, 2], [3, 4]]"),
            ('[{"a": 1} {"b": 2}]', '[{"a": 1}, {"b": 2}]'),
            # String values
            ('{"a": "hello" "b": "world"}', '{"a": "hello", "b": "world"}'),
            ('["hello" "world"]', '["hello", "world"]'),
            # Mixed types
            (
                '{"str": "x" "num": 1 "bool": true "nil": null}',
                '{"str": "x", "num": 1, "bool": true, "nil": null}',
            ),
            ('[1 "two" true null]', '[1, "two", true, null]'),
            # Multiple spaces
            ('{"a": 1   "b": 2}', '{"a": 1, "b": 2}'),
            ("[1   2   3]", "[1, 2, 3]"),
            # Tab separated
            ('{"a": 1\t"b": 2}', '{"a": 1, "b": 2}'),
            ("[1\t2\t3]", "[1, 2, 3]"),
            # Objects in array without commas
            (
                '[{"id": 1, "name": "a"} {"id": 2, "name": "b"}]',
                '[{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]',
            ),
        ],
    )
    def test_valid_missing_commas(self, input_json: str, expected: str):
        """Test that missing commas are handled correctly when option is enabled."""
        opts = RecoveryOptions(allow_missing_commas=True)
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json",
        [
            '{"a": 1 "b": 2}',
            "[1 2 3]",
            '{"a": "x" "b": "y"}',
        ],
    )
    def test_fails_without_option(self, input_json: str):
        """Test that missing commas fail without the option enabled."""
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, RecoveryOptions())

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Standard JSON should still work
            ('{"a": 1, "b": 2}', '{"a": 1, "b": 2}'),
            ("[1, 2, 3]", "[1, 2, 3]"),
            ('{"nested": {"a": 1, "b": 2}}', '{"nested": {"a": 1, "b": 2}}'),
        ],
    )
    def test_valid_json_still_works(self, input_json: str, expected: str):
        """Test that valid JSON still works with option enabled."""
        opts = RecoveryOptions(allow_missing_commas=True)
        assert parse(input_json, opts) == expected

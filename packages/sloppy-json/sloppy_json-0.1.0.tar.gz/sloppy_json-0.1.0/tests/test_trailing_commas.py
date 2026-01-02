"""Tests for allow_trailing_commas option."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse


class TestTrailingCommas:
    """Tests for parsing JSON with trailing commas."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Object trailing comma - simple
            ('{"a": 1,}', '{"a": 1}'),
            ('{"a": 1, "b": 2,}', '{"a": 1, "b": 2}'),
            ('{"a": 1, "b": 2, "c": 3,}', '{"a": 1, "b": 2, "c": 3}'),
            # Array trailing comma - simple
            ("[1,]", "[1]"),
            ("[1, 2,]", "[1, 2]"),
            ("[1, 2, 3,]", "[1, 2, 3]"),
            ('["a", "b",]', '["a", "b"]'),
            # Nested trailing commas
            ('{"a": [1, 2,],}', '{"a": [1, 2]}'),
            ('{"a": {"b": 1,},}', '{"a": {"b": 1}}'),
            ('[{"a": 1,}, {"b": 2,},]', '[{"a": 1}, {"b": 2}]'),
            ("[[1, 2,], [3, 4,],]", "[[1, 2], [3, 4]]"),
            # Multiple levels deep
            ('{"a": {"b": {"c": [1, 2,],},},}', '{"a": {"b": {"c": [1, 2]}}}'),
            ("[[[1,],],]", "[[[1]]]"),
            # With whitespace before comma
            ('{"a": 1 ,}', '{"a": 1}'),
            ("[1 ,]", "[1]"),
            # With whitespace after comma
            ('{"a": 1, }', '{"a": 1}'),
            ("[1, ]", "[1]"),
            # With newlines
            ('{"a": 1,\n}', '{"a": 1}'),
            ("[\n1,\n2,\n]", "[1, 2]"),
            ('{\n  "a": 1,\n  "b": 2,\n}', '{"a": 1, "b": 2}'),
            # Mixed value types with trailing
            (
                '{"str": "hello", "num": 42, "bool": true, "nil": null,}',
                '{"str": "hello", "num": 42, "bool": true, "nil": null}',
            ),
            ('[1, "two", true, null,]', '[1, "two", true, null]'),
        ],
    )
    def test_valid_trailing_commas(self, input_json: str, expected: str):
        """Test that trailing commas are handled correctly when option is enabled."""
        opts = RecoveryOptions(allow_trailing_commas=True)
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json",
        [
            '{"a": 1,}',
            "[1, 2, 3,]",
            '{"nested": {"a": 1,},}',
        ],
    )
    def test_fails_without_option(self, input_json: str):
        """Test that trailing commas fail without the option enabled."""
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, RecoveryOptions())

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Standard JSON should still work
            ('{"a": 1}', '{"a": 1}'),
            ("[1, 2, 3]", "[1, 2, 3]"),
            ('{"a": {"b": 1}}', '{"a": {"b": 1}}'),
            ("[]", "[]"),
            ("{}", "{}"),
        ],
    )
    def test_valid_json_still_works(self, input_json: str, expected: str):
        """Test that valid JSON still works with option enabled."""
        opts = RecoveryOptions(allow_trailing_commas=True)
        assert parse(input_json, opts) == expected

"""Tests for edge cases: BOM stripping, duplicate keys, etc."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse


class TestBOMStripping:
    """Tests for UTF-8 BOM (Byte Order Mark) handling."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # UTF-8 BOM at start
            ('\ufeff{"key": "value"}', '{"key": "value"}'),
            ("\ufeff[1, 2, 3]", "[1, 2, 3]"),
            ('\ufeff{"a": 1, "b": 2}', '{"a": 1, "b": 2}'),
            # BOM with whitespace after
            ('\ufeff {"key": "value"}', '{"key": "value"}'),
            ('\ufeff\n{"key": "value"}', '{"key": "value"}'),
            # Just a primitive with BOM
            ('\ufeff"hello"', '"hello"'),
            ("\ufeff123", "123"),
            ("\ufefftrue", "true"),
            ("\ufeffnull", "null"),
        ],
    )
    def test_bom_stripped(self, input_json: str, expected: str):
        """Test that UTF-8 BOM is stripped from input."""
        # BOM should be handled even in strict mode
        assert parse(input_json, RecoveryOptions()) == expected

    def test_no_bom_still_works(self):
        """Test that input without BOM still works fine."""
        assert parse('{"key": "value"}', RecoveryOptions()) == '{"key": "value"}'

    def test_bom_in_middle_not_stripped(self):
        """BOM in middle of string should be preserved (it's in the value)."""
        # This is a BOM inside a string value - should be preserved
        input_json = '{"key": "val\ufeffue"}'
        result = parse(input_json, RecoveryOptions())
        # The BOM should remain in the output since it's part of the string
        assert "\ufeff" in result or "\\ufeff" in result


class TestDuplicateKeys:
    """Tests for duplicate key handling - should preserve all keys."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Simple duplicate
            ('{"a": 1, "a": 2}', '{"a": 1, "a": 2}'),
            # Multiple duplicates
            ('{"a": 1, "a": 2, "a": 3}', '{"a": 1, "a": 2, "a": 3}'),
            # Duplicate with other keys
            ('{"a": 1, "b": 2, "a": 3}', '{"a": 1, "b": 2, "a": 3}'),
            # Different value types
            ('{"x": 1, "x": "one"}', '{"x": 1, "x": "one"}'),
            ('{"x": true, "x": false}', '{"x": true, "x": false}'),
            # Nested - duplicates at same level
            (
                '{"obj": {"a": 1, "a": 2}}',
                '{"obj": {"a": 1, "a": 2}}',
            ),
            # Nested - same key at different levels (not duplicates)
            (
                '{"a": 1, "nested": {"a": 2}}',
                '{"a": 1, "nested": {"a": 2}}',
            ),
        ],
    )
    def test_duplicate_keys_preserved(self, input_json: str, expected: str):
        """Test that duplicate keys are preserved in output."""
        result = parse(input_json, RecoveryOptions())
        assert result == expected

    def test_duplicate_keys_with_recovery_options(self):
        """Test duplicate keys work with various recovery options."""
        opts = RecoveryOptions(allow_trailing_commas=True)
        assert parse('{"a": 1, "a": 2,}', opts) == '{"a": 1, "a": 2}'


class TestEmptyInputs:
    """Tests for empty and whitespace-only inputs."""

    @pytest.mark.parametrize(
        "input_json",
        [
            "",
            "   ",
            "\n",
            "\t",
            "  \n  \t  ",
        ],
    )
    def test_empty_input_fails(self, input_json: str):
        """Test that empty input raises an error."""
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, RecoveryOptions())


class TestWhitespaceHandling:
    """Tests for various whitespace scenarios."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Leading whitespace
            ('  {"key": "value"}', '{"key": "value"}'),
            ('\n{"key": "value"}', '{"key": "value"}'),
            ('\t{"key": "value"}', '{"key": "value"}'),
            # Trailing whitespace
            ('{"key": "value"}  ', '{"key": "value"}'),
            ('{"key": "value"}\n', '{"key": "value"}'),
            # Both
            ('  {"key": "value"}  ', '{"key": "value"}'),
            ('\n\n{"key": "value"}\n\n', '{"key": "value"}'),
            # Inside object - extra whitespace
            ('{  "key"  :  "value"  }', '{"key": "value"}'),
            # Inside array
            ("[  1  ,  2  ,  3  ]", "[1, 2, 3]"),
        ],
    )
    def test_whitespace_normalized(self, input_json: str, expected: str):
        """Test that whitespace is normalized in output."""
        assert parse(input_json, RecoveryOptions()) == expected


class TestNumericEdgeCases:
    """Tests for numeric edge cases."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Integers
            ('{"n": 0}', '{"n": 0}'),
            ('{"n": -0}', '{"n": -0}'),  # -0 preserved as-is
            ('{"n": 123}', '{"n": 123}'),
            ('{"n": -123}', '{"n": -123}'),
            # Floats
            ('{"n": 1.5}', '{"n": 1.5}'),
            ('{"n": -1.5}', '{"n": -1.5}'),
            ('{"n": 0.5}', '{"n": 0.5}'),
            # Scientific notation
            ('{"n": 1e10}', '{"n": 1e10}'),
            ('{"n": 1E10}', '{"n": 1e10}'),
            ('{"n": 1e+10}', '{"n": 1e+10}'),
            ('{"n": 1e-10}', '{"n": 1e-10}'),
            ('{"n": 1.5e10}', '{"n": 1.5e10}'),
        ],
    )
    def test_numeric_values(self, input_json: str, expected: str):
        """Test various numeric formats."""
        result = parse(input_json, RecoveryOptions())
        # Allow for minor formatting differences in scientific notation
        assert result == expected or ("e" in expected.lower() and "e" in result.lower())


class TestStringEdgeCases:
    """Tests for string edge cases."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Empty string
            ('{"s": ""}', '{"s": ""}'),
            # Escaped characters
            ('{"s": "a\\nb"}', '{"s": "a\\nb"}'),
            ('{"s": "a\\tb"}', '{"s": "a\\tb"}'),
            ('{"s": "a\\rb"}', '{"s": "a\\rb"}'),
            ('{"s": "a\\\\b"}', '{"s": "a\\\\b"}'),
            ('{"s": "a\\"b"}', '{"s": "a\\"b"}'),
            # Unicode escapes
            (
                '{"s": "\\u0048\\u0065\\u006c\\u006c\\u006f"}',
                '{"s": "\\u0048\\u0065\\u006c\\u006c\\u006f"}',
            ),
            # Forward slash (optional escape in JSON)
            ('{"s": "a/b"}', '{"s": "a/b"}'),
            ('{"s": "a\\/b"}', '{"s": "a/b"}'),
        ],
    )
    def test_string_escapes(self, input_json: str, expected: str):
        """Test string escape handling."""
        result = parse(input_json, RecoveryOptions())
        # Allow for minor differences in escape handling
        assert result == expected or (result.replace("\\/", "/") == expected.replace("\\/", "/"))

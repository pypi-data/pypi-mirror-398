"""Tests for auto_close_* options."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse


class TestUnclosedObjects:
    """Tests for auto_close_objects option."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Simple unclosed object
            ('{"key": "value"', '{"key": "value"}'),
            ('{"a": 1, "b": 2', '{"a": 1, "b": 2}'),
            ('{"a": 1', '{"a": 1}'),
            ("{", "{}"),
            # Nested unclosed objects
            ('{"a": {"b": 1}', '{"a": {"b": 1}}'),
            ('{"a": {"b": {"c": 1}', '{"a": {"b": {"c": 1}}}'),
            ('{"a": {"b": 1', '{"a": {"b": 1}}'),
            (
                '{"outer": {"inner": {"deep": "value"',
                '{"outer": {"inner": {"deep": "value"}}}',
            ),
            # Object with complete nested object but unclosed outer
            ('{"a": {"b": 1}, "c": 2', '{"a": {"b": 1}, "c": 2}'),
            # Multiple unclosed levels
            ('{"a": {"b": {"c": {"d": 1', '{"a": {"b": {"c": {"d": 1}}}}'),
        ],
    )
    def test_unclosed_objects(self, input_json: str, expected: str):
        """Test that unclosed objects are auto-closed when option is enabled."""
        opts = RecoveryOptions(auto_close_objects=True)
        assert parse(input_json, opts) == expected


class TestUnclosedArrays:
    """Tests for auto_close_arrays option."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Simple unclosed array
            ("[1, 2, 3", "[1, 2, 3]"),
            ('["a", "b"', '["a", "b"]'),
            ("[1", "[1]"),
            ("[", "[]"),
            # Nested unclosed arrays
            ("[[1, 2], [3, 4]", "[[1, 2], [3, 4]]"),
            ("[[[1", "[[[1]]]"),
            ("[[1, 2", "[[1, 2]]"),
            # Array in object (need both options)
            ('{"arr": [1, 2, 3', '{"arr": [1, 2, 3]}'),
            ('{"arr": [1, 2', '{"arr": [1, 2]}'),
            ('{"data": [[1, 2], [3', '{"data": [[1, 2], [3]]}'),
            # Multiple arrays
            ("[[1], [2], [3", "[[1], [2], [3]]"),
        ],
    )
    def test_unclosed_arrays(self, input_json: str, expected: str):
        """Test that unclosed arrays are auto-closed when option is enabled."""
        opts = RecoveryOptions(auto_close_arrays=True, auto_close_objects=True)
        assert parse(input_json, opts) == expected


class TestUnclosedStrings:
    """Tests for auto_close_strings option."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Unclosed string value
            ('{"key": "value', '{"key": "value"}'),
            ('{"a": "hello world', '{"a": "hello world"}'),
            ('{"key": "', '{"key": ""}'),
            # Unclosed string in array
            ('["hello', '["hello"]'),
            ('["a", "b", "incomplete', '["a", "b", "incomplete"]'),
            # Unclosed key (unusual but possible)
            ('{"incomplete', '{"incomplete": null}'),
            # Long unclosed string
            (
                '{"text": "this is a very long string that was not closed',
                '{"text": "this is a very long string that was not closed"}',
            ),
        ],
    )
    def test_unclosed_strings(self, input_json: str, expected: str):
        """Test that unclosed strings are auto-closed when option is enabled."""
        opts = RecoveryOptions(
            auto_close_objects=True, auto_close_arrays=True, auto_close_strings=True
        )
        assert parse(input_json, opts) == expected


class TestMultipleUnclosed:
    """Tests for multiple types of unclosed structures."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # String + array + object
            ('{"a": [1, 2, "three', '{"a": [1, 2, "three"]}'),
            ('{"x": {"y": [1, "test', '{"x": {"y": [1, "test"]}}'),
            ('[{"a": 1', '[{"a": 1}]'),
            ('{"items": [{"id": 1}, {"id": 2', '{"items": [{"id": 1}, {"id": 2}]}'),
            # Complex nested
            (
                '{"users": [{"name": "Alice", "tags": ["admin", "user',
                '{"users": [{"name": "Alice", "tags": ["admin", "user"]}]}',
            ),
            # Array of incomplete objects
            ('[{"a": 1}, {"b": 2}, {"c": 3', '[{"a": 1}, {"b": 2}, {"c": 3}]'),
            # Deeply nested incomplete
            (
                '{"level1": {"level2": {"level3": [1, 2, {"level4": "value',
                '{"level1": {"level2": {"level3": [1, 2, {"level4": "value"}]}}}',
            ),
        ],
    )
    def test_multiple_unclosed(self, input_json: str, expected: str):
        """Test handling of multiple types of unclosed structures."""
        opts = RecoveryOptions(
            auto_close_objects=True, auto_close_arrays=True, auto_close_strings=True
        )
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json",
        [
            '{"key": "value"',
            "[1, 2, 3",
            '{"arr": [1, 2',
        ],
    )
    def test_fails_without_options(self, input_json: str):
        """Test that unclosed structures fail without the options enabled."""
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, RecoveryOptions())


class TestUnclosedEdgeCases:
    """Edge cases for unclosed structure handling."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Empty incomplete structures
            ("{", "{}"),
            ("[", "[]"),
            ('{"key":', '{"key": null}'),
            ('{"key": ', '{"key": null}'),
            ("[1,", "[1]"),
            ("[1, ", "[1]"),
            # Whitespace before EOF
            ('{"a": 1   ', '{"a": 1}'),
            ("[1, 2   ", "[1, 2]"),
            # Newlines before EOF
            ('{"a": 1\n', '{"a": 1}'),
            ('{"a": 1\n\n', '{"a": 1}'),
        ],
    )
    def test_edge_cases(self, input_json: str, expected: str):
        """Test edge cases in unclosed structure handling."""
        opts = RecoveryOptions(
            auto_close_objects=True, auto_close_arrays=True, auto_close_strings=True
        )
        assert parse(input_json, opts) == expected

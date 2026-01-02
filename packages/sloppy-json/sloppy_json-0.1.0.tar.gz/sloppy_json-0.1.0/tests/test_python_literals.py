"""Tests for convert_python_literals option."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse


class TestPythonLiterals:
    """Tests for converting Python literals to JSON equivalents."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Boolean True -> true
            ('{"flag": True}', '{"flag": true}'),
            ('{"a": True, "b": True}', '{"a": true, "b": true}'),
            ("[True]", "[true]"),
            ("[True, True, True]", "[true, true, true]"),
            # Boolean False -> false
            ('{"flag": False}', '{"flag": false}'),
            ('{"a": False, "b": False}', '{"a": false, "b": false}'),
            ("[False]", "[false]"),
            ("[False, False]", "[false, false]"),
            # None -> null
            ('{"value": None}', '{"value": null}'),
            ('{"a": None, "b": None}', '{"a": null, "b": null}'),
            ("[None]", "[null]"),
            ("[None, None]", "[null, null]"),
            # Mixed Python literals
            (
                '{"a": True, "b": False, "c": None}',
                '{"a": true, "b": false, "c": null}',
            ),
            ("[True, False, None]", "[true, false, null]"),
            # In arrays
            ('{"arr": [True, False, None]}', '{"arr": [true, false, null]}'),
            ("[[True], [False], [None]]", "[[true], [false], [null]]"),
            # Mixed with regular JSON values
            ('{"py": True, "js": true}', '{"py": true, "js": true}'),
            ('{"py": False, "js": false}', '{"py": false, "js": false}'),
            ('{"py": None, "js": null}', '{"py": null, "js": null}'),
            ("[True, true, False, false]", "[true, true, false, false]"),
            # Nested structures
            ('{"outer": {"inner": True}}', '{"outer": {"inner": true}}'),
            ('{"a": {"b": {"c": None}}}', '{"a": {"b": {"c": null}}}'),
            ('[{"flag": True}, {"flag": False}]', '[{"flag": true}, {"flag": false}]'),
            # With other value types
            (
                '{"str": "hello", "num": 42, "bool": True, "nil": None}',
                '{"str": "hello", "num": 42, "bool": true, "nil": null}',
            ),
            ('[1, "two", True, None]', '[1, "two", true, null]'),
            # Complex structure
            (
                '{"users": [{"name": "Alice", "active": True, "score": None}, '
                '{"name": "Bob", "active": False, "score": 100}]}',
                '{"users": [{"name": "Alice", "active": true, "score": null}, '
                '{"name": "Bob", "active": false, "score": 100}]}',
            ),
        ],
    )
    def test_python_literals(self, input_json: str, expected: str):
        """Test that Python literals are converted correctly."""
        opts = RecoveryOptions(convert_python_literals=True)
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json",
        [
            '{"flag": True}',
            '{"value": None}',
            "[True, False]",
        ],
    )
    def test_fails_without_option(self, input_json: str):
        """Test that Python literals fail without the option enabled."""
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, RecoveryOptions())

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Standard JSON should still work
            ('{"flag": true}', '{"flag": true}'),
            ('{"flag": false}', '{"flag": false}'),
            ('{"value": null}', '{"value": null}'),
            ("[true, false, null]", "[true, false, null]"),
        ],
    )
    def test_valid_json_still_works(self, input_json: str, expected: str):
        """Test that valid JSON still works with option enabled."""
        opts = RecoveryOptions(convert_python_literals=True)
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Ensure case sensitivity - only exact Python case should match
            ('{"a": True}', '{"a": true}'),
            ('{"a": False}', '{"a": false}'),
            ('{"a": None}', '{"a": null}'),
        ],
    )
    def test_case_sensitivity(self, input_json: str, expected: str):
        """Test that only exact Python case is converted."""
        opts = RecoveryOptions(convert_python_literals=True)
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json",
        [
            # These should fail - wrong case
            '{"a": TRUE}',
            '{"a": FALSE}',
            '{"a": NONE}',
            '{"a": true_}',
            '{"a": _True}',
        ],
    )
    def test_wrong_case_fails(self, input_json: str):
        """Test that wrong case literals fail."""
        opts = RecoveryOptions(convert_python_literals=True)
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, opts)

    def test_true_false_none_in_strings_preserved(self):
        """Ensure True/False/None inside strings are not converted."""
        opts = RecoveryOptions(convert_python_literals=True)
        assert parse('{"key": "True"}', opts) == '{"key": "True"}'
        assert parse('{"key": "False"}', opts) == '{"key": "False"}'
        assert parse('{"key": "None"}', opts) == '{"key": "None"}'

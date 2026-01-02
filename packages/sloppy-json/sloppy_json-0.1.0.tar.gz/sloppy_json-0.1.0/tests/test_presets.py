"""Tests for preset parsing modes."""

import pytest

from sloppy_json import (
    RecoveryOptions,
    SloppyJSONDecodeError,
    parse,
    parse_lenient,
    parse_permissive,
    parse_strict,
)


class TestStrictMode:
    """Tests for strict parsing mode."""

    @pytest.mark.parametrize(
        "input_json",
        [
            '{name: "value"}',  # unquoted key
            "{'key': 'value'}",  # single quotes
            '{"a": 1,}',  # trailing comma
            '{"a": True}',  # Python literal
            '{"a": 1 "b": 2}',  # missing comma
            '{"key": "value"',  # unclosed
            '// comment\n{"a": 1}',  # comment
        ],
    )
    def test_strict_rejects_sloppy(self, input_json: str):
        """Strict mode should reject non-standard JSON."""
        with pytest.raises(SloppyJSONDecodeError):
            parse_strict(input_json)

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            ('{"key": "value"}', '{"key": "value"}'),
            ("[1, 2, 3]", "[1, 2, 3]"),
            ('{"a": true, "b": null}', '{"a": true, "b": null}'),
            ('{"nested": {"key": [1, 2]}}', '{"nested": {"key": [1, 2]}}'),
            ("[]", "[]"),
            ("{}", "{}"),
            ("null", "null"),
            ("true", "true"),
            ("false", "false"),
            ("123", "123"),
            ('"string"', '"string"'),
            ('{"a": -123.456e+10}', '{"a": -123.456e+10}'),
        ],
    )
    def test_strict_accepts_valid(self, input_json: str, expected: str):
        """Strict mode should accept valid JSON."""
        assert parse_strict(input_json) == expected

    def test_strict_is_default(self):
        """Strict mode should be equivalent to default RecoveryOptions."""
        valid_json = '{"key": "value"}'
        assert parse(valid_json, RecoveryOptions()) == parse_strict(valid_json)

        invalid_json = '{key: "value"}'
        with pytest.raises(SloppyJSONDecodeError):
            parse(invalid_json, RecoveryOptions())


class TestLenientMode:
    """Tests for lenient parsing mode."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Trailing commas
            ('{"a": 1,}', '{"a": 1}'),
            ("[1, 2, 3,]", "[1, 2, 3]"),
            # Single quotes
            ("{'key': 'value'}", '{"key": "value"}'),
            ("['a', 'b']", '["a", "b"]'),
            # Python literals
            ('{"a": True}', '{"a": true}'),
            ('{"a": False}', '{"a": false}'),
            ('{"a": None}', '{"a": null}'),
            # Code blocks
            ('```json\n{"a": 1}\n```', '{"a": 1}'),
            ("```\n[1, 2, 3]\n```", "[1, 2, 3]"),
            # Comments
            ('{"a": 1} // comment', '{"a": 1}'),
            ('/* comment */ {"a": 1}', '{"a": 1}'),
            # Combinations
            ("{'a': True,}", '{"a": true}'),
            ('```json\n{"flag": True,}\n```', '{"flag": true}'),
        ],
    )
    def test_lenient_common_issues(self, input_json: str, expected: str):
        """Lenient mode should handle common LLM issues."""
        assert parse_lenient(input_json) == expected

    @pytest.mark.parametrize(
        "input_json",
        [
            '{key: "value"}',  # unquoted key - not in lenient
            '{"a": 1 "b": 2}',  # missing comma - not in lenient
            '{"key": "value"',  # unclosed - not in lenient
        ],
    )
    def test_lenient_still_rejects_some(self, input_json: str):
        """Lenient mode should still reject some issues."""
        with pytest.raises(SloppyJSONDecodeError):
            parse_lenient(input_json)


class TestPermissiveMode:
    """Tests for permissive parsing mode."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # All the things lenient handles
            ('{"a": 1,}', '{"a": 1}'),
            ("{'key': 'value'}", '{"key": "value"}'),
            ('{"a": True}', '{"a": true}'),
            ('```json\n{"a": 1}\n```', '{"a": 1}'),
            ('{"a": 1} // comment', '{"a": 1}'),
            # Plus more aggressive recovery
            ('{key: "value"}', '{"key": "value"}'),
            ('{"a": 1 "b": 2}', '{"a": 1, "b": 2}'),
            ('{"key": "value"', '{"key": "value"}'),
            ("[1, 2, 3", "[1, 2, 3]"),
            ('{"key": "unclosed', '{"key": "unclosed"}'),
            # Special values
            ('{"a": undefined}', '{"a": null}'),
            ('{"a": NaN}', '{"a": "NaN"}'),
            ('{"a": Infinity}', '{"a": "Infinity"}'),
            # Text extraction
            ('Here is the JSON: {"a": 1}', '{"a": 1}'),
            ('{"a": 1} Hope this helps!', '{"a": 1}'),
            # Unescaped newlines
            ('{"text": "line1\nline2"}', '{"text": "line1\\nline2"}'),
        ],
    )
    def test_permissive_everything(self, input_json: str, expected: str):
        """Permissive mode should handle all recovery options."""
        assert parse_permissive(input_json) == expected

    def test_permissive_complex_case(self):
        """Test a complex case with multiple issues."""
        input_json = """Here is the JSON:
```json
{
  name: 'test',  // a comment
  values: [1, 2, 3,],
  flag: True,
  data: None,
"""
        result = parse_permissive(input_json)
        # Expected: properly formed JSON string
        assert '"name": "test"' in result
        assert '"flag": true' in result
        assert '"data": null' in result


class TestPresetOptions:
    """Tests for preset option configurations."""

    def test_strict_options(self):
        """Test that strict preset has all options disabled."""
        opts = RecoveryOptions.strict()
        assert opts.allow_unquoted_keys == False
        assert opts.allow_single_quotes == False
        assert opts.allow_trailing_commas == False
        assert opts.auto_close_objects == False
        # Note: handle_undefined/nan/infinity now default to recovery modes
        assert opts.handle_undefined == "null"
        assert opts.handle_nan == "string"
        assert opts.handle_infinity == "string"

    def test_lenient_options(self):
        """Test that lenient preset has expected options enabled."""
        opts = RecoveryOptions.lenient()
        assert opts.allow_single_quotes == True
        assert opts.allow_trailing_commas == True
        assert opts.convert_python_literals == True
        assert opts.extract_from_code_blocks == True
        assert opts.allow_comments == True
        # But not these
        assert opts.allow_unquoted_keys == False
        assert opts.allow_missing_commas == False
        assert opts.auto_close_objects == False

    def test_permissive_options(self):
        """Test that permissive preset has all options enabled."""
        opts = RecoveryOptions.permissive()
        assert opts.allow_unquoted_keys == True
        assert opts.allow_single_quotes == True
        assert opts.allow_trailing_commas == True
        assert opts.allow_missing_commas == True
        assert opts.auto_close_objects == True
        assert opts.auto_close_arrays == True
        assert opts.auto_close_strings == True
        assert opts.extract_json_from_text == True
        assert opts.extract_from_code_blocks == True
        assert opts.convert_python_literals == True
        assert opts.handle_undefined == "null"
        assert opts.handle_nan == "string"
        assert opts.handle_infinity == "string"
        assert opts.allow_comments == True
        assert opts.escape_newlines_in_strings == True

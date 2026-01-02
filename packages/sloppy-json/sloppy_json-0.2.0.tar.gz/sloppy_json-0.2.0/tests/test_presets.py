"""Tests for parsing modes: strict, default (permissive), and custom options."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse


class TestStrictMode:
    """Tests for strict parsing mode (RecoveryOptions(strict=True))."""

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
            parse(input_json, RecoveryOptions(strict=True))

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
        assert parse(input_json, RecoveryOptions(strict=True)) == expected

    def test_strict_with_empty_options(self):
        """RecoveryOptions() (no flags) should also reject non-standard JSON."""
        invalid_json = '{key: "value"}'
        with pytest.raises(SloppyJSONDecodeError):
            parse(invalid_json, RecoveryOptions())


class TestDefaultPermissiveMode:
    """Tests for default permissive parsing mode (no options = permissive)."""

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
            # Unquoted keys
            ('{key: "value"}', '{"key": "value"}'),
            # Missing commas
            ('{"a": 1 "b": 2}', '{"a": 1, "b": 2}'),
            # Unclosed structures
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
            # Combinations
            ("{'a': True,}", '{"a": true}'),
            ('```json\n{"flag": True,}\n```', '{"flag": true}'),
        ],
    )
    def test_permissive_handles_everything(self, input_json: str, expected: str):
        """Default permissive mode should handle all recovery options."""
        assert parse(input_json) == expected

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
        result = parse(input_json)
        assert '"name": "test"' in result
        assert '"flag": true' in result
        assert '"data": null' in result


class TestCustomOptions:
    """Tests for custom option configurations."""

    def test_only_single_quotes(self):
        """Test enabling only single quotes."""
        opts = RecoveryOptions(allow_single_quotes=True)
        assert parse("{'key': 'value'}", opts) == '{"key": "value"}'
        # But trailing comma should fail
        with pytest.raises(SloppyJSONDecodeError):
            parse("{'key': 'value',}", opts)

    def test_only_trailing_commas(self):
        """Test enabling only trailing commas."""
        opts = RecoveryOptions(allow_trailing_commas=True)
        assert parse('{"a": 1,}', opts) == '{"a": 1}'
        # But single quotes should fail
        with pytest.raises(SloppyJSONDecodeError):
            parse("{'key': 'value'}", opts)

    def test_combination_options(self):
        """Test combining specific options."""
        opts = RecoveryOptions(
            allow_single_quotes=True,
            allow_trailing_commas=True,
            convert_python_literals=True,
        )
        assert parse("{'flag': True,}", opts) == '{"flag": true}'
        # But unquoted keys should fail
        with pytest.raises(SloppyJSONDecodeError):
            parse("{key: 'value'}", opts)


class TestRecoveryOptionsRepr:
    """Tests for RecoveryOptions __repr__ output."""

    def test_empty_options_repr(self):
        """Empty options should have clean repr."""
        opts = RecoveryOptions()
        assert repr(opts) == "RecoveryOptions()"

    def test_strict_repr(self):
        """Strict options should show strict=True."""
        opts = RecoveryOptions(strict=True)
        assert repr(opts) == "RecoveryOptions(strict=True)"

    def test_single_option_repr(self):
        """Single option should show cleanly."""
        opts = RecoveryOptions(allow_single_quotes=True)
        assert repr(opts) == "RecoveryOptions(allow_single_quotes=True)"

    def test_multiple_options_repr(self):
        """Multiple options should show cleanly."""
        opts = RecoveryOptions(allow_single_quotes=True, allow_trailing_commas=True)
        assert "allow_single_quotes=True" in repr(opts)
        assert "allow_trailing_commas=True" in repr(opts)

    def test_detect_from_repr(self):
        """Detected options should have nice repr."""
        samples = ["{'key': 'value',}"]
        opts = RecoveryOptions.detect_from(samples)
        r = repr(opts)
        assert "allow_single_quotes=True" in r
        assert "allow_trailing_commas=True" in r


class TestDetectFrom:
    """Tests for RecoveryOptions.detect_from()."""

    def test_detect_single_quotes(self):
        """Should detect single quotes."""
        opts = RecoveryOptions.detect_from(["{'key': 'value'}"])
        assert opts.allow_single_quotes is True

    def test_detect_trailing_commas(self):
        """Should detect trailing commas."""
        opts = RecoveryOptions.detect_from(['{"a": 1,}'])
        assert opts.allow_trailing_commas is True

    def test_detect_python_literals(self):
        """Should detect Python literals."""
        opts = RecoveryOptions.detect_from(['{"flag": True}'])
        assert opts.convert_python_literals is True

    def test_detect_unquoted_keys(self):
        """Should detect unquoted keys."""
        opts = RecoveryOptions.detect_from(['{key: "value"}'])
        assert opts.allow_unquoted_keys is True

    def test_detect_multiple(self):
        """Should detect multiple issues."""
        samples = ["{'key': 'value',}", "{name: True}"]
        opts = RecoveryOptions.detect_from(samples)
        assert opts.allow_single_quotes is True
        assert opts.allow_trailing_commas is True
        assert opts.allow_unquoted_keys is True
        assert opts.convert_python_literals is True

    def test_detect_empty_samples(self):
        """Empty samples should return default options."""
        opts = RecoveryOptions.detect_from([])
        assert opts.allow_single_quotes is False
        assert opts.allow_trailing_commas is False

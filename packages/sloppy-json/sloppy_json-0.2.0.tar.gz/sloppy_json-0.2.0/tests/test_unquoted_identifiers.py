"""Tests for allow_unquoted_identifiers option."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse


class TestUnquotedIdentifiers:
    """Tests for parsing unquoted identifier values."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Simple identifiers
            ('{"status": ok}', '{"status": "ok"}'),
            ('{"result": success}', '{"result": "success"}'),
            ('{"type": user}', '{"type": "user"}'),
            ('{"mode": auto}', '{"mode": "auto"}'),
            # With underscore
            ('{"status": not_found}', '{"status": "not_found"}'),
            ('{"type": user_admin}', '{"type": "user_admin"}'),
            ('{"key": snake_case_value}', '{"key": "snake_case_value"}'),
            ('{"key": __private}', '{"key": "__private"}'),
            # With dollar sign (JS identifier)
            ('{"var": $value}', '{"var": "$value"}'),
            ('{"ref": $ref}', '{"ref": "$ref"}'),
            ('{"jquery": $elem}', '{"jquery": "$elem"}'),
            # Starting with underscore
            ('{"key": _private}', '{"key": "_private"}'),
            ('{"key": _}', '{"key": "_"}'),
            # CamelCase
            ('{"key": camelCase}', '{"key": "camelCase"}'),
            ('{"key": PascalCase}', '{"key": "PascalCase"}'),
            # With numbers (not at start)
            ('{"key": value123}', '{"key": "value123"}'),
            ('{"key": abc123def}', '{"key": "abc123def"}'),
            ('{"key": _123}', '{"key": "_123"}'),
            # Multiple values
            ('{"a": foo, "b": bar}', '{"a": "foo", "b": "bar"}'),
            ('{"status": ok, "code": success}', '{"status": "ok", "code": "success"}'),
            # In arrays
            ("[ok, error, pending]", '["ok", "error", "pending"]'),
            ("[foo]", '["foo"]'),
            ("[a, b, c]", '["a", "b", "c"]'),
            # Mixed with other value types
            ('{"str": hello, "num": 42}', '{"str": "hello", "num": 42}'),
            ('{"id": foo, "count": 10, "flag": true}', '{"id": "foo", "count": 10, "flag": true}'),
            ("[ok, 1, true, null]", '["ok", 1, true, null]'),
            # Nested
            ('{"outer": {"inner": value}}', '{"outer": {"inner": "value"}}'),
            ('{"data": [{"status": ok}]}', '{"data": [{"status": "ok"}]}'),
        ],
    )
    def test_unquoted_identifiers(self, input_json: str, expected: str):
        """Test that unquoted identifiers are converted to strings."""
        opts = RecoveryOptions(allow_unquoted_identifiers=True)
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json",
        [
            '{"status": ok}',
            "[foo, bar]",
            '{"key": value}',
        ],
    )
    def test_fails_without_option(self, input_json: str):
        """Test that unquoted identifiers fail without the option."""
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, RecoveryOptions())

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # These are valid JSON and should still work
            ('{"key": "value"}', '{"key": "value"}'),
            ('{"key": 123}', '{"key": 123}'),
            ('{"key": true}', '{"key": true}'),
            ('{"key": false}', '{"key": false}'),
            ('{"key": null}', '{"key": null}'),
            ("[1, 2, 3]", "[1, 2, 3]"),
        ],
    )
    def test_valid_json_still_works(self, input_json: str, expected: str):
        """Test that valid JSON still works with option enabled."""
        opts = RecoveryOptions(allow_unquoted_identifiers=True)
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json",
        [
            # Starting with number - invalid identifier
            '{"key": 123abc}',
            '{"key": 1st}',
            # Contains invalid characters
            '{"key": hello-world}',  # hyphen
            '{"key": hello.world}',  # dot
            '{"key": hello@world}',  # at sign
            '{"key": hello world}',  # space (would be parsed differently)
        ],
    )
    def test_invalid_identifiers_fail(self, input_json: str):
        """Test that invalid identifiers still fail."""
        opts = RecoveryOptions(allow_unquoted_identifiers=True)
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, opts)


class TestUnquotedIdentifiersWithOtherOptions:
    """Tests combining unquoted identifiers with other options."""

    def test_with_unquoted_keys(self):
        """Test unquoted identifiers combined with unquoted keys."""
        input_json = "{status: ok, type: user}"
        opts = RecoveryOptions(
            allow_unquoted_keys=True,
            allow_unquoted_identifiers=True,
        )
        assert parse(input_json, opts) == '{"status": "ok", "type": "user"}'

    def test_with_trailing_comma(self):
        """Test unquoted identifiers with trailing comma."""
        input_json = '{"status": ok,}'
        opts = RecoveryOptions(
            allow_unquoted_identifiers=True,
            allow_trailing_commas=True,
        )
        assert parse(input_json, opts) == '{"status": "ok"}'

    def test_with_single_quotes(self):
        """Test mixing unquoted identifiers with single quotes."""
        input_json = "{'status': ok, 'type': 'admin'}"
        opts = RecoveryOptions(
            allow_single_quotes=True,
            allow_unquoted_identifiers=True,
        )
        assert parse(input_json, opts) == '{"status": "ok", "type": "admin"}'

    def test_not_confused_with_keywords(self):
        """Test that keywords are not treated as identifiers."""
        # true, false, null should be parsed as their actual values, not strings
        opts = RecoveryOptions(allow_unquoted_identifiers=True)
        assert parse('{"a": true}', opts) == '{"a": true}'
        assert parse('{"a": false}', opts) == '{"a": false}'
        assert parse('{"a": null}', opts) == '{"a": null}'
        # But similar-looking identifiers should become strings
        assert parse('{"a": trueish}', opts) == '{"a": "trueish"}'
        assert parse('{"a": nullable}', opts) == '{"a": "nullable"}'

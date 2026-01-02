"""Tests for escape_newlines_in_strings option."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse


class TestUnescapedNewlines:
    """Tests for handling unescaped newlines in strings."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Literal newlines in strings
            ('{"text": "line1\nline2"}', '{"text": "line1\\nline2"}'),
            ('{"text": "a\nb\nc"}', '{"text": "a\\nb\\nc"}'),
            ('["line1\nline2"]', '["line1\\nline2"]'),
            # Multiple newlines
            ('{"text": "a\n\nb"}', '{"text": "a\\n\\nb"}'),
            ('{"text": "\n\n\n"}', '{"text": "\\n\\n\\n"}'),
            # Newline at start/end
            ('{"text": "\nstart"}', '{"text": "\\nstart"}'),
            ('{"text": "end\n"}', '{"text": "end\\n"}'),
        ],
    )
    def test_unescaped_newlines(self, input_json: str, expected: str):
        """Test that unescaped newlines are properly escaped."""
        opts = RecoveryOptions(escape_newlines_in_strings=True)
        assert parse(input_json, opts) == expected


class TestUnescapedTabs:
    """Tests for handling unescaped tabs in strings."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Literal tabs in strings
            ('{"text": "col1\tcol2"}', '{"text": "col1\\tcol2"}'),
            ('{"text": "a\tb\tc"}', '{"text": "a\\tb\\tc"}'),
            ('["col1\tcol2"]', '["col1\\tcol2"]'),
            # Multiple tabs
            ('{"text": "a\t\tb"}', '{"text": "a\\t\\tb"}'),
        ],
    )
    def test_unescaped_tabs(self, input_json: str, expected: str):
        """Test that unescaped tabs are properly escaped."""
        opts = RecoveryOptions(escape_newlines_in_strings=True)
        assert parse(input_json, opts) == expected


class TestCarriageReturn:
    """Tests for handling carriage returns in strings."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Carriage return + newline (Windows style)
            ('{"text": "line1\r\nline2"}', '{"text": "line1\\r\\nline2"}'),
            # Just carriage return
            ('{"text": "line1\rline2"}', '{"text": "line1\\rline2"}'),
            # Mixed
            ('{"text": "a\rb\nc\r\nd"}', '{"text": "a\\rb\\nc\\r\\nd"}'),
        ],
    )
    def test_carriage_returns(self, input_json: str, expected: str):
        """Test that carriage returns are properly escaped."""
        opts = RecoveryOptions(escape_newlines_in_strings=True)
        assert parse(input_json, opts) == expected


class TestMixedEscapes:
    """Tests for mixed escape scenarios."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Mix of newlines and tabs
            ('{"text": "a\tb\nc"}', '{"text": "a\\tb\\nc"}'),
            ('{"text": "\t\n\t\n"}', '{"text": "\\t\\n\\t\\n"}'),
            # With regular content
            (
                '{"title": "Hello", "body": "Line 1\nLine 2"}',
                '{"title": "Hello", "body": "Line 1\\nLine 2"}',
            ),
            # In arrays
            ('["a\tb", "c\nd"]', '["a\\tb", "c\\nd"]'),
            # Nested objects
            ('{"outer": {"inner": "a\nb"}}', '{"outer": {"inner": "a\\nb"}}'),
        ],
    )
    def test_mixed_escapes(self, input_json: str, expected: str):
        """Test handling of mixed escape scenarios."""
        opts = RecoveryOptions(escape_newlines_in_strings=True)
        assert parse(input_json, opts) == expected


class TestAlreadyEscaped:
    """Tests ensuring already-escaped sequences are not double-escaped."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Already properly escaped should stay the same
            ('{"text": "line1\\nline2"}', '{"text": "line1\\nline2"}'),
            ('{"text": "col1\\tcol2"}', '{"text": "col1\\tcol2"}'),
            ('{"text": "a\\r\\nb"}', '{"text": "a\\r\\nb"}'),
            # Mix of escaped and unescaped
            (
                '{"text": "escaped\\n and unescaped\n"}',
                '{"text": "escaped\\n and unescaped\\n"}',
            ),
        ],
    )
    def test_already_escaped(self, input_json: str, expected: str):
        """Test that already-escaped sequences are not double-escaped."""
        opts = RecoveryOptions(escape_newlines_in_strings=True)
        assert parse(input_json, opts) == expected


class TestEscapeEdgeCases:
    """Edge cases for escape handling."""

    @pytest.mark.parametrize(
        "input_json",
        [
            '{"text": "line1\nline2"}',  # Unescaped newline
        ],
    )
    def test_fails_without_option(self, input_json: str):
        """Test that unescaped control characters fail without the option."""
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, RecoveryOptions())

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Valid JSON with proper escapes still works
            ('{"text": "line1\\nline2"}', '{"text": "line1\\nline2"}'),
            ('{"text": "col1\\tcol2"}', '{"text": "col1\\tcol2"}'),
            ('{"text": "normal text"}', '{"text": "normal text"}'),
        ],
    )
    def test_valid_json_still_works(self, input_json: str, expected: str):
        """Test that valid JSON still works with option enabled."""
        opts = RecoveryOptions(escape_newlines_in_strings=True)
        assert parse(input_json, opts) == expected

    def test_empty_string_with_option(self):
        """Test empty strings work with option enabled."""
        opts = RecoveryOptions(escape_newlines_in_strings=True)
        assert parse('{"key": ""}', opts) == '{"key": ""}'

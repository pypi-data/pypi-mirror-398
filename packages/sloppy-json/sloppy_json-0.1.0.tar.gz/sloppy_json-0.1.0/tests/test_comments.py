"""Tests for allow_comments option."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse


class TestSingleLineComments:
    """Tests for single-line // comments."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # End of line comments
            ('{"key": "value" // comment\n}', '{"key": "value"}'),
            ('{"a": 1, // inline\n"b": 2}', '{"a": 1, "b": 2}'),
            ('{"a": 1 // first\n, "b": 2 // second\n}', '{"a": 1, "b": 2}'),
            # Comment before content
            ('// header comment\n{"key": "value"}', '{"key": "value"}'),
            ('// line 1\n// line 2\n{"key": "value"}', '{"key": "value"}'),
            # Comment after content
            ('{"key": "value"}\n// trailing', '{"key": "value"}'),
            ('{"key": "value"} // same line', '{"key": "value"}'),
            # Comments on their own lines
            ('{\n// comment\n"key": "value"\n}', '{"key": "value"}'),
            ('{\n"a": 1,\n// separator\n"b": 2\n}', '{"a": 1, "b": 2}'),
            # Array with comments
            ("[1, // one\n2, // two\n3]", "[1, 2, 3]"),
            ("[\n// first\n1,\n// second\n2\n]", "[1, 2]"),
            # Empty comment
            ('{"key": "value"} //\n', '{"key": "value"}'),
            ('{"key": "value"} //    \n', '{"key": "value"}'),
        ],
    )
    def test_single_line_comments(self, input_json: str, expected: str):
        """Test that single-line comments are removed."""
        opts = RecoveryOptions(allow_comments=True)
        assert parse(input_json, opts) == expected


class TestBlockComments:
    """Tests for block /* */ comments."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Inline block comments
            ('{"key": /* comment */ "value"}', '{"key": "value"}'),
            ('{"a": 1, /* between */ "b": 2}', '{"a": 1, "b": 2}'),
            ('/* start */ {"key": "value"}', '{"key": "value"}'),
            ('{"key": "value"} /* end */', '{"key": "value"}'),
            # Block comment before value
            ('{"a": /* comment */ 1}', '{"a": 1}'),
            ('{"key": /* comment */ "value"}', '{"key": "value"}'),
            # Block comment spanning lines
            ('{\n/* multi\nline\ncomment */\n"key": "value"\n}', '{"key": "value"}'),
            ('/* start\ncomment */ {"key": "value"}', '{"key": "value"}'),
            # Multiple block comments
            ('/* a */ {"key": /* b */ "value"} /* c */', '{"key": "value"}'),
            # Block comment in array
            ("[/* a */ 1, /* b */ 2]", "[1, 2]"),
            ("[1 /* comment */, 2]", "[1, 2]"),
            # Empty block comment
            ('{"key": /**/ "value"}', '{"key": "value"}'),
        ],
    )
    def test_block_comments(self, input_json: str, expected: str):
        """Test that block comments are removed."""
        opts = RecoveryOptions(allow_comments=True)
        assert parse(input_json, opts) == expected


class TestMixedComments:
    """Tests for mixed comment styles."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Both styles together
            ('{\n// line comment\n"a": 1, /* block */ "b": 2\n}', '{"a": 1, "b": 2}'),
            ('/* header */ {"a": 1} // trailing', '{"a": 1}'),
            # Alternating styles
            ('// start\n{"a": /* comment */ 1}\n// end', '{"a": 1}'),
            # Nested structures with comments
            ('{"outer": { // inner object\n"inner": 1}}', '{"outer": {"inner": 1}}'),
            ('{"arr": [/* comment */ 1, 2, /* comment */ 3]}', '{"arr": [1, 2, 3]}'),
            # Complex example
            (
                """
        // Configuration
        {
            /* User settings */
            "name": "test", // user name
            "values": [
                1, // first
                2  /* second */
            ]
        }
        """,
                '{"name": "test", "values": [1, 2]}',
            ),
        ],
    )
    def test_mixed_comments(self, input_json: str, expected: str):
        """Test that mixed comment styles work together."""
        opts = RecoveryOptions(allow_comments=True)
        assert parse(input_json, opts) == expected


class TestCommentsInStrings:
    """Tests ensuring comment-like content in strings is preserved."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # URL with // should be preserved
            ('{"url": "http://example.com"}', '{"url": "http://example.com"}'),
            (
                '{"url": "https://example.com/path"}',
                '{"url": "https://example.com/path"}',
            ),
            # Comment-like content in string values
            ('{"code": "// not a comment"}', '{"code": "// not a comment"}'),
            ('{"code": "/* not a comment */"}', '{"code": "/* not a comment */"}'),
            # Mixed real comments and string content
            ('{"url": "http://x.com"} // real comment', '{"url": "http://x.com"}'),
            ('/* comment */ {"code": "// in string"}', '{"code": "// in string"}'),
            # Multiple slashes in strings
            ('{"path": "a//b//c"}', '{"path": "a//b//c"}'),
            ('{"regex": "a/b/c"}', '{"regex": "a/b/c"}'),
        ],
    )
    def test_comment_like_string_preserved(self, input_json: str, expected: str):
        """Ensure // and /* inside strings are not treated as comments."""
        opts = RecoveryOptions(allow_comments=True)
        assert parse(input_json, opts) == expected


class TestCommentsEdgeCases:
    """Edge cases for comment handling."""

    @pytest.mark.parametrize(
        "input_json",
        [
            '{"key": "value" // comment\n}',
            '/* comment */ {"key": "value"}',
        ],
    )
    def test_fails_without_option(self, input_json: str):
        """Test that comments fail without the option enabled."""
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, RecoveryOptions())

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Valid JSON without comments still works
            ('{"key": "value"}', '{"key": "value"}'),
            ("[1, 2, 3]", "[1, 2, 3]"),
        ],
    )
    def test_valid_json_still_works(self, input_json: str, expected: str):
        """Test that valid JSON still works with option enabled."""
        opts = RecoveryOptions(allow_comments=True)
        assert parse(input_json, opts) == expected

    def test_unclosed_block_comment(self):
        """Test that unclosed block comments fail."""
        opts = RecoveryOptions(allow_comments=True)
        with pytest.raises(SloppyJSONDecodeError):
            parse('{"key": "value"} /* unclosed', opts)

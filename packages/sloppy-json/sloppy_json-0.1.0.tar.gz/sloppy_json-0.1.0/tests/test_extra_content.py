"""Tests for extract_json_from_text and extract_from_code_blocks options."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse


class TestExtractFromText:
    """Tests for extract_json_from_text option."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Leading text
            ('Here is the JSON: {"key": "value"}', '{"key": "value"}'),
            ('Sure! {"a": 1}', '{"a": 1}'),
            ('The result is {"x": 10}', '{"x": 10}'),
            ("Response: [1, 2, 3]", "[1, 2, 3]"),
            ('OK {"data": true}', '{"data": true}'),
            # Trailing text
            ('{"key": "value"} Let me know if you need more.', '{"key": "value"}'),
            ('{"a": 1} Hope this helps!', '{"a": 1}'),
            ("[1, 2, 3] - these are the numbers", "[1, 2, 3]"),
            ('{"done": true} Thanks!', '{"done": true}'),
            # Both leading and trailing
            ('The answer is {"a": 1} as requested.', '{"a": 1}'),
            ("Here: [1, 2, 3]. Done!", "[1, 2, 3]"),
            ('Result: {"x": 42} - verified.', '{"x": 42}'),
            # Multiple sentences before
            (
                'I analyzed your request. Based on the data, here is what I found. {"result": 42}',
                '{"result": 42}',
            ),
            (
                'Let me help. First, note that this is important. Here: {"key": "val"}',
                '{"key": "val"}',
            ),
            # With newlines
            ('Here is the data:\n{"key": "value"}', '{"key": "value"}'),
            ('Result:\n\n{"a": 1}\n\nLet me know!', '{"a": 1}'),
            ("Output:\n[1, 2, 3]\nDone.", "[1, 2, 3]"),
            # Nested structures
            (
                'Here: {"nested": {"deep": [1, 2, 3]}}',
                '{"nested": {"deep": [1, 2, 3]}}',
            ),
            ('Data: [{"id": 1}, {"id": 2}] ready', '[{"id": 1}, {"id": 2}]'),
            # With punctuation near JSON
            ('Result: {"a": 1}.', '{"a": 1}'),
            ('See {"a": 1}, it works!', '{"a": 1}'),
            ('({"a": 1})', '{"a": 1}'),
            # Long surrounding text
            (
                "After careful analysis of the provided information and considering all factors, "
                'the computed result is {"answer": 42} which represents the final output.',
                '{"answer": 42}',
            ),
        ],
    )
    def test_extract_json_from_text(self, input_json: str, expected: str):
        """Test JSON extraction from surrounding text."""
        opts = RecoveryOptions(extract_json_from_text=True)
        assert parse(input_json, opts) == expected

    def test_prefers_first_valid_json(self):
        """When multiple JSON objects exist, prefer the first complete one."""
        opts = RecoveryOptions(extract_json_from_text=True)
        # This behavior might vary - documenting expected behavior
        result = parse('First {"a": 1} then {"b": 2}', opts)
        assert result == '{"a": 1}'

    @pytest.mark.parametrize(
        "input_json",
        [
            "No JSON here at all",
            "Just some text with {broken: json}",
            'Almost {"key": but not quite',
        ],
    )
    def test_fails_when_no_valid_json(self, input_json: str):
        """Test that extraction fails when no valid JSON is found."""
        opts = RecoveryOptions(extract_json_from_text=True)
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, opts)


class TestExtractFromCodeBlocks:
    """Tests for extract_from_code_blocks option."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Basic code blocks with json tag
            ('```json\n{"key": "value"}\n```', '{"key": "value"}'),
            ("```json\n[1, 2, 3]\n```", "[1, 2, 3]"),
            # Without language tag
            ('```\n{"key": "value"}\n```', '{"key": "value"}'),
            ("```\n[1, 2, 3]\n```", "[1, 2, 3]"),
            # Case variations
            ('```JSON\n{"a": 1}\n```', '{"a": 1}'),
            ('```Json\n{"a": 1}\n```', '{"a": 1}'),
            # With surrounding text
            (
                'Here is the code:\n```json\n{"key": "value"}\n```\nHope this helps!',
                '{"key": "value"}',
            ),
            ("Result:\n```json\n[1, 2, 3]\n```\nDone.", "[1, 2, 3]"),
            # Multiline JSON in code block
            ('```json\n{\n  "a": 1,\n  "b": 2\n}\n```', '{"a": 1, "b": 2}'),
            ("```json\n[\n  1,\n  2,\n  3\n]\n```", "[1, 2, 3]"),
            # Complex nested in code block
            (
                '```json\n{"users": [{"name": "Alice"}, {"name": "Bob"}]}\n```',
                '{"users": [{"name": "Alice"}, {"name": "Bob"}]}',
            ),
            # Multiple paragraphs around code block
            (
                'First paragraph.\n\n```json\n{"a": 1}\n```\n\nSecond paragraph.',
                '{"a": 1}',
            ),
            # Code block with extra whitespace
            ('```json\n\n{"key": "value"}\n\n```', '{"key": "value"}'),
            ('```json  \n{"key": "value"}\n```', '{"key": "value"}'),
        ],
    )
    def test_extract_from_code_blocks(self, input_json: str, expected: str):
        """Test JSON extraction from markdown code blocks."""
        opts = RecoveryOptions(extract_from_code_blocks=True)
        assert parse(input_json, opts) == expected

    def test_code_block_takes_priority(self):
        """When both options enabled, code block extraction should take priority."""
        input_json = 'Some text {"ignored": 1} more text\n```json\n{"actual": 2}\n```'
        opts = RecoveryOptions(extract_json_from_text=True, extract_from_code_blocks=True)
        assert parse(input_json, opts) == '{"actual": 2}'

    def test_first_code_block_wins(self):
        """When multiple code blocks exist, use the first one."""
        input_json = '```json\n{"first": 1}\n```\n\n```json\n{"second": 2}\n```'
        opts = RecoveryOptions(extract_from_code_blocks=True)
        assert parse(input_json, opts) == '{"first": 1}'

    @pytest.mark.parametrize(
        "input_json",
        [
            '```python\nprint("hello")\n```',
            "```\nNot JSON at all\n```",
            "No code blocks here",
        ],
    )
    def test_fails_when_no_json_code_block(self, input_json: str):
        """Test that extraction fails when no valid JSON code block is found."""
        opts = RecoveryOptions(extract_from_code_blocks=True)
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, opts)


class TestExtractCombined:
    """Tests combining extraction options with other recovery options."""

    def test_extract_and_fix_trailing_comma(self):
        """Test extraction combined with trailing comma handling."""
        input_json = 'Here is the data: {"a": 1, "b": 2,}'
        opts = RecoveryOptions(extract_json_from_text=True, allow_trailing_commas=True)
        assert parse(input_json, opts) == '{"a": 1, "b": 2}'

    def test_code_block_with_single_quotes(self):
        """Test code block extraction with single quote handling."""
        input_json = "```json\n{'key': 'value'}\n```"
        opts = RecoveryOptions(extract_from_code_blocks=True, allow_single_quotes=True)
        assert parse(input_json, opts) == '{"key": "value"}'

    def test_extract_and_auto_close(self):
        """Test extraction combined with auto-close."""
        input_json = 'Result: {"key": "value"'
        opts = RecoveryOptions(
            extract_json_from_text=True,
            auto_close_objects=True,
            auto_close_strings=True,
        )
        assert parse(input_json, opts) == '{"key": "value"}'


class TestExtractFromTripleQuotes:
    """Tests for extract_from_triple_quotes option."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # Double triple quotes - basic
            ('"""{"key": "value"}"""', '{"key": "value"}'),
            ('"""[1, 2, 3]"""', "[1, 2, 3]"),
            # Double triple quotes - with newlines
            ('"""\n{"key": "value"}\n"""', '{"key": "value"}'),
            ('"""\n{\n  "a": 1,\n  "b": 2\n}\n"""', '{"a": 1, "b": 2}'),
            # Single triple quotes - basic
            ("'''[1, 2, 3]'''", "[1, 2, 3]"),
            # With json prefix (like markdown)
            ('"""json\n{"key": "value"}\n"""', '{"key": "value"}'),
            ('"""JSON\n{"a": 1}\n"""', '{"a": 1}'),
            # With surrounding text
            ('Here it is: """{"a": 1}""" done', '{"a": 1}'),
            ('Result:\n"""{"key": "value"}"""\nThanks!', '{"key": "value"}'),
            # Multiline with indentation
            (
                '"""\n{\n    "name": "test",\n    "value": 42\n}\n"""',
                '{"name": "test", "value": 42}',
            ),
            # Empty whitespace inside
            ('"""   {"a": 1}   """', '{"a": 1}'),
            ('"""\n\n{"a": 1}\n\n"""', '{"a": 1}'),
            # Complex nested
            (
                '"""{"users": [{"name": "Alice"}, {"name": "Bob"}]}"""',
                '{"users": [{"name": "Alice"}, {"name": "Bob"}]}',
            ),
        ],
    )
    def test_extract_from_triple_quotes(self, input_json: str, expected: str):
        """Test JSON extraction from Python triple-quoted strings."""
        opts = RecoveryOptions(extract_from_triple_quotes=True)
        assert parse(input_json, opts) == expected

    def test_triple_quotes_with_single_quotes_inside(self):
        """Test triple double quotes containing single-quoted JSON."""
        input_json = """\"\"\"{'key': 'value'}\"\"\""""
        opts = RecoveryOptions(
            extract_from_triple_quotes=True,
            allow_single_quotes=True,
        )
        assert parse(input_json, opts) == '{"key": "value"}'

    def test_first_triple_quote_wins(self):
        """When multiple triple-quoted blocks exist, use the first one."""
        input_json = '"""{"first": 1}""" and """{"second": 2}"""'
        opts = RecoveryOptions(extract_from_triple_quotes=True)
        assert parse(input_json, opts) == '{"first": 1}'

    def test_code_block_priority_over_triple_quotes(self):
        """Code blocks should take priority over triple quotes."""
        input_json = '"""{"ignored": 1}"""\n```json\n{"actual": 2}\n```'
        opts = RecoveryOptions(
            extract_from_code_blocks=True,
            extract_from_triple_quotes=True,
        )
        assert parse(input_json, opts) == '{"actual": 2}'

    @pytest.mark.parametrize(
        "input_json",
        [
            '"""Not JSON at all"""',
            "'''also not json'''",
            "No triple quotes here",
            '"""{"broken": """',  # malformed
        ],
    )
    def test_fails_when_no_valid_json(self, input_json: str):
        """Test that extraction fails when no valid JSON is found."""
        opts = RecoveryOptions(extract_from_triple_quotes=True)
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, opts)

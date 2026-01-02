"""Complex tests combining multiple recovery options."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse, parse_permissive


class TestRealWorldLLMOutputs:
    """Tests simulating real-world LLM outputs."""

    def test_chatgpt_style_response(self):
        """Test typical ChatGPT-style JSON response."""
        input_json = """Here's the JSON you requested:

```json
{
  "name": "John Doe",
  "age": 30,
  "active": True,
  "email": None,
}
```

Let me know if you need anything else!"""

        opts = RecoveryOptions(
            extract_from_code_blocks=True,
            convert_python_literals=True,
            allow_trailing_commas=True,
        )
        result = parse(input_json, opts)
        assert '"name": "John Doe"' in result
        assert '"active": true' in result
        assert '"email": null' in result

    def test_claude_style_response(self):
        """Test typical Claude-style JSON response."""
        input_json = """I'll help you with that. Here's the configuration:

{
  'api_key': 'sk-xxx',
  'model': 'gpt-4',
  'settings': {
    'temperature': 0.7,
    'max_tokens': 1000,
  },
}

You can modify these values as needed."""

        opts = RecoveryOptions(
            extract_json_from_text=True,
            allow_single_quotes=True,
            allow_trailing_commas=True,
        )
        result = parse(input_json, opts)
        assert '"api_key": "sk-xxx"' in result
        assert '"temperature": 0.7' in result

    def test_truncated_streaming_response(self):
        """Test handling truncated streaming response."""
        input_json = """{"users": [
  {"id": 1, "name": "Alice", "roles": ["admin", "user"]},
  {"id": 2, "name": "Bob", "roles": ["user"]},
  {"id": 3, "name": "Charlie", "roles": ["user", "moderator"""

        opts = RecoveryOptions(
            auto_close_objects=True,
            auto_close_arrays=True,
            auto_close_strings=True,
        )
        result = parse(input_json, opts)
        assert '"id": 1' in result
        assert '"name": "Alice"' in result
        assert '"id": 3' in result

    def test_javascript_object_notation(self):
        """Test JavaScript object literal style (common in LLM outputs)."""
        input_json = """{
  name: "config",
  version: 1.0,
  enabled: true,
  data: null,
  items: [1, 2, 3],
  nested: {
    key: "value"
  }
}"""
        opts = RecoveryOptions(allow_unquoted_keys=True)
        result = parse(input_json, opts)
        assert '"name": "config"' in result
        assert '"version": 1.0' in result
        assert '"enabled": true' in result


class TestCombinedOptions:
    """Tests for multiple options working together."""

    def test_all_quoting_options(self):
        """Test combining all quoting-related options."""
        input_json = "{name: 'John', age: 30, \"city\": 'NYC'}"
        opts = RecoveryOptions(
            allow_unquoted_keys=True,
            allow_single_quotes=True,
        )
        result = parse(input_json, opts)
        assert '"name": "John"' in result
        assert '"age": 30' in result
        assert '"city": "NYC"' in result

    def test_all_comma_options(self):
        """Test combining trailing and missing comma options."""
        input_json = '{"a": 1, "b": 2 "c": 3,}'
        opts = RecoveryOptions(
            allow_trailing_commas=True,
            allow_missing_commas=True,
        )
        result = parse(input_json, opts)
        assert '"a": 1' in result
        assert '"b": 2' in result
        assert '"c": 3' in result

    def test_all_auto_close_options(self):
        """Test combining all auto-close options."""
        input_json = '{"outer": {"inner": [1, 2, "incomplete'
        opts = RecoveryOptions(
            auto_close_objects=True,
            auto_close_arrays=True,
            auto_close_strings=True,
        )
        result = parse(input_json, opts)
        assert '"outer"' in result
        assert '"inner"' in result
        assert '"incomplete"' in result

    def test_all_extraction_options(self):
        """Test combining extraction options."""
        input_json = """Here is the response:
```json
{"key": "value"}
```
Done!"""
        opts = RecoveryOptions(
            extract_from_code_blocks=True,
            extract_json_from_text=True,
        )
        result = parse(input_json, opts)
        assert result == '{"key": "value"}'

    def test_all_special_values(self):
        """Test combining all special value options."""
        input_json = (
            '{"a": undefined, "b": NaN, "c": Infinity, "d": -Infinity, "e": True, "f": None}'
        )
        opts = RecoveryOptions(
            handle_undefined="null",
            handle_nan="null",
            handle_infinity="null",
            convert_python_literals=True,
        )
        result = parse(input_json, opts)
        assert '"a": null' in result
        assert '"b": null' in result
        assert '"c": null' in result
        assert '"d": null' in result
        assert '"e": true' in result
        assert '"f": null' in result


class TestDeepNesting:
    """Tests for deeply nested structures."""

    def test_deep_nested_objects(self):
        """Test deeply nested objects."""
        input_json = '{"a": {"b": {"c": {"d": {"e": {"f": "deep"}}}}}}'
        result = parse(input_json, RecoveryOptions())
        assert result == input_json

    def test_deep_nested_arrays(self):
        """Test deeply nested arrays."""
        input_json = "[[[[[[1]]]]]]"
        result = parse(input_json, RecoveryOptions())
        assert result == input_json

    def test_deep_mixed_nesting(self):
        """Test deeply nested mixed structures."""
        input_json = '{"a": [{"b": [{"c": [1, 2, 3]}]}]}'
        result = parse(input_json, RecoveryOptions())
        assert result == input_json

    def test_deep_nested_with_recovery(self):
        """Test deep nesting with recovery options."""
        input_json = "{a: {b: {c: {d: {e: 'deep',},},},},}"
        opts = RecoveryOptions(
            allow_unquoted_keys=True,
            allow_single_quotes=True,
            allow_trailing_commas=True,
        )
        result = parse(input_json, opts)
        assert '"a"' in result
        assert '"e": "deep"' in result

    def test_deep_nested_unclosed(self):
        """Test deeply nested unclosed structures."""
        input_json = '{"a": {"b": {"c": {"d": {"e": "deep'
        opts = RecoveryOptions(
            auto_close_objects=True,
            auto_close_strings=True,
        )
        result = parse(input_json, opts)
        assert '"e": "deep"' in result
        # Should have all closing braces
        assert result.count("}") == 5


class TestLargePayloads:
    """Tests for larger JSON payloads."""

    def test_large_array(self):
        """Test large array."""
        items = ", ".join([f"{i}" for i in range(1000)])
        input_json = f"[{items}]"
        result = parse(input_json, RecoveryOptions())
        assert result == input_json

    def test_large_object(self):
        """Test large object."""
        items = ", ".join([f'"key{i}": {i}' for i in range(100)])
        input_json = f"{{{items}}}"
        result = parse(input_json, RecoveryOptions())
        assert result == input_json

    def test_large_with_recovery(self):
        """Test large payload with recovery options."""
        items = " ".join([f'"key{i}": {i}' for i in range(50)])  # missing commas
        input_json = f"{{{items}}}"
        opts = RecoveryOptions(allow_missing_commas=True)
        result = parse(input_json, opts)
        assert '"key0": 0' in result
        assert '"key49": 49' in result


class TestEdgeCases:
    """Edge cases and corner cases."""

    def test_empty_string(self):
        """Test empty string input."""
        with pytest.raises(SloppyJSONDecodeError):
            parse("", RecoveryOptions())

    def test_whitespace_only(self):
        """Test whitespace-only input."""
        with pytest.raises(SloppyJSONDecodeError):
            parse("   \n\t  ", RecoveryOptions())

    def test_just_primitives(self):
        """Test parsing just primitive values."""
        assert parse("null", RecoveryOptions()) == "null"
        assert parse("true", RecoveryOptions()) == "true"
        assert parse("false", RecoveryOptions()) == "false"
        assert parse("123", RecoveryOptions()) == "123"
        assert parse('"string"', RecoveryOptions()) == '"string"'
        assert parse("-45.67", RecoveryOptions()) == "-45.67"
        assert parse("1.23e10", RecoveryOptions()) == "1.23e10"

    def test_unicode_content(self):
        """Test Unicode content in strings."""
        input_json = '{"emoji": "\\u0048\\u0065\\u006c\\u006c\\u006f", "text": "Hello"}'
        result = parse(input_json, RecoveryOptions())
        assert result == input_json

    def test_escaped_characters(self):
        """Test properly escaped characters."""
        input_json = '{"text": "line1\\nline2\\ttab\\r\\n"}'
        result = parse(input_json, RecoveryOptions())
        assert result == input_json

    def test_empty_containers(self):
        """Test empty containers."""
        assert parse("{}", RecoveryOptions()) == "{}"
        assert parse("[]", RecoveryOptions()) == "[]"
        assert parse('{"a": {}, "b": []}', RecoveryOptions()) == '{"a": {}, "b": []}'

    def test_null_in_various_positions(self):
        """Test null value in various positions."""
        assert parse("[null]", RecoveryOptions()) == "[null]"
        assert parse('{"key": null}', RecoveryOptions()) == '{"key": null}'
        assert parse("[null, null, null]", RecoveryOptions()) == "[null, null, null]"


class TestPermissiveMode:
    """Integration tests for parse_permissive."""

    def test_handles_everything(self):
        """Test that permissive mode handles many issues at once."""
        input_json = """Here is the data:
```json
{
  name: 'Test',  // the name
  count: 42,
  active: True
  items: [1, 2, 3,],
  meta: {
    created: undefined,
    score: NaN,
"""
        result = parse_permissive(input_json)
        assert '"name": "Test"' in result
        assert '"count": 42' in result
        assert '"active": true' in result

    def test_worst_case_json(self):
        """Test extremely malformed JSON."""
        input_json = "Sure here it is {name: 'test' value: True items: [1 2 3"
        result = parse_permissive(input_json)
        assert '"name": "test"' in result
        assert '"value": true' in result


class TestConsistency:
    """Tests for consistent behavior."""

    def test_idempotent_valid_json(self):
        """Parsing valid JSON should be idempotent."""
        input_json = '{"key": "value", "num": 123}'
        first = parse(input_json, RecoveryOptions())
        second = parse(first, RecoveryOptions())
        assert first == second

    def test_normalized_output(self):
        """Output should be normalized (minimal whitespace)."""
        input_json = """
        {
            "key"  :   "value"   ,
            "num"  :   123
        }
        """
        result = parse(input_json, RecoveryOptions())
        assert "\n" not in result  # Should be single line
        assert "  " not in result  # No double spaces

    def test_key_order_preserved(self):
        """Key order should be preserved (Python 3.7+)."""
        input_json = '{"z": 1, "a": 2, "m": 3}'
        result = parse(input_json, RecoveryOptions())
        z_pos = result.index('"z"')
        a_pos = result.index('"a"')
        m_pos = result.index('"m"')
        assert z_pos < a_pos < m_pos

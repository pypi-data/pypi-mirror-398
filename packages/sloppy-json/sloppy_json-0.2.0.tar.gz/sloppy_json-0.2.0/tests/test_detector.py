"""Tests for auto-detection of required options."""

from sloppy_json import RecoveryOptions


# Helper alias for cleaner test code
def detect_required_options(samples: list[str]) -> RecoveryOptions:
    return RecoveryOptions.detect_from(samples)


class TestDetectUnquotedKeys:
    """Tests for detecting unquoted keys."""

    def test_detects_unquoted_keys(self):
        samples = ['{name: "John"}', "{age: 30}"]
        options = detect_required_options(samples)
        assert options.allow_unquoted_keys == True
        assert options.allow_single_quotes == False

    def test_no_false_positive_for_quoted_keys(self):
        samples = ['{"name": "John"}', '{"age": 30}']
        options = detect_required_options(samples)
        assert options.allow_unquoted_keys == False


class TestDetectSingleQuotes:
    """Tests for detecting single quotes."""

    def test_detects_single_quotes(self):
        samples = ["{'key': 'value'}", "{'a': 1}"]
        options = detect_required_options(samples)
        assert options.allow_single_quotes == True
        assert options.allow_unquoted_keys == False

    def test_detects_single_quoted_values_only(self):
        samples = ["{\"key\": 'value'}"]
        options = detect_required_options(samples)
        assert options.allow_single_quotes == True


class TestDetectTrailingCommas:
    """Tests for detecting trailing commas."""

    def test_detects_trailing_commas_in_objects(self):
        samples = ['{"a": 1,}', '{"b": 2, "c": 3,}']
        options = detect_required_options(samples)
        assert options.allow_trailing_commas == True

    def test_detects_trailing_commas_in_arrays(self):
        samples = ["[1, 2,]", '["a", "b", "c",]']
        options = detect_required_options(samples)
        assert options.allow_trailing_commas == True


class TestDetectMissingCommas:
    """Tests for detecting missing commas."""

    def test_detects_missing_commas(self):
        samples = ['{"a": 1 "b": 2}', "[1 2 3]"]
        options = detect_required_options(samples)
        assert options.allow_missing_commas == True


class TestDetectUnclosed:
    """Tests for detecting unclosed structures."""

    def test_detects_unclosed_objects(self):
        samples = ['{"key": "value"', '{"a": 1']
        options = detect_required_options(samples)
        assert options.auto_close_objects == True

    def test_detects_unclosed_arrays(self):
        samples = ["[1, 2, 3", '["a", "b"']
        options = detect_required_options(samples)
        assert options.auto_close_arrays == True

    def test_detects_unclosed_strings(self):
        samples = ['{"key": "value', '["hello']
        options = detect_required_options(samples)
        assert options.auto_close_strings == True


class TestDetectPythonLiterals:
    """Tests for detecting Python literals."""

    def test_detects_python_true(self):
        samples = ['{"a": True}']
        options = detect_required_options(samples)
        assert options.convert_python_literals == True

    def test_detects_python_false(self):
        samples = ['{"a": False}']
        options = detect_required_options(samples)
        assert options.convert_python_literals == True

    def test_detects_python_none(self):
        samples = ['{"a": None}']
        options = detect_required_options(samples)
        assert options.convert_python_literals == True

    def test_detects_mixed_python_literals(self):
        samples = ['{"a": True, "b": False, "c": None}']
        options = detect_required_options(samples)
        assert options.convert_python_literals == True


class TestDetectSpecialValues:
    """Tests for detecting special JavaScript values."""

    def test_detects_undefined(self):
        samples = ['{"a": undefined}']
        options = detect_required_options(samples)
        assert options.handle_undefined != "error"

    def test_detects_nan(self):
        samples = ['{"a": NaN}']
        options = detect_required_options(samples)
        assert options.handle_nan != "error"

    def test_detects_infinity(self):
        samples = ['{"a": Infinity}', '{"b": -Infinity}']
        options = detect_required_options(samples)
        assert options.handle_infinity != "error"


class TestDetectComments:
    """Tests for detecting comments."""

    def test_detects_single_line_comments(self):
        samples = ['{"a": 1} // comment', '// header\n{"b": 2}']
        options = detect_required_options(samples)
        assert options.allow_comments == True

    def test_detects_block_comments(self):
        samples = ['/* comment */ {"a": 1}', '{"b": /* inline */ 2}']
        options = detect_required_options(samples)
        assert options.allow_comments == True


class TestDetectExtraContent:
    """Tests for detecting extra content around JSON."""

    def test_detects_code_blocks(self):
        samples = ['```json\n{"a": 1}\n```']
        options = detect_required_options(samples)
        assert options.extract_from_code_blocks == True

    def test_detects_extra_text(self):
        samples = ['Here is JSON: {"a": 1}', '{"b": 2} hope this helps']
        options = detect_required_options(samples)
        assert options.extract_json_from_text == True


class TestDetectMultipleIssues:
    """Tests for detecting multiple issues at once."""

    def test_detects_single_quotes_and_trailing_comma(self):
        samples = ["{'key': 'value',}"]
        options = detect_required_options(samples)
        assert options.allow_single_quotes == True
        assert options.allow_trailing_commas == True
        assert options.allow_unquoted_keys == False  # not needed

    def test_detects_unquoted_keys_and_python_literals(self):
        samples = ["{flag: True, count: None}"]
        options = detect_required_options(samples)
        assert options.allow_unquoted_keys == True
        assert options.convert_python_literals == True

    def test_detects_all_issues(self):
        samples = [
            "{'key': 'value',}",  # single quotes, trailing comma
            "{name: True}",  # unquoted key, Python literal
            '{"a": 1 "b": 2',  # missing comma, unclosed
            '// comment\n{"x": undefined}',  # comment, undefined
        ]
        options = detect_required_options(samples)
        assert options.allow_single_quotes == True
        assert options.allow_trailing_commas == True
        assert options.allow_unquoted_keys == True
        assert options.convert_python_literals == True
        assert options.allow_missing_commas == True
        assert options.auto_close_objects == True
        assert options.allow_comments == True
        assert options.handle_undefined != "error"


class TestDetectMinimum:
    """Tests ensuring detection returns minimum required options."""

    def test_returns_minimum_options(self):
        """Detection should return only what's needed, not everything."""
        samples = ['{"a": 1,}']  # only trailing comma issue
        options = detect_required_options(samples)

        # Should have trailing commas enabled
        assert options.allow_trailing_commas == True

        # But not these (they're not needed)
        assert options.allow_single_quotes == False
        assert options.allow_unquoted_keys == False
        assert options.allow_missing_commas == False
        assert options.auto_close_objects == False
        assert options.convert_python_literals == False

    def test_empty_samples(self):
        """Empty sample list should return strict options."""
        options = detect_required_options([])
        assert options.allow_trailing_commas == False
        assert options.allow_single_quotes == False

    def test_valid_json_samples(self):
        """Valid JSON samples should return strict options."""
        samples = ['{"a": 1}', "[1, 2, 3]", '{"nested": {"key": "value"}}']
        options = detect_required_options(samples)

        # All should be false/error since valid JSON needs no recovery
        assert options.allow_trailing_commas == False
        assert options.allow_single_quotes == False
        assert options.allow_unquoted_keys == False


class TestDetectEdgeCases:
    """Edge cases for detection."""

    def test_mixed_valid_and_invalid(self):
        """Mixed samples should detect issues from invalid ones."""
        samples = [
            '{"valid": 1}',  # valid
            "{'invalid': 2,}",  # single quotes + trailing comma
        ]
        options = detect_required_options(samples)
        assert options.allow_single_quotes == True
        assert options.allow_trailing_commas == True

    def test_comments_in_string_not_detected(self):
        """Comment-like content in strings should not trigger detection."""
        samples = ['{"url": "http://example.com"}']  # // is in URL
        options = detect_required_options(samples)
        assert options.allow_comments == False

    def test_python_literal_in_string_not_detected(self):
        """Python literal-like content in strings should not trigger detection."""
        samples = ['{"text": "True or False"}']
        options = detect_required_options(samples)
        assert options.convert_python_literals == False

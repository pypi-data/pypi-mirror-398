"""Tests for error reporting and partial recovery."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse
from sloppy_json.exceptions import ErrorInfo


class TestErrorMessages:
    """Tests for error message quality."""

    def test_error_includes_position(self):
        """Errors should include position information."""
        try:
            parse('{"key": }', RecoveryOptions())
            pytest.fail("Should have raised SloppyJSONDecodeError")
        except SloppyJSONDecodeError as e:
            assert e.position >= 0
            assert e.line >= 1
            assert e.column >= 1

    def test_error_includes_line_column(self):
        """Errors should include line and column numbers."""
        try:
            parse('{\n  "key": \n}', RecoveryOptions())
            pytest.fail("Should have raised SloppyJSONDecodeError")
        except SloppyJSONDecodeError as e:
            # Error is on line 2 or 3
            assert e.line >= 2

    def test_error_message_descriptive(self):
        """Error messages should be descriptive."""
        try:
            parse("{invalid}", RecoveryOptions())
            pytest.fail("Should have raised SloppyJSONDecodeError")
        except SloppyJSONDecodeError as e:
            assert len(e.message) > 0

    def test_error_to_error_info(self):
        """Test conversion to ErrorInfo."""
        try:
            parse('{"key": }', RecoveryOptions())
            pytest.fail("Should have raised SloppyJSONDecodeError")
        except SloppyJSONDecodeError as e:
            info = e.to_error_info()
            assert isinstance(info, ErrorInfo)
            assert info.position == e.position
            assert info.line == e.line
            assert info.column == e.column
            assert info.message == e.message


class TestPartialRecovery:
    """Tests for partial_recovery option."""

    def test_partial_recovery_returns_tuple(self):
        """With partial_recovery, parse should return (result, errors) tuple."""
        opts = RecoveryOptions(partial_recovery=True)
        result = parse('{"a": 1}', opts)
        assert isinstance(result, tuple)
        assert len(result) == 2
        result_json, errors = result
        assert result_json == '{"a": 1}'
        assert errors == []

    def test_partial_recovery_with_errors(self):
        """Partial recovery should return parsed content and errors."""
        opts = RecoveryOptions(
            partial_recovery=True,
            auto_close_objects=True,
        )
        result_json, errors = parse('{"a": 1, "b": 2', opts)
        assert '"a": 1' in result_json
        assert '"b": 2' in result_json
        # Should have at least one error about unclosed object
        assert len(errors) >= 1

    def test_partial_recovery_multiple_errors(self):
        """Partial recovery should collect multiple errors."""
        opts = RecoveryOptions(
            partial_recovery=True,
            auto_close_objects=True,
            auto_close_arrays=True,
            auto_close_strings=True,
        )
        result_json, errors = parse('{"a": [1, 2, "three', opts)
        # Multiple unclosed structures
        assert len(errors) >= 1

    def test_partial_recovery_error_info(self):
        """Errors in partial recovery should be ErrorInfo instances."""
        opts = RecoveryOptions(
            partial_recovery=True,
            auto_close_objects=True,
        )
        _, errors = parse('{"key": "value"', opts)
        for error in errors:
            assert isinstance(error, ErrorInfo)
            assert hasattr(error, "message")
            assert hasattr(error, "position")
            assert hasattr(error, "line")
            assert hasattr(error, "column")


class TestPartialRecoveryScenarios:
    """Specific scenarios for partial recovery."""

    def test_recover_unclosed_with_valid_content(self):
        """Should recover valid content even with unclosed structures."""
        opts = RecoveryOptions(
            partial_recovery=True,
            auto_close_objects=True,
        )
        result_json, errors = parse('{"name": "Alice", "age": 30', opts)
        assert '"name": "Alice"' in result_json
        assert '"age": 30' in result_json

    def test_recover_mixed_issues(self):
        """Should recover with multiple types of issues."""
        opts = RecoveryOptions(
            partial_recovery=True,
            allow_trailing_commas=True,
            auto_close_objects=True,
        )
        result_json, errors = parse('{"a": 1, "b": 2,', opts)
        assert '"a": 1' in result_json
        assert '"b": 2' in result_json

    def test_no_partial_recovery_strict_fails(self):
        """Without partial_recovery, invalid JSON should raise exception."""
        opts = RecoveryOptions(partial_recovery=False)
        with pytest.raises(SloppyJSONDecodeError):
            parse('{"key": }', opts)


class TestErrorPositionAccuracy:
    """Tests for accurate error position reporting."""

    @pytest.mark.parametrize(
        "input_json,expected_line",
        [
            ('{"key": }', 1),
            ('{\n"key": }', 2),
            ('{\n\n"key": }', 3),
        ],
    )
    def test_error_line_accuracy(self, input_json: str, expected_line: int):
        """Error line numbers should be accurate."""
        try:
            parse(input_json, RecoveryOptions())
            pytest.fail("Should have raised SloppyJSONDecodeError")
        except SloppyJSONDecodeError as e:
            assert e.line == expected_line

    def test_error_column_accuracy(self):
        """Error column numbers should be accurate."""
        try:
            # Error at position of }
            parse('{"key":}', RecoveryOptions())
            pytest.fail("Should have raised SloppyJSONDecodeError")
        except SloppyJSONDecodeError as e:
            # Column should point to the unexpected }
            assert e.column > 1


class TestErrorRecoveryInteraction:
    """Tests for interaction between error reporting and recovery options."""

    def test_recovery_reduces_errors(self):
        """Enabling recovery options should reduce/eliminate errors."""
        input_json = '{"a": 1,}'

        # Without option - should fail
        with pytest.raises(SloppyJSONDecodeError):
            parse(input_json, RecoveryOptions())

        # With option and partial recovery - should succeed with no errors
        opts = RecoveryOptions(
            partial_recovery=True,
            allow_trailing_commas=True,
        )
        result_json, errors = parse(input_json, opts)
        assert result_json == '{"a": 1}'
        assert len(errors) == 0

    def test_partial_recovery_unrecoverable(self):
        """Some errors may not be recoverable even with partial recovery."""
        opts = RecoveryOptions(
            partial_recovery=True,
            # No auto_close options enabled
        )
        # Completely broken JSON
        result_json, errors = parse("{{{", opts)
        # Should have errors
        assert len(errors) > 0

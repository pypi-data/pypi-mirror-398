"""Tests for handle_undefined, handle_nan, and handle_infinity options."""

import pytest

from sloppy_json import RecoveryOptions, SloppyJSONDecodeError, parse


class TestUndefined:
    """Tests for handling JavaScript undefined values."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            ('{"key": undefined}', '{"key": null}'),
            ('{"a": 1, "b": undefined}', '{"a": 1, "b": null}'),
            ('{"a": undefined, "b": 2}', '{"a": null, "b": 2}'),
            ("[1, undefined, 3]", "[1, null, 3]"),
            ("[undefined]", "[null]"),
            ("[undefined, undefined]", "[null, null]"),
            ('{"nested": {"val": undefined}}', '{"nested": {"val": null}}'),
        ],
    )
    def test_undefined_as_null(self, input_json: str, expected: str):
        """Test that undefined is converted to null."""
        opts = RecoveryOptions(handle_undefined="null")
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            ('{"key": undefined}', "{}"),
            ('{"a": 1, "b": undefined}', '{"a": 1}'),
            ('{"a": undefined, "b": 2}', '{"b": 2}'),
            ('{"a": undefined, "b": undefined, "c": 3}', '{"c": 3}'),
            ('{"nested": {"val": undefined}}', '{"nested": {}}'),
        ],
    )
    def test_undefined_remove(self, input_json: str, expected: str):
        """Test that undefined keys are removed from objects."""
        opts = RecoveryOptions(handle_undefined="remove")
        assert parse(input_json, opts) == expected

    def test_undefined_remove_in_array(self):
        """Test undefined handling in arrays with remove option.

        In arrays, undefined should become null (can't remove array elements).
        """
        opts = RecoveryOptions(handle_undefined="remove")
        # Arrays can't have elements removed, so undefined becomes null
        assert parse("[1, undefined, 3]", opts) == "[1, null, 3]"

    def test_undefined_error(self):
        """Test that undefined raises error with error option."""
        opts = RecoveryOptions(handle_undefined="error")
        with pytest.raises(SloppyJSONDecodeError):
            parse('{"key": undefined}', opts)

    def test_undefined_default_is_null(self):
        """Test that default handling of undefined is null."""
        assert parse('{"key": undefined}', RecoveryOptions()) == '{"key": null}'


class TestNaN:
    """Tests for handling NaN values."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            ('{"key": NaN}', '{"key": null}'),
            ('{"a": 1, "b": NaN}', '{"a": 1, "b": null}'),
            ("[1, NaN, 3]", "[1, null, 3]"),
            ("[NaN]", "[null]"),
            ('{"nested": {"val": NaN}}', '{"nested": {"val": null}}'),
        ],
    )
    def test_nan_as_null(self, input_json: str, expected: str):
        """Test that NaN is converted to null."""
        opts = RecoveryOptions(handle_nan="null")
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            ('{"key": NaN}', '{"key": "NaN"}'),
            ("[NaN]", '["NaN"]'),
            ("[1, NaN, 3]", '[1, "NaN", 3]'),
            ('{"a": NaN, "b": NaN}', '{"a": "NaN", "b": "NaN"}'),
        ],
    )
    def test_nan_as_string(self, input_json: str, expected: str):
        """Test that NaN is converted to string "NaN"."""
        opts = RecoveryOptions(handle_nan="string")
        assert parse(input_json, opts) == expected

    def test_nan_error(self):
        """Test that NaN raises error with error option."""
        opts = RecoveryOptions(handle_nan="error")
        with pytest.raises(SloppyJSONDecodeError):
            parse('{"key": NaN}', opts)

    def test_nan_default_is_string(self):
        """Test that default handling of NaN is string."""
        assert parse('{"key": NaN}', RecoveryOptions()) == '{"key": "NaN"}'


class TestInfinity:
    """Tests for handling Infinity values."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            ('{"key": Infinity}', '{"key": null}'),
            ('{"key": -Infinity}', '{"key": null}'),
            ("[Infinity, -Infinity]", "[null, null]"),
            ('{"a": Infinity, "b": -Infinity}', '{"a": null, "b": null}'),
            ("[1, Infinity, 3]", "[1, null, 3]"),
            ('{"nested": {"val": Infinity}}', '{"nested": {"val": null}}'),
        ],
    )
    def test_infinity_as_null(self, input_json: str, expected: str):
        """Test that Infinity/-Infinity is converted to null."""
        opts = RecoveryOptions(handle_infinity="null")
        assert parse(input_json, opts) == expected

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            ('{"key": Infinity}', '{"key": "Infinity"}'),
            ('{"key": -Infinity}', '{"key": "-Infinity"}'),
            ("[Infinity, -Infinity]", '["Infinity", "-Infinity"]'),
            ("[1, Infinity, -Infinity, 4]", '[1, "Infinity", "-Infinity", 4]'),
        ],
    )
    def test_infinity_as_string(self, input_json: str, expected: str):
        """Test that Infinity/-Infinity is converted to string."""
        opts = RecoveryOptions(handle_infinity="string")
        assert parse(input_json, opts) == expected

    def test_infinity_error(self):
        """Test that Infinity raises error with error option."""
        opts = RecoveryOptions(handle_infinity="error")
        with pytest.raises(SloppyJSONDecodeError):
            parse('{"key": Infinity}', opts)
        with pytest.raises(SloppyJSONDecodeError):
            parse('{"key": -Infinity}', opts)

    def test_infinity_default_is_string(self):
        """Test that default handling of Infinity is string."""
        assert parse('{"key": Infinity}', RecoveryOptions()) == '{"key": "Infinity"}'
        assert parse('{"key": -Infinity}', RecoveryOptions()) == '{"key": "-Infinity"}'


class TestMixedSpecialValues:
    """Tests for combinations of special values."""

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # All special values together
            (
                '{"a": undefined, "b": NaN, "c": Infinity}',
                '{"a": null, "b": null, "c": null}',
            ),
            ("[undefined, NaN, Infinity, -Infinity]", "[null, null, null, null]"),
        ],
    )
    def test_all_special_as_null(self, input_json: str, expected: str):
        """Test handling all special values as null."""
        opts = RecoveryOptions(handle_undefined="null", handle_nan="null", handle_infinity="null")
        assert parse(input_json, opts) == expected

    def test_mixed_strategies(self):
        """Test different strategies for different special values."""
        input_json = '{"a": undefined, "b": NaN, "c": Infinity}'
        opts = RecoveryOptions(
            handle_undefined="remove", handle_nan="string", handle_infinity="null"
        )
        assert parse(input_json, opts) == '{"b": "NaN", "c": null}'

    @pytest.mark.parametrize(
        "input_json,expected",
        [
            # With regular values
            (
                '{"num": 42, "undef": undefined, "nan": NaN, "inf": Infinity, "str": "hello"}',
                '{"num": 42, "undef": null, "nan": null, "inf": null, "str": "hello"}',
            ),
        ],
    )
    def test_special_with_regular_values(self, input_json: str, expected: str):
        """Test special values mixed with regular JSON values."""
        opts = RecoveryOptions(handle_undefined="null", handle_nan="null", handle_infinity="null")
        assert parse(input_json, opts) == expected

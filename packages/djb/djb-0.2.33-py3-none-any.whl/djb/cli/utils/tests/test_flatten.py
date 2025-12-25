"""Tests for djb.cli.utils.flatten module."""

from __future__ import annotations

from djb.cli.utils.flatten import flatten_dict


class TestFlattenDict:
    """Tests for flatten_dict function."""

    def test_empty_dict(self):
        """Test flattening empty dict."""
        result = flatten_dict({})
        assert result == {}

    def test_flat_dict(self):
        """Test flattening already flat dict."""
        result = flatten_dict({"key": "value", "other": "data"})
        assert result == {"KEY": "value", "OTHER": "data"}

    def test_nested_dict(self):
        """Test flattening nested dict."""
        result = flatten_dict({"db": {"host": "localhost", "port": 5432}})
        assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}

    def test_deeply_nested_dict(self):
        """Test flattening deeply nested dict."""
        result = flatten_dict({"a": {"b": {"c": "value"}}})
        assert result == {"A_B_C": "value"}

    def test_mixed_nesting(self):
        """Test flattening dict with mixed nesting levels."""
        result = flatten_dict(
            {
                "simple": "value",
                "nested": {"key": "data"},
                "deep": {"level1": {"level2": "deep_value"}},
            }
        )
        assert result == {
            "SIMPLE": "value",
            "NESTED_KEY": "data",
            "DEEP_LEVEL1_LEVEL2": "deep_value",
        }

    def test_converts_non_string_values(self):
        """Test converts non-string values to strings."""
        result = flatten_dict({"count": 42, "enabled": True, "ratio": 3.14})
        assert result == {"COUNT": "42", "ENABLED": "True", "RATIO": "3.14"}

    def test_uppercase_keys(self):
        """Test all keys are uppercased."""
        result = flatten_dict({"mixedCase": "value", "UPPER": "data", "lower": "test"})
        assert result == {"MIXEDCASE": "value", "UPPER": "data", "LOWER": "test"}

    def test_none_value(self):
        """Test that None values are converted to 'None' string."""
        result = flatten_dict({"key": None})
        assert result == {"KEY": "None"}

    def test_empty_string_value(self):
        """Test that empty string values are preserved."""
        result = flatten_dict({"key": ""})
        assert result == {"KEY": ""}

    def test_empty_nested_dict(self):
        """Test that empty nested dict produces no output for that branch."""
        result = flatten_dict({"outer": {"inner": {}}, "other": "value"})
        assert result == {"OTHER": "value"}

    def test_keys_with_underscores(self):
        """Test that keys with underscores are handled correctly."""
        result = flatten_dict({"my_key": "value", "nested": {"sub_key": "data"}})
        assert result == {"MY_KEY": "value", "NESTED_SUB_KEY": "data"}

    def test_keys_with_dashes(self):
        """Test that keys with dashes are preserved (not converted to underscores)."""
        result = flatten_dict({"my-key": "value"})
        assert result == {"MY-KEY": "value"}

    def test_keys_with_dots(self):
        """Test that keys with dots are preserved."""
        result = flatten_dict({"my.key": "value"})
        assert result == {"MY.KEY": "value"}

    def test_numeric_values_various_types(self):
        """Test various numeric types are converted correctly."""
        result = flatten_dict({"int": 42, "float": 3.14, "negative": -5, "zero": 0})
        assert result == {"INT": "42", "FLOAT": "3.14", "NEGATIVE": "-5", "ZERO": "0"}

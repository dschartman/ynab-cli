"""Tests for utility functions."""

import json

from ynab_cli.utils import convert_monetary_fields, sanitize_string


class TestSanitizeString:
    """Tests for sanitize_string function."""

    def test_clean_string_unchanged(self):
        """Clean strings pass through unmodified."""
        assert sanitize_string("Hello world") == "Hello world"

    def test_preserves_newlines(self):
        """Newlines are preserved (json.dumps handles them)."""
        assert sanitize_string("line1\nline2") == "line1\nline2"

    def test_preserves_tabs(self):
        """Tabs are preserved (json.dumps handles them)."""
        assert sanitize_string("col1\tcol2") == "col1\tcol2"

    def test_preserves_carriage_returns(self):
        """Carriage returns are preserved (json.dumps handles them)."""
        assert sanitize_string("line1\r\nline2") == "line1\r\nline2"

    def test_removes_null_bytes(self):
        """Null bytes are removed."""
        assert sanitize_string("hello\x00world") == "helloworld"

    def test_removes_bell_character(self):
        """Bell character (\\x07) is removed."""
        assert sanitize_string("hello\x07world") == "helloworld"

    def test_removes_backspace(self):
        """Backspace character (\\x08) is removed."""
        assert sanitize_string("hello\x08world") == "helloworld"

    def test_removes_vertical_tab(self):
        """Vertical tab (\\x0b) is removed."""
        assert sanitize_string("hello\x0bworld") == "helloworld"

    def test_removes_form_feed(self):
        """Form feed (\\x0c) is removed."""
        assert sanitize_string("hello\x0cworld") == "helloworld"

    def test_removes_multiple_control_chars(self):
        """Multiple different control characters are all removed."""
        assert sanitize_string("a\x00b\x01c\x02d") == "abcd"

    def test_empty_string(self):
        """Empty string returns empty string."""
        assert sanitize_string("") == ""

    def test_only_control_chars(self):
        """String of only control chars returns empty string."""
        assert sanitize_string("\x00\x01\x02\x03") == ""


class TestConvertMonetaryFieldsSanitization:
    """Tests for string sanitization within convert_monetary_fields."""

    def test_sanitizes_string_values_in_dict(self):
        """String values in dicts are sanitized."""
        data = {"note": "budget\x00note\x07here"}
        result = convert_monetary_fields(data)
        assert result["note"] == "budgetnotehere"

    def test_sanitizes_nested_strings(self):
        """Strings nested in dicts/lists are sanitized."""
        data = {"categories": [{"name": "test\x00cat", "note": "line1\nline2\x0bextra"}]}
        result = convert_monetary_fields(data)
        assert result["categories"][0]["name"] == "testcat"
        assert result["categories"][0]["note"] == "line1\nline2extra"

    def test_sanitized_output_produces_valid_json(self):
        """Output with sanitized strings produces valid JSON."""
        data = {
            "note": "Category notes\x00with\x07control\x0bchars\nand newlines",
            "budgeted": 250000,
        }
        result = convert_monetary_fields(data)
        # This should not raise JSONDecodeError
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        assert parsed["note"] == "Category noteswithcontrolchars\nand newlines"
        assert parsed["budgeted"] == 250.0

    def test_monetary_conversion_still_works(self):
        """Monetary field conversion is unaffected by string sanitization."""
        data = {"budgeted": 250000, "activity": -100000, "name": "Test"}
        result = convert_monetary_fields(data)
        assert result["budgeted"] == 250.0
        assert result["activity"] == -100.0
        assert result["name"] == "Test"

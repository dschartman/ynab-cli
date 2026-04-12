"""Tests for utility functions."""

import json

from ynab_cli.utils import convert_monetary_fields, sanitize_string


class TestSanitizeString:
    """Tests for sanitize_string function."""

    def test_clean_string_unchanged(self):
        """Clean strings pass through unmodified."""
        assert sanitize_string("Hello world") == "Hello world"

    def test_removes_newlines(self):
        """Newlines are removed so they never appear raw in JSON string values."""
        assert sanitize_string("line1\nline2") == "line1line2"

    def test_removes_tabs(self):
        """Tabs are removed so they never appear raw in JSON string values."""
        assert sanitize_string("col1\tcol2") == "col1col2"

    def test_removes_carriage_returns(self):
        """Carriage returns are removed so they never appear raw in JSON string values."""
        assert sanitize_string("line1\r\nline2") == "line1line2"

    def test_removes_all_control_chars_including_whitespace_controls(self):
        """All control characters 0x00-0x1f are removed, including \\t, \\n, \\r."""
        # Build a string with every control character in range 0x00-0x1f
        all_controls = "".join(chr(i) for i in range(0x20))
        result = sanitize_string(f"a{all_controls}b")
        assert result == "ab"

    def test_json_output_is_valid_when_note_has_raw_newlines(self):
        """Strings with raw newlines produce valid JSON when serialized."""
        import json

        # Raw newline inside a JSON string literal is invalid per the JSON spec.
        # sanitize_string must remove it so json.dumps output is always valid.
        note_with_raw_newline = "budget note\nwith a newline"
        cleaned = sanitize_string(note_with_raw_newline)
        json_str = json.dumps({"note": cleaned})
        # Confirm the JSON is parse-able and the value contains no raw newline
        parsed = json.loads(json_str)
        assert "\n" not in parsed["note"]

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
        # \n and \x0b are both stripped
        assert result["categories"][0]["note"] == "line1line2extra"

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
        # All control chars including \n are stripped
        assert parsed["note"] == "Category noteswithcontrolcharsand newlines"
        assert parsed["budgeted"] == 250.0

    def test_monetary_conversion_still_works(self):
        """Monetary field conversion is unaffected by string sanitization."""
        data = {"budgeted": 250000, "activity": -100000, "name": "Test"}
        result = convert_monetary_fields(data)
        assert result["budgeted"] == 250.0
        assert result["activity"] == -100.0
        assert result["name"] == "Test"


class TestGoalTypeNameEnrichment:
    """Tests for goal_type_name enrichment in convert_monetary_fields."""

    def test_adds_goal_type_name_for_known_types(self):
        """Known goal types get a human-readable name added."""
        data = {"goal_type": "MF", "name": "Electric"}
        result = convert_monetary_fields(data)
        assert result["goal_type"] == "MF"
        assert result["goal_type_name"] == "Monthly Funding"

    def test_all_known_goal_types(self):
        """All known goal types are mapped."""
        expected = {
            "MF": "Monthly Funding",
            "NEED": "Plan Your Spending",
            "TBD": "Target by Date",
            "TB": "Target Balance",
            "DEBT": "Debt Payoff",
        }
        for code, name in expected.items():
            result = convert_monetary_fields({"goal_type": code})
            assert result["goal_type_name"] == name

    def test_no_goal_type_name_for_none(self):
        """No goal_type_name added when goal_type is None."""
        data = {"goal_type": None, "name": "Test"}
        result = convert_monetary_fields(data)
        assert "goal_type_name" not in result

    def test_no_goal_type_name_for_unknown_code(self):
        """No goal_type_name added for unrecognized codes."""
        data = {"goal_type": "UNKNOWN"}
        result = convert_monetary_fields(data)
        assert "goal_type_name" not in result

    def test_no_goal_type_name_when_no_goal_type_field(self):
        """No goal_type_name added when goal_type field is absent."""
        data = {"name": "Test", "budgeted": 100000}
        result = convert_monetary_fields(data)
        assert "goal_type_name" not in result

    def test_nested_categories_get_goal_type_name(self):
        """goal_type_name is added to nested category dicts."""
        data = {
            "categories": [
                {"name": "Electric", "goal_type": "MF", "budgeted": 150000},
                {"name": "Vacation", "goal_type": "TBD", "budgeted": 200000},
                {"name": "No Goal", "goal_type": None, "budgeted": 0},
            ]
        }
        result = convert_monetary_fields(data)
        assert result["categories"][0]["goal_type_name"] == "Monthly Funding"
        assert result["categories"][1]["goal_type_name"] == "Target by Date"
        assert "goal_type_name" not in result["categories"][2]

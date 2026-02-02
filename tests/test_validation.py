"""Tests for input validation."""

import pytest

from ynab_cli.validation import (
    ValidationError,
    validate_amount,
    validate_date,
    validate_uuid,
)


class TestValidateDate:
    """Tests for date validation."""

    def test_valid_date_format(self):
        """Should accept valid YYYY-MM-DD format."""
        assert validate_date("2025-01-15") == "2025-01-15"
        assert validate_date("2024-12-31") == "2024-12-31"

    def test_invalid_date_format_raises_error(self):
        """Should raise ValidationError for invalid format."""
        with pytest.raises(ValidationError, match="date.*YYYY-MM-DD"):
            validate_date("01/15/2025")

        with pytest.raises(ValidationError, match="date.*YYYY-MM-DD"):
            validate_date("2025-1-15")

        with pytest.raises(ValidationError, match="date.*YYYY-MM-DD"):
            validate_date("15-01-2025")

    def test_invalid_date_values_raises_error(self):
        """Should raise ValidationError for invalid date values."""
        with pytest.raises(ValidationError, match="Invalid date"):
            validate_date("2025-13-01")  # Month 13

        with pytest.raises(ValidationError, match="Invalid date"):
            validate_date("2025-02-30")  # Feb 30th

    def test_empty_date_raises_error(self):
        """Should raise ValidationError for empty date."""
        with pytest.raises(ValidationError):
            validate_date("")


class TestValidateAmount:
    """Tests for amount validation."""

    def test_valid_positive_amount(self):
        """Should accept valid positive amounts."""
        assert validate_amount("10.50") == 10.50
        assert validate_amount("100") == 100.0
        assert validate_amount("0.01") == 0.01

    def test_valid_negative_amount(self):
        """Should accept valid negative amounts."""
        assert validate_amount("-10.50") == -10.50
        assert validate_amount("-100") == -100.0

    def test_valid_zero_amount(self):
        """Should accept zero."""
        assert validate_amount("0") == 0.0
        assert validate_amount("0.00") == 0.0

    def test_too_many_decimal_places_raises_error(self):
        """Should raise ValidationError for more than 2 decimal places."""
        with pytest.raises(ValidationError, match="two decimal places"):
            validate_amount("10.123")

        with pytest.raises(ValidationError, match="two decimal places"):
            validate_amount("1.999")

    def test_invalid_amount_format_raises_error(self):
        """Should raise ValidationError for non-numeric input."""
        with pytest.raises(ValidationError, match="valid number"):
            validate_amount("abc")

        with pytest.raises(ValidationError, match="valid number"):
            validate_amount("$10.50")

    def test_empty_amount_raises_error(self):
        """Should raise ValidationError for empty amount."""
        with pytest.raises(ValidationError):
            validate_amount("")


class TestValidateUUID:
    """Tests for UUID validation."""

    def test_valid_uuid(self):
        """Should accept valid UUID format."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert validate_uuid(valid_uuid) == valid_uuid

    def test_valid_uuid_uppercase(self):
        """Should accept valid UUID in uppercase."""
        valid_uuid = "550E8400-E29B-41D4-A716-446655440000"
        assert validate_uuid(valid_uuid) == valid_uuid

    def test_special_values_allowed(self):
        """Should accept special YNAB budget ID values."""
        assert validate_uuid("last-used") == "last-used"
        assert validate_uuid("default") == "default"

    def test_invalid_uuid_format_raises_error(self):
        """Should raise ValidationError for invalid UUID format."""
        with pytest.raises(ValidationError, match="UUID"):
            validate_uuid("not-a-uuid")

        with pytest.raises(ValidationError, match="UUID"):
            validate_uuid("123")

        with pytest.raises(ValidationError, match="UUID"):
            validate_uuid("550e8400e29b41d4a716446655440000")  # Missing dashes

    def test_empty_uuid_raises_error(self):
        """Should raise ValidationError for empty UUID."""
        with pytest.raises(ValidationError):
            validate_uuid("")

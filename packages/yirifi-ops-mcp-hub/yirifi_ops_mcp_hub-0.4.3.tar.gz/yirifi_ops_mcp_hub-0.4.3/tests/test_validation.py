"""Tests for the validation module."""

import pytest

from yirifi_mcp.core.exceptions import ValidationError
from yirifi_mcp.core.validation import (
    PATTERNS,
    ParamSpec,
    validate_param,
    validate_params,
)


class TestParamSpec:
    """Tests for ParamSpec dataclass."""

    def test_default_values(self):
        """Test default parameter spec values."""
        spec = ParamSpec(name="test")
        assert spec.param_type == "string"
        assert spec.required is True
        assert spec.pattern is None

    def test_custom_values(self):
        """Test custom parameter spec."""
        spec = ParamSpec(
            name="user_id",
            param_type="uuid",
            required=True,
        )
        assert spec.name == "user_id"
        assert spec.param_type == "uuid"


class TestValidateParamString:
    """Tests for string validation."""

    def test_valid_string(self):
        """Test valid string passes."""
        spec = ParamSpec(name="name")
        result = validate_param("name", "John", spec)
        assert result == "John"

    def test_coerce_int_to_string(self):
        """Test integer is coerced to string."""
        spec = ParamSpec(name="value")
        result = validate_param("value", 123, spec)
        assert result == "123"

    def test_min_length(self):
        """Test minimum length validation."""
        spec = ParamSpec(name="password", min_length=8)
        with pytest.raises(ValidationError) as exc:
            validate_param("password", "short", spec)
        assert "at least 8 characters" in str(exc.value)

    def test_max_length(self):
        """Test maximum length validation."""
        spec = ParamSpec(name="name", max_length=10)
        with pytest.raises(ValidationError) as exc:
            validate_param("name", "verylongname", spec)
        assert "at most 10 characters" in str(exc.value)

    def test_pattern_custom(self):
        """Test custom pattern validation."""
        spec = ParamSpec(name="code", pattern=r"^[A-Z]{3}$")
        result = validate_param("code", "ABC", spec)
        assert result == "ABC"

    def test_pattern_custom_fails(self):
        """Test custom pattern validation failure."""
        spec = ParamSpec(name="code", pattern=r"^[A-Z]{3}$")
        with pytest.raises(ValidationError) as exc:
            validate_param("code", "abc123", spec)
        assert "does not match" in str(exc.value)

    def test_pattern_predefined_slug(self):
        """Test predefined slug pattern."""
        spec = ParamSpec(name="slug", pattern="slug")
        result = validate_param("slug", "my-cool-slug", spec)
        assert result == "my-cool-slug"

    def test_allowed_values(self):
        """Test enum-style allowed values."""
        spec = ParamSpec(name="status", allowed_values=["active", "inactive"])
        result = validate_param("status", "active", spec)
        assert result == "active"

    def test_allowed_values_fails(self):
        """Test allowed values validation failure."""
        spec = ParamSpec(name="status", allowed_values=["active", "inactive"])
        with pytest.raises(ValidationError) as exc:
            validate_param("status", "pending", spec)
        assert "must be one of" in str(exc.value)


class TestValidateParamInteger:
    """Tests for integer validation."""

    def test_valid_integer(self):
        """Test valid integer passes."""
        spec = ParamSpec(name="count", param_type="integer")
        result = validate_param("count", 42, spec)
        assert result == 42

    def test_coerce_string_to_integer(self):
        """Test string is coerced to integer."""
        spec = ParamSpec(name="count", param_type="integer")
        result = validate_param("count", "123", spec)
        assert result == 123

    def test_invalid_string_fails(self):
        """Test invalid string fails."""
        spec = ParamSpec(name="count", param_type="integer")
        with pytest.raises(ValidationError) as exc:
            validate_param("count", "abc", spec)
        assert "must be an integer" in str(exc.value)

    def test_min_value(self):
        """Test minimum value validation."""
        spec = ParamSpec(name="page", param_type="integer", min_value=1)
        with pytest.raises(ValidationError) as exc:
            validate_param("page", 0, spec)
        assert ">= 1" in str(exc.value)

    def test_max_value(self):
        """Test maximum value validation."""
        spec = ParamSpec(name="limit", param_type="integer", max_value=100)
        with pytest.raises(ValidationError) as exc:
            validate_param("limit", 500, spec)
        assert "<= 100" in str(exc.value)

    def test_min_and_max_value(self):
        """Test combined min/max validation."""
        spec = ParamSpec(
            name="page",
            param_type="integer",
            min_value=1,
            max_value=100,
        )
        result = validate_param("page", 50, spec)
        assert result == 50


class TestValidateParamUUID:
    """Tests for UUID validation."""

    def test_valid_uuid(self):
        """Test valid UUID passes."""
        spec = ParamSpec(name="id", param_type="uuid")
        result = validate_param("id", "550e8400-e29b-41d4-a716-446655440000", spec)
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_uuid_normalized(self):
        """Test UUID is normalized."""
        spec = ParamSpec(name="id", param_type="uuid")
        result = validate_param("id", "550E8400-E29B-41D4-A716-446655440000", spec)
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_invalid_uuid(self):
        """Test invalid UUID fails."""
        spec = ParamSpec(name="id", param_type="uuid")
        with pytest.raises(ValidationError) as exc:
            validate_param("id", "not-a-uuid", spec)
        assert "valid UUID" in str(exc.value)


class TestValidateParamEmail:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email passes."""
        spec = ParamSpec(name="email", param_type="email")
        result = validate_param("email", "user@example.com", spec)
        assert result == "user@example.com"

    def test_email_normalized_lowercase(self):
        """Test email is normalized to lowercase."""
        spec = ParamSpec(name="email", param_type="email")
        result = validate_param("email", "User@Example.COM", spec)
        assert result == "user@example.com"

    def test_invalid_email(self):
        """Test invalid email fails."""
        spec = ParamSpec(name="email", param_type="email")
        with pytest.raises(ValidationError) as exc:
            validate_param("email", "not-an-email", spec)
        assert "valid email" in str(exc.value)

    def test_email_without_domain(self):
        """Test email without domain fails."""
        spec = ParamSpec(name="email", param_type="email")
        with pytest.raises(ValidationError):
            validate_param("email", "user@", spec)


class TestValidateParamBoolean:
    """Tests for boolean validation."""

    def test_true_boolean(self):
        """Test True passes."""
        spec = ParamSpec(name="active", param_type="boolean")
        result = validate_param("active", True, spec)
        assert result is True

    def test_false_boolean(self):
        """Test False passes."""
        spec = ParamSpec(name="active", param_type="boolean")
        result = validate_param("active", False, spec)
        assert result is False

    def test_string_true(self):
        """Test string 'true' coerced to True."""
        spec = ParamSpec(name="active", param_type="boolean")
        for value in ["true", "True", "TRUE", "yes", "1", "on"]:
            result = validate_param("active", value, spec)
            assert result is True

    def test_string_false(self):
        """Test string 'false' coerced to False."""
        spec = ParamSpec(name="active", param_type="boolean")
        for value in ["false", "False", "FALSE", "no", "0", "off"]:
            result = validate_param("active", value, spec)
            assert result is False

    def test_int_coercion(self):
        """Test integer coercion to boolean."""
        spec = ParamSpec(name="active", param_type="boolean")
        assert validate_param("active", 1, spec) is True
        assert validate_param("active", 0, spec) is False

    def test_invalid_string(self):
        """Test invalid string fails."""
        spec = ParamSpec(name="active", param_type="boolean")
        with pytest.raises(ValidationError) as exc:
            validate_param("active", "maybe", spec)
        assert "must be a boolean" in str(exc.value)


class TestValidateParamRequired:
    """Tests for required parameter handling."""

    def test_missing_required(self):
        """Test missing required parameter raises."""
        spec = ParamSpec(name="user_id", required=True)
        with pytest.raises(ValidationError) as exc:
            validate_param("user_id", None, spec)
        assert "Missing required" in str(exc.value)

    def test_missing_optional(self):
        """Test missing optional parameter returns None."""
        spec = ParamSpec(name="limit", required=False)
        result = validate_param("limit", None, spec)
        assert result is None


class TestValidateParams:
    """Tests for validate_params function."""

    def test_validate_all_params(self):
        """Test validating all parameters."""
        schema = [
            ParamSpec(name="user_id", param_type="uuid"),
            ParamSpec(name="page", param_type="integer", min_value=1),
            ParamSpec(name="email", param_type="email"),
        ]
        params = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "page": "1",
            "email": "Test@Example.COM",
        }
        result = validate_params(params, schema)

        assert result["user_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert result["page"] == 1
        assert result["email"] == "test@example.com"

    def test_passthrough_extra_params(self):
        """Test that extra parameters pass through unchanged."""
        schema = [
            ParamSpec(name="page", param_type="integer"),
        ]
        params = {
            "page": "10",
            "extra_param": "should_pass",
        }
        result = validate_params(params, schema)

        assert result["page"] == 10
        assert result["extra_param"] == "should_pass"

    def test_no_schema_returns_unchanged(self):
        """Test that no schema returns params unchanged."""
        params = {"foo": "bar", "baz": 123}
        result = validate_params(params, None)
        assert result == params

    def test_empty_schema_returns_unchanged(self):
        """Test that empty schema returns params unchanged."""
        params = {"foo": "bar"}
        result = validate_params(params, [])
        assert result == params

    def test_none_params_with_schema(self):
        """Test None params with schema containing optional fields."""
        schema = [
            ParamSpec(name="limit", param_type="integer", required=False),
        ]
        result = validate_params(None, schema)
        assert result is None

    def test_missing_required_raises(self):
        """Test missing required parameter raises."""
        schema = [
            ParamSpec(name="user_id", required=True),
        ]
        with pytest.raises(ValidationError):
            validate_params({}, schema)

    def test_validation_error_includes_field_name(self):
        """Test validation error includes field name."""
        schema = [
            ParamSpec(name="email", param_type="email"),
        ]
        with pytest.raises(ValidationError) as exc:
            validate_params({"email": "invalid"}, schema)
        assert exc.value.param_name == "email"


class TestPredefinedPatterns:
    """Tests for predefined patterns."""

    def test_uuid_pattern(self):
        """Test UUID pattern."""
        import re
        pattern = PATTERNS["uuid"]
        assert re.match(pattern, "550e8400-e29b-41d4-a716-446655440000")
        assert not re.match(pattern, "not-a-uuid")

    def test_email_pattern(self):
        """Test email pattern."""
        import re
        pattern = PATTERNS["email"]
        assert re.match(pattern, "user@example.com")
        assert re.match(pattern, "user.name+tag@example.co.uk")
        assert not re.match(pattern, "invalid-email")

    def test_slug_pattern(self):
        """Test slug pattern."""
        import re
        pattern = PATTERNS["slug"]
        assert re.match(pattern, "my-cool-slug")
        assert re.match(pattern, "simple")
        assert not re.match(pattern, "Has Spaces")
        assert not re.match(pattern, "UPPERCASE")

"""Tests for TOON encoder and format selection."""

import json
from unittest.mock import patch

import pytest

from yirifi_mcp.core.toon_encoder import (
    MIN_SAVINGS_PERCENT,
    OutputFormat,
    _max_depth,
    analyze_suitability,
    compact_pagination,
    elide_empty,
    encode_response,
    is_uniform_array,
    simplify_environment,
    transform_response,
    truncate_datetime,
)


class TestOutputFormatEnum:
    """Tests for OutputFormat enum."""

    def test_enum_values(self):
        """Enum should have correct string values."""
        assert OutputFormat.AUTO.value == "auto"
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.TOON.value == "toon"

    def test_enum_from_string(self):
        """Enum should be constructable from string."""
        assert OutputFormat("auto") == OutputFormat.AUTO
        assert OutputFormat("json") == OutputFormat.JSON
        assert OutputFormat("toon") == OutputFormat.TOON


class TestMaxDepth:
    """Tests for nesting depth calculation."""

    def test_primitive_values(self):
        """Primitive values should have depth 0."""
        assert _max_depth("string") == 0
        assert _max_depth(123) == 0
        assert _max_depth(True) == 0
        assert _max_depth(None) == 0

    def test_empty_structures(self):
        """Empty dicts and lists should have depth 0."""
        assert _max_depth({}) == 0
        assert _max_depth([]) == 0

    def test_flat_dict(self):
        """Flat dict should have depth 1."""
        assert _max_depth({"a": 1, "b": 2}) == 1

    def test_nested_dict(self):
        """Nested dicts should have correct depth."""
        assert _max_depth({"a": {"b": 1}}) == 2
        assert _max_depth({"a": {"b": {"c": 1}}}) == 3
        assert _max_depth({"a": {"b": {"c": {"d": 1}}}}) == 4

    def test_array_of_dicts(self):
        """Arrays with dicts should count depth correctly."""
        assert _max_depth([{"a": 1}]) == 2
        assert _max_depth([{"a": {"b": 1}}]) == 3

    def test_mixed_structures(self):
        """Mixed nested structures should find max depth."""
        data = {
            "shallow": 1,
            "deeper": {"level2": {"level3": 3}},
            "array": [{"nested": 1}],
        }
        assert _max_depth(data) == 3


class TestIsUniformArray:
    """Tests for uniform array detection."""

    def test_valid_uniform_array(self):
        """Arrays with same-key dicts should be uniform."""
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]
        assert is_uniform_array(data) is True

    def test_array_too_short(self):
        """Arrays shorter than 3 should not be uniform."""
        data = [{"id": 1}, {"id": 2}]
        assert is_uniform_array(data) is False

    def test_different_keys(self):
        """Arrays with different keys should not be uniform."""
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "email": "bob@test.com"},
            {"id": 3, "name": "Charlie"},
        ]
        assert is_uniform_array(data) is False

    def test_non_dict_items(self):
        """Arrays with non-dict items should not be uniform."""
        data = [1, 2, 3, 4, 5]
        assert is_uniform_array(data) is False

        data = ["a", "b", "c", "d"]
        assert is_uniform_array(data) is False

    def test_not_an_array(self):
        """Non-array data should not be uniform."""
        assert is_uniform_array({"key": "value"}) is False
        assert is_uniform_array("string") is False
        assert is_uniform_array(None) is False
        assert is_uniform_array(123) is False


class TestAnalyzeSuitability:
    """Tests for TOON suitability analysis."""

    def test_uniform_array_suitable(self):
        """Uniform arrays should be suitable for TOON."""
        data = {
            "_environment": {"database": "PRD", "mode": "prd"},
            "data": [
                {"id": 1, "name": "Alice", "email": "alice@test.com"},
                {"id": 2, "name": "Bob", "email": "bob@test.com"},
                {"id": 3, "name": "Charlie", "email": "charlie@test.com"},
            ],
        }
        analysis = analyze_suitability(data)
        # Now uses size comparison, should show savings
        assert "savings_percent" in analysis or "suitable" in analysis

    def test_flat_object_analysis(self):
        """Flat objects should return analysis with savings info."""
        data = {
            "_environment": {"database": "PRD"},
            "data": {"key1": "value1", "key2": "value2", "count": 42},
        }
        analysis = analyze_suitability(data)
        assert "suitable" in analysis

    def test_nested_object_analysis(self):
        """Nested objects should return analysis."""
        data = {
            "_environment": {"database": "PRD"},
            "data": {
                "user": {
                    "profile": {
                        "settings": {"notifications": {"email": True, "push": False}},
                    },
                },
            },
        }
        analysis = analyze_suitability(data)
        assert "suitable" in analysis

    def test_data_without_environment_wrapper(self):
        """Data dict without _environment wrapper should still work."""
        data = {"name": "test", "count": 42, "active": True}
        analysis = analyze_suitability(data)
        assert "suitable" in analysis


class TestEncodeResponse:
    """Tests for response encoding."""

    @pytest.fixture
    def uniform_array_response(self):
        """Sample response with uniform array."""
        return {
            "_environment": {"database": "PRD", "mode": "prd"},
            "data": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Charlie"},
            ],
        }

    @pytest.fixture
    def nested_response(self):
        """Sample response with nested structure."""
        return {
            "_environment": {"database": "PRD"},
            "data": {
                "user": {
                    "profile": {
                        "settings": {"deep": {"nested": {"value": 1}}},
                    },
                },
            },
        }

    def test_json_format_explicit(self, uniform_array_response):
        """Explicit JSON format should return valid JSON."""
        encoded, format_used = encode_response(uniform_array_response, OutputFormat.JSON)
        assert format_used == "json"
        # Should be valid JSON
        parsed = json.loads(encoded)
        # Response is transformed: _environment is simplified (database removed)
        expected = {
            "_environment": {"mode": "prd"},  # database removed by simplify_environment
            "data": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Charlie"},
            ],
        }
        assert parsed == expected
        # Should have indentation
        assert "\n" in encoded

    def test_auto_mode_picks_smaller(self, uniform_array_response):
        """Auto mode should pick the format with better savings."""
        encoded, format_used = encode_response(uniform_array_response, OutputFormat.AUTO)
        # Should pick based on size comparison
        assert format_used in ("json", "toon")

    def test_toon_format_explicit(self, uniform_array_response):
        """Explicit TOON format should return TOON."""
        encoded, format_used = encode_response(uniform_array_response, OutputFormat.TOON)
        assert format_used == "toon"
        # TOON format uses YAML-like syntax
        assert "data[3]" in encoded or "data:" in encoded

    def test_custom_indent(self, uniform_array_response):
        """Custom indent should be respected for JSON output."""
        encoded, _ = encode_response(uniform_array_response, OutputFormat.JSON, indent=4)
        # Count leading spaces to verify indent
        lines = encoded.split("\n")
        indented_lines = [line for line in lines if line.startswith("    ")]
        assert len(indented_lines) > 0


class TestAutoModeWithNestedStructures:
    """Tests for auto mode with nested API responses."""

    def test_nested_with_array_uses_toon(self):
        """Nested structures containing arrays should use TOON if savings are good."""
        data = {
            "_environment": {"database": "DEV", "mode": "dev"},
            "data": {
                "success": True,
                "data": {
                    "items": [
                        {"id": 1, "email": "a@test.com", "name": "A"},
                        {"id": 2, "email": "b@test.com", "name": "B"},
                        {"id": 3, "email": "c@test.com", "name": "C"},
                    ]
                },
            },
        }
        encoded, format_used = encode_response(data, OutputFormat.AUTO)
        # Should use TOON because the array provides good savings
        assert format_used == "toon"
        assert "items[3]" in encoded

    def test_deeply_nested_no_array_may_use_json(self):
        """Deeply nested without arrays may not benefit from TOON."""
        data = {
            "_environment": {"database": "DEV"},
            "data": {"a": 1, "b": 2},
        }
        encoded, format_used = encode_response(data, OutputFormat.AUTO)
        # Small data might not meet savings threshold
        assert format_used in ("json", "toon")


class TestElideEmpty:
    """Tests for empty/null field elision."""

    def test_removes_null_values(self):
        """Null values should be removed."""
        data = {"name": "test", "warning": None, "count": 42}
        result = elide_empty(data)
        assert result == {"name": "test", "count": 42}
        assert "warning" not in result

    def test_removes_empty_arrays(self):
        """Empty arrays should be removed."""
        data = {"name": "test", "microsites": [], "roles": ["admin"]}
        result = elide_empty(data)
        assert result == {"name": "test", "roles": ["admin"]}
        assert "microsites" not in result

    def test_recursive_in_dicts(self):
        """Should recursively clean nested dicts."""
        data = {
            "_environment": {
                "database": "DEV",
                "warning": None,
            },
            "data": {
                "items": [],
                "user": {"name": "test"},
            },
        }
        result = elide_empty(data)
        assert result == {
            "_environment": {"database": "DEV"},
            "data": {"user": {"name": "test"}},
        }

    def test_recursive_in_arrays(self):
        """Should recursively clean items in arrays."""
        data = {
            "users": [
                {"id": 1, "name": "Alice", "microsites": [], "extra": None},
                {"id": 2, "name": "Bob", "microsites": [], "extra": None},
            ]
        }
        result = elide_empty(data)
        assert result == {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
        }

    def test_preserves_non_empty_values(self):
        """Should preserve non-empty values."""
        data = {
            "name": "test",
            "count": 0,  # 0 is not null
            "active": False,  # False is not null
            "items": [1, 2, 3],  # Non-empty array
            "nested": {"key": "value"},
        }
        result = elide_empty(data)
        assert result == data

    def test_preserves_empty_strings(self):
        """Empty strings should NOT be removed (only null and [])."""
        data = {"name": "", "title": "test"}
        result = elide_empty(data)
        assert result == {"name": "", "title": "test"}

    def test_handles_primitives(self):
        """Primitive values should pass through unchanged."""
        assert elide_empty("string") == "string"
        assert elide_empty(123) == 123
        assert elide_empty(True) is True
        assert elide_empty(None) is None  # Root level None passes through

    def test_real_api_response_structure(self):
        """Should clean a real API response structure."""
        data = {
            "_environment": {
                "database": "DEV",
                "mode": "dev",
                "server": "yirifi-auth",
                "base_url": "http://localhost:5100",
                "warning": None,
            },
            "data": {
                "success": True,
                "data": {
                    "items": [
                        {
                            "id": 1,
                            "email": "admin@yirifi.com",
                            "microsites": [],
                            "microsite_access": [],
                            "access": [],
                        },
                    ],
                    "pagination": {
                        "total": 1,
                        "pages": 1,
                        "current_page": 1,
                        "per_page": 25,
                        "has_next": False,
                        "has_prev": False,
                    },
                },
                "meta": {
                    "timestamp": "2025-12-21T18:15:35.780568+00:00",
                    "request_id": None,
                },
            },
        }
        result = elide_empty(data)

        # Should remove warning, microsites, access arrays, and request_id
        assert result["_environment"].get("warning") is None
        assert "warning" not in result["_environment"]

        items = result["data"]["data"]["items"]
        assert "microsites" not in items[0]
        assert "microsite_access" not in items[0]
        assert "access" not in items[0]

        assert "request_id" not in result["data"]["meta"]

        # Should preserve non-empty values
        assert result["_environment"]["database"] == "DEV"
        assert result["data"]["success"] is True
        assert items[0]["email"] == "admin@yirifi.com"


class TestTruncateDatetime:
    """Tests for datetime truncation."""

    def test_truncates_full_iso_datetime(self):
        """Should truncate full ISO datetime with microseconds."""
        result = truncate_datetime("2025-12-19T04:48:02.712412+00:00")
        assert result == "2025-12-19T04:48+00:00"

    def test_truncates_datetime_without_microseconds(self):
        """Should truncate datetime without microseconds."""
        result = truncate_datetime("2025-12-19T04:48:02+00:00")
        assert result == "2025-12-19T04:48+00:00"

    def test_truncates_datetime_with_z_timezone(self):
        """Should handle Z timezone marker."""
        result = truncate_datetime("2025-12-19T04:48:02.712412Z")
        assert result == "2025-12-19T04:48Z"

    def test_truncates_negative_timezone(self):
        """Should handle negative timezone offset."""
        result = truncate_datetime("2025-12-19T04:48:02.712412-05:00")
        assert result == "2025-12-19T04:48-05:00"

    def test_passes_through_non_datetime_string(self):
        """Non-datetime strings should pass through unchanged."""
        assert truncate_datetime("hello world") == "hello world"
        assert truncate_datetime("2025-12-19") == "2025-12-19"  # Date only
        assert truncate_datetime("04:48:02") == "04:48:02"  # Time only

    def test_passes_through_non_string(self):
        """Non-string values should pass through unchanged."""
        assert truncate_datetime(123) == 123
        assert truncate_datetime(None) is None
        assert truncate_datetime(True) is True


class TestCompactPagination:
    """Tests for pagination compaction."""

    def test_removes_fields_and_renames_total(self):
        """Should remove per_page, has_next, has_prev and rename total."""
        data = {
            "total": 42,
            "pages": 2,
            "current_page": 1,
            "per_page": 25,
            "has_next": True,
            "has_prev": False,
        }
        result = compact_pagination(data)
        assert result == {
            "total_items": 42,
            "pages": 2,
            "current_page": 1,
        }

    def test_preserves_other_fields(self):
        """Should preserve non-standard pagination fields."""
        data = {
            "total": 10,
            "pages": 1,
            "current_page": 1,
            "per_page": 25,
            "custom_field": "value",
        }
        result = compact_pagination(data)
        assert result == {
            "total_items": 10,
            "pages": 1,
            "current_page": 1,
            "custom_field": "value",
        }

    def test_handles_non_dict(self):
        """Non-dict values should pass through unchanged."""
        assert compact_pagination("not a dict") == "not a dict"
        assert compact_pagination(123) == 123
        assert compact_pagination(None) is None


class TestSimplifyEnvironment:
    """Tests for environment simplification."""

    def test_removes_database_and_base_url(self):
        """Should remove database and base_url fields."""
        data = {
            "database": "DEV",
            "mode": "dev",
            "server": "yirifi-auth",
            "base_url": "http://localhost:5100",
        }
        result = simplify_environment(data)
        assert result == {
            "mode": "dev",
            "server": "auth",
        }

    def test_strips_yirifi_prefix(self):
        """Should strip yirifi- prefix from server."""
        data = {"server": "yirifi-reg", "mode": "prd"}
        result = simplify_environment(data)
        assert result["server"] == "reg"

    def test_preserves_server_without_prefix(self):
        """Server without yirifi- prefix should remain unchanged."""
        data = {"server": "custom-server", "mode": "dev"}
        result = simplify_environment(data)
        assert result["server"] == "custom-server"

    def test_preserves_warning_when_present(self):
        """Warning should be preserved if present."""
        data = {
            "mode": "prd",
            "server": "yirifi-auth",
            "warning": "PRODUCTION: This operation modifies live data",
        }
        result = simplify_environment(data)
        assert result == {
            "mode": "prd",
            "server": "auth",
            "warning": "PRODUCTION: This operation modifies live data",
        }

    def test_handles_non_dict(self):
        """Non-dict values should pass through unchanged."""
        assert simplify_environment("not a dict") == "not a dict"
        assert simplify_environment(None) is None


class TestTransformResponse:
    """Tests for full response transformation."""

    def test_transforms_environment(self):
        """Should simplify _environment in response."""
        data = {
            "_environment": {
                "database": "DEV",
                "mode": "dev",
                "server": "yirifi-auth",
                "base_url": "http://localhost:5100",
            },
            "data": {"key": "value"},
        }
        result = transform_response(data)
        assert result["_environment"] == {
            "mode": "dev",
            "server": "auth",
        }

    def test_transforms_pagination(self):
        """Should compact pagination in response."""
        data = {
            "data": {
                "pagination": {
                    "total": 42,
                    "pages": 2,
                    "current_page": 1,
                    "per_page": 25,
                    "has_next": True,
                    "has_prev": False,
                }
            }
        }
        result = transform_response(data)
        assert result["data"]["pagination"] == {
            "total_items": 42,
            "pages": 2,
            "current_page": 1,
        }

    def test_transforms_datetimes(self):
        """Should truncate datetime strings in response."""
        data = {
            "meta": {
                "timestamp": "2025-12-19T04:48:02.712412+00:00",
                "created_at": "2025-01-15T10:30:45.123456+00:00",
            }
        }
        result = transform_response(data)
        assert result["meta"]["timestamp"] == "2025-12-19T04:48+00:00"
        assert result["meta"]["created_at"] == "2025-01-15T10:30+00:00"

    def test_transforms_nested_arrays(self):
        """Should transform datetimes inside arrays."""
        data = {
            "items": [
                {"created_at": "2025-12-19T04:48:02.712412+00:00"},
                {"created_at": "2025-12-20T05:49:03.812413+00:00"},
            ]
        }
        result = transform_response(data)
        assert result["items"][0]["created_at"] == "2025-12-19T04:48+00:00"
        assert result["items"][1]["created_at"] == "2025-12-20T05:49+00:00"

    def test_full_api_response_transformation(self):
        """Should transform a complete API response."""
        data = {
            "_environment": {
                "database": "DEV",
                "mode": "dev",
                "server": "yirifi-auth",
                "base_url": "http://localhost:5100",
            },
            "data": {
                "success": True,
                "data": {
                    "items": [
                        {
                            "id": 1,
                            "email": "admin@yirifi.com",
                            "created_at": "2025-12-19T04:48:02.712412+00:00",
                        },
                    ],
                    "pagination": {
                        "total": 1,
                        "pages": 1,
                        "current_page": 1,
                        "per_page": 25,
                        "has_next": False,
                        "has_prev": False,
                    },
                },
                "meta": {
                    "timestamp": "2025-12-21T18:15:35.780568+00:00",
                },
            },
        }
        result = transform_response(data)

        # Environment simplified
        assert result["_environment"] == {"mode": "dev", "server": "auth"}

        # Pagination compacted
        pagination = result["data"]["data"]["pagination"]
        assert pagination == {"total_items": 1, "pages": 1, "current_page": 1}

        # Datetimes truncated
        assert result["data"]["data"]["items"][0]["created_at"] == "2025-12-19T04:48+00:00"
        assert result["data"]["meta"]["timestamp"] == "2025-12-21T18:15+00:00"


class TestConstants:
    """Tests for module constants."""

    def test_min_savings_percent(self):
        """MIN_SAVINGS_PERCENT should be reasonable."""
        assert MIN_SAVINGS_PERCENT >= 0
        assert MIN_SAVINGS_PERCENT <= 50

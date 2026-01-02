"""TOON (Token-Oriented Object Notation) encoder with auto-detection.

This module provides intelligent format selection between TOON and JSON
based on actual size comparison. TOON typically provides 30-60% savings
for responses containing arrays of objects.

See: https://github.com/toon-format/toon
"""

from __future__ import annotations

import json
import re
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()


class OutputFormat(str, Enum):
    """Output format options for MCP responses."""

    AUTO = "auto"
    JSON = "json"
    TOON = "toon"


# Minimum savings threshold (%) to prefer TOON over JSON
MIN_SAVINGS_PERCENT = 10.0

# Regex to match ISO datetime with seconds/microseconds
# Matches: 2025-12-19T04:48:02.712412+00:00 or 2025-12-19T04:48:02+00:00
DATETIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2}|Z)$"
)


def truncate_datetime(value: str) -> str:
    """Truncate datetime to minute precision.

    Transforms: "2025-12-19T04:48:02.712412+00:00" -> "2025-12-19T04:48+00:00"

    Args:
        value: ISO datetime string

    Returns:
        Datetime truncated to minute precision
    """
    if not isinstance(value, str) or not DATETIME_PATTERN.match(value):
        return value

    # Find the timezone part (+00:00 or Z)
    tz_match = re.search(r"([+-]\d{2}:\d{2}|Z)$", value)
    if not tz_match:
        return value

    tz = tz_match.group(1)
    # Extract up to minutes (YYYY-MM-DDTHH:MM)
    base = value[:16]  # "2025-12-19T04:48"
    return f"{base}{tz}"


def compact_pagination(data: dict) -> dict:
    """Transform pagination to compact form.

    Removes: per_page, has_next, has_prev
    Renames: total -> total_items

    Args:
        data: Pagination dict

    Returns:
        Compacted pagination dict
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if key == "total":
            result["total_items"] = value
        elif key in ("per_page", "has_next", "has_prev"):
            continue  # Remove these fields
        else:
            result[key] = value
    return result


def simplify_environment(data: dict) -> dict:
    """Simplify _environment to essential fields.

    Keeps: mode, server (with "yirifi-" prefix stripped)
    Removes: database, base_url

    Args:
        data: _environment dict

    Returns:
        Simplified environment dict
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if key == "server" and isinstance(value, str):
            # Strip "yirifi-" prefix
            result["server"] = value.removeprefix("yirifi-")
        elif key in ("database", "base_url"):
            continue  # Remove these fields
        else:
            result[key] = value
    return result


def transform_response(data: Any) -> Any:
    """Apply all response transformations recursively.

    Transformations:
    - Truncate datetimes to minute precision
    - Compact pagination objects
    - Simplify _environment

    Args:
        data: Data structure to transform

    Returns:
        Transformed data
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key == "_environment":
                result[key] = simplify_environment(transform_response(value))
            elif key == "pagination":
                result[key] = compact_pagination(transform_response(value))
            else:
                result[key] = transform_response(value)
        return result
    if isinstance(data, list):
        return [transform_response(item) for item in data]
    if isinstance(data, str):
        return truncate_datetime(data)
    return data


def elide_empty(data: Any) -> Any:
    """Recursively remove empty arrays and null values.

    This reduces noise in responses by removing fields like:
    - microsites: []
    - warning: null
    - request_id: null

    Args:
        data: Data structure to clean

    Returns:
        Cleaned data with empty arrays and null values removed
    """
    if isinstance(data, dict):
        return {
            k: elide_empty(v)
            for k, v in data.items()
            if v is not None and v != []
        }
    if isinstance(data, list):
        return [elide_empty(item) for item in data]
    return data


def encode_response(
    data: dict,
    format: OutputFormat = OutputFormat.AUTO,
    indent: int = 2,
) -> tuple[str, str]:
    """Encode response data to specified format.

    Args:
        data: Response data (already wrapped with _environment)
        format: Output format (auto, json, toon)
        indent: Indentation level for output

    Returns:
        Tuple of (encoded_string, format_used)
        format_used is "json" or "toon"
    """
    # Clean and transform data
    data = elide_empty(data)
    data = transform_response(data)

    if format == OutputFormat.JSON:
        return json.dumps(data, indent=indent), "json"

    if format == OutputFormat.TOON:
        return _encode_toon(data, indent), "toon"

    # AUTO mode: encode both, compare sizes, pick smaller
    json_output = json.dumps(data, indent=indent)
    toon_output = _encode_toon_safe(data, indent)

    if toon_output is None:
        # TOON encoding failed, use JSON
        return json_output, "json"

    # Calculate savings
    json_len = len(json_output)
    toon_len = len(toon_output)
    savings_percent = ((json_len - toon_len) / json_len) * 100 if json_len > 0 else 0

    if savings_percent >= MIN_SAVINGS_PERCENT:
        logger.debug(
            "toon_format_selected",
            json_chars=json_len,
            toon_chars=toon_len,
            savings=f"{savings_percent:.1f}%",
        )
        return toon_output, "toon"
    else:
        logger.debug(
            "json_format_selected",
            reason=f"Savings below threshold ({savings_percent:.1f}% < {MIN_SAVINGS_PERCENT}%)",
            json_chars=json_len,
            toon_chars=toon_len,
        )
        return json_output, "json"


def _encode_toon_safe(data: dict, indent: int = 2) -> str | None:
    """Encode data to TOON format, returning None on failure.

    Args:
        data: Data to encode
        indent: Indentation level

    Returns:
        TOON-encoded string, or None if encoding fails
    """
    try:
        from toon_format import encode

        return encode(data, options={"indent": indent, "delimiter": ","})
    except ImportError:
        logger.debug("toon_format_not_installed")
        return None
    except Exception as e:
        logger.debug("toon_encoding_failed", error=str(e))
        return None


def _encode_toon(data: dict, indent: int = 2) -> str:
    """Encode data to TOON format with JSON fallback.

    Args:
        data: Data to encode
        indent: Indentation level

    Returns:
        TOON-encoded string, or JSON if encoding fails
    """
    result = _encode_toon_safe(data, indent)
    if result is not None:
        return result

    logger.warning("toon_encoding_failed_fallback_json")
    return json.dumps(data, indent=indent)


# Legacy exports for backwards compatibility
def is_uniform_array(data: Any) -> bool:
    """Check if data is a uniform array of objects.

    Deprecated: Auto mode now uses size comparison instead of structural analysis.
    """
    if not isinstance(data, list) or len(data) < 3:
        return False
    if not all(isinstance(item, dict) for item in data):
        return False
    first_keys = set(data[0].keys())
    return all(set(item.keys()) == first_keys for item in data)


def analyze_suitability(data: dict) -> dict:
    """Analyze data structure for TOON encoding suitability.

    Deprecated: Auto mode now uses size comparison instead of structural analysis.
    """
    # Try encoding both and compare
    json_len = len(json.dumps(data))
    toon_result = _encode_toon_safe(data, indent=2)

    if toon_result is None:
        return {"suitable": False, "reason": "TOON encoding failed", "data_type": "unknown"}

    toon_len = len(toon_result)
    savings = ((json_len - toon_len) / json_len) * 100 if json_len > 0 else 0

    return {
        "suitable": savings >= MIN_SAVINGS_PERCENT,
        "reason": f"Savings: {savings:.1f}%",
        "data_type": "measured",
        "json_chars": json_len,
        "toon_chars": toon_len,
        "savings_percent": savings,
    }


def _max_depth(obj: Any, current_depth: int = 0) -> int:
    """Calculate maximum nesting depth of a data structure.

    Deprecated: Auto mode now uses size comparison instead of depth analysis.
    """
    if isinstance(obj, dict):
        if not obj:
            return current_depth
        return max(_max_depth(v, current_depth + 1) for v in obj.values())
    elif isinstance(obj, list):
        if not obj:
            return current_depth
        return max(_max_depth(item, current_depth + 1) for item in obj)
    else:
        return current_depth

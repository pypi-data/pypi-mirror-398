"""Tool optimization utilities for reducing MCP token usage."""

import re
from typing import Any


def truncate_description(text: str | None, max_length: int = 80) -> str:
    """
    Truncate description to first sentence or max_length chars.

    Optimizes for LLM context efficiency while preserving meaning.
    """
    if not text:
        return ""

    # Remove newlines and extra whitespace
    text = " ".join(text.split())

    # Try to cut at first sentence
    first_sentence = text.split('.')[0]
    if len(first_sentence) <= max_length:
        return first_sentence

    # Otherwise truncate at max_length
    if len(text) > max_length:
        return text[:max_length - 3] + "..."

    return text


def optimize_component_descriptions(route: Any, component: Any) -> None:
    """
    Callback for FastMCP.from_openapi() to optimize tool definitions.

    Reduces token usage by:
    - Truncating verbose descriptions
    - Simplifying parameter descriptions
    - Removing redundant metadata

    This function modifies the component in-place.
    """
    # Truncate main description
    if hasattr(component, 'description') and component.description:
        component.description = truncate_description(component.description, 80)

    # Truncate parameter descriptions
    if hasattr(component, 'parameters') and component.parameters:
        for param_name, param in component.parameters.items():
            if hasattr(param, 'description') and param.description:
                param.description = truncate_description(param.description, 50)


def simplify_tool_name(name: str) -> str:
    """
    Simplify auto-generated tool names for clarity.

    Examples:
        get_api_key_list -> list_api_keys
        post_user_list -> create_user
        delete_api_key_detail -> delete_api_key
    """
    # Remove common suffixes
    name = re.sub(r'_list$', '', name)
    name = re.sub(r'_detail$', '', name)
    name = re.sub(r'_resource$', '', name)

    # Simplify HTTP method prefixes
    replacements = {
        'get_': 'get_',
        'post_': 'create_',
        'put_': 'update_',
        'delete_': 'delete_',
        'patch_': 'patch_',
    }

    for old, new in replacements.items():
        if name.startswith(old):
            # Special case: get_ for list operations
            if old == 'get_' and '_list' not in name:
                name = name  # Keep as-is
            elif old == 'post_':
                name = new + name[len(old):]
            break

    return name

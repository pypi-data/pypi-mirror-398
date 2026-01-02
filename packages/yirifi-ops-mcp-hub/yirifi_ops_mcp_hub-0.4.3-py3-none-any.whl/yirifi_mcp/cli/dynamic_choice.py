"""Dynamic service choice for Click CLI.

This module provides DynamicServiceChoice, a custom Click parameter type
that validates service names at runtime rather than decoration time.
This enables auto-discovery of services via entry points.
"""

import click


class DynamicServiceChoice(click.ParamType):
    """Click parameter type for dynamic service choices.

    This solves the problem that click.Choice needs values at decoration time,
    but we want to discover services dynamically from entry points.

    The validation happens at runtime when the CLI is invoked, not when
    the decorator is applied.

    Example:
        >>> @click.option(
        ...     "--service", "-s",
        ...     default="all",
        ...     type=DynamicServiceChoice(include_all=True),
        ...     help="Service to run",
        ... )
        ... def cli(service):
        ...     pass

    Attributes:
        include_all: Whether to include "all" as a valid choice
        _cached_names: Cache of service names to avoid repeated discovery
    """

    name = "service"

    def __init__(self, include_all: bool = True):
        """Initialize the dynamic choice.

        Args:
            include_all: If True, "all" is a valid choice meaning all services
        """
        self.include_all = include_all
        self._cached_names: list[str] | None = None

    def _get_available_services(self) -> list[str]:
        """Get list of available service names.

        Caches the result to avoid repeated discovery calls.

        Returns:
            Sorted list of service names
        """
        if self._cached_names is None:
            from yirifi_mcp.core.unified_registry import get_unified_registry

            registry = get_unified_registry()
            registry.discover()
            self._cached_names = registry.get_available_names()

        return self._cached_names

    def get_metavar(self, param) -> str:
        """Get the metavar for help text."""
        return "SERVICE"

    def convert(self, value, param, ctx):
        """Convert and validate the service name.

        Args:
            value: The value provided by the user
            param: The click parameter
            ctx: The click context

        Returns:
            The validated service name

        Raises:
            click.BadParameter: If the service name is invalid
        """
        # Handle special case
        if value == "all" and self.include_all:
            return value

        available = self._get_available_services()
        valid_choices = (["all"] if self.include_all else []) + available

        if value not in valid_choices:
            choices_str = ", ".join(valid_choices)
            self.fail(
                f"'{value}' is not a valid service. Choose from: {choices_str}",
                param,
                ctx,
            )

        return value

    def shell_complete(self, ctx, param, incomplete):
        """Provide shell completion for services.

        Args:
            ctx: The click context
            param: The click parameter
            incomplete: The incomplete string to complete

        Returns:
            List of completion items matching the incomplete string
        """
        available = self._get_available_services()
        choices = (["all"] if self.include_all else []) + available

        return [
            click.shell_completion.CompletionItem(name)
            for name in choices
            if name.startswith(incomplete)
        ]


def get_service_help_text(include_all: bool = True) -> str:
    """Generate help text listing available services.

    This is useful for providing dynamic help text that reflects
    the currently available services.

    Args:
        include_all: Whether to include "all" in the help text

    Returns:
        Help text string listing available services
    """
    from yirifi_mcp.core.unified_registry import get_unified_registry

    registry = get_unified_registry()
    registry.discover()

    names = registry.get_available_names()
    if include_all:
        choices = ["all"] + names
    else:
        choices = names

    return f"Service to use. Choices: {', '.join(choices)}"

"""Override configuration files for spec-driven catalogs.

This package contains minimal override configurations for each service.
These overrides are applied on top of OpenAPI spec when using SpecDrivenCatalog.

Usage:
    from yirifi_mcp.catalog.overrides.auth import (
        DIRECT_ENDPOINTS,
        EXCLUDE_PATTERNS,
        RISK_OVERRIDES,
    )

    factory = MCPServerFactory(
        config=config,
        tier_overrides={ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS},
        risk_overrides=RISK_OVERRIDES,
        exclude_patterns=EXCLUDE_PATTERNS,
    )
"""

"""API response schemas organized by domain.

This package contains external-facing API schemas with semantic field names
(test_id, product_id) used by MCP tools and REST endpoints.

Organization:
- shared.py: Cross-domain schemas (pagination, platform requirements)
- products.py: Product-related schemas
- features.py: Feature-related schemas
- bugs.py: Bug-related schemas
- tests.py: Test-related schemas and aggregates

All schemas are re-exported here for convenient imports:
    from testio_mcp.schemas.api import TestStatusOutput, ProductInfo
"""

# Shared schemas
# Bug schemas
from testio_mcp.schemas.api.bugs import BugListItem, BugSummary, ListBugsOutput

# Feature schemas
from testio_mcp.schemas.api.features import FeatureInfo

# Product schemas
from testio_mcp.schemas.api.products import ProductInfo, ProductInfoSummary
from testio_mcp.schemas.api.shared import PaginationInfo, PlatformRequirement

# Test schemas
from testio_mcp.schemas.api.tests import (
    ListTestsOutput,
    TestDetails,
    TestStatusOutput,
    TestSummary,
)

__all__ = [
    # Shared
    "PaginationInfo",
    "PlatformRequirement",
    # Products
    "ProductInfo",
    "ProductInfoSummary",
    # Features
    "FeatureInfo",
    # Bugs
    "BugSummary",
    "BugListItem",
    "ListBugsOutput",
    # Tests
    "TestSummary",
    "ListTestsOutput",
    "TestDetails",
    "TestStatusOutput",
]

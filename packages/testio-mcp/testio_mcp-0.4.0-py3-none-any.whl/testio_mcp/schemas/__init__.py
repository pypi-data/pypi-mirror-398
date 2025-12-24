"""Shared schemas for API responses and service layer contracts.

This module contains:
- Constants: Shared constants (status values, etc.)
- DTOs: Internal service layer representations (use database field names)
- API schemas: External API models (use semantic names like test_id)
  - Organized by domain in schemas/api/ (tests, products, features, bugs, shared)

Separation ensures clean boundaries and prevents layering violations.
"""

from testio_mcp.schemas.api import (
    BugSummary,
    FeatureInfo,
    ListTestsOutput,
    PaginationInfo,
    PlatformRequirement,
    ProductInfo,
    ProductInfoSummary,
    TestDetails,
    TestStatusOutput,
    TestSummary,
)
from testio_mcp.schemas.constants import EXECUTED_TEST_STATUSES, VALID_TEST_STATUSES, TestStatus
from testio_mcp.schemas.dtos import ServiceBugDTO, ServiceProductDTO, ServiceTestDTO

__all__ = [
    # Constants
    "VALID_TEST_STATUSES",
    "EXECUTED_TEST_STATUSES",
    "TestStatus",
    # DTOs (service layer)
    "ServiceTestDTO",
    "ServiceProductDTO",
    "ServiceBugDTO",
    # Test schemas (API layer)
    "TestSummary",
    "ProductInfoSummary",
    "PaginationInfo",
    "ListTestsOutput",
    "ProductInfo",
    "FeatureInfo",
    "PlatformRequirement",
    "TestDetails",
    "BugSummary",
    "TestStatusOutput",
]

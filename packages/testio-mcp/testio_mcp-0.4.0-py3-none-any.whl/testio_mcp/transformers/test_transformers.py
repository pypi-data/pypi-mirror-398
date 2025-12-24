"""Data transformers for converting service layer dicts to API models.

This module implements the Anti-Corruption Layer (ACL) pattern, translating
between internal service representations (using 'id') and external API contracts
(using semantic names like 'test_id', 'product_id').

Key Pattern:
    Service Layer (dict with 'id') → DTO validation → API Model ('test_id')

Type Safety:
    DTOs validate service layer data before transformation to catch schema
    mismatches early.
"""

from typing import Any

from testio_mcp.schemas.api import TestSummary
from testio_mcp.schemas.dtos import ServiceTestDTO


def to_test_summary(test: dict[str, Any]) -> TestSummary:
    """Transform service layer test dict to TestSummary model.

    Handles id → test_id mapping at transport boundary (ACL pattern).

    Args:
        test: Test dictionary from service layer (with 'id' field)

    Returns:
        TestSummary with semantic field names (test_id)

    Raises:
        ValidationError: If test dict doesn't match ServiceTestDTO schema

    Example:
        >>> service_test = {"id": 123, "title": "Login test", "status": "running", ...}
        >>> api_model = to_test_summary(service_test)
        >>> api_model.test_id  # 123 (semantic name)
    """
    # Validate with DTO for type safety
    dto = ServiceTestDTO(**test)

    return TestSummary(
        test_id=dto.id,
        title=dto.title,
        goal=dto.goal,
        status=dto.status,
        review_status=dto.review_status,
        testing_type=dto.testing_type,
        duration=dto.duration,
        starts_at=dto.starts_at,
        ends_at=dto.ends_at,
        test_environment=dto.test_environment,
    )


def to_test_summary_list(tests: list[dict[str, Any]]) -> list[TestSummary]:
    """Batch transform for list endpoints.

    Args:
        tests: List of test dicts from service layer

    Returns:
        List of TestSummary models

    Example:
        >>> service_tests = [{"id": 1, ...}, {"id": 2, ...}]
        >>> api_models = to_test_summary_list(service_tests)
        >>> len(api_models)  # 2
    """
    return [to_test_summary(test) for test in tests]

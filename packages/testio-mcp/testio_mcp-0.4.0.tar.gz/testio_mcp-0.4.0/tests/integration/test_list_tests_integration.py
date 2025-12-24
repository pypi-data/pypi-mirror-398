"""Integration tests for list_tests tool with real TestIO API.

Tests error handling with the complete flow: tool → service → repository → API.

These tests focus on integration concerns (API contracts, error handling) and
avoid testing business logic (covered by service tests).

Test Strategy:
- Error handling: Invalid product IDs, API failures
- API contract validation: Response structure (if needed)
- Business logic: Tested in tests/unit/test_test_service.py (~454 lines)

Usage:
    uv run pytest tests/integration/test_list_tests_integration.py -m integration
"""

import pytest

from testio_mcp.client import TestIOClient
from testio_mcp.config import settings
from testio_mcp.database import PersistentCache
from testio_mcp.exceptions import ProductNotFoundException
from testio_mcp.services.test_service import TestService


@pytest.mark.integration
@pytest.mark.skipif(
    settings.TESTIO_CUSTOMER_API_TOKEN == "test_token_placeholder",
    reason="Requires TESTIO_CUSTOMER_API_TOKEN environment variable",
)
@pytest.mark.asyncio
async def test_list_tests_invalid_product_id_raises_exception(
    shared_client: TestIOClient,
    shared_cache: PersistentCache,
    bug_repository,
) -> None:
    """Test error handling with invalid product ID (404).

    This test verifies that ProductNotFoundException is raised when the API
    returns a 404 for an invalid product ID.

    Integration concerns tested:
    - API error response handling
    - Exception propagation through service layer
    - Error transformation at service boundary

    Usage:
        uv run pytest -m integration
    """
    # Create service with real dependencies
    from testio_mcp.repositories.product_repository import ProductRepository

    async with shared_cache.async_session_maker() as session:
        product_repo = ProductRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        service = TestService(
            client=shared_client,
            test_repo=shared_cache.repo,
            bug_repo=bug_repository,
            product_repo=product_repo,
        )

        # Execute with invalid product ID (guaranteed not to exist)
        with pytest.raises(ProductNotFoundException) as exc_info:
            await service.list_tests(product_id=999999999, page=1, per_page=100, statuses=[])

        # Verify exception details
        assert exc_info.value.product_id == 999999999
        assert "999999999" in str(exc_info.value)

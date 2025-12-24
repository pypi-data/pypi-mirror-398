"""Unit tests for service registry (TD-002).

Tests the factory-based service registry pattern that eliminates if/elif ladders
and reduces boilerplate in service instantiation.

References:
    - docs/planning/tech-debt-remediation-plan.md (TD-002)
    - docs/planning/critical-tech-debt-implementation.md (Phase 2, Step 2.4)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from testio_mcp.services.analytics_service import AnalyticsService
from testio_mcp.services.base_service import BaseService
from testio_mcp.services.bug_service import BugService
from testio_mcp.services.diagnostics_service import DiagnosticsService
from testio_mcp.services.feature_service import FeatureService
from testio_mcp.services.multi_test_report_service import MultiTestReportService
from testio_mcp.services.product_service import ProductService
from testio_mcp.services.search_service import SearchService
from testio_mcp.services.sync_service import SyncService
from testio_mcp.services.test_service import TestService
from testio_mcp.services.user_service import UserService
from testio_mcp.services.user_story_service import UserStoryService
from testio_mcp.utilities.service_registry import build_service, get_service_registry


@pytest.mark.unit
def test_all_services_registered():
    """Verify all service classes have registry entries."""
    expected = {
        TestService,
        ProductService,
        BugService,
        FeatureService,
        UserService,
        UserStoryService,
        AnalyticsService,
        SearchService,
        DiagnosticsService,
        SyncService,
        MultiTestReportService,
    }

    assert set(get_service_registry().keys()) == expected


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_service_creates_valid_instance():
    """Verify registry builds working service instances."""
    # Create mocks
    mock_client = MagicMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    # Create a single mock session that will be returned by session_maker
    mock_session = AsyncMock()
    mock_session.close = AsyncMock()

    # Configure session_maker to return the SAME session instance
    mock_cache.async_session_maker = MagicMock(return_value=mock_session)

    async with build_service(FeatureService, mock_client, mock_cache) as service:
        assert isinstance(service, FeatureService)
        assert service.feature_repo is not None

    # Session should be closed after exiting context
    mock_session.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_service_closes_session():
    """Verify session is closed after context manager exits.

    FIXED (Codex review): Previous test created a different session instance
    than build_service() would use. Now we configure the mock to return a
    single session instance that we can verify.
    """
    # Create a single mock session that will be returned by session_maker
    mock_session = AsyncMock()
    mock_session.close = AsyncMock()

    # Create mocks
    mock_client = MagicMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    # Configure session_maker to return the SAME session instance
    mock_cache.async_session_maker = MagicMock(return_value=mock_session)

    async with build_service(FeatureService, mock_client, mock_cache):
        # Session should not be closed yet
        mock_session.close.assert_not_awaited()

    # After exiting context, session.close() should have been awaited
    mock_session.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_service_fails_fast_for_unregistered():
    """Verify unregistered services raise KeyError (no silent fallback)."""

    class UnregisteredService(BaseService):
        """Test service not in registry."""

        pass

    mock_client = MagicMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    with pytest.raises(KeyError, match="not in SERVICE_REGISTRY"):
        async with build_service(UnregisteredService, mock_client, mock_cache):
            pass


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_service_no_session_for_product_service():
    """Verify ProductService doesn't create a session (uses factory pattern)."""
    mock_client = MagicMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123
    mock_cache.async_session_maker = MagicMock()

    async with build_service(ProductService, mock_client, mock_cache) as service:
        assert isinstance(service, ProductService)
        # ProductService should NOT call async_session_maker directly
        # (it receives the factory itself)
        assert service.session_factory == mock_cache.async_session_maker


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_service_no_session_for_sync_service():
    """Verify SyncService doesn't create a session (manages internally)."""
    mock_client = MagicMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123
    mock_session = AsyncMock()
    mock_session.close = AsyncMock()
    mock_cache.async_session_maker = MagicMock(return_value=mock_session)

    async with build_service(SyncService, mock_client, mock_cache) as service:
        assert isinstance(service, SyncService)
        # SyncService manages its own sessions internally
        # session_maker should NOT be called by build_service
        mock_cache.async_session_maker.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_service_analytics_has_cache():
    """Verify AnalyticsService receives cache parameter (Codex fix)."""
    mock_client = MagicMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_session.close = AsyncMock()
    mock_cache.async_session_maker = MagicMock(return_value=mock_session)

    async with build_service(AnalyticsService, mock_client, mock_cache) as service:
        assert isinstance(service, AnalyticsService)
        assert service.cache == mock_cache  # Codex: was missing cache

    mock_session.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_service_test_service_has_repos():
    """Verify TestService gets all required repositories."""
    mock_client = MagicMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_session.close = AsyncMock()
    mock_cache.async_session_maker = MagicMock(return_value=mock_session)

    async with build_service(TestService, mock_client, mock_cache) as service:
        assert isinstance(service, TestService)
        assert service.test_repo is not None
        assert service.bug_repo is not None
        assert service.product_repo is not None

    mock_session.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_service_closes_session_on_exception():
    """Verify session is closed even if an exception occurs during service usage."""
    mock_client = MagicMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_session.close = AsyncMock()

    # Configure session_maker to return the session
    mock_cache.async_session_maker = MagicMock(return_value=mock_session)

    # First call should succeed normally
    async with build_service(FeatureService, mock_client, mock_cache) as service:
        assert isinstance(service, FeatureService)

    # Session should be closed after normal exit
    mock_session.close.assert_awaited_once()

    # Second call - simulate exception during usage
    mock_session.close.reset_mock()
    with pytest.raises(RuntimeError, match="Simulated error"):
        async with build_service(FeatureService, mock_client, mock_cache) as service:
            # Simulate an error happening during service usage
            raise RuntimeError("Simulated error")

    # Session should still be closed even after exception
    mock_session.close.assert_awaited_once()

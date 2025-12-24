"""Unit tests for service_helpers.

Verifies dependency injection and resource management logic.
Specifically tests the AsyncSession lifecycle management in get_service_context.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastmcp import Context

from testio_mcp.services.diagnostics_service import DiagnosticsService
from testio_mcp.services.test_service import TestService
from testio_mcp.utilities.service_helpers import get_service_context


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_cache(mock_session):
    cache = MagicMock()
    cache.customer_id = 123
    cache.async_session_maker = MagicMock(return_value=mock_session)
    return cache


@pytest.fixture
def mock_ctx(mock_cache):
    ctx = MagicMock(spec=Context)
    ctx.request_context = MagicMock()
    ctx.request_context.lifespan_context = {"testio_client": AsyncMock(), "cache": mock_cache}
    return ctx


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_service_context_closes_session(mock_ctx, mock_session):
    """Verify session is closed after context manager exits."""

    # Use TestService which requires a session
    async with get_service_context(mock_ctx, TestService) as service:
        assert isinstance(service, TestService)
        # Session should be created but not closed yet
        mock_ctx.request_context.lifespan_context["cache"].async_session_maker.assert_called_once()
        mock_session.close.assert_not_called()

    # Session should be closed after exit
    mock_session.close.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_service_context_closes_session_on_error(mock_ctx, mock_session):
    """Verify session is closed even if exception occurs."""

    with pytest.raises(ValueError):
        async with get_service_context(mock_ctx, TestService):
            raise ValueError("Test error")

    # Session should be closed despite exception
    mock_session.close.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_service_context_no_session_for_simple_service(mock_ctx, mock_session):
    """Verify no session created for services that don't need it (e.g., DiagnosticsService)."""

    # DiagnosticsService doesn't need a session (manages own connections)
    async with get_service_context(mock_ctx, DiagnosticsService) as service:
        assert isinstance(service, DiagnosticsService)
        # Session maker should NOT be called
        mock_ctx.request_context.lifespan_context["cache"].async_session_maker.assert_not_called()

    # Session close should NOT be called
    mock_session.close.assert_not_called()

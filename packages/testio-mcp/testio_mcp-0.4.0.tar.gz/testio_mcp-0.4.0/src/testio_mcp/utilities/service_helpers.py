"""Helper functions for service instantiation with dependency injection.

This module provides utilities to reduce boilerplate in MCP tool implementations
by centralizing the dependency extraction and service instantiation pattern.

TD-002: Refactored to use registry-based factory pattern (service_registry.py)
to eliminate if/elif ladders and reduce boilerplate.

STORY-023f: Added _build_service() and get_service_from_server_context() to support
both MCP tools and REST endpoints with shared service construction logic.
"""

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, cast

from fastmcp import Context

from testio_mcp.services.base_service import BaseService
from testio_mcp.utilities.service_registry import build_service

if TYPE_CHECKING:
    from testio_mcp.server import ServerContext


@asynccontextmanager
async def get_service_context[ServiceT: BaseService](
    ctx: Context, service_class: type[ServiceT]
) -> AsyncIterator[ServiceT]:
    """Create service with proper AsyncSession lifecycle (context manager pattern).

    Uses factory-based registry for consistent, maintainable service creation (TD-002).

    Args:
        ctx: FastMCP context (injected automatically by framework)
        service_class: Service class to instantiate (must inherit BaseService)

    Yields:
        Service instance with injected dependencies and managed AsyncSession

    Example:
        >>> @mcp.tool()
        >>> async def my_tool(param: str, ctx: Context) -> dict:
        ...     async with get_service_context(ctx, MyService) as service:
        ...         return await service.my_method(param)
        ...     # Session automatically closed here

    Type Safety:
        >>> async with get_service_context(ctx, TestService) as service:
        ...     result = await service.get_test_status(123)  # type-checked!

    Note:
        This replaces get_service() for MCP tools to fix resource leak (STORY-033).
        The session is guaranteed to be closed even if an exception occurs.
    """
    # Extract dependencies from lifespan context (ADR-007)
    assert ctx.request_context is not None, "Context must be available in tool execution"
    server_ctx = cast("ServerContext", ctx.request_context.lifespan_context)

    client = server_ctx["testio_client"]
    cache = server_ctx["cache"]

    async with build_service(service_class, client, cache) as service:
        yield service


@asynccontextmanager
async def get_service_context_from_server_context[ServiceT: BaseService](
    server_ctx: "ServerContext", service_class: type[ServiceT]
) -> AsyncGenerator[ServiceT, None]:
    """Create service instance from ServerContext with proper session cleanup.

    Uses factory-based registry for consistent, maintainable service creation (TD-002).

    Use this in REST endpoints to prevent SQLAlchemy warnings about unclosed connections.

    Args:
        server_ctx: Server context with testio_client and cache
        service_class: Service class to instantiate (must inherit BaseService)

    Yields:
        Service instance with injected dependencies

    Example:
        >>> @api.get("/api/tests/{test_id}")
        >>> async def get_test_rest(test_id: int, request: Request):
        ...     server_ctx = get_server_context_from_request(request)
        ...     async with get_service_context_from_server_context(
        ...         server_ctx, TestService
        ...     ) as service:
        ...         return await service.get_test_status(test_id)

    Type Safety:
        >>> async with get_service_context_from_server_context(
        ...     server_ctx, TestService
        ... ) as service:
        ...     result = await service.get_test_status(123)  # type-checked!
    """
    client = server_ctx["testio_client"]
    cache = server_ctx["cache"]

    async with build_service(service_class, client, cache) as service:
        yield service

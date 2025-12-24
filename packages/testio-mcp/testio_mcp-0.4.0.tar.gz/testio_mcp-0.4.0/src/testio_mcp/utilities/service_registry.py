"""Service registry for factory-based service instantiation.

This module implements TD-002 (Service Instantiation Boilerplate remediation)
using a registry-based factory pattern to eliminate if/elif ladders and reduce
boilerplate when creating service instances.

Pattern:
    1. Each service has a ServiceConfig entry in SERVICE_REGISTRY
    2. ServiceConfig specifies whether session is needed and provides a factory function
    3. build_service() uses the registry to create services with proper lifecycle management
    4. Fail-fast on unregistered services (no silent fallback)

References:
    - docs/planning/tech-debt-remediation-plan.md (TD-002)
    - docs/planning/critical-tech-debt-implementation.md (Phase 2)
"""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.services.base_service import BaseService

if TYPE_CHECKING:
    from testio_mcp.database.cache import PersistentCache

# Type alias for service factory functions
# Parameters: session, client, cache, customer_id
ServiceFactory = Callable[
    [AsyncSession | None, TestIOClient, "PersistentCache", int],
    BaseService,
]


@dataclass
class ServiceConfig:
    """Factory-based service configuration.

    Attributes:
        needs_session: Whether to create an AsyncSession before calling factory
        factory: Callable that creates the fully-configured service instance
    """

    needs_session: bool
    factory: ServiceFactory


def _build_test_service(
    session: AsyncSession | None,
    client: TestIOClient,
    cache: "PersistentCache",
    customer_id: int,
) -> "BaseService":
    """Factory for TestService with proper repo wiring.

    CRITICAL: UserRepository must be created first and passed to
    TestRepository/BugRepository for user extraction (STORY-036).
    """
    # Import here to avoid circular imports
    from testio_mcp.repositories.bug_repository import BugRepository
    from testio_mcp.repositories.product_repository import ProductRepository
    from testio_mcp.repositories.test_repository import TestRepository
    from testio_mcp.repositories.user_repository import UserRepository
    from testio_mcp.services.test_service import TestService

    assert session is not None
    user_repo = UserRepository(session=session, client=client, customer_id=customer_id)
    test_repo = TestRepository(
        session=session,
        client=client,
        customer_id=customer_id,
        user_repo=user_repo,
        cache=cache,
    )
    bug_repo = BugRepository(
        session=session,
        client=client,
        customer_id=customer_id,
        user_repo=user_repo,
        cache=cache,
    )
    product_repo = ProductRepository(session=session, client=client, customer_id=customer_id)
    return TestService(
        client=client,
        test_repo=test_repo,
        bug_repo=bug_repo,
        product_repo=product_repo,
    )


def _build_bug_service(
    session: AsyncSession | None,
    client: TestIOClient,
    cache: "PersistentCache",
    customer_id: int,
) -> "BaseService":
    """Factory for BugService with proper repo wiring."""
    # Import here to avoid circular imports
    from testio_mcp.repositories.bug_repository import BugRepository
    from testio_mcp.repositories.test_repository import TestRepository
    from testio_mcp.repositories.user_repository import UserRepository
    from testio_mcp.services.bug_service import BugService

    assert session is not None
    user_repo = UserRepository(session=session, client=client, customer_id=customer_id)
    bug_repo = BugRepository(
        session=session,
        client=client,
        customer_id=customer_id,
        user_repo=user_repo,
        cache=cache,
    )
    test_repo = TestRepository(
        session=session,
        client=client,
        customer_id=customer_id,
        user_repo=user_repo,
        cache=cache,
    )
    return BugService(client=client, bug_repo=bug_repo, test_repo=test_repo)


def _build_multi_test_report_service(
    session: AsyncSession | None,
    client: TestIOClient,
    cache: "PersistentCache",
    customer_id: int,
) -> "BaseService":
    """Factory for MultiTestReportService with proper repo wiring."""
    # Import here to avoid circular imports
    from testio_mcp.repositories.bug_repository import BugRepository
    from testio_mcp.repositories.product_repository import ProductRepository
    from testio_mcp.repositories.test_repository import TestRepository
    from testio_mcp.repositories.user_repository import UserRepository
    from testio_mcp.services.multi_test_report_service import MultiTestReportService

    assert session is not None
    user_repo = UserRepository(session=session, client=client, customer_id=customer_id)
    test_repo = TestRepository(
        session=session,
        client=client,
        customer_id=customer_id,
        user_repo=user_repo,
        cache=cache,
    )
    bug_repo = BugRepository(
        session=session,
        client=client,
        customer_id=customer_id,
        user_repo=user_repo,
        cache=cache,
    )
    product_repo = ProductRepository(session=session, client=client, customer_id=customer_id)
    return MultiTestReportService(
        client=client,
        test_repo=test_repo,
        bug_repo=bug_repo,
        product_repo=product_repo,
    )


def _get_service_registry() -> dict[type[BaseService], ServiceConfig]:
    """Build service registry with lazy imports to avoid circular dependencies.

    Returns:
        Dictionary mapping service classes to their configuration
    """
    # Import here to avoid circular imports at module load time
    from testio_mcp.repositories.feature_repository import FeatureRepository
    from testio_mcp.repositories.search_repository import SearchRepository
    from testio_mcp.repositories.user_repository import UserRepository
    from testio_mcp.services.analytics_service import AnalyticsService
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

    return {
        # Complex services with inter-repo dependencies
        TestService: ServiceConfig(
            needs_session=True,
            factory=_build_test_service,
        ),
        MultiTestReportService: ServiceConfig(
            needs_session=True,
            factory=_build_multi_test_report_service,
        ),
        BugService: ServiceConfig(
            needs_session=True,
            factory=_build_bug_service,
        ),
        # Simple services with single repo (no inter-dependencies)
        FeatureService: ServiceConfig(
            needs_session=True,
            factory=lambda s, c, cache, cid: FeatureService(
                feature_repo=FeatureRepository(s, c, cid)  # type: ignore[arg-type]
            ),
        ),
        UserStoryService: ServiceConfig(
            needs_session=True,
            factory=lambda s, c, cache, cid: UserStoryService(
                feature_repo=FeatureRepository(s, c, cid)  # type: ignore[arg-type]
            ),
        ),
        UserService: ServiceConfig(
            needs_session=True,
            factory=lambda s, c, cache, cid: UserService(
                user_repo=UserRepository(s, c, cid)  # type: ignore[arg-type]
            ),
        ),
        SearchService: ServiceConfig(
            needs_session=True,
            factory=lambda s, c, cache, cid: SearchService(
                search_repo=SearchRepository(s, c, cid)  # type: ignore[arg-type]
            ),
        ),
        # AnalyticsService: needs session + cache (Codex fix: was missing cache)
        AnalyticsService: ServiceConfig(
            needs_session=True,
            factory=lambda s, c, cache, cid: AnalyticsService(
                session=s,  # type: ignore[arg-type]
                customer_id=cid,
                client=c,
                cache=cache,
            ),
        ),
        # ProductService: uses session factory pattern (no session needed)
        ProductService: ServiceConfig(
            needs_session=False,
            factory=lambda s, c, cache, cid: ProductService(
                client=c,
                cache=cache,
                session_factory=cache.async_session_maker,
                customer_id=cid,
            ),
        ),
        # Default client+cache services (manage own sessions internally)
        DiagnosticsService: ServiceConfig(
            needs_session=False,
            factory=lambda s, c, cache, cid: DiagnosticsService(client=c, cache=cache),
        ),
        SyncService: ServiceConfig(
            needs_session=False,
            factory=lambda s, c, cache, cid: SyncService(client=c, cache=cache),
        ),
    }


# Lazily initialized registry (cached after first access)
_SERVICE_REGISTRY_CACHE: dict[type[BaseService], ServiceConfig] | None = None


def _get_registry() -> dict[type[BaseService], ServiceConfig]:
    """Get service registry (cached for performance)."""
    global _SERVICE_REGISTRY_CACHE
    if _SERVICE_REGISTRY_CACHE is None:
        _SERVICE_REGISTRY_CACHE = _get_service_registry()
    return _SERVICE_REGISTRY_CACHE


@asynccontextmanager
async def build_service[T: BaseService](
    service_class: type[T],
    client: TestIOClient,
    cache: "PersistentCache",
) -> AsyncIterator[T]:
    """Generic service builder using registry configuration.

    Args:
        service_class: Service class to instantiate
        client: TestIO API client
        cache: Persistent cache with session maker

    Yields:
        Configured service instance

    Raises:
        KeyError: If service not in registry (fail-fast, no silent fallback)
    """
    # FAIL-FAST: Require explicit registration (Codex recommendation)
    registry = _get_registry()
    if service_class not in registry:
        raise KeyError(
            f"Service {service_class.__name__} not in SERVICE_REGISTRY. "
            "Add an explicit ServiceConfig entry to register this service."
        )

    config = registry[service_class]
    session: AsyncSession | None = None
    customer_id = cache.customer_id

    try:
        # Create session if needed
        if config.needs_session:
            assert cache.async_session_maker is not None
            session = cache.async_session_maker()

        # Call factory with all dependencies
        service = config.factory(session, client, cache, customer_id)
        yield service  # type: ignore[misc]

    finally:
        # CRITICAL: Always close session to prevent resource leak
        if session is not None:
            await session.close()


# Export registry getter for external use (tests, documentation)
def get_service_registry() -> dict[type[BaseService], ServiceConfig]:
    """Get the service registry (for tests and introspection).

    Returns:
        Dictionary mapping service classes to their configuration
    """
    return _get_registry()

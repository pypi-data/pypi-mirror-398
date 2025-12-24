"""Base service class providing common patterns for all services.

This module provides the BaseService class for standard dependency injection.

STORY-023c: Simplified after removing in-memory cache. Services now use repositories
for data access instead of cache.get/set pattern.

Example:
    >>> class TestService(BaseService):
    ...     def __init__(
    ...         self,
    ...         client: TestIOClient,
    ...         test_repo: TestRepository,
    ...         bug_repo: BugRepository
    ...     ):
    ...         super().__init__(client)
    ...         self.test_repo = test_repo
    ...         self.bug_repo = bug_repo
"""

from testio_mcp.client import TestIOClient


class BaseService:
    """Base class for all service layer classes.

    Provides common dependency injection pattern.
    Services inject repositories for data access (STORY-023c).

    Attributes:
        client: TestIO API client for making HTTP requests
    """

    def __init__(self, client: TestIOClient) -> None:
        """Initialize service with API client.

        Args:
            client: TestIO API client for making HTTP requests
        """
        self.client = client

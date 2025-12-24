"""Product service for product listing and discovery operations.

This service handles business logic for product queries, following
the service layer pattern (ADR-006). It is framework-agnostic and can
be used from MCP tools, REST APIs, CLI, or webhooks.

STORY-023d: Simplified to product-only operations (list_tests moved to TestService).

Responsibilities:
- Product listing and filtering (search, product_type)
- Database query orchestration (local SQLite cache)
- Domain exception raising

Does NOT handle:
- MCP protocol formatting
- User-facing error messages
- HTTP transport concerns
- Test operations (now handled by TestService)
"""

import logging
from typing import Any

from testio_mcp.repositories.product_repository import ProductRepository
from testio_mcp.services.base_service import BaseService

logger = logging.getLogger(__name__)


class ProductService(BaseService):
    """Business logic for product operations.

    Uses ProductRepository for database persistence (STORY-032A).

    Example:
        ```python
        service = ProductService(
            client=client, cache=cache, session_factory=session_factory, customer_id=123
        )
        products = await service.list_products(search="studio")
        ```
    """

    def __init__(
        self,
        client: Any,
        cache: Any,
        session_factory: Any = None,
        customer_id: int | None = None,
    ) -> None:
        """Initialize service with API client and persistence dependencies.

        Args:
            client: TestIO API client
            cache: Legacy PersistentCache (kept for compatibility)
            session_factory: Factory for creating AsyncSession
            customer_id: Customer ID for data isolation
        """
        super().__init__(client)
        self.cache = cache
        self.session_factory = session_factory
        self.customer_id = customer_id

    async def list_products(
        self,
        search: str | None = None,
        product_type: str | list[str] | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
        page: int = 1,
        per_page: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List all products accessible to the user with optional filtering.

        STORY-055: Adds sorting and pagination support.
        STORY-058: Always uses database query path to return enriched counts
        (test_count, bug_count, feature_count, recency indicators).

        Fetches from API and updates local database (Read-through/Write-through).
        Then queries from local database to return enriched product data.

        Args:
            search: Optional search term (filters by name/description)
            product_type: Optional filter by product type(s) - single string or list
            sort_by: Optional field to sort by (title, product_type, last_synced).
                     Defaults to "title" to ensure database query path is used.
            sort_order: Sort direction (asc, desc), default: asc
            page: Page number (1-indexed), default: 1
            per_page: Items per page, default: 50
            offset: Alternative to page (0-indexed), default: 0

        Returns:
            Dictionary with product list and metadata (including computed counts)

        Raises:
            TestIOAPIError: If API returns error response
            ValueError: If sort_by field is invalid
        """
        # STORY-058: Always use database query path to get enriched counts
        # Default to sorting by title when session_factory available
        if self.session_factory and self.customer_id:
            sort_by = sort_by or "title"

        # Normalize product_type to list for SQL filtering
        product_type_list: list[str] | None = None
        if product_type:
            product_type_list = (
                [product_type] if isinstance(product_type, str) else list(product_type)
            )

        # STORY-055: If sorting requested, use database query
        if sort_by and self.session_factory and self.customer_id:
            # Sync products from API first
            raw_response = await self.client.get("products")
            all_products = raw_response.get("products", [])

            # Update local database
            try:
                async with self.session_factory() as session:
                    repo = ProductRepository(session, self.client, self.customer_id)
                    for product in all_products:
                        await repo.upsert_product(product)
                    await repo.commit()
            except Exception as e:
                logger.error(f"Failed to update local product cache: {e}")
                # Fall back to in-memory filtering
                filtered_products = self._apply_filters(all_products, search, product_type)
                return {
                    "total_count": len(filtered_products),
                    "filters_applied": {
                        "search": search,
                        "product_type": product_type,
                    },
                    "products": filtered_products,
                    "page": page,
                    "per_page": per_page,
                }

            # Query from database with sorting AND filtering at SQL level
            # FIX: Pass filters to repository so total_count reflects all matching products
            async with self.session_factory() as session:
                repo = ProductRepository(session, self.client, self.customer_id)
                result = await repo.query_products(
                    sort_by=sort_by,
                    sort_order=sort_order,
                    page=page,
                    per_page=per_page,
                    offset=offset,
                    search=search,
                    product_type=product_type_list,
                )

            # No longer need in-memory filtering - SQL handles it
            # result["total_count"] now reflects ALL matching products (not just page size)
            return {
                "total_count": result["total_count"],
                "filters_applied": {
                    "search": search,
                    "product_type": product_type,
                },
                "products": result["products"],
                "page": result["page"],
                "per_page": result["per_page"],
            }

        # Original behavior: Fetch from API, sort in-memory
        raw_response = await self.client.get("products")
        all_products = raw_response.get("products", [])

        # Update local database if session factory is available
        if self.session_factory and self.customer_id:
            try:
                async with self.session_factory() as session:
                    repo = ProductRepository(session, self.client, self.customer_id)
                    for product in all_products:
                        await repo.upsert_product(product)
                    await repo.commit()
            except Exception as e:
                # Log error but don't fail the request (graceful degradation)
                logger.error(f"Failed to update local product cache: {e}")

        # Filter in-memory (fast, <1ms)
        filtered_products = self._apply_filters(all_products, search, product_type)

        # Apply pagination manually if not using DB query
        if page > 1 or per_page != 50:
            start_idx = offset if offset > 0 else (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_products = filtered_products[start_idx:end_idx]
        else:
            paginated_products = filtered_products

        # Build result with filter metadata
        return {
            "total_count": len(filtered_products),
            "filters_applied": {
                "search": search,
                "product_type": product_type,
            },
            "products": paginated_products,
            "page": page,
            "per_page": per_page,
        }

    async def get_product_summary(self, product_id: int) -> dict[str, Any]:
        """Get product summary with metadata and computed counts.

        STORY-057: Added for get_product_summary tool.

        SQLite-only (no API calls). Uses cached data with counts computed via subqueries.

        Args:
            product_id: Product identifier

        Returns:
            Product summary with metadata and counts

        Raises:
            ProductNotFoundException: If product not found

        Example:
            >>> summary = await service.get_product_summary(598)
            >>> print(summary["test_count"])
            216
        """
        from datetime import UTC, datetime

        from testio_mcp.exceptions import ProductNotFoundException
        from testio_mcp.repositories.product_repository import ProductRepository

        if not self.session_factory or not self.customer_id:
            raise ValueError(
                "ProductService requires session_factory and customer_id for summary operations"
            )

        async with self.session_factory() as session:
            repo = ProductRepository(session, self.client, self.customer_id)
            product_with_counts = await repo.get_product_with_counts(product_id)

        if not product_with_counts:
            raise ProductNotFoundException(product_id)

        # Add data_as_of timestamp for staleness visibility (AC requirement)
        return {
            **product_with_counts,
            "data_as_of": datetime.now(UTC).isoformat(),
        }

    def _apply_filters(
        self,
        products: list[dict[str, Any]],
        search: str | None,
        product_type: str | list[str] | None,
    ) -> list[dict[str, Any]]:
        """Apply search and type filters to products.

        This is a private helper method that filters raw product data:
        - Search: Case-insensitive substring match on name or description
        - Product type: Match on type field (single value or list)

        Args:
            products: List of product dictionaries from API
            search: Optional search term
            product_type: Optional product type filter(s) - single string or list

        Returns:
            Filtered list of products

        Example:
            >>> products = [
            ...     {"id": "1", "name": "Studio Pro", "type": "website"},
            ...     {"id": "2", "name": "Mobile App", "type": "mobile"}
            ... ]
            >>> filtered = service._apply_filters(products, "studio", None)
            >>> len(filtered)
            1
            >>> filtered[0]["name"]
            'Studio Pro'
        """
        filtered = products

        # Filter by search term (case-insensitive, name or description)
        if search:
            search_lower = search.lower()
            filtered = [
                p
                for p in filtered
                if search_lower in (p.get("name") or "").lower()
                or search_lower in (p.get("description") or "").lower()
            ]

        # Filter by product type(s)
        if product_type:
            # Normalize to list for consistent filtering
            types = [product_type] if isinstance(product_type, str) else product_type
            filtered = [p for p in filtered if p.get("type") in types]

        return filtered

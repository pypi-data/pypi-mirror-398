"""
Product Repository - Data access layer for product-related database operations.

This repository handles all ORM queries for products using SQLModel.
It maintains clean separation between business logic (services) and data access.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.models.orm import Product
from testio_mcp.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ProductRepository(BaseRepository):
    """Repository for product-related database operations.

    Handles pure ORM queries with no business logic.
    All queries are scoped to a specific customer for data isolation.

    Attributes:
        session: AsyncSession for ORM operations (inherited from BaseRepository)
        client: TestIO API client for refresh operations (inherited)
        customer_id: Stable customer identifier (inherited)
    """

    # Override type hint to indicate session is always present in this repository
    session: AsyncSession

    def __init__(self, session: AsyncSession, client: TestIOClient, customer_id: int) -> None:
        """Initialize repository with async session and API client.

        Args:
            session: Active AsyncSession for ORM operations
            client: TestIO API client for refresh operations
            customer_id: Stable customer identifier from TestIO system
        """
        super().__init__(session, client, customer_id)

    async def count_products(self) -> int:
        """Count total products for current customer.

        Returns:
            Total number of products
        """
        statement = (
            select(func.count()).select_from(Product).where(Product.customer_id == self.customer_id)
        )
        result = await self.session.exec(statement)
        count = result.one()
        return count

    async def get_product_info(self, product_id: int) -> dict[str, Any] | None:
        """Get product information from database.

        STORY-054: Now uses denormalized product_type field instead of JSON extraction.

        Args:
            product_id: Product identifier

        Returns:
            Product info dictionary with id, name, type, or None if not found

        Note:
            Provides fallback values when database has empty JSON.
        """
        statement = select(Product).where(
            Product.id == product_id, Product.customer_id == self.customer_id
        )
        result = await self.session.exec(statement)
        product = result.first()

        if not product:
            return None

        # Parse JSON data column for name
        # (title is also denormalized but we keep name for API consistency)
        product_data = json.loads(product.data) if product.data else {}

        # STORY-054: Use denormalized product_type field with fallback to JSON
        product_type = product.product_type or product_data.get("type") or "unknown"

        # Extract fields from data with fallback values (handles empty JSON gracefully)
        return {
            "id": product.id,
            "name": product_data.get("name") or f"Product {product.id}",
            "type": product_type,  # STORY-054: Prefer denormalized field
        }

    async def get_synced_products_info(self) -> list[dict[str, Any]]:
        """Get information about synced products for current customer.

        Returns:
            List of product info dictionaries with id, name, last_synced, test_count
        """
        # Note: This query uses a subquery to count tests per product
        # In a future iteration, we could use SQLModel relationships for this
        from sqlmodel import col

        # STORY-062: Simplified - only last_synced needed for staleness checks
        statement = (
            select(Product.id, Product.data, Product.last_synced)
            .where(Product.customer_id == self.customer_id)
            .order_by(col(Product.last_synced).desc())
        )

        result = await self.session.exec(statement)
        rows = result.all()

        # For now, we'll use a separate query for test counts
        # In the future, this could be optimized with a join or relationship
        from testio_mcp.models.orm import Test

        products_info: list[dict[str, Any]] = []
        for row in rows:
            product_id, data, last_synced = row

            # Parse product name from JSON data
            product_data = json.loads(data) if data else {}
            name = product_data.get("name") or f"Product {product_id}"

            # Count tests for this product
            test_count_stmt = (
                select(func.count())
                .select_from(Test)
                .where(Test.product_id == product_id, Test.customer_id == self.customer_id)
            )
            test_count_result = await self.session.exec(test_count_stmt)
            test_count = test_count_result.one()

            products_info.append(
                {
                    "id": product_id,
                    "name": name,
                    "last_synced": last_synced.isoformat() if last_synced else None,
                    "test_count": test_count,
                }
            )

        return products_info

    async def get_product(self, product_id: int) -> Product | None:
        """Get product ORM instance by ID.

        Args:
            product_id: Product identifier

        Returns:
            Product ORM instance or None if not found

        Note:
            Use this when you need the ORM instance (e.g., for staleness checks).
            Use get_product_info() when you only need dict with id/name/type.
        """
        statement = select(Product).where(
            Product.id == product_id, Product.customer_id == self.customer_id
        )
        result = await self.session.exec(statement)
        return result.first()

    async def update_product_last_synced(self, product_id: int) -> None:
        """Update product's last_synced timestamp without modifying data.

        Uses session.merge() to upsert the product record.

        Args:
            product_id: Product identifier
        """
        now_utc = datetime.now(UTC)

        # Try to get existing product
        statement = select(Product).where(
            Product.id == product_id, Product.customer_id == self.customer_id
        )
        result = await self.session.exec(statement)
        product = result.first()

        if product:
            # Update existing product
            product.last_synced = now_utc
            self.session.add(product)
        else:
            # Create minimal product record
            new_product = Product(
                id=product_id,
                customer_id=self.customer_id,
                title="Untitled Product",  # Default title for new products
                data="{}",
                last_synced=now_utc,
            )
            self.session.add(new_product)

        await self.session.commit()

    # STORY-062: Removed update_features_last_synced() - use SyncService instead

    async def get_all_products(self) -> list[dict[str, Any]]:
        """Get all products with full details from database.

        Returns:
            List of product dictionaries (parsed from JSON data)
        """
        statement = select(Product.data).where(Product.customer_id == self.customer_id)
        result = await self.session.exec(statement)
        products_json = result.all()
        return [json.loads(data) for data in products_json]

    async def upsert_product(self, product_data: dict[str, Any]) -> None:
        """Insert or update a product.

        This method stages the product for insertion/update but does NOT commit.
        Caller must explicitly commit the session to persist changes.
        This allows efficient batching of multiple upserts in a single transaction.

        Extracts denormalized fields (title, product_type) from product_data JSON for analytics.

        STORY-054: Added product_type extraction for filtering without JSON queries.

        Note: last_synced is NOT updated here - it tracks test sync freshness
        and is updated by refresh_mutable_tests() in the read-through cache.

        Args:
            product_data: Product dictionary from API

        Example:
            ```python
            async with session_maker() as session:
                repo = ProductRepository(session, client, customer_id)
                for product in products:
                    await repo.upsert_product(product)
                await session.commit()  # Commit all at once
            ```
        """
        product_id = product_data["id"]
        statement = select(Product).where(Product.id == product_id)
        result = await self.session.exec(statement)
        existing = result.first()

        # Extract denormalized fields from JSON for analytics (STORY-054)
        title = product_data.get("name", "Untitled Product")
        product_type = product_data.get("type")  # STORY-054: Extract product type

        if existing:
            existing.title = title
            existing.product_type = product_type  # STORY-054
            existing.data = json.dumps(product_data)
            self.session.add(existing)
        else:
            new_product = Product(
                id=product_id,
                customer_id=self.customer_id,
                title=title,
                product_type=product_type,  # STORY-054
                data=json.dumps(product_data),
                last_synced=None,
            )
            self.session.add(new_product)

    async def delete_all_products(self) -> None:
        """Delete all products for the current customer.

        This is a destructive operation used for rebuilding the cache.
        """
        # We select and delete individually to avoid SQLAlchemy delete() type issues
        # and ensure proper ORM event handling if we add hooks later.
        statement = select(Product).where(Product.customer_id == self.customer_id)
        result = await self.session.exec(statement)
        products = result.all()

        for product in products:
            await self.session.delete(product)

        await self.commit()

    async def get_product_with_counts(self, product_id: int) -> dict[str, Any] | None:
        """Get product with computed counts (test_count, feature_count).

        STORY-057: Added for get_product_summary tool.
        STORY-083: Removes bug_count (use get_product_quality_report instead).

        Args:
            product_id: Product identifier

        Returns:
            Product dictionary with metadata and computed counts, or None if not found

        Example:
            >>> await repo.get_product_with_counts(598)
            {
                "id": 598,
                "title": "Canva",
                "type": "website",
                "description": "...",
                "test_count": 216,
                "feature_count": 45,
                "last_synced": "2025-11-28T..."
            }
        """
        from testio_mcp.models.orm import Feature, Test

        # Get product
        product = await self.get_product(product_id)
        if not product:
            return None

        # Parse JSON data
        product_data = json.loads(product.data) if product.data else {}

        # Count tests
        test_count_stmt = (
            select(func.count())
            .select_from(Test)
            .where(Test.product_id == product_id, Test.customer_id == self.customer_id)
        )
        test_count_result = await self.session.exec(test_count_stmt)
        test_count = test_count_result.one()

        # Count features
        feature_count_stmt = (
            select(func.count()).select_from(Feature).where(Feature.product_id == product_id)
        )
        feature_count_result = await self.session.exec(feature_count_stmt)
        feature_count = feature_count_result.one()

        return {
            "id": product.id,
            "title": product_data.get("name") or product.title,
            "type": product.product_type or product_data.get("type") or "unknown",
            "description": product_data.get("description"),
            "test_count": test_count,
            "feature_count": feature_count,
            "last_synced": product.last_synced.isoformat() if product.last_synced else None,
        }

    async def query_products(
        self,
        sort_by: str | None = None,
        sort_order: str = "asc",
        page: int = 1,
        per_page: int = 50,
        offset: int = 0,
        search: str | None = None,
        product_type: list[str] | None = None,
    ) -> dict[str, Any]:
        """Query products with sorting, pagination, and filtering.

        STORY-055: Adds sorting and pagination support for list_products tool.
        STORY-058: Adds computed counts (test_count, feature_count).
        STORY-083: Removes bug_count (use get_product_quality_report instead).
        FIX: Adds search/product_type filtering at SQL level for accurate total_count.

        Args:
            sort_by: Field to sort by (title, product_type, last_synced)
            sort_order: Sort direction (asc, desc)
            page: Page number (1-indexed)
            per_page: Items per page
            offset: Alternative to page (0-indexed)
            search: Optional search term (case-insensitive, matches title/description)
            product_type: Optional filter by product type(s)

        Returns:
            Dictionary with products (including counts), total_count, page, per_page
            Note: total_count reflects ALL products matching filters, not just page items

        Raises:
            ValueError: If sort_by field is invalid

        Example:
            >>> await repo.query_products(
            ...     sort_by="title", sort_order="asc", page=1, per_page=10,
            ...     search="studio", product_type=["website"]
            ... )
            {
                "products": [...],  # 10 items (page)
                "total_count": 25,  # Total matching products across all pages
                "page": 1,
                "per_page": 10
            }
        """
        from sqlmodel import col, desc

        from testio_mcp.models.orm import Feature, Test

        # Validate sort_by field
        VALID_SORT_FIELDS = ["title", "product_type", "last_synced"]
        if sort_by and sort_by not in VALID_SORT_FIELDS:
            raise ValueError(f"Invalid sort_by: {sort_by}. Must be one of: {VALID_SORT_FIELDS}")

        # Define correlated scalar subqueries for counts (STORY-058 N+1 fix)
        # Pattern from feature_repository.py:411-428
        test_count_subquery = (
            select(func.count(Test.id))  # type: ignore[arg-type]
            .where(Test.product_id == Product.id, Test.customer_id == self.customer_id)
            .correlate(Product)
            .scalar_subquery()
            .label("test_count")
        )

        feature_count_subquery = (
            select(func.count(Feature.id))  # type: ignore[arg-type]
            .where(Feature.product_id == Product.id)
            .correlate(Product)
            .scalar_subquery()
            .label("feature_count")
        )

        # Recent activity subqueries (recency indicators)
        from datetime import datetime, timedelta

        now = datetime.now(UTC)
        cutoff_30_days = now - timedelta(days=30)
        cutoff_90_days = now - timedelta(days=90)

        tests_last_30_days_subquery = (
            select(func.count(Test.id))  # type: ignore[arg-type]
            .where(
                Test.product_id == Product.id,
                Test.customer_id == self.customer_id,
                Test.end_at.is_not(None),  # type: ignore[union-attr]
                col(Test.end_at) >= cutoff_30_days,
                Test.status.in_(["running", "locked", "archived"]),  # type: ignore[attr-defined]
            )
            .correlate(Product)
            .scalar_subquery()
            .label("tests_last_30_days")
        )

        tests_last_90_days_subquery = (
            select(func.count(Test.id))  # type: ignore[arg-type]
            .where(
                Test.product_id == Product.id,
                Test.customer_id == self.customer_id,
                Test.end_at.is_not(None),  # type: ignore[union-attr]
                col(Test.end_at) >= cutoff_90_days,
                Test.status.in_(["running", "locked", "archived"]),  # type: ignore[attr-defined]
            )
            .correlate(Product)
            .scalar_subquery()
            .label("tests_last_90_days")
        )

        last_test_end_at_subquery = (
            select(func.max(Test.end_at))
            .where(
                Test.product_id == Product.id,
                Test.customer_id == self.customer_id,
                Test.status.in_(["running", "locked", "archived"]),  # type: ignore[attr-defined]
            )
            .correlate(Product)
            .scalar_subquery()
            .label("last_test_end_at")
        )

        # Build filter conditions (applied to both data query and count query)
        filter_conditions = [Product.customer_id == self.customer_id]

        # Search filter: case-insensitive match on title (denormalized column)
        # Note: description is in JSON 'data' column, would require JSON extraction
        # For simplicity, we only search title (covers 90%+ of search use cases)
        if search:
            search_lower = search.lower()
            filter_conditions.append(
                func.lower(Product.title).contains(search_lower)  # type: ignore[arg-type]
            )

        # Product type filter: match denormalized product_type column
        if product_type:
            filter_conditions.append(
                col(Product.product_type).in_(product_type)  # type: ignore[arg-type]
            )

        # Base query: SELECT Product + all count/recency subqueries
        statement = select(  # type: ignore[call-overload]
            Product,
            test_count_subquery,
            feature_count_subquery,
            tests_last_30_days_subquery,
            tests_last_90_days_subquery,
            last_test_end_at_subquery,
        ).where(*filter_conditions)

        # Apply sorting
        if sort_by:
            sort_column = getattr(Product, sort_by)
            if sort_order == "desc":
                statement = statement.order_by(desc(sort_column))
            else:
                statement = statement.order_by(col(sort_column).asc())
        else:
            # Default sort by title ascending
            statement = statement.order_by(col(Product.title).asc())

        # Count total matching products BEFORE pagination (same filters applied)
        count_stmt = select(func.count()).select_from(Product).where(*filter_conditions)
        count_result = await self.session.exec(count_stmt)
        total_count = count_result.one()

        # Apply pagination
        # Calculate offset from page if not provided
        if offset == 0 and page > 1:
            offset = (page - 1) * per_page

        statement = statement.offset(offset).limit(per_page)

        # Execute query - returns tuples with all subquery results
        result = await self.session.exec(statement)
        rows = result.all()

        # Convert tuples to dict with computed counts and recency indicators
        products_list = []
        for (
            product,
            test_count,
            feature_count,
            tests_last_30_days,
            tests_last_90_days,
            last_test_end_at,
        ) in rows:
            product_data = json.loads(product.data) if product.data else {}

            products_list.append(
                {
                    "id": product.id,
                    "name": product_data.get("name") or product.title,
                    "type": product.product_type or product_data.get("type") or "unknown",
                    "description": product_data.get("description"),
                    "test_count": test_count,
                    "feature_count": feature_count,
                    "tests_last_30_days": tests_last_30_days,
                    "tests_last_90_days": tests_last_90_days,
                    "last_test_end_at": last_test_end_at.isoformat() if last_test_end_at else None,
                }
            )

        return {
            "products": products_list,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
        }

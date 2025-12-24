"""Feature Repository - Data access layer for feature-related database operations.

This repository handles section-aware feature sync from TestIO API and ORM queries.
Features can be organized with or without sections, requiring different API endpoints.

STORY-035A: Feature Repository & Sync
Epic: EPIC-005 (Data Enhancement and Serving)
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.models.orm import Feature
from testio_mcp.repositories.base_repository import BaseRepository
from testio_mcp.utilities.progress import BatchProgressCallback, safe_batch_callback
from testio_mcp.utilities.section_detection import get_section_ids, has_sections

logger = logging.getLogger(__name__)


class FeatureRepository(BaseRepository):
    """Repository for Feature entity operations.

    Handles section-aware feature sync:
    - Non-section products: GET /products/{id}/features
    - Section products: GET /products/{id}/sections/{sid}/features (undocumented)

    Section Detection:
    - Uses shared helper from Task 1.5 (has_sections, get_section_ids)
    - Validated logic: len(sections) > 0 OR len(sections_with_default) > 1
    - Default-section (single item) = legacy non-section product

    Inherits from BaseRepository for:
    - Standard constructor (session, client injection)
    - Async context manager pattern
    - Resource cleanup in finally blocks

    Attributes:
        session: AsyncSession for ORM operations (inherited from BaseRepository)
        client: TestIO API client for refresh operations (inherited)
        customer_id: Stable customer identifier (inherited)
    """

    # Override type hint to indicate session is always present in this repository
    session: AsyncSession

    def __init__(
        self,
        session: AsyncSession,
        client: TestIOClient,
        customer_id: int,
        cache: Any | None = None,
    ) -> None:
        """Initialize repository.

        Args:
            session: SQLModel AsyncSession (managed by caller)
            cache: Optional PersistentCache for per-entity refresh locks (STORY-046, AC6)
            client: TestIO API client
            customer_id: Customer ID for API calls
        """
        super().__init__(session, client, customer_id, cache)

    async def sync_features(self, product_id: int) -> dict[str, int]:
        """Sync features for product (section-aware).

        Detects if product has sections and uses appropriate API endpoint:
        - Non-section: GET /products/{id}/features
        - Section: GET /products/{id}/sections/{sid}/features (per section)

        Uses shared section detection helper (Task 1.5) to avoid
        misclassifying single-default-section products.

        Args:
            product_id: Product ID to sync features for

        Returns:
            Sync statistics: {"created": int, "updated": int, "total": int}

        Raises:
            TestIOAPIError: If API calls fail
        """
        # 1. Get product data (prefer database, fallback to API)
        product_data = await self._get_product_data(product_id)

        # 2. Use shared helper (Task 1.5) - fixes single-section bug
        if has_sections(product_data):
            features_data = await self._sync_sectioned_product(product_id, product_data)
        else:
            features_data = await self._sync_non_sectioned_product(product_id)

        # 3. Upsert features to database
        stats = await self._upsert_features(product_id, features_data)

        # 4. Commit changes (sync_features is a public API method)
        # NOTE: _upsert_features doesn't commit to support concurrent calls
        # via asyncio.gather() in get_features_cached_or_refresh()
        # STORY-062 follow-up: Write semaphore wraps entire transaction in caller
        await self.session.commit()

        return stats

    async def _get_product_data(self, product_id: int) -> dict[str, Any]:
        """Get product data from database with API fallback.

        Optimization: During 4-phase sync, products are upserted in Phase 1,
        so Phase 2 (feature refresh) can read from database instead of making
        redundant API calls. This saves N API calls where N = number of products.

        If product not found in database (edge case for standalone feature refresh),
        falls back to GET /products/{product_id} API endpoint.

        Args:
            product_id: Product ID

        Returns:
            Product data dictionary with sections field

        Raises:
            TestIOAPIError: If API call fails (from client)
        """
        from sqlmodel import select

        from testio_mcp.models.orm.product import Product

        # Try database first (Phase 1 optimization)
        result = await self.session.exec(
            select(Product).where(Product.id == product_id, Product.customer_id == self.customer_id)
        )
        product = result.first()

        if product and product.data:
            # Parse JSON data from database
            product_data: dict[str, Any] = json.loads(product.data)
            logger.debug(f"Using cached product data for {product_id} from database")
            return product_data

        # Fallback to API (edge case: standalone feature refresh)
        logger.debug(
            f"Product {product_id} not in database, fetching from API "
            "(this is expected outside of 4-phase sync)"
        )
        response = await self.client.get(f"products/{product_id}")
        product_data_api: dict[str, Any] = response.get("product", {})
        return product_data_api

    async def _sync_non_sectioned_product(self, product_id: int) -> list[dict[str, Any]]:
        """Fetch features for non-section product.

        Args:
            product_id: Product ID

        Returns:
            List of feature dictionaries
        """
        response = await self.client.get(f"products/{product_id}/features")
        features: list[dict[str, Any]] = response.get("features", [])
        return features

    async def _sync_sectioned_product(
        self, product_id: int, product_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Fetch features for section product (all sections).

        Uses undocumented endpoint: GET /products/{id}/sections/{sid}/features

        IMPORTANT: Features are SHARED across sections. The same feature ID
        appears in multiple section responses. This method:
        1. Deduplicates by feature ID (keeps first occurrence)
        2. Tracks section membership by adding 'section_ids' to each feature dict

        Uses shared helper (Task 1.5) to extract section IDs consistently
        with UserStoryRepository.

        Args:
            product_id: Product ID
            product_data: Product API response (contains sections)

        Returns:
            Deduplicated list of features with 'section_ids' field added
        """
        # Use shared helper (Task 1.5) - consistent with UserStoryRepository
        section_ids = get_section_ids(product_data)
        feature_sections: dict[int, list[int]] = {}  # feature_id -> [section_ids]
        unique_features: dict[int, dict[str, Any]] = {}  # feature_id -> feature_data

        # Concurrency control: Reuse client semaphore (2-3 concurrent calls)
        # Build tuples of (section_id, task) to maintain section context through gather
        section_tasks = [
            (section_id, self._fetch_section_features(product_id, section_id))
            for section_id in section_ids
        ]

        # Gather results (client semaphore enforces concurrency limit)
        section_results = await asyncio.gather(
            *[task for _, task in section_tasks], return_exceptions=True
        )

        # Build section membership map
        for idx, result in enumerate(section_results):
            section_id = section_tasks[idx][0]  # Get corresponding section_id from tuple

            if isinstance(result, Exception):
                # Log error but continue (partial sync better than failure)
                logger.warning(f"Section {section_id} feature fetch failed: {result}")
                continue
            if isinstance(result, list):
                for feature in result:
                    feature_id = feature.get("id")
                    if not feature_id:
                        continue

                    # Track which sections this feature appears in
                    if feature_id not in feature_sections:
                        feature_sections[feature_id] = []
                        unique_features[feature_id] = feature
                    feature_sections[feature_id].append(section_id)

        # Add section_ids to each feature
        result_features = []
        for feature_id, feature_data in unique_features.items():
            feature_data["section_ids"] = feature_sections[feature_id]
            result_features.append(feature_data)

        return result_features

    async def _fetch_section_features(
        self, product_id: int, section_id: int
    ) -> list[dict[str, Any]]:
        """Fetch features for single section.

        Note: Features are shared across sections, so the same feature
        may be returned from multiple section endpoints.

        Args:
            product_id: Product ID
            section_id: Section ID

        Returns:
            List of feature dictionaries for section
        """
        response = await self.client.get(f"products/{product_id}/sections/{section_id}/features")
        features: list[dict[str, Any]] = response.get("features", [])
        return features

    async def _upsert_features(
        self, product_id: int, features_data: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Upsert features to database with embedded user stories.

        User stories are stored as JSON array of title strings from the
        features endpoint. No additional API calls or title matching needed.

        See ADR-013 for rationale: docs/architecture/adrs/ADR-013-user-story-embedding-strategy.md

        Args:
            product_id: Product ID
            features_data: List of feature dictionaries from API

        Returns:
            Sync statistics
        """
        created = 0
        updated = 0
        now = datetime.now(UTC)

        for feature_data in features_data:
            feature_id = feature_data.get("id")
            if not feature_id:
                continue

            # Extract user stories array (list of strings from API)
            user_stories = feature_data.get("user_stories", [])

            # Extract section membership (STORY-038)
            # For sectioned products, _sync_sectioned_product() adds 'section_ids'
            # For non-sectioned products, this will be empty list
            section_ids = feature_data.get("section_ids", [])

            # Check if feature exists
            result = await self.session.exec(select(Feature).where(Feature.id == feature_id))
            existing = result.first()

            if existing:
                # Update existing feature
                existing.title = feature_data.get("title", "")
                existing.description = feature_data.get("description")
                existing.howtofind = feature_data.get("howtofind")
                existing.user_stories = json.dumps(user_stories)  # Embed user stories
                existing.section_ids = json.dumps(section_ids)  # Track section membership
                existing.raw_data = json.dumps(feature_data)
                existing.last_synced = now
                updated += 1
            else:
                # Create new feature
                feature = Feature(
                    id=feature_id,
                    product_id=product_id,
                    title=feature_data.get("title", ""),
                    description=feature_data.get("description"),
                    howtofind=feature_data.get("howtofind"),
                    user_stories=json.dumps(user_stories),  # Embed user stories
                    section_ids=json.dumps(section_ids),  # Track section membership
                    raw_data=json.dumps(feature_data),
                    last_synced=now,
                )
                self.session.add(feature)
                created += 1

        # NOTE: Commit removed - parent caller handles transaction commit
        # This allows concurrent upserts with shared session (STORY-050 bug fix)

        return {
            "created": created,
            "updated": updated,
            "total": created + updated,
        }

    async def get_features_for_product(
        self,
        product_id: int,
        page: int = 1,
        per_page: int = 100,
        offset: int = 0,
    ) -> list[Feature]:
        """Get features for product with pagination.

        Note: Features are shared across sections, so this returns all
        unique features for the product regardless of section organization.

        Args:
            product_id: Product ID
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 100)
            offset: Additional offset (default: 0)

        Returns:
            List of Feature ORM models for requested page
        """
        # Calculate actual offset: offset + (page - 1) * per_page
        actual_offset = offset + (page - 1) * per_page

        query = (
            select(Feature)
            .where(Feature.product_id == product_id)
            .order_by(col(Feature.id).asc())  # Consistent ordering for pagination
            .limit(per_page)
            .offset(actual_offset)
        )
        result = await self.session.exec(query)
        features = result.all()
        return list(features)

    async def query_features(
        self,
        product_id: int,
        sort_by: str | None = None,
        sort_order: str = "asc",
        page: int = 1,
        per_page: int = 100,
        offset: int = 0,
        has_user_stories: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Query features for product with sorting and pagination.

        STORY-055: Adds sorting support with computed subqueries for test_count and bug_count.
        STORY-055 Fix: Now returns computed counts in response, not just for sorting.
        STORY-058: Adds has_user_stories filter parameter.

        Args:
            product_id: Product ID
            sort_by: Field to sort by (title, test_count, bug_count, last_synced)
            sort_order: Sort direction (asc, desc), default: asc
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 100)
            offset: Additional offset (default: 0)
            has_user_stories: Filter by user story presence.
                - True: only features with user_story_count > 0
                - False/None: all features

        Returns:
            List of dicts with Feature data + computed counts:
            {
                "feature": Feature ORM model,
                "test_count": int,
                "bug_count": int
            }

        Raises:
            ValueError: If sort_by field is invalid
        """
        from sqlmodel import desc, func

        from testio_mcp.models.orm.bug import Bug
        from testio_mcp.models.orm.test_feature import TestFeature

        # Validate sort_by field
        VALID_SORT_FIELDS = ["title", "test_count", "bug_count", "last_synced"]
        if sort_by and sort_by not in VALID_SORT_FIELDS:
            raise ValueError(f"Invalid sort_by: {sort_by}. Must be one of: {VALID_SORT_FIELDS}")

        # Calculate actual offset
        actual_offset = offset + (page - 1) * per_page

        # Define subqueries for test_count and bug_count (always computed for display)
        test_count_subquery = (
            select(func.count(TestFeature.id))  # type: ignore[arg-type]
            .where(TestFeature.feature_id == Feature.id)
            .correlate(Feature)
            .scalar_subquery()
            .label("test_count")
        )

        bug_count_subquery = (
            select(func.count(Bug.id))  # type: ignore[arg-type]
            .select_from(Bug)
            .join(TestFeature, Bug.test_feature_id == TestFeature.id)  # type: ignore[arg-type]
            .where(TestFeature.feature_id == Feature.id)
            .correlate(Feature)
            .scalar_subquery()
            .label("bug_count")
        )

        # Base query: SELECT Feature, test_count, bug_count
        query = select(Feature, test_count_subquery, bug_count_subquery).where(
            Feature.product_id == product_id
        )

        # Apply has_user_stories filter (STORY-058)
        if has_user_stories is True:
            # Filter to features with user stories (user_stories != "[]")
            # SQLite: Check JSON array is not empty
            query = query.where(Feature.user_stories != "[]")

        # Apply sorting
        if sort_by == "test_count":
            if sort_order == "desc":
                query = query.order_by(desc(test_count_subquery))
            else:
                query = query.order_by(test_count_subquery.asc())
        elif sort_by == "bug_count":
            if sort_order == "desc":
                query = query.order_by(desc(bug_count_subquery))
            else:
                query = query.order_by(bug_count_subquery.asc())
        elif sort_by:
            # Simple field sorting (title, last_synced)
            sort_column = getattr(Feature, sort_by)
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(col(sort_column).asc())
        else:
            # Default: sort by title ascending
            query = query.order_by(col(Feature.title).asc())

        # Apply pagination
        query = query.limit(per_page).offset(actual_offset)

        # Execute query
        result = await self.session.exec(query)
        rows = result.all()

        # Transform rows to dict format
        return [
            {"feature": row[0], "test_count": row[1] or 0, "bug_count": row[2] or 0} for row in rows
        ]

    async def get_feature_with_counts(self, feature_id: int) -> dict[str, Any] | None:
        """Get feature with computed counts and associated product info.

        STORY-057: Added for get_feature_summary tool.

        Args:
            feature_id: Feature identifier

        Returns:
            Feature dictionary with metadata and computed counts, or None if not found

        Example:
            >>> await repo.get_feature_with_counts(123)
            {
                "id": 123,
                "title": "User Authentication",
                "description": "Login and signup flows",
                "howtofind": "Navigate to login page",
                "user_stories": ["As a user...", "As an admin..."],
                "test_count": 15,
                "bug_count": 42,
                "product": {"id": 598, "name": "Canva"}
            }
        """
        from sqlmodel import func

        from testio_mcp.models.orm.bug import Bug
        from testio_mcp.models.orm.product import Product
        from testio_mcp.models.orm.test_feature import TestFeature

        # Define subqueries for counts
        test_count_subquery = (
            select(func.count(TestFeature.id))  # type: ignore[arg-type]
            .where(TestFeature.feature_id == Feature.id)
            .correlate(Feature)
            .scalar_subquery()
            .label("test_count")
        )

        bug_count_subquery = (
            select(func.count(Bug.id))  # type: ignore[arg-type]
            .select_from(Bug)
            .join(TestFeature, Bug.test_feature_id == TestFeature.id)  # type: ignore[arg-type]
            .where(TestFeature.feature_id == Feature.id)
            .correlate(Feature)
            .scalar_subquery()
            .label("bug_count")
        )

        # Query feature with counts
        query = select(Feature, test_count_subquery, bug_count_subquery).where(
            Feature.id == feature_id
        )
        result = await self.session.exec(query)
        row = result.first()

        if not row:
            return None

        feature, test_count, bug_count = row

        # Parse embedded user stories
        user_stories = json.loads(feature.user_stories) if feature.user_stories else []

        # Get associated product info
        product_query = select(Product).where(Product.id == feature.product_id)
        product_result = await self.session.exec(product_query)
        product = product_result.first()

        # Parse product data
        product_data = json.loads(product.data) if product and product.data else {}
        product_info = {
            "id": feature.product_id,
            "name": product_data.get("name", f"Product {feature.product_id}")
            if product
            else f"Product {feature.product_id}",
        }

        return {
            "id": feature.id,
            "title": feature.title,
            "description": feature.description,
            "howtofind": feature.howtofind,
            "user_stories": user_stories,
            "test_count": test_count or 0,
            "bug_count": bug_count or 0,
            "product": product_info,
        }

    async def count_features(self, product_id: int, has_user_stories: bool | None = None) -> int:
        """Count features for product with optional filtering.

        FIX: Added has_user_stories filter for accurate pagination total_count.

        Args:
            product_id: Product ID
            has_user_stories: Filter by user story presence.
                - True: only count features with user_story_count > 0
                - False/None: count all features

        Returns:
            Total count of features matching criteria
        """
        from sqlmodel import func

        query = select(func.count()).select_from(Feature).where(Feature.product_id == product_id)

        # Apply same filter as query_features() for accurate total_count
        if has_user_stories is True:
            query = query.where(Feature.user_stories != "[]")

        result = await self.session.exec(query)
        return result.one()

    async def get_features_cached_or_refresh(
        self,
        product_ids: list[int],
        force_refresh: bool = False,
        on_batch_progress: BatchProgressCallback | None = None,
    ) -> tuple[dict[int, list[dict[str, Any]]], dict[str, Any]]:
        """Get features with intelligent caching based on staleness.

        Batch-aware method: Pass single product ID or multiple for efficient batch processing.

        Decision Logic (per product, priority order):
        1. Check products.last_synced timestamp (STORY-062: simplified from features_synced_at)
        2. If force_refresh=True → mark for refresh (user override)
        3. If last_synced IS NULL → mark for refresh (never synced!)
        4. If last_synced is stale (>TTL seconds) → mark for refresh
        5. If last_synced is fresh → use cache
        6. Batch refresh all products marked for refresh
        7. Return features for all product IDs from SQLite

        Args:
            product_ids: List of product identifiers (single or multiple)
            force_refresh: Bypass cache and fetch from API for all products (default: False)
            on_batch_progress: Optional callback invoked after each product refresh completes.
                Args: (current_completed: int, total_products: int). Best-effort (errors swallowed).

        Returns:
            Tuple of (features_dict, cache_stats):
                - features_dict: Dictionary mapping product_id -> list of feature dicts
                  Example: {598: [{feature1}, {feature2}], 1024: [{feature3}]}
                - cache_stats: Cache efficiency metrics dict with:
                  - total_products: int
                  - cache_hits: int
                  - api_calls: int
                  - cache_hit_rate: float (0-100)
                  - breakdown: dict with decision category counts

        Performance:
            - Single product cache hit: ~10ms (SQLite query)
            - Batch processing: Efficient concurrent API calls
            - Features never change (no mutability check needed)

        Logging:
            - DEBUG: Per-product decisions (SQLite vs API, with reason)
            - INFO: Summary stats (cache hit rate, breakdown by category)
            Example logs:
                Product 598: SQLite (fresh (0.5h))
                Product 1024: API (stale (2.3h))
                Feature cache: 1/2 from SQLite (50.0% hit rate), 1 from API
                Breakdown: 1 fresh (cached), 1 stale (API)
        """
        from testio_mcp.config import settings

        if not product_ids:
            return {}, {
                "total_products": 0,
                "cache_hits": 0,
                "api_calls": 0,
                "cache_hit_rate": 0.0,
                "breakdown": {},
            }

        # 1. Bulk query: Get last_synced for all product IDs (STORY-062: simplified)
        from testio_mcp.models.orm.product import Product

        statement = select(Product.id, Product.last_synced).where(
            col(Product.id).in_(product_ids), Product.customer_id == self.customer_id
        )
        product_result = await self.session.exec(statement)
        rows = product_result.all()
        product_metadata: dict[int, datetime | None] = {
            row[0]: row[1] for row in rows if row[0] is not None
        }

        # 2. Determine which products need refreshing
        products_to_refresh: list[int] = []
        now = datetime.now(UTC)

        # Track decision stats for logging
        cache_decisions = {
            "fresh_cached": 0,
            "stale_refresh": 0,
            "never_synced": 0,
            "force_refresh": 0,
            "not_in_db": 0,
        }

        for product_id in product_ids:
            last_synced_value = product_metadata.get(product_id)

            if product_id not in product_metadata:
                # Product not in DB - need to refresh (will likely 404 from API)
                products_to_refresh.append(product_id)
                cache_decisions["not_in_db"] += 1
                logger.debug(f"Product {product_id}: API (not in database)")
                continue

            # Parse last_synced timestamp (STORY-062: simplified)
            synced_at: datetime | None = None
            if last_synced_value:
                try:
                    # last_synced can be str, datetime, or None from DB
                    if isinstance(last_synced_value, str):
                        synced_at = datetime.fromisoformat(last_synced_value)
                    elif isinstance(last_synced_value, datetime):
                        synced_at = last_synced_value

                    # Ensure timezone awareness (assume UTC if naive)
                    if synced_at and synced_at.tzinfo is None:
                        synced_at = synced_at.replace(tzinfo=UTC)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid last_synced for product {product_id}, will refresh")

            # Apply decision logic
            should_refresh = False
            decision_reason = ""

            if force_refresh:
                should_refresh = True
                decision_reason = "force_refresh=True"
                cache_decisions["force_refresh"] += 1
            elif synced_at is None:
                # Never synced - MUST fetch
                should_refresh = True
                decision_reason = "never synced"
                cache_decisions["never_synced"] += 1
            else:
                # Check staleness
                seconds_since_sync = (now - synced_at).total_seconds()
                hours_since_sync = seconds_since_sync / 3600

                if seconds_since_sync > settings.CACHE_TTL_SECONDS:
                    should_refresh = True
                    decision_reason = f"stale ({hours_since_sync:.1f}h)"
                    cache_decisions["stale_refresh"] += 1
                else:
                    should_refresh = False
                    decision_reason = f"fresh ({hours_since_sync:.1f}h)"
                    cache_decisions["fresh_cached"] += 1

            # Log decision
            source = "API" if should_refresh else "SQLite"
            logger.debug(f"Product {product_id}: {source} ({decision_reason})")

            if should_refresh:
                products_to_refresh.append(product_id)

        # 3. Log cache efficiency summary
        cache_hits = len(product_ids) - len(products_to_refresh)
        cache_hit_rate = (cache_hits / len(product_ids) * 100) if product_ids else 0

        logger.info(
            f"Feature cache decisions: {cache_hits}/{len(product_ids)} from SQLite "
            f"({cache_hit_rate:.1f}% hit rate), {len(products_to_refresh)} from API"
        )

        # Log breakdown by category (non-zero only)
        breakdown_parts = []
        if cache_decisions["fresh_cached"]:
            breakdown_parts.append(f"{cache_decisions['fresh_cached']} fresh (cached)")
        if cache_decisions["stale_refresh"]:
            breakdown_parts.append(f"{cache_decisions['stale_refresh']} stale (API)")
        if cache_decisions["never_synced"]:
            breakdown_parts.append(f"{cache_decisions['never_synced']} never synced (API)")
        if cache_decisions["force_refresh"]:
            breakdown_parts.append(f"{cache_decisions['force_refresh']} force refresh (API)")
        if cache_decisions["not_in_db"]:
            breakdown_parts.append(f"{cache_decisions['not_in_db']} not in DB (API)")

        if breakdown_parts:
            logger.info(f"Breakdown: {', '.join(breakdown_parts)}")

        # 4. Batch refresh products that need it (with per-entity locks + timestamp bug fix,
        #    STORY-046 AC6 + AC9, STORY-062 async session management, decoupled API/DB pattern)
        #
        # Architecture (decoupled API/DB):
        # - API fetch: OUTSIDE semaphore (~10 concurrent via HTTP client)
        # - DB write: INSIDE semaphore (default 1, serialized; configurable 2-5
        #   via MAX_CONCURRENT_DB_WRITES)
        # - Timestamp update: INSIDE same session as feature write (incremental persistence)
        #
        # This allows ~10 concurrent API calls while serializing DB writes to ~5,
        # and ensures partial failures preserve completed products.
        all_succeeded: list[int] = []
        all_failed: list[int] = []
        errors: list[str] = []

        if products_to_refresh:
            # STORY-062: Per-operation session pattern for batch operations
            # WARNING: asyncio.gather() with shared session causes "Cannot operate on a closed
            # database" errors. Each concurrent task MUST get its own session.
            # See CLAUDE.md "Async Session Management" section for details.

            # Thread-safe counter for progress reporting (PEP 703 future-proof)
            counter_lock = asyncio.Lock()
            completed_products = 0
            total_products = len(products_to_refresh)

            async def refresh_with_lock(product_id: int) -> tuple[int, str | None]:
                """Refresh features with decoupled API/DB and incremental persistence.

                Architecture:
                - Step 1: API fetch OUTSIDE semaphore (~10 concurrent via HTTP client)
                - Step 2: DB write INSIDE semaphore (~5 concurrent to prevent locks)
                - Step 3: Update timestamp in SAME transaction (incremental persistence)

                Returns:
                    Tuple of (product_id always, error message if failed else None)
                    (Fix for Issue #3: Failure Attribution Bug - always return product_id)
                """
                nonlocal completed_products  # For progress tracking

                if not self.cache:
                    # Cache is required for safe concurrent operations
                    raise RuntimeError(
                        "FeatureRepository.get_features_cached_or_refresh requires cache "
                        "for concurrent batch operations"
                    )

                lock = self.cache.get_refresh_lock("feature", product_id)
                async with lock:
                    try:
                        logger.debug(f"Acquired feature refresh lock for product {product_id}")

                        # Step 1: API fetch OUTSIDE semaphore (~10 concurrent via HTTP client)
                        # This allows many concurrent API calls while only serializing DB writes
                        features_data = await self._fetch_features_from_api(product_id)

                        # Step 2: DB write INSIDE semaphore (~5 concurrent to prevent SQLite locks)
                        async with self.cache._write_semaphore:
                            async with self.cache.async_session_maker() as isolated_session:
                                try:
                                    isolated_repo = FeatureRepository(
                                        session=isolated_session,
                                        client=self.client,
                                        customer_id=self.customer_id,
                                        cache=self.cache,
                                    )

                                    # Write features to DB
                                    await isolated_repo._write_features_to_db(
                                        features_data, product_id
                                    )

                                    # Step 3: Update timestamp in SAME transaction
                                    # (incremental persistence - features + timestamp commit
                                    # atomically)
                                    await isolated_repo._update_last_synced_in_session(product_id)

                                    # Atomic commit: features + timestamp together
                                    await isolated_session.commit()

                                except Exception:
                                    # Explicit rollback to release pending transactions immediately
                                    # (Fix for Issue #5: Missing Explicit Rollback)
                                    await isolated_session.rollback()
                                    raise

                        # Progress callback after successful product (thread-safe counter)
                        async with counter_lock:
                            completed_products += 1
                            current = completed_products
                        await safe_batch_callback(on_batch_progress, current, total_products)

                        return product_id, None

                    except Exception as e:
                        error_msg = f"{type(e).__name__}: {e!s}"
                        logger.error(
                            f"Failed to refresh features for product {product_id}: {error_msg}"
                        )

                        # Increment counter even on failure so progress reaches 100%
                        # (Codex review finding: stalled progress bars)
                        async with counter_lock:
                            completed_products += 1
                            current = completed_products
                        await safe_batch_callback(on_batch_progress, current, total_products)

                        return product_id, error_msg

            # Concurrent API calls (client semaphore enforces concurrency limit)
            # Each task has its own isolated session - safe for concurrent execution
            results = await asyncio.gather(*[refresh_with_lock(pid) for pid in products_to_refresh])

            # Aggregate results for reporting (collect & report pattern)
            # (Fix for Issue #3: Failure Attribution Bug - product_id always returned)
            for product_id, error in results:
                if error is None:
                    all_succeeded.append(product_id)
                else:
                    all_failed.append(product_id)
                    errors.append(f"Product {product_id}: {error}")

            # Log summary
            if all_failed:
                logger.warning(
                    f"Feature refresh: {len(all_succeeded)} succeeded, {len(all_failed)} failed"
                )
            else:
                total_refreshed = len(all_succeeded)
                total_to_refresh = len(products_to_refresh)
                logger.info(f"Refreshed features for {total_refreshed}/{total_to_refresh} products")

            # NOTE: Removed post-gather timestamp update - now done inside each product
            # This enables incremental persistence (partial failures preserve progress)

        # 5. Return features for ALL requested product IDs from SQLite
        # Use fresh session if we just did concurrent refreshes (prevents stale reads)
        # (Fix for Issue #2: Stale Read Bug from async-session-concurrency-review)
        result: dict[int, list[dict[str, Any]]] = {}

        # Only use fresh session if we actually refreshed any products (stale read risk)
        # Otherwise use existing long-lived session (safe - no concurrent writes happened)
        needs_fresh_session = self.cache and len(products_to_refresh) > 0

        for product_id in product_ids:
            if needs_fresh_session:
                # Use fresh session to avoid stale reads after concurrent refresh
                async with self.cache.async_session_maker() as fresh_session:  # type: ignore[union-attr]
                    # Query features from DB
                    query = select(Feature).where(Feature.product_id == product_id)
                    feature_result = await fresh_session.exec(query)
                    features = feature_result.all()

                    # Convert ORM models to dicts
                    feature_dicts = []
                    for feature in features:
                        feature_dict = {
                            "id": feature.id,
                            "product_id": feature.product_id,
                            "title": feature.title,
                            "description": feature.description,
                            "howtofind": feature.howtofind,
                            "user_stories": json.loads(feature.user_stories)
                            if feature.user_stories
                            else [],
                            "section_ids": json.loads(feature.section_ids)
                            if feature.section_ids
                            else [],
                        }
                        feature_dicts.append(feature_dict)

                    result[product_id] = feature_dicts
            else:
                # No refresh happened - safe to use long-lived session
                query = select(Feature).where(Feature.product_id == product_id)
                feature_result = await self.session.exec(query)
                features = feature_result.all()

                # Convert ORM models to dicts
                feature_dicts = []
                for feature in features:
                    feature_dict = {
                        "id": feature.id,
                        "product_id": feature.product_id,
                        "title": feature.title,
                        "description": feature.description,
                        "howtofind": feature.howtofind,
                        "user_stories": json.loads(feature.user_stories)
                        if feature.user_stories
                        else [],
                        "section_ids": json.loads(feature.section_ids)
                        if feature.section_ids
                        else [],
                    }
                    feature_dicts.append(feature_dict)

                result[product_id] = feature_dicts

        # 6. Build cache stats for transparency (includes failed product reporting)
        cache_stats = {
            "total_products": len(product_ids),
            "cache_hits": cache_hits,
            "api_calls": len(products_to_refresh),
            "api_succeeded": len(all_succeeded),
            "api_failed": len(all_failed),
            "failed_product_ids": all_failed,  # For transparency
            "errors": errors,  # Error messages for debugging
            "cache_hit_rate": cache_hit_rate,
            "breakdown": {k: v for k, v in cache_decisions.items() if v > 0},  # Only non-zero
        }

        return result, cache_stats

    async def _update_last_synced_batch(
        self, product_ids: list[int], session: AsyncSession | None = None
    ) -> None:
        """Update last_synced timestamp for multiple products (bulk update).

        STORY-062: Simplified - single last_synced timestamp for background sync.
        Uses isolated session for concurrent execution safety.

        Args:
            product_ids: List of product identifiers to update
            session: Optional session to use; if None, uses cache.async_session_maker()
                    or falls back to self.session
        """
        if not product_ids:
            return

        from testio_mcp.models.orm.product import Product

        # Use isolated session for batch timestamp updates
        # This ensures timestamps are updated consistently after concurrent operations
        if session is not None:
            # Use provided session
            target_session = session
            should_commit = False  # Caller manages commit
        elif self.cache:
            # Create isolated session via cache
            async with self.cache.async_session_maker() as isolated_session:
                now_utc = datetime.now(UTC)
                statement = select(Product).where(
                    col(Product.id).in_(product_ids), Product.customer_id == self.customer_id
                )
                update_result = await isolated_session.exec(statement)
                products = update_result.all()

                for product in products:
                    product.last_synced = now_utc
                    isolated_session.add(product)

                await isolated_session.commit()
            return
        else:
            # Fallback to self.session (legacy behavior)
            target_session = self.session
            should_commit = True

        # Bulk update using SQLModel
        now_utc = datetime.now(UTC)
        statement = select(Product).where(
            col(Product.id).in_(product_ids), Product.customer_id == self.customer_id
        )
        update_result = await target_session.exec(statement)
        products = update_result.all()

        for product in products:
            product.last_synced = now_utc
            target_session.add(product)

        if should_commit:
            await target_session.commit()

    async def _fetch_features_from_api(self, product_id: int) -> list[dict[str, Any]]:
        """Fetch features from API only (section-aware, no DB operations).

        This method is used by the decoupled API/DB pattern to fetch features
        concurrently while serializing DB writes.

        Args:
            product_id: Product ID to fetch features for

        Returns:
            List of feature dictionaries from API
        """
        # Get product data to determine if it has sections
        product_data = await self._get_product_data(product_id)

        # Use section-aware fetching (same logic as sync_features)
        if has_sections(product_data):
            return await self._sync_sectioned_product(product_id, product_data)
        else:
            return await self._sync_non_sectioned_product(product_id)

    async def _write_features_to_db(
        self, features_data: list[dict[str, Any]], product_id: int
    ) -> dict[str, int]:
        """Write features to DB using self.session (no API, no commit).

        Caller must commit the transaction.

        Args:
            features_data: Raw feature data from API
            product_id: Product ID

        Returns:
            Sync statistics: {"created": int, "updated": int, "total": int}
        """
        return await self._upsert_features(product_id, features_data)

    async def _update_last_synced_in_session(self, product_id: int) -> None:
        """Update Product.last_synced in current session (no commit).

        Uses self.session directly - caller manages transaction.
        This is used for incremental persistence where features and timestamps
        are committed together atomically per product.

        Args:
            product_id: Product ID to update
        """
        from testio_mcp.models.orm.product import Product

        result = await self.session.exec(
            select(Product).where(Product.id == product_id, Product.customer_id == self.customer_id)
        )
        product = result.first()
        if product:
            product.last_synced = datetime.now(UTC)
            self.session.add(product)
        # No commit - caller manages transaction

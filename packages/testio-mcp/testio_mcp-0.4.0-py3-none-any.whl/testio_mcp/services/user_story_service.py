"""User Story Service - Business logic for user story operations.

This service handles user story-related business logic including:
- Query user stories by product/feature
- Parse embedded user stories from Feature model
- Format responses for MCP/REST

STORY-037: Data Serving Layer (MCP Tools + REST API)
Epic: EPIC-005 (Data Enhancement and Serving)

IMPORTANT: User stories are embedded in Feature model as JSON array of title strings.
This is a temporary approach per ADR-013 until TestIO API adds 'id' field.
"""

import json
from typing import Any

from testio_mcp.repositories.feature_repository import FeatureRepository
from testio_mcp.services.base_service import BaseService


class UserStoryService(BaseService):
    """Service for user story operations.

    Business logic for user stories:
    - Query user stories by product, feature
    - Parse embedded user stories from Feature.user_stories JSON
    - Format responses for MCP/REST

    Note: User stories are embedded in Feature model (ADR-013).
    This service parses feature.user_stories JSON to expose them.
    """

    def __init__(self, feature_repo: FeatureRepository) -> None:
        """Initialize service.

        Args:
            feature_repo: FeatureRepository instance (user stories embedded in features)
        """
        # UserStoryService doesn't need client (repository handles data)
        super().__init__(client=None)  # type: ignore[arg-type]
        self.feature_repo = feature_repo

    async def list_user_stories(
        self,
        product_id: int,
        feature_id: int | None = None,
        page: int = 1,
        per_page: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List user stories for product with optional feature filter and in-memory pagination.

        Note: User stories are embedded in Feature.user_stories JSON (ADR-013).
        This method loads all features, parses JSON, then slices results in-memory.
        Performance is acceptable for MVP (< 200ms for 346 features).

        Args:
            product_id: Product ID
            feature_id: Optional feature ID filter
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 100)
            offset: Additional offset (default: 0)

        Returns:
            {
                "product_id": int,
                "feature_id": int | null,
                "user_stories": [...],
                "total": int,           # Items in current page
                "total_count": int,     # Total matching results across all pages
                "offset": int,          # Actual offset used
                "has_more": bool        # True if more results available
            }
        """
        # Load all features (cannot paginate at SQL level for embedded user stories)
        features = await self.feature_repo.get_features_for_product(product_id=product_id)

        # Filter by feature_id if provided
        if feature_id is not None:
            features = [f for f in features if f.id == feature_id]

        # Extract all user stories from features (in-memory)
        all_user_stories = []
        for feature in features:
            # Parse embedded user stories JSON
            stories = json.loads(feature.user_stories) if feature.user_stories else []
            for story_title in stories:
                all_user_stories.append(
                    {
                        "title": story_title,
                        "feature_id": feature.id,
                        "feature_title": feature.title,
                    }
                )

        # Calculate pagination (in-memory slicing)
        total_count = len(all_user_stories)
        actual_offset = offset + (page - 1) * per_page
        start_index = actual_offset
        end_index = min(actual_offset + per_page, total_count)

        # Slice results for current page
        paginated_stories = all_user_stories[start_index:end_index]

        # Determine has_more: true if there are more results beyond current page
        has_more = end_index < total_count

        return {
            "product_id": product_id,
            "feature_id": feature_id,
            "user_stories": paginated_stories,
            "total": len(paginated_stories),
            "total_count": total_count,
            "offset": actual_offset,
            "has_more": has_more,
        }

    async def get_user_story_summary(self, product_id: int) -> dict[str, Any]:
        """Get user story summary statistics.

        Args:
            product_id: Product ID

        Returns:
            {
                "product_id": int,
                "total_user_stories": int,
                "by_feature": {feature_id: count, ...}
            }
        """
        features = await self.feature_repo.get_features_for_product(product_id=product_id)

        total = 0
        by_feature: dict[int, int] = {}

        for feature in features:
            stories = json.loads(feature.user_stories) if feature.user_stories else []
            count = len(stories)
            total += count
            if count > 0:
                by_feature[feature.id] = count

        return {
            "product_id": product_id,
            "total_user_stories": total,
            "by_feature": by_feature if by_feature else None,
        }

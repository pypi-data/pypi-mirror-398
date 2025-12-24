"""Feature Service - Business logic for feature operations.

This service handles feature-related business logic including:
- Query features by product
- Format responses for MCP/REST

STORY-037: Data Serving Layer (MCP Tools + REST API)
Epic: EPIC-005 (Data Enhancement and Serving)
"""

import json
from typing import Any

from testio_mcp.models.orm import Feature
from testio_mcp.repositories.feature_repository import FeatureRepository
from testio_mcp.services.base_service import BaseService


class FeatureService(BaseService):
    """Service for feature operations.

    Business logic for features:
    - Query features by product
    - Format responses for MCP/REST

    Inherits from BaseService for:
    - Standard constructor (client injection)

    Note: FeatureService uses repository pattern (not API client directly).
    """

    def __init__(self, feature_repo: FeatureRepository) -> None:
        """Initialize service.

        Args:
            feature_repo: FeatureRepository instance
        """
        # FeatureService doesn't need client (repository handles data)
        super().__init__(client=None)  # type: ignore[arg-type]
        self.feature_repo = feature_repo

    async def list_features(
        self,
        product_id: int,
        page: int = 1,
        per_page: int = 100,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str = "asc",
        has_user_stories: bool | None = None,
    ) -> dict[str, Any]:
        """List features for product with pagination and sorting.

        STORY-055: Adds sorting support.
        STORY-055 Fix: Now includes test_count and bug_count in response.
        STORY-058: Adds has_user_stories filter parameter.

        Args:
            product_id: Product ID
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 100)
            offset: Additional offset (default: 0)
            sort_by: Field to sort by (title, test_count, bug_count, last_synced),
                default: None
            sort_order: Sort direction (asc, desc), default: asc
            has_user_stories: Filter by user story presence (True = only with stories),
                default: None

        Returns:
            {
                "product_id": int,
                "features": [
                    {
                        "id": int,
                        "title": str,
                        "description": str | null,
                        "howtofind": str | null,
                        "user_story_count": int,
                        "test_count": int,
                        "bug_count": int
                    },
                    ...
                ],
                "total": int,           # Items in current page
                "total_count": int,     # Total matching results across all pages
                "offset": int,          # Actual offset used
                "has_more": bool        # Pagination heuristic
            }
        """
        # STORY-055: Always use query_features (now returns counts for all queries)
        # STORY-058: Pass through has_user_stories filter
        feature_dicts = await self.feature_repo.query_features(
            product_id=product_id,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page,
            offset=offset,
            has_user_stories=has_user_stories,
        )

        # Get total count for pagination metadata (with same filter applied)
        # FIX: Pass has_user_stories to count_features for accurate total_count
        total_count = await self.feature_repo.count_features(
            product_id=product_id, has_user_stories=has_user_stories
        )

        # Calculate actual offset
        actual_offset = offset + (page - 1) * per_page

        # Determine has_more (exact: check if more results exist beyond current page)
        has_more = (actual_offset + len(feature_dicts)) < total_count

        return {
            "product_id": product_id,
            "features": [self._format_feature_with_counts(fd) for fd in feature_dicts],
            "total": len(feature_dicts),
            "total_count": total_count,
            "offset": actual_offset,
            "has_more": has_more,
        }

    async def get_feature_summary(self, feature_id: int) -> dict[str, Any]:
        """Get feature summary with metadata and computed counts.

        STORY-057: Renamed from product-level summary to single-feature summary.

        SQLite-only (no API calls). Uses cached data with counts computed via subqueries.

        Args:
            feature_id: Feature identifier

        Returns:
            Feature summary with metadata, user stories, and counts

        Raises:
            FeatureNotFoundException: If feature not found

        Example:
            >>> summary = await service.get_feature_summary(123)
            >>> print(summary["test_count"])
            15
        """
        from datetime import UTC, datetime

        from testio_mcp.exceptions import FeatureNotFoundException

        feature_with_counts = await self.feature_repo.get_feature_with_counts(feature_id)

        if not feature_with_counts:
            raise FeatureNotFoundException(feature_id)

        # Add data_as_of timestamp for staleness visibility (AC requirement)
        return {
            **feature_with_counts,
            "data_as_of": datetime.now(UTC).isoformat(),
        }

    def _format_feature(self, feature: Feature) -> dict[str, Any]:
        """Format feature for response.

        Args:
            feature: Feature ORM model

        Returns:
            Formatted feature dict
        """
        # Parse embedded user stories JSON
        user_stories = json.loads(feature.user_stories) if feature.user_stories else []

        return {
            "id": feature.id,
            "title": feature.title,
            "description": feature.description,
            "howtofind": feature.howtofind,
            "user_story_count": len(user_stories),
        }

    def _format_feature_with_counts(self, feature_dict: dict[str, Any]) -> dict[str, Any]:
        """Format feature with computed counts for response.

        STORY-055 Fix: Includes test_count and bug_count from query_features.

        Args:
            feature_dict: Dict with "feature", "test_count", "bug_count" keys

        Returns:
            Formatted feature dict with counts
        """
        feature = feature_dict["feature"]
        user_stories = json.loads(feature.user_stories) if feature.user_stories else []

        return {
            "id": feature.id,
            "title": feature.title,
            "description": feature.description,
            "howtofind": feature.howtofind,
            "user_story_count": len(user_stories),
            "test_count": feature_dict["test_count"],
            "bug_count": feature_dict["bug_count"],
        }

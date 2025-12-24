"""Unit tests for TestRepository referential integrity pattern (STORY-044C).

Tests the proactive integrity check methods that prevent FK violations:
- _feature_exists(): Check if feature exists locally
- _fetch_and_store_features_for_product(): Fetch missing features via composition

Pattern: Mock database and repository dependencies, verify behavior in isolation.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.repositories.test_repository import TestRepository


@pytest.mark.unit
@pytest.mark.asyncio
class TestFeatureExistsMethod:
    """Test _feature_exists() helper method."""

    async def test_feature_exists_returns_true_when_feature_in_database(self) -> None:
        """Given feature exists in database, _feature_exists should return True."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)

        # Mock exec result: feature found
        mock_result = MagicMock()
        mock_result.first.return_value = 123  # Feature ID exists
        mock_session.exec.return_value = mock_result

        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        # Act
        exists = await repo._feature_exists(feature_id=123)

        # Assert
        assert exists is True
        mock_session.exec.assert_called_once()  # Verify query was executed

    async def test_feature_exists_returns_false_when_feature_missing(self) -> None:
        """Given feature missing from database, _feature_exists should return False."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)

        # Mock exec result: feature not found
        mock_result = MagicMock()
        mock_result.first.return_value = None  # No feature found
        mock_session.exec.return_value = mock_result

        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        # Act
        exists = await repo._feature_exists(feature_id=999)

        # Assert
        assert exists is False
        mock_session.exec.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestFetchAndStoreFeatures:
    """Test _fetch_and_store_features_for_product() composition pattern."""

    async def test_creates_feature_repository_with_correct_dependencies(self) -> None:
        """Should create FeatureRepository via composition with shared session/client."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        customer_id = 1
        product_id = 456

        # Mock count query: no features exist (trigger fetch)
        mock_count_result = MagicMock()
        mock_count_result.one.return_value = 0  # No features
        mock_session.exec.return_value = mock_count_result

        repo = TestRepository(session=mock_session, client=mock_client, customer_id=customer_id)

        # Mock FeatureRepository (import happens inside method, patch at source)
        with patch(
            "testio_mcp.repositories.feature_repository.FeatureRepository"
        ) as MockFeatureRepo:
            mock_feature_repo_instance = AsyncMock()
            mock_feature_repo_instance.sync_features.return_value = {"total": 10}
            MockFeatureRepo.return_value = mock_feature_repo_instance

            # Act
            await repo._fetch_and_store_features_for_product(product_id)

            # Assert: FeatureRepository created with correct args
            MockFeatureRepo.assert_called_once_with(
                mock_session,  # Same session (transaction integrity)
                mock_client,  # Same client
                customer_id,  # Same customer_id
            )

            # Assert: sync_features called with product_id
            mock_feature_repo_instance.sync_features.assert_called_once_with(product_id)

    async def test_acquires_lock_to_prevent_thundering_herd(self) -> None:
        """Should acquire per-product lock before fetching features."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        product_id = 789

        # Mock count query: no features exist
        mock_count_result = MagicMock()
        mock_count_result.one.return_value = 0
        mock_session.exec.return_value = mock_count_result

        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        # Mock FeatureRepository (import happens inside method, patch at source)
        with patch(
            "testio_mcp.repositories.feature_repository.FeatureRepository"
        ) as MockFeatureRepo:
            mock_feature_repo_instance = AsyncMock()
            mock_feature_repo_instance.sync_features.return_value = {"total": 5}
            MockFeatureRepo.return_value = mock_feature_repo_instance

            # Act
            await repo._fetch_and_store_features_for_product(product_id)

            # Assert: Lock was created for this product_id
            assert product_id in repo._feature_fetch_locks
            assert isinstance(repo._feature_fetch_locks[product_id], asyncio.Lock)

    async def test_double_check_pattern_skips_fetch_if_features_exist(self) -> None:
        """Should skip fetch if features exist after acquiring lock (another coroutine fetched)."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        product_id = 999

        # Mock count query: features NOW exist (double-check finds them)
        mock_count_result = MagicMock()
        mock_count_result.one.return_value = 15  # Features exist!
        mock_session.exec.return_value = mock_count_result

        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        # Mock FeatureRepository (import happens inside method, patch at source)
        with patch(
            "testio_mcp.repositories.feature_repository.FeatureRepository"
        ) as MockFeatureRepo:
            mock_feature_repo_instance = AsyncMock()
            MockFeatureRepo.return_value = mock_feature_repo_instance

            # Act
            await repo._fetch_and_store_features_for_product(product_id)

            # Assert: FeatureRepository was NOT created (double-check skipped)
            MockFeatureRepo.assert_not_called()
            mock_feature_repo_instance.sync_features.assert_not_called()

    async def test_raises_exception_on_sync_failure(self) -> None:
        """Should propagate exception if FeatureRepository.sync_features fails."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        product_id = 111

        # Mock count query: no features exist
        mock_count_result = MagicMock()
        mock_count_result.one.return_value = 0
        mock_session.exec.return_value = mock_count_result

        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        # Mock FeatureRepository to raise exception (import happens inside method, patch at source)
        with patch(
            "testio_mcp.repositories.feature_repository.FeatureRepository"
        ) as MockFeatureRepo:
            mock_feature_repo_instance = AsyncMock()
            mock_feature_repo_instance.sync_features.side_effect = Exception("API timeout")
            MockFeatureRepo.return_value = mock_feature_repo_instance

            # Act & Assert: Exception should propagate (caller handles graceful degradation)
            with pytest.raises(Exception, match="API timeout"):
                await repo._fetch_and_store_features_for_product(product_id)


@pytest.mark.unit
@pytest.mark.asyncio
class TestUpsertTestFeatureIntegrity:
    """Test _upsert_test_feature() proactive integrity checks (AC1)."""

    async def test_skips_integrity_check_when_feature_exists(self) -> None:
        """Given feature exists, should NOT trigger integrity fill."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)

        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        # Mock _feature_exists to return True (feature exists)
        with patch.object(repo, "_feature_exists", return_value=True):
            with patch.object(repo, "_fetch_and_store_features_for_product") as mock_fetch:
                # Mock TestFeature query: not exists (insert path)
                mock_result = MagicMock()
                mock_result.first.return_value = None
                mock_session.exec.return_value = mock_result

                feature_data = {
                    "id": 1001,
                    "feature_id": 500,
                    "title": "Test Feature",
                    "user_stories": ["Story 1"],
                }

                # Act
                await repo._upsert_test_feature(
                    test_id=100, feature_data=feature_data, product_id=10
                )

                # Assert: Integrity fill NOT triggered
                mock_fetch.assert_not_called()

    async def test_triggers_integrity_fill_when_feature_missing(self) -> None:
        """Given feature missing, should trigger _fetch_and_store_features_for_product."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        product_id = 20

        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        # Mock _feature_exists to return False (feature missing)
        with patch.object(repo, "_feature_exists", return_value=False):
            with patch.object(repo, "_fetch_and_store_features_for_product") as mock_fetch:
                mock_fetch.return_value = None  # Successful fetch

                # Mock TestFeature query: not exists (insert path)
                mock_result = MagicMock()
                mock_result.first.return_value = None
                mock_session.exec.return_value = mock_result

                feature_data = {
                    "id": 2002,
                    "feature_id": 600,
                    "title": "Missing Feature",
                    "user_stories": [],
                }

                # Act
                await repo._upsert_test_feature(
                    test_id=200, feature_data=feature_data, product_id=product_id
                )

                # Assert: Integrity fill WAS triggered
                mock_fetch.assert_called_once_with(product_id)

    async def test_skips_upsert_when_integrity_fill_fails(self) -> None:
        """Given integrity fill fails, should skip test_feature upsert.

        Tests AC8 graceful degradation.
        """
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)

        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        # Mock _feature_exists to return False (feature missing)
        with patch.object(repo, "_feature_exists", return_value=False):
            with patch.object(repo, "_fetch_and_store_features_for_product") as mock_fetch:
                mock_fetch.side_effect = Exception("API failure")  # Fetch fails

                feature_data = {
                    "id": 3003,
                    "feature_id": 700,
                    "title": "Failed Feature",
                    "user_stories": None,
                }

                # Act (should NOT raise exception - graceful degradation)
                await repo._upsert_test_feature(
                    test_id=300, feature_data=feature_data, product_id=30
                )

                # Assert: session.add was NOT called (upsert skipped)
                mock_session.add.assert_not_called()

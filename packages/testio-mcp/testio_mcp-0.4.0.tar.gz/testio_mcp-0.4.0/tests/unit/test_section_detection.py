"""Unit tests for section detection utilities.

Tests validate the section detection logic copied from research_features_api.py
and ensure correct handling of legacy non-section products (default-section).
"""

import pytest

from testio_mcp.utilities.section_detection import get_section_ids, has_sections


@pytest.mark.unit
class TestHasSections:
    """Tests for has_sections() function."""

    def test_no_sections_empty_arrays(self) -> None:
        """Product with empty sections arrays is non-section."""
        product = {"sections": [], "sections_with_default": []}
        assert has_sections(product) is False

    def test_no_sections_missing_keys(self) -> None:
        """Product missing sections keys is non-section."""
        product = {}  # type: ignore[var-annotated]
        assert has_sections(product) is False

    def test_default_section_only_is_non_section(self) -> None:
        """Product with single default-section is legacy non-section.

        This is the CRITICAL test case that validates the fix.
        Flourish (21362) has sections_with_default=[default-section] but uses
        non-section endpoint: GET /products/21362/features (no section_id).
        """
        product = {
            "sections": [],
            "sections_with_default": [{"id": 21855, "name": "default-section"}],
        }
        assert has_sections(product) is False

    def test_real_sections_array(self) -> None:
        """Product with sections array is section product."""
        product = {"sections": [{"id": 100}, {"id": 101}]}
        assert has_sections(product) is True

    def test_multiple_sections_with_default(self) -> None:
        """Product with multiple sections_with_default is section product."""
        product = {
            "sections": [],
            "sections_with_default": [
                {"id": 25543, "name": "Section 1"},
                {"id": 25544, "name": "Section 2"},
            ],
        }
        assert has_sections(product) is True

    def test_both_sections_and_sections_with_default(self) -> None:
        """Product with both arrays prefers sections (non-empty)."""
        product = {
            "sections": [{"id": 100}],
            "sections_with_default": [{"id": 200}, {"id": 201}],
        }
        assert has_sections(product) is True

    def test_flourish_real_product(self) -> None:
        """Integration-like test with real Flourish product structure."""
        product = {
            "id": 21362,
            "sections": [],
            "sections_with_default": [
                {
                    "id": 21855,
                    "name": "default-section",
                    "features_amount": 28,
                    "user_stories_amount": 54,
                }
            ],
        }
        assert has_sections(product) is False

    def test_canva_real_product(self) -> None:
        """Integration-like test with real Canva product structure."""
        product = {
            "id": 18559,
            "sections": [
                {"id": 22041, "name": "Section 1"},
                {"id": 22042, "name": "Section 2"},
            ],
        }
        assert has_sections(product) is True


@pytest.mark.unit
class TestGetSectionIds:
    """Tests for get_section_ids() function."""

    def test_no_sections_empty_list(self) -> None:
        """Product with no sections returns empty list."""
        product = {"sections": [], "sections_with_default": []}
        assert get_section_ids(product) == []

    def test_no_sections_missing_keys(self) -> None:
        """Product missing sections keys returns empty list."""
        product = {}  # type: ignore[var-annotated]
        assert get_section_ids(product) == []

    def test_extract_from_sections_array(self) -> None:
        """Extract IDs from sections array."""
        product = {"sections": [{"id": 100}, {"id": 101}, {"id": 102}]}
        assert get_section_ids(product) == [100, 101, 102]

    def test_extract_from_sections_with_default(self) -> None:
        """Extract IDs from sections_with_default array."""
        product = {
            "sections": [],
            "sections_with_default": [{"id": 200}, {"id": 201}],
        }
        assert get_section_ids(product) == [200, 201]

    def test_prioritize_sections_over_sections_with_default(self) -> None:
        """Prefer sections array when both exist."""
        product = {
            "sections": [{"id": 100}, {"id": 101}],
            "sections_with_default": [{"id": 200}, {"id": 201}],
        }
        assert get_section_ids(product) == [100, 101]

    def test_default_section_single_id(self) -> None:
        """Extract single default-section ID."""
        product = {
            "sections": [],
            "sections_with_default": [{"id": 21855, "name": "default-section"}],
        }
        assert get_section_ids(product) == [21855]

    def test_malformed_section_missing_id(self) -> None:
        """Skip sections without 'id' field."""
        product = {"sections": [{"id": 100}, {"name": "no-id"}, {"id": 101}]}
        assert get_section_ids(product) == [100, 101]

    def test_empty_sections_array_uses_default(self) -> None:
        """Empty sections array falls back to sections_with_default."""
        product = {
            "sections": [],
            "sections_with_default": [{"id": 300}],
        }
        assert get_section_ids(product) == [300]

    def test_flourish_real_product_ids(self) -> None:
        """Extract section ID from real Flourish product."""
        product = {
            "sections": [],
            "sections_with_default": [{"id": 21855, "name": "default-section"}],
        }
        assert get_section_ids(product) == [21855]

    def test_canva_real_product_ids(self) -> None:
        """Extract section IDs from real Canva product."""
        product = {
            "sections": [
                {"id": 22041, "name": "Section 1"},
                {"id": 22042, "name": "Section 2"},
            ],
        }
        assert get_section_ids(product) == [22041, 22042]

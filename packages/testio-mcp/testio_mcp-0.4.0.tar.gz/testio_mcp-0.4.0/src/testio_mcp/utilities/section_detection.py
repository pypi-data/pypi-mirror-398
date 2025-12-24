"""Section detection utilities for TestIO products.

This module provides helpers to determine if a product uses section-based organization
and extract section IDs. This logic is shared across FeatureRepository and
UserStoryRepository to ensure consistent behavior.

Key Insight (Validated 2025-11-23):
- Products with `sections=[]` and `sections_with_default=[single-default-section]` are
  LEGACY non-section products (e.g., Flourish 21362)
- Check: `len(sections) > 0 OR len(sections_with_default) > 1`
- The `> 1` threshold correctly identifies default-section as non-section
"""

from typing import Any


def has_sections(product: dict[str, Any]) -> bool:
    """Detect if product uses section-based organization.

    Section detection logic (validated via research_features_api.py):
    - Real sections: len(sections) > 0
    - Legacy non-section: len(sections_with_default) == 1 (default-section only)
    - Multi-section: len(sections_with_default) > 1

    Examples:
        >>> # Flourish (21362) - Legacy non-section product
        >>> product = {
        ...     "sections": [],
        ...     "sections_with_default": [{"id": 21855, "name": "default-section"}]
        ... }
        >>> has_sections(product)
        False

        >>> # Canva (18559) - Section product
        >>> product = {"sections": [{"id": 100}, {"id": 101}]}
        >>> has_sections(product)
        True

        >>> # remove.bg (24959) - Section product
        >>> product = {"sections_with_default": [
        ...     {"id": 25543, "name": "Section 1"},
        ...     {"id": 25544, "name": "Section 2"}
        ... ]}
        >>> has_sections(product)
        True

    Args:
        product: Product data dictionary from TestIO API

    Returns:
        True if product uses sections, False otherwise
    """
    sections = product.get("sections", [])
    sections_with_default = product.get("sections_with_default", [])
    return len(sections) > 0 or len(sections_with_default) > 1


def get_section_ids(product: dict[str, Any]) -> list[int]:
    """Extract section IDs from product data.

    Handles both `sections` and `sections_with_default` arrays.
    Priority: `sections` (if non-empty), else `sections_with_default`.

    Examples:
        >>> # Product with sections array
        >>> product = {"sections": [{"id": 100}, {"id": 101}]}
        >>> get_section_ids(product)
        [100, 101]

        >>> # Product with sections_with_default only
        >>> product = {
        ...     "sections": [],
        ...     "sections_with_default": [{"id": 25543}, {"id": 25544}]
        ... }
        >>> get_section_ids(product)
        [25543, 25544]

        >>> # No sections
        >>> product = {"sections": [], "sections_with_default": []}
        >>> get_section_ids(product)
        []

    Args:
        product: Product data dictionary from TestIO API

    Returns:
        List of section IDs (empty if no sections)
    """
    sections = product.get("sections", [])
    sections_with_default = product.get("sections_with_default", [])

    # Priority: sections (if non-empty), else sections_with_default
    source = sections if sections else sections_with_default

    return [section["id"] for section in source if "id" in section]

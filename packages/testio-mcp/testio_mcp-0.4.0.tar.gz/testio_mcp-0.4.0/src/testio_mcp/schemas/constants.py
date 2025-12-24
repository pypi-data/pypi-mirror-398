"""Shared constants for test schemas and validation.

This module provides a single source of truth for test-related constants
to prevent definition drift across services, tools, and utilities.
"""

from typing import Literal

# Test status values (complete list from TestIO API)
TestStatus = Literal[
    "running", "locked", "archived", "cancelled", "customer_finalized", "initialized"
]

VALID_TEST_STATUSES = [
    "running",
    "locked",
    "archived",
    "cancelled",
    "customer_finalized",
    "initialized",
]

# Default statuses for quality metrics (excludes unexecuted tests)
# Used by: get_product_quality_report, query_metrics
# Rationale: Quality metrics should reflect only executed tests
EXECUTED_TEST_STATUSES = [
    "running",
    "locked",
    "archived",
    "customer_finalized",
]

# Searchable entity types (STORY-064 - FTS5 Infrastructure)
SEARCHABLE_ENTITIES = ("product", "feature", "test", "bug")

# Entity → indexed fields mapping (single source of truth for FTS5 content)
# Maps each entity type to the tuple of fields used for full-text search indexing
SEARCH_CONTENT_FIELDS: dict[str, tuple[str, ...]] = {
    "product": ("title",),
    "feature": ("title", "description", "howtofind", "user_stories"),
    "test": ("title", "goal", "instructions", "out_of_scope"),
    "bug": ("title", "steps", "actual_result", "expected_result"),
}

# Rejection reasons for parsing bug comments (STORY-067)
REJECTION_REASONS = [
    {
        "key": "device_not_relevant",
        "default_comment": "This device is not relevant and the bug will not be fixed.",
    },
    {"key": "ignored_instructions", "default_comment": "The test instructions were not followed."},
    {
        "key": "intended_behavior",
        "default_comment": "The behaviour/design described here is intentional.",
    },
    {"key": "irrelevant", "default_comment": "This bug is not relevant and will not be fixed."},
    {"key": "known_bug", "default_comment": "This is a legit bug but already known."},
    {
        "key": "not_reproducible",
        "default_comment": (
            "With the information provided it was not possible to reproduce this bug."
        ),
    },
    {
        "key": "request_timeout",
        "default_comment": (
            "Your bug was rejected automatically, because you didn't respond to the "
            "request within 24 hours"
        ),
    },
]

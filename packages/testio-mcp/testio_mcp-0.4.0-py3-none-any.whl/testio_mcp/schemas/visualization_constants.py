"""Visualization hint constants and thresholds.

Configurable constants for the visualization hint system that recommends
chart types based on query dimensions, metrics, and result cardinality.

These values are designed to be easily tunable without code changes.
Consider moving to environment variables if runtime configurability is needed.
"""

# =============================================================================
# ROW/SERIES COUNT THRESHOLDS
# =============================================================================

# Maximum categories for pie chart (more than this → horizontal_bar)
# Rationale: Beyond 7 slices, pie charts become difficult to read
PIE_MAX_CATEGORIES: int = 7

# Maximum rows for bar charts (more than this → table fallback)
# Rationale: Beyond 15 bars, horizontal bar charts become cluttered
BAR_MAX_ROWS: int = 15

# Maximum series for multi-line charts (more than this → table fallback)
# Rationale: Beyond 8 lines, line charts become unreadable
MULTI_LINE_MAX_SERIES: int = 8


# =============================================================================
# DIMENSION CLASSIFICATION
# =============================================================================

# Time dimensions - suitable for line charts (x-axis = time)
TIME_DIMS: frozenset[str] = frozenset(
    {
        "month",
        "week",
        "quarter",
        "day",
        "date",
        "year",
    }
)

# Categorical dimensions - suitable for pie (small N) or bar charts
# These have a fixed, small set of possible values
CATEGORICAL_DIMS: frozenset[str] = frozenset(
    {
        "severity",
        "status",
        "testing_type",
        "rejection_reason",
        "known_bug",
    }
)

# Entity dimensions - suitable for bar charts (ranked comparison)
# These can have many unique values (features, testers, etc.)
ENTITY_DIMS: frozenset[str] = frozenset(
    {
        "feature",
        "tester",
        "customer",
        "product",
        "platform",
        "test_environment",
    }
)


# =============================================================================
# METRIC CLASSIFICATION
# =============================================================================

# Rate metrics - values between 0.0 and 1.0 (or small floats like bugs_per_test)
# These should use a secondary y-axis when combined with count metrics
RATE_METRICS: frozenset[str] = frozenset(
    {
        "overall_acceptance_rate",
        "rejection_rate",
        "review_rate",
        "active_acceptance_rate",
        "auto_acceptance_rate",
        "bugs_per_test",
    }
)

# Count metrics - integer values (can be large)
# These use the primary y-axis
COUNT_METRICS: frozenset[str] = frozenset(
    {
        "bug_count",
        "test_count",
        "features_tested",
        "active_testers",
        "tests_created",
        "tests_submitted",
        "bug_severity_score",
    }
)

# Analytics Engine Guide

Query TestIO data with flexible pivot tables - no SQL required.

**Implementation:**
- MCP Tool: [`src/testio_mcp/tools/query_metrics_tool.py`](../src/testio_mcp/tools/query_metrics_tool.py)
- Service Layer: [`src/testio_mcp/services/analytics_service.py`](../src/testio_mcp/services/analytics_service.py)
- Repository: [`src/testio_mcp/repositories/analytics_repository.py`](../src/testio_mcp/repositories/analytics_repository.py)
- Architecture: [`docs/architecture/ARCHITECTURE.md`](architecture/ARCHITECTURE.md)

---

## Quick Start

**Chat prompts → tool calls:**

| You ask... | Tool call |
|------------|-----------|
| "Show bugs by severity" | `query_metrics(metrics=["bug_count"], dimensions=["severity"])` |
| "Monthly bug trends" | `query_metrics(metrics=["bug_count"], dimensions=["month"])` |
| "Bugs by feature and platform" | `query_metrics(metrics=["bug_count"], dimensions=["feature", "platform"])` |

**Direct tool call:**

```python
query_metrics(
    metrics=["bug_count", "rejection_rate"],
    dimensions=["feature"],
    filters={"product_id": 598},
    start_date="last 30 days"
)
```

---

## Core Concepts

### Dimensions (How to slice data)

Dimensions are **grouping categories** - they determine the rows in your results.

| Dimension | Groups By | Example Values |
|-----------|-----------|----------------|
| `feature` | Feature Title | Login, Dashboard, Checkout |
| `product` | Product Name | Canva iOS, Zoom Android |
| `platform` | Operating System | iOS, Android, Windows |
| `tester` | Bug Reporter Username | alice, bob, charlie |
| `customer` | Test Creator | acme_corp, beta_user_1 |
| `severity` | Bug Severity | critical, major, minor |
| `status` | Bug Status | accepted, rejected, pending |
| `testing_type` | Test Type | coverage, focused, rapid |
| `rejection_reason` | Why Bug Rejected | not_reproducible, duplicate |
| `month` | Time Bucket (Monthly) | 2024-11, 2024-12 |
| `week` | Time Bucket (Weekly) | 2024-W47, 2024-W48 |
| `quarter` | Time Bucket (Quarterly) | 2024-Q3, 2024-Q4 |
| `test_environment` | Test Environment | iOS 14, Android 12 |
| `known_bug` | Known Bug Flag | true, false |

### Metrics (What to measure)

Metrics are **aggregations** - they determine the numbers in your results.

| Metric | Description | Formula |
|--------|-------------|---------|
| `test_count` | Number of tests | COUNT(DISTINCT test_id) |
| `bug_count` | Number of bugs | COUNT(DISTINCT bug_id) |
| `features_tested` | Unique features tested | COUNT(DISTINCT feature_id) |
| `active_testers` | Unique bug reporters | COUNT(DISTINCT user_id) |
| `bugs_per_test` | Bug density (fragility) | bug_count / test_count |
| `bug_severity_score` | Weighted severity | critical=5, major=3, minor=1 |

**Rate Metrics (percentages):**

| Metric | Description | Formula | Healthy |
|--------|-------------|---------|---------|
| `overall_acceptance_rate` | All accepted bugs / total | `(accepted + auto_accepted) / total` | Higher is better |
| `rejection_rate` | Rejected bugs / total | `rejected / total` | < 20% |
| `review_rate` | Human-reviewed bugs / total | `(accepted + rejected) / total` | > 80% |
| `active_acceptance_rate` | Manually accepted bugs / total | `accepted / total` | Higher is better |
| `auto_acceptance_rate` | Auto-accepted / all accepted | `auto_accepted / (accepted + auto_accepted)` | < 20% |

**Customer Activity Metrics:**

| Metric | Description | Formula |
|--------|-------------|---------|
| `tests_created` | Tests created by customers | `COUNT(DISTINCT test_id WHERE created_by IS NOT NULL)` |
| `tests_submitted` | Tests submitted for review | `COUNT(DISTINCT test_id WHERE submitted_by IS NOT NULL)` |

---

## Query Patterns

### Pattern 1: Single Dimension

*"Which features have the most bugs?"*

```python
query_metrics(
    metrics=["bug_count"],
    dimensions=["feature"],
    sort_by="bug_count",
    sort_order="desc"
)
```

**Result:**
```
| feature_id | feature        | bug_count |
|------------|----------------|-----------|
| 42         | Login          | 28        |
| 67         | Checkout       | 21        |
| 53         | Dashboard      | 15        |
```

### Pattern 2: Two Dimensions (Pivot Table)

*"How do bugs distribute across features and platforms?"*

```python
query_metrics(
    metrics=["bug_count"],
    dimensions=["feature", "platform"],
    sort_by="bug_count"
)
```

**Result:**
```
| feature_id | feature  | platform_id | platform | bug_count |
|------------|----------|-------------|----------|-----------|
| 42         | Login    | 1           | iOS      | 18        |
| 42         | Login    | 2           | Android  | 10        |
| 67         | Checkout | 1           | iOS      | 12        |
| 67         | Checkout | 2           | Android  | 9         |
```

### Pattern 3: Time Trends

*"Show monthly bug volume for the past quarter"*

```python
query_metrics(
    metrics=["bug_count", "test_count"],
    dimensions=["month"],
    start_date="3 months ago",
    sort_by="month",
    sort_order="asc"
)
```

**Result:**
```
| month   | bug_count | test_count |
|---------|-----------|------------|
| 2024-09 | 45        | 8          |
| 2024-10 | 62        | 12         |
| 2024-11 | 38        | 6          |
```

### Pattern 4: Filtered Analysis

*"Show critical bugs by feature for product 598"*

```python
query_metrics(
    metrics=["bug_count"],
    dimensions=["feature"],
    filters={"product_id": 598, "severity": "critical"},
    sort_by="bug_count"
)
```

### Pattern 5: Quality Rates

*"Compare rejection rates across platforms"*

```python
query_metrics(
    metrics=["bug_count", "rejection_rate", "review_rate"],
    dimensions=["platform"],
    start_date="last 30 days"
)
```

**Result:**
```
| platform | bug_count | rejection_rate | review_rate |
|----------|-----------|----------------|-------------|
| iOS      | 156       | 0.32           | 0.78        |
| Android  | 98        | 0.18           | 0.92        |
| Web      | 43        | 0.12           | 0.95        |
```

### Pattern 6: Tester Performance

*"Who are the most active testers?"*

```python
query_metrics(
    metrics=["bug_count", "overall_acceptance_rate"],
    dimensions=["tester"],
    start_date="this quarter",
    sort_by="bug_count",
    limit=10
)
```

**Result:**
```
| tester_id | tester  | bug_count | overall_acceptance_rate |
|-----------|---------|-----------|-------------------------|
| 26        | alice   | 185       | 0.82                    |
| 1         | bob     | 145       | 0.76                    |
| 75        | charlie | 133       | 0.91                    |
```

**Note:** Use `active_testers` for aggregate counts (e.g., `dimensions=["month"]`), not with `tester` dimension where it always equals 1 per row.

### Pattern 7: Feature Fragility

*"Which features have the highest bug density?"*

```python
query_metrics(
    metrics=["bugs_per_test", "bug_count", "test_count"],
    dimensions=["feature"],
    sort_by="bugs_per_test",
    limit=10
)
```

**Note:** `bugs_per_test` automatically includes `test_count` for context when comparing single-test vs multi-test features.

---

## Date Filtering

Dates filter on `Test.end_at` (when the test cycle completed).

**Timezone:** All dates are interpreted and compared in **UTC**. TestIO stores timestamps in UTC.

**Boundaries:** Date ranges are **inclusive** on both ends:
- `start_date="2024-11-01"` → includes tests ending on or after 2024-11-01 00:00:00 UTC
- `end_date="2024-11-30"` → includes tests ending on or before 2024-11-30 23:59:59 UTC

**Supported formats:**

| Format | Example | Meaning |
|--------|---------|---------|
| ISO 8601 | `2024-11-01` | Specific date (start of day UTC) |
| Relative | `7 days ago` | Rolling window from today |
| Named | `last week` | Previous 7 days |
| Named | `last month` | Previous 30 days |
| Named | `last quarter` | Previous 90 days |
| Named | `this quarter` | Current quarter |
| Named | `today` | Today only |
| Year-based | `YTD` | Year to date |

**Examples:**

```python
# Last 30 days
query_metrics(..., start_date="30 days ago")

# Q3 2024 (inclusive)
query_metrics(..., start_date="2024-07-01", end_date="2024-09-30")

# This year
query_metrics(..., start_date="YTD")
```

---

## Filters

Filter results by dimension values. All filters are AND-combined.

**Filter by dimension value:**

```python
# Single value
filters={"severity": "critical"}

# Multiple values (OR within filter)
filters={"severity": ["critical", "major"]}

# Combined filters (AND between filters)
filters={"severity": "critical", "status": "accepted"}
```

**Special filters:**

| Filter | Description | Example |
|--------|-------------|---------|
| `product_id` | Scope to single product | `{"product_id": 598}` |
| `status` | Test status filter | `{"status": ["running", "locked"]}` |

**Default status filter:**

By default, `query_metrics` includes only **executed tests**:
- ✅ Included: `running`, `locked`, `archived`, `customer_finalized`
- ❌ Excluded: `initialized` (not started), `cancelled` (never executed)

Override with explicit status filter:

```python
# Include all test statuses (including unexecuted)
filters={"status": ["running", "locked", "archived", "cancelled", "customer_finalized", "initialized"]}
```

---

## Response Format

Every query returns structured data with metadata:

```json
{
  "data": [
    {"feature_id": 42, "feature": "Login", "bug_count": 28},
    {"feature_id": 67, "feature": "Checkout", "bug_count": 21}
  ],
  "metadata": {
    "total_rows": 15,
    "dimensions_used": ["feature"],
    "metrics_used": ["bug_count"],
    "query_time_ms": 45
  },
  "query_explanation": "Showing bug count grouped by feature, sorted by bug_count descending",
  "warnings": []
}
```

**Rich context:** Results include both IDs (`feature_id`) and display names (`feature`) for each dimension.

**Warnings:** The system warns you about:
- Results limited to 1000 rows
- Data refresh triggered during query
- Date range spanning long periods

---

## Discovery Tool

Call `get_analytics_capabilities()` to see all available dimensions and metrics:

```bash
"What metrics can I analyze?"
```

**Returns:**

```json
{
  "dimensions": [
    {"key": "feature", "description": "Group by Feature Title", "example": "Login, Signup, Dashboard"},
    {"key": "month", "description": "Group by Month (test end date)", "example": "2024-11, 2024-12"}
  ],
  "metrics": [
    {"key": "bug_count", "description": "Total number of bugs found", "formula": "COUNT(DISTINCT bug_id)"},
    {"key": "rejection_rate", "description": "Rejection rate", "formula": "rejected / total"}
  ],
  "limits": {
    "max_dimensions": 2,
    "max_rows": 1000,
    "timeout_seconds": 90
  }
}
```

---

## Limits

| Limit | Value | Rationale |
|-------|-------|-----------|
| Max dimensions | 2 | Prevents combinatorial explosion |
| Max rows | 1000 | Memory protection |
| Query timeout | 90 seconds | Prevents runaway queries |

If you hit the row limit, narrow your query with filters or shorter date ranges.

---

## Common Use Cases

### Executive Business Review (EBR)

```python
# Volume trends
query_metrics(dimensions=["month"], metrics=["test_count", "bug_count"], start_date="6 months ago")

# Quality trends
query_metrics(dimensions=["month"], metrics=["rejection_rate", "review_rate"], start_date="6 months ago")

# Top issues
query_metrics(dimensions=["feature"], metrics=["bug_count", "bug_severity_score"], limit=5)
```

### Escalation Investigation

```python
# Rejection breakdown
query_metrics(dimensions=["rejection_reason"], metrics=["bug_count"], filters={"product_id": 598})

# Platform comparison
query_metrics(dimensions=["platform"], metrics=["bug_count", "rejection_rate"], filters={"product_id": 598})
```

### Feature Health Check

```python
# Feature fragility ranking
query_metrics(dimensions=["feature"], metrics=["bugs_per_test", "test_count"], sort_by="bugs_per_test")

# Feature-severity matrix
query_metrics(dimensions=["feature", "severity"], metrics=["bug_count"])
```

### Tester Performance

```python
# Most active testers (by volume)
query_metrics(dimensions=["tester"], metrics=["bug_count"], start_date="this quarter", limit=10)

# Tester quality (acceptance rates)
query_metrics(dimensions=["tester"], metrics=["bug_count", "overall_acceptance_rate"], start_date="this quarter")

# Monthly tester engagement
query_metrics(dimensions=["month"], metrics=["active_testers", "bug_count"], start_date="6 months ago")
```

---

## Tips

1. **Start simple:** Begin with one dimension, add complexity as needed.

2. **Use discovery:** Call `get_analytics_capabilities()` to see what's available.

3. **Narrow first:** Apply product_id filter and date range before adding dimensions.

4. **Watch warnings:** Pay attention to staleness warnings - data may have been refreshed.

5. **Context matters:** `bugs_per_test` is more meaningful than raw `bug_count` for comparisons.

6. **Time vs Volume:** Time dimensions (`month`, `quarter`) work best with volume metrics (`bug_count`, `test_count`).

---

## Related Tools

| Tool | Use When |
|------|----------|
| `query_metrics` | Dynamic analysis with grouping |
| `generate_quality_report` | Pre-built EBR report (single or multi-product) |
| `list_bugs` | Browse specific bugs from a test |
| `get_bug_summary` | Deep-dive into single bug |
| `search` | Find entities by keyword |

---

## Prompts

For guided analysis workflows, use the built-in prompts:

- **`analyze-product-quality`** - Interactive 5-phase quality analysis
- **`prep-meeting`** - Generate meeting materials from analysis

---

## Technical Notes

### How It Works

The analytics engine implements a "Metric Cube" pattern:

1. **Registry-driven:** Dimensions and metrics are defined in registries (not hard-coded SQL)
2. **Dynamic SQL:** Queries are built at runtime from your dimension/metric selections
3. **Direct attribution:** Bugs link directly to features via `test_feature_id` (no approximation)
4. **Read-through cache:** Stale data is refreshed on-demand during queries

### Data Freshness

- Background sync runs hourly (products, features, new tests)
- Bug and test metadata use read-through caching
- Queries on stale data trigger automatic refresh
- Immutable tests (`archived`, `cancelled`) always serve from cache

### Security

- All queries filter by `customer_id` (multi-tenant isolation)
- Registry pattern prevents SQL injection
- Only validated dimension/metric keys accepted

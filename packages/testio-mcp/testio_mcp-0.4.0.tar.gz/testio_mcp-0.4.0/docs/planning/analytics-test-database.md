# Analytics Test Database Strategy

**Created:** 2024-12-01
**Status:** Planning
**Context:** Need automated testing of all 14 analytics dimensions and their 91 two-dimension combinations

## Problem

The `query_metrics` tool supports 14 dimensions that can be combined in pairs. Manual validation caught a join ambiguity bug (`tester + platform` combination) that wasn't covered by existing tests. We need automated testing to prevent regressions.

Current test gaps:
- Unit tests mock the session, only verify SQL generation structure
- Integration tests hit real customer API (slow, data changes unpredictably)
- No tests verify all dimension combinations execute successfully

## Proposed Solution: Testcloud E2E Testing

Use TestIO's internal test customer (`testcloud.test.io`) as a dedicated test environment:

```
TESTIO_CUSTOMER_API_BASE_URL=https://api.testcloud.test.io/customer/v2
TESTIO_CUSTOMER_API_TOKEN=<testcloud-token>
```

### Benefits

1. **Real E2E coverage** - Tests actual API → sync → SQLite → analytics pipeline
2. **Stable test data** - We control testcloud data, no surprises from customer changes
3. **No fixture maintenance** - Data already exists, no seed scripts to maintain
4. **Tests actual sync logic** - Validates full data flow, not just query building
5. **Catches real bugs** - Would have caught the `tester + platform` join issue

### Test Structure

```
tests/
├── unit/                          # Mocked - fast, isolated (~0.5s)
│   └── test_query_builder.py      # SQL generation tests
├── integration/                   # Real API - current customer
│   └── test_analytics_*.py        # Existing integration tests
└── e2e/                           # Testcloud API - full pipeline
    └── test_dimension_combinations.py  # All 91 combinations
```

### Implementation

#### 1. Environment Configuration

```bash
# .env.testcloud (new file, gitignored)
TESTIO_CUSTOMER_API_BASE_URL=https://api.testcloud.test.io/customer/v2
TESTIO_CUSTOMER_API_TOKEN=<testcloud-token>
TESTIO_CUSTOMER_ID=<testcloud-customer-id>
```

#### 2. Pytest Marker

```python
# conftest.py
@pytest.fixture(scope="session")
def testcloud_client():
    """Client configured for testcloud environment."""
    # Load testcloud-specific config
    ...

# pytest.ini
[pytest]
markers =
    testcloud: Tests requiring testcloud environment
```

#### 3. Parametrized Dimension Tests

```python
# tests/e2e/test_dimension_combinations.py
from itertools import combinations

DIMENSIONS = [
    "feature", "product", "platform", "tester", "customer",
    "severity", "status", "testing_type", "month", "week",
    "quarter", "rejection_reason", "test_environment", "known_bug"
]

@pytest.mark.testcloud
@pytest.mark.parametrize("dim1,dim2", list(combinations(DIMENSIONS, 2)))
@pytest.mark.asyncio
async def test_dimension_pair_executes(testcloud_service, dim1, dim2):
    """Test all 91 dimension combinations execute without error."""
    result = await testcloud_service.query_metrics(
        metrics=["bug_count"],
        dimensions=[dim1, dim2],
        limit=5,
    )
    assert result.data is not None
    assert "error" not in str(result).lower()
```

#### 4. CI/CD Integration

```yaml
# .github/workflows/test.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - run: uv run pytest -m unit

  e2e-tests:
    runs-on: ubuntu-latest
    environment: testcloud  # GitHub environment with secrets
    steps:
      - run: uv run pytest -m testcloud
    env:
      TESTIO_CUSTOMER_API_TOKEN: ${{ secrets.TESTCLOUD_API_TOKEN }}
```

## Considerations

### Data Requirements

Testcloud must have data covering all dimension paths:

| Dimension | Required Data |
|-----------|---------------|
| `platform` | Tests with `TestPlatform` records (extracted from requirements JSON) |
| `tester` | Users with `user_type="tester"` linked to bugs |
| `customer` | Tests with `created_by` / `created_by_user_id` populated |
| `test_environment` | Tests with `test_environment` JSON field populated |
| `known_bug` | Bugs with `known=true` and `known=false` |
| `rejection_reason` | Rejected bugs with various rejection reasons |
| `severity` | Bugs with different severities (critical, high, low, etc.) |

**Action item:** Audit testcloud data to ensure coverage, seed missing entity types if needed.

### Test Isolation

Options for handling shared state:

1. **Read-only tests** - Only query data, never modify (simplest)
2. **Fresh sync per test module** - `sync_data()` before each test module
3. **Snapshot testing** - Compare results against known-good baselines

Recommendation: Start with read-only tests. Sync once at start of test session.

### Performance

| Test Type | Estimated Time | When to Run |
|-----------|---------------|-------------|
| Unit tests | ~0.5s | Every commit |
| Testcloud E2E (91 combinations) | ~2-5 min | PR merge, nightly |

## Alternative: Hybrid Approach

If testcloud access is problematic, consider a hybrid:

1. **SQL generation tests** (unit) - Verify `QueryBuilder.build()` succeeds for all combinations
2. **Seeded local SQLite** (integration) - Fixture with minimal test data
3. **Testcloud E2E** (optional) - Full pipeline validation when available

```python
# tests/unit/test_dimension_sql_generation.py
@pytest.mark.parametrize("dim1,dim2", list(combinations(DIMENSIONS, 2)))
def test_dimension_pair_generates_valid_sql(dim1, dim2):
    """Test SQL generation succeeds (no join ambiguity errors)."""
    builder = QueryBuilder(session=mock_session, customer_id=123)
    builder.set_dimensions([dim1, dim2], DIMENSION_REGISTRY)
    builder.set_metrics(["bug_count"], METRIC_REGISTRY)
    builder.set_sort("bug_count", "desc")

    # Should not raise "Can't determine join" error
    stmt = builder.build()
    assert stmt is not None
```

This catches join ambiguity issues without needing any database.

## Next Steps

1. [ ] Confirm testcloud API access and credentials
2. [ ] Audit testcloud data coverage for all dimensions
3. [ ] Seed missing entity types in testcloud if needed
4. [ ] Implement `testcloud` pytest marker and fixture
5. [ ] Write parametrized dimension combination tests
6. [ ] Add to CI/CD pipeline (separate job with testcloud secrets)

## References

- [CLAUDE.md - Testing Strategy](../../CLAUDE.md#testing-strategy)
- [docs/architecture/TESTING.md](../architecture/TESTING.md)
- Bug fixed: `tester + platform` join ambiguity in `query_builder.py:_get_join_condition()`

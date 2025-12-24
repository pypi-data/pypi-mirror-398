### High Priority
- **Bulk detail queries:** Add `detail_level: "basic" | "full"` parameter to `list_*` tools to optionally include rich details (devices, assignments, activity) without requiring individual `get_*_summary` calls. Would significantly improve performance for "show me all tests with full details" queries. Needs careful design for response size, token usage, and performance.
- **500+ error handling:** Need review of handling of API errors during sync or tool calls - need robust retry/fallback strategy to guarantee data integrity.

### Medium Priority
- **Deleted test strategy:** Design and implement robust strategy for handling disappearing (deleted) tests - detect, mark as deleted, prevent sync failures.
- **Early product insertion:** Insert products to database as soon as API data arrives, not after full sync completes. Keep `last_synced_at` until sync completes, but capture metadata early for faster availability.
- **Sync concurrency optimization:** Review and optimize concurrent API calls during sync and on-demand tool invocations - potential for significant performance gains.

## Analytics Extensions
- **3D Metric Cube:** Extend `query_metrics` to support 3 dimensions (e.g., `feature × month × severity`) for deeper trend analysis.
- **Raw Data Export:** Add `export_file` parameter to `query_metrics` for exporting large result sets to `.json` files (reuse EBR export pattern).
- **Metric Cube Pagination:** Add pagination support for queries returning >1000 rows (currently hard-limited).
- **Custom Metric Definitions:** Allow users to define custom metrics via configuration (e.g., `weighted_severity_score = critical*5 + high*3 + low*1`).
- **Time-Series Dimensions:** Add `week`, `quarter`, `year` dimensions for temporal analysis (currently only `month` is planned).
- **Entity ID filters:** Extend analytics tools to support explicit filtering by product_id, feature_id, and test_id for targeted analysis.
- **Analytics filter review:** Review and standardize filtering and sorting options across all analytics tools for consistency.
- **HTTP instrumentation:** Add middleware/instrumentation to httpx client to capture and log API calls including request bodies for debugging and monitoring.

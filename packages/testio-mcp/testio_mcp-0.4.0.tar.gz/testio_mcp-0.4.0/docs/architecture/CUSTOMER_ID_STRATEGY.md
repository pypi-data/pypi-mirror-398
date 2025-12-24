# Customer ID Strategy

**Date:** 2025-11-20
**Status:** Implemented
**Related:** STORY-010 (Multi-Tenant Architecture), STORY-021 (Local Data Store)

---

## Problem Statement

The TestIO MCP Server requires a `customer_id` for SQLite database isolation (multi-tenant ready schema). However:

1. **TestIO Customer API has no metadata endpoint** - No `/me` or `/whoami` to auto-discover customer ID
2. **Customers don't know their customer ID** - It's an internal TestIO/Cirro system identifier
3. **Customer ID is not in API responses** - Not exposed in products, tests, or bugs endpoints

**User Impact:** Customers setting up the server don't know what value to use for `TESTIO_CUSTOMER_ID`.

---

## Solution: Default to Customer ID = 1

### Design Decision

Make `TESTIO_CUSTOMER_ID` **optional with default value of `1`** for single-tenant deployments.

```python
# config.py
TESTIO_CUSTOMER_ID: int = Field(
    default=1,
    gt=0,
    description="Customer ID for local database isolation (default: 1). "
    "For single-tenant deployments, the default value is sufficient. "
    "For multi-tenant deployments (STORY-010), use unique IDs per customer."
)
```

### Rationale

**Why `customer_id=1` is the right choice:**

1. **Simple and predictable** - No magic hashing, no API calls
2. **Survives token rotation** - Database doesn't become orphaned when API token changes
3. **Zero configuration burden** - Customers just provide API token, everything works
4. **Multi-tenant ready** - Future deployments use IDs 2, 3, 4... for different customers
5. **Local identifier only** - Doesn't need to match TestIO's internal customer ID

**Why NOT hash-based auto-generation:**
- ❌ Breaks on API token rotation (database becomes orphaned)
- ❌ Magic behavior (harder to understand)
- ❌ Doesn't provide real value over simple default

**Why NOT require explicit customer ID:**
- ❌ Customers don't know their customer ID
- ❌ No API endpoint to discover it
- ❌ Creates setup friction for no benefit

---

## Implementation

### Configuration Changes

**Before (Required):**
```bash
# .env
TESTIO_CUSTOMER_API_TOKEN=your-token-here
TESTIO_CUSTOMER_ID=12345  # ❌ Required but unknown to customer
```

**After (Optional):**
```bash
# .env
TESTIO_CUSTOMER_API_TOKEN=your-token-here
# TESTIO_CUSTOMER_ID=1  # ✅ Optional, defaults to 1
```

### Database Schema

The SQLite schema remains unchanged - `customer_id` column exists in all tables:

```sql
CREATE TABLE tests (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,  -- Defaults to 1 for single-tenant
    product_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    -- ...
);

CREATE INDEX idx_tests_customer_product ON tests(customer_id, product_id);
```

### Migration Path

**Existing Users (0.1.x → 0.2.0):**
- Remove `TESTIO_CUSTOMER_ID` from `.env` file
- Server uses default value of `1`
- Existing databases continue to work (customer_id column unchanged)

**New Users (0.2.0+):**
- Don't set `TESTIO_CUSTOMER_ID` at all
- Server automatically uses `1`
- Zero configuration needed

---

## Multi-Tenant Future (STORY-010)

### Single-Tenant vs Multi-Tenant

**Single-Tenant (Current MVP):**
- One customer per server instance
- `customer_id=1` (default)
- Simple `.env` file configuration
- **Use case:** Individual customers running their own server

**Multi-Tenant (Future):**
- Multiple customers per server instance
- Explicit customer IDs (1, 2, 3...)
- YAML configuration file mapping `customer_id → api_token`
- **Use case:** Internal company users managing multiple customer accounts

### Multi-Tenant Configuration (Future)

```yaml
# customers.yaml (STORY-010)
customers:
  - id: 1
    name: "AcmeCorp"
    api_token: "testio-token-for-acme"
  - id: 2
    name: "GlobexInc"
    api_token: "testio-token-for-globex"
  - id: 3
    name: "InitechLLC"
    api_token: "testio-token-for-initech"
```

**Key Points:**
- Customer IDs are **local identifiers** for database isolation
- They don't need to match TestIO's internal customer IDs
- Each customer gets unique ID to prevent data leakage
- Background sync loops over all customers

---

## FAQ

### Q: What if I want to use a different customer ID?

**A:** Set `TESTIO_CUSTOMER_ID` in your `.env` file:

```bash
TESTIO_CUSTOMER_ID=42
```

The server will use your custom value instead of the default.

### Q: What happens if I change customer ID after initial setup?

**A:** The server will create a new isolated database namespace. Your old data remains in the database under the previous customer ID, but won't be visible to queries (filtered by new customer_id).

**Recovery:**
1. Change `TESTIO_CUSTOMER_ID` back to original value, OR
2. Run `testio-mcp sync --nuke --yes` to rebuild database with new customer ID

### Q: Can I merge databases from two different customer IDs?

**A:** Not currently supported. Each customer ID is isolated. If you need to consolidate data, export reports separately and merge externally.

### Q: Does customer_id=1 match my TestIO account ID?

**A:** No, and that's intentional. The `customer_id` in our SQLite database is a **local identifier** for data isolation. It doesn't need to match TestIO's internal customer ID.

### Q: What if two different customers both use customer_id=1?

**A:** That's fine! Each customer runs their own server instance with their own SQLite database. The customer IDs don't conflict because the databases are separate files.

### Q: Will this break multi-tenancy (STORY-010)?

**A:** No. Multi-tenant deployments will use explicit customer IDs (2, 3, 4...) configured in a YAML file. The default value of `1` is only for single-tenant deployments.

---

## Design Alternatives Considered

### Alternative 1: Hash API Token for Customer ID

**Approach:** Derive customer ID from API token hash

```python
def derive_customer_id(api_token: str) -> int:
    hash_bytes = hashlib.sha256(api_token.encode()).digest()
    return int.from_bytes(hash_bytes[:8], byteorder='big') & 0x7FFFFFFFFFFFFFFF
```

**Rejected because:**
- ❌ Breaks on API token rotation (database orphaned)
- ❌ Magic behavior (harder to debug)
- ❌ No real benefit over simple default

### Alternative 2: Require Explicit Customer ID

**Approach:** Make `TESTIO_CUSTOMER_ID` required (no default)

**Rejected because:**
- ❌ Customers don't know their customer ID
- ❌ No API endpoint to discover it
- ❌ Creates setup friction

### Alternative 3: API Endpoint to Discover Customer ID

**Approach:** Add `GET /customer/me` endpoint to TestIO API

**Rejected because:**
- ❌ Requires TestIO API changes (out of our control)
- ❌ Endpoint doesn't exist currently
- ❌ Adds startup dependency on API call

---

## Conclusion

**Decision:** Default `TESTIO_CUSTOMER_ID=1` for single-tenant deployments.

**Benefits:**
- ✅ Zero configuration for customers
- ✅ Survives token rotation
- ✅ Simple and predictable
- ✅ Multi-tenant ready

**Trade-offs:**
- ⚠️ Local identifier doesn't match TestIO's internal customer ID (acceptable - not needed)
- ⚠️ Changing customer ID requires database rebuild (rare, documented)

This design prioritizes **user experience** (zero configuration) over theoretical purity (matching internal IDs).

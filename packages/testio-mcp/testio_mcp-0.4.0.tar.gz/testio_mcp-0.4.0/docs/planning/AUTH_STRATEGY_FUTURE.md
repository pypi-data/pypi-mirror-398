# Authentication Strategy - Future Multi-Tenant Architecture

**Status:** 📋 PLANNING DOCUMENT - NOT IMPLEMENTED
**Related Story:** [STORY-010: Multi-Tenant Architecture](../stories/story-010-multi-tenant-architecture.md) (not yet prioritized)
**Current Implementation:** See [AUTH_STRATEGY.md](../architecture/AUTH_STRATEGY.md)
**Last Updated:** 2025-11-20

---

## Planning Context

This document contains future planning for multi-tenant authentication architecture. **None of this is currently implemented.** The current MVP uses single-tenant, server-side token authentication.

**When to implement:** After STORY-010 (Multi-Tenant Architecture) is prioritized and approved.

**Current State:** Single TestIO API token in `.env`, stdio transport, no user authentication.

---

## Future State (Multi-Tenant - Phase 3)

### Target Architecture

**Transport:** HTTP (REST API) + MCP (stdio for local clients)
**User Auth:** JWT/OIDC (corporate IdP integration)
**API Auth:** Per-user TestIO tokens (stored encrypted)
**Tenant Model:** Multi-tenant (many users → many TestIO customer accounts)

### Authentication Flow

```
User → Corporate IdP (OIDC/SAML) → JWT → Auth Service
  ↓
Auth Service → User ID → Tenant Mapping → TestIO API Token (encrypted DB)
  ↓
Tool Layer → Create TestIOClient(user_token) → Service Layer
  ↓
Service Layer → TestIO API (with user's token)
```

---

## Migration Path

### Phase 2: Multi-User (Same Tenant)

**Characteristics:**
- Add HTTP transport (REST API)
- User authentication (JWT from corporate IdP)
- Multiple users share same TestIO API token
- User permissions managed application-side (RBAC)

**New Components:**
- **Auth Service:** Normalizes JWT/OIDC, issues session claims, provides TokenProvider interface
- **Structured Logging:** Records user IDs for audit trail
- **Per-User Quotas:** (noop backend initially, enables rate limiting later)

**Code Changes (Tool Layer Only - Repository Pattern):**
```python
# Tool extracts user from JWT, creates session
@mcp.tool()
async def get_test_status(test_id: int, ctx: Context, user_token: str):
    # Validate JWT, extract user_id
    user = ctx["auth_service"].validate_token(user_token)

    # Still use server-wide TestIO client (same tenant)
    client = ctx["testio_client"]
    test_repo = ctx["test_repository"]
    bug_repo = ctx["bug_repository"]

    # Log user action
    logger.info(f"User {user.id} requesting test {test_id}")

    # Service unchanged (repository pattern)
    service = TestService(client=client, test_repo=test_repo, bug_repo=bug_repo)
    return await service.get_test_status(test_id)
```

**Service Layer:** ✅ **No changes required**

**Security:**
- JWT validation at API gateway
- RBAC enforced before service call
- Audit log includes user IDs

---

### Phase 3: Multi-Tenant (Different Customers)

**Characteristics:**
- Multiple TestIO customer accounts
- Each user has their own TestIO API token
- Per-tenant isolation (data, cache, rate limits)

**New Components:**
- **Tenant Mapping Service:** User → Tenant → TestIO Token
- **Client Factory:** Reuses AsyncClient per token (connection pooling)
- **Encrypted Token Storage:** PostgreSQL with envelope encryption (KMS)
- **Token Rotation:** Automated with valid_from/valid_until metadata
- **Policy Enforcement:** OPA/Cedar for RBAC/ABAC

**Code Changes (Tool Layer Only - Repository Pattern):**
```python
# Tool creates per-user client
@mcp.tool()
async def get_test_status(test_id: int, ctx: Context, user_token: str):
    # Validate JWT, extract user_id
    user = ctx["auth_service"].validate_token(user_token)

    # Get user's TestIO token (encrypted storage)
    user_auth = ctx["tenant_service"].get_user_auth(user.id)

    # Create client with user's token (NOT server token)
    # Uses ClientFactory for connection pooling
    client = ctx["client_factory"].get_client(
        api_token=user_auth.TESTIO_CUSTOMER_API_TOKEN  # User-specific
    )

    # Get repositories (PersistentCache has multi-tenant support via customer_id)
    test_repo = ctx["test_repository"]  # Filters by customer_id internally
    bug_repo = ctx["bug_repository"]

    # Service unchanged - still receives client + repositories
    service = TestService(client=client, test_repo=test_repo, bug_repo=bug_repo)
    return await service.get_test_status(test_id)
```

**Service Layer:** ✅ **Still no changes required**

---

## Critical Components (Not Yet Implemented)

### 1. Client Factory Pattern (Phase 3)

**Problem:** Creating new `TestIOClient` per request re-opens TLS connections.

**Solution:**
```python
# src/testio_mcp/factories/client_factory.py

from typing import Dict
import asyncio
from datetime import datetime, timedelta

class ClientFactory:
    """Reuses AsyncClient instances per token with connection pooling."""

    def __init__(self, max_idle_time: int = 300):
        self._clients: Dict[str, TestIOClient] = {}
        self._last_used: Dict[str, datetime] = {}
        self._max_idle_time = max_idle_time
        self._cleanup_task = None

    async def start(self):
        """Start background cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_idle_clients())

    def get_client(self, api_token: str) -> TestIOClient:
        """Get or create client for token."""
        # Hash token for lookup (don't store plaintext as key)
        token_hash = hashlib.sha256(api_token.encode()).hexdigest()[:16]

        if token_hash not in self._clients:
            # Create new client with connection pooling
            self._clients[token_hash] = TestIOClient(
                base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
                api_token=api_token,
                max_connections=100,
                max_keepalive_connections=20
            )

        self._last_used[token_hash] = datetime.utcnow()
        return self._clients[token_hash]

    async def _cleanup_idle_clients(self):
        """Close clients idle longer than max_idle_time."""
        while True:
            await asyncio.sleep(60)  # Check every minute

            now = datetime.utcnow()
            for token_hash in list(self._clients.keys()):
                if now - self._last_used[token_hash] > timedelta(seconds=self._max_idle_time):
                    # Close idle client
                    await self._clients[token_hash].close()
                    del self._clients[token_hash]
                    del self._last_used[token_hash]

    async def close_all(self):
        """Close all clients on shutdown."""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
```

---

### 2. Token Storage with Envelope Encryption

**Requirements:**
- Encrypt TestIO tokens at application layer (KMS or libsodium)
- Never log plaintext tokens
- Store only hash/fingerprint for lookups
- Rotation metadata (valid_from, valid_until)

**Schema:**
```sql
CREATE TABLE user_credentials (
    user_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    testio_token_encrypted BYTEA NOT NULL,  -- Envelope encrypted
    token_fingerprint VARCHAR(64) NOT NULL,  -- SHA-256 hash for lookups
    valid_from TIMESTAMP NOT NULL,
    valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_tenant_id (tenant_id),
    INDEX idx_fingerprint (token_fingerprint)
);
```

**Encryption:**
```python
# src/testio_mcp/security/token_encryption.py

import boto3
from cryptography.fernet import Fernet
import hashlib

class TokenEncryption:
    """Envelope encryption for TestIO tokens using AWS KMS."""

    def __init__(self, kms_key_id: str):
        self.kms = boto3.client('kms')
        self.kms_key_id = kms_key_id

    def encrypt_token(self, plaintext_token: str) -> tuple[bytes, str]:
        """Encrypt token with envelope encryption.

        Returns:
            (encrypted_token, token_fingerprint)
        """
        # Generate data key from KMS
        response = self.kms.generate_data_key(
            KeyId=self.kms_key_id,
            KeySpec='AES_256'
        )

        plaintext_key = response['Plaintext']
        encrypted_key = response['CiphertextBlob']

        # Encrypt token with data key
        f = Fernet(plaintext_key)
        encrypted_token = f.encrypt(plaintext_token.encode())

        # Prepend encrypted data key (envelope pattern)
        envelope = encrypted_key + encrypted_token

        # Generate fingerprint for lookups
        fingerprint = hashlib.sha256(plaintext_token.encode()).hexdigest()

        return envelope, fingerprint

    def decrypt_token(self, envelope: bytes) -> str:
        """Decrypt token with envelope decryption."""
        # Extract encrypted data key
        encrypted_key = envelope[:352]  # KMS ciphertext size
        encrypted_token = envelope[352:]

        # Decrypt data key with KMS
        response = self.kms.decrypt(CiphertextBlob=encrypted_key)
        plaintext_key = response['Plaintext']

        # Decrypt token with data key
        f = Fernet(plaintext_key)
        plaintext_token = f.decrypt(encrypted_token).decode()

        return plaintext_token
```

---

### 3. Database Multi-Tenancy (SQLite-First Architecture)

**Current (MVP - Single Tenant):**
```sql
-- PersistentCache schema has customer_id column (built-in multi-tenant support)
SELECT * FROM tests WHERE product_id = ?;  -- No customer_id filter (single tenant)
```

**Future (Multi-Tenant):**
```sql
-- Repository queries filter by customer_id automatically
SELECT * FROM tests WHERE customer_id = ? AND product_id = ?;
#                          ^
#                          └─ Tenant isolation at database level
```

**Implementation (Repository Pattern):**
```python
# Repository receives customer_id from PersistentCache
class TestRepository:
    def __init__(self, cache: PersistentCache):
        self.cache = cache
        self.customer_id = cache.customer_id  # Tenant isolation

    async def get_test_by_id(self, test_id: int) -> dict | None:
        # Query filters by customer_id automatically
        async with self.cache.get_connection() as conn:
            result = await conn.execute(
                "SELECT * FROM tests WHERE customer_id = ? AND id = ?",
                (self.customer_id, test_id)
            )
            # Multi-tenant isolation enforced at database query level
```

**Multi-Tenant Migration Path:**
```python
# Phase 1 (MVP): Single customer_id in .env
cache = PersistentCache(customer_id=12345)  # From config

# Phase 3 (Multi-Tenant): Per-user customer_id from auth
user = auth_service.validate_token(jwt)
cache = cache_factory.get_cache(customer_id=user.tenant_id)  # Per-tenant isolation
```

---

### 4. Auth Service Facade

**Purpose:** Normalize JWT/OIDC input, issue session claims, provide TokenProvider interface

**Interface:**
```python
# src/testio_mcp/services/auth_service.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class UserContext:
    user_id: str
    tenant_id: str
    email: str
    roles: list[str]
    testio_token: str  # Decrypted, in-memory only

class AuthService:
    """Authentication and authorization service."""

    def __init__(self, token_encryption: TokenEncryption, db_session):
        self.token_encryption = token_encryption
        self.db = db_session
        self._token_cache = {}  # LRU + TTL

    async def validate_token(self, jwt_token: str) -> UserContext:
        """Validate JWT and return user context."""
        # Decode JWT, verify signature
        claims = jwt.decode(jwt_token, settings.JWT_PUBLIC_KEY, algorithms=["RS256"])

        user_id = claims["sub"]

        # Get user's TestIO token from encrypted storage
        user_cred = await self.db.get_user_credential(user_id)

        # Decrypt token (cache in memory with TTL)
        if user_id not in self._token_cache:
            testio_token = self.token_encryption.decrypt_token(user_cred.testio_token_encrypted)
            self._token_cache[user_id] = testio_token
        else:
            testio_token = self._token_cache[user_id]

        return UserContext(
            user_id=user_id,
            tenant_id=user_cred.tenant_id,
            email=claims["email"],
            roles=claims.get("roles", []),
            testio_token=testio_token
        )

    def clear_user_cache(self, user_id: str):
        """Clear cached token on logout/rotation."""
        if user_id in self._token_cache:
            del self._token_cache[user_id]
```

---

## Token Rotation Strategy

### Automated Rotation

**Cadence:** Every 90 days (configurable)

**Process:**
1. Background job checks `valid_until` timestamps
2. For tokens expiring soon (< 7 days):
   - Request new token from TestIO API
   - Encrypt new token
   - Update database with new token + extended `valid_until`
   - Invalidate user cache
   - Notify user (email)
3. For expired tokens:
   - Mark as invalid
   - Clear from client factory
   - Force user re-authentication

**Schema Support:**
```sql
ALTER TABLE user_credentials ADD COLUMN rotation_scheduled_at TIMESTAMP;
ALTER TABLE user_credentials ADD COLUMN rotation_notified_at TIMESTAMP;
```

### Manual Rotation (Incident Response)

**Trigger:** Token compromise suspected

**Process:**
1. Admin marks token as compromised
2. System invalidates immediately (cache + client factory)
3. User forced to re-authenticate
4. Audit log entry created
5. Notify security team

---

## Open Questions

### 1. TestIO Token Issuance

**Question:** Does TestIO issue distinct API tokens per customer account?

**Impact:**
- If yes: Our architecture works as-is
- If no (single org token): Need internal brokering layer

**Action:** Verify with TestIO API documentation or support

### 2. Corporate IdP Integration

**Question:** OIDC/SAML or bespoke JWT?

**Impact:**
- OIDC/SAML: Standard integration (Auth0, Okta, Azure AD)
- Bespoke: Need to implement JWT issuance

**Action:** Clarify with stakeholders before Phase 2

### 3. Secrets in Transit

**Question:** How do secrets transit between auth service and tools?

**Options:**
- In-process calls (same Python process, no network)
- mTLS (if services separated)
- Service mesh (Istio, Linkerd)

**Action:** Decide before Phase 2 (recommend in-process for MVP)

---

## Security Checklist

### Phase 2 (Multi-User)
- [ ] JWT validation at API gateway
- [ ] Auth service facade
- [ ] Structured logging (user IDs)
- [ ] Per-user quotas (noop backend)
- [ ] RBAC enforcement

### Phase 3 (Multi-Tenant)
- [ ] Encrypted token storage (envelope encryption)
- [ ] Client factory (connection pooling)
- [ ] Cache namespacing (tenant_id)
- [ ] Token rotation (automated + manual)
- [ ] Policy enforcement (OPA/Cedar)
- [ ] Per-tenant rate limiting
- [ ] Request signing or mTLS
- [ ] Background token verification job

---

## Recommendations

### Phase 2 (Multi-User)
1. Build auth service facade now (even if JWT validation is simple)
2. Add structured logging with user IDs
3. Create noop quota backend (interface ready)

### Phase 3 (Multi-Tenant)
1. Implement client factory pattern
2. Setup encrypted token storage (KMS + PostgreSQL)
3. Add tenant namespacing to cache keys
4. Build token rotation automation
5. Integrate policy engine (OPA recommended)

---

## SQLite-First Multi-Tenancy Benefits

**Benefits of SQLite-First Multi-Tenancy:**
1. ✅ **Database-level isolation** - Cleaner than cache key prefixing
2. ✅ **Already implemented** - `customer_id` field exists in schema
3. ✅ **Simpler migration** - Change customer_id config, repositories filter automatically
4. ✅ **No cache key versioning** - Database schema migrations handle version changes

**Authentication Strategy Compatibility:**
- ✅ **Phase 1 (MVP):** Single `customer_id` from config → Works as-is
- ✅ **Phase 2 (Multi-User):** Same `customer_id`, user auth for RBAC → No changes needed
- ✅ **Phase 3 (Multi-Tenant):** Per-user `customer_id` → Repositories auto-filter queries

---

## Conclusion

**Key Strengths:**
- Service layer enables clean auth migration (validated in production)
- User-level tokens provide security and auditability
- Migration path is incremental and realistic
- **SQLite-first multi-tenancy** - Database-level isolation already implemented

**Critical Additions:**
- Client factory (Phase 3) - avoids TLS handshake overhead
- Envelope encryption for token storage
- ~~Cache namespacing by tenant_id~~ **✅ Database isolation via customer_id (already implemented)**
- Auth service facade
- Runtime guards for MVP

**SQLite-First Advantages:**
- ✅ **Multi-tenant foundation** - customer_id column exists in schema
- ✅ **Repository pattern** - Clean data access layer for tenant filtering
- ✅ **Simpler migration** - No cache key prefix management
- ✅ **Better performance** - Database indexes on customer_id for fast isolation

---

**Document Status:** 📋 Planning Document (Not Implemented)
**Implementation Trigger:** STORY-010 prioritization
**Author:** Winston (Architect) + Codex AI
**Created:** 2025-11-20 (extracted from AUTH_STRATEGY.md)

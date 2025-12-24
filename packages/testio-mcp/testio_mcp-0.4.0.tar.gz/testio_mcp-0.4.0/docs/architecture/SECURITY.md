# Security Guidelines - TestIO MCP Server

**Version:** 1.1
**Last Updated:** 2025-11-18 (Updated for SQLite-First Architecture)

---

## Security Posture

### MVP Threat Model

**Deployment:** Local/single-user (Claude Desktop, Cursor on developer machine)

**Attack Surface:**
- ✅ **Low:** No network exposure by default (stdio mode)
- ⚠️ **Medium:** HTTP mode exposes localhost:8080 (if enabled)
- ✅ **Low:** Single-user access (no multi-tenancy in MVP)
- ⚠️ **Medium:** API token stored in plaintext `.env` file
- ⚠️ **Medium:** SQLite database file stored unencrypted on disk
- ⚠️ **Medium:** Bug descriptions may contain user-generated content
- ⚠️ **Low:** Input validation (Pydantic handles most edge cases)

**Primary Risks:**
1. **API Token Leakage** - Token in `.env` committed to git or shared
2. **Database File Exposure** - SQLite database file (`~/.testio-mcp/cache.db`) contains unencrypted test/bug data
3. **Injection Attacks** - SQL injection if parameterized queries not used, or malicious content in bug descriptions
4. **Rate Limit Abuse** - User queries overwhelming TestIO API
5. **HTTP Mode Exposure** - Localhost HTTP endpoint accessible to any local process (if HTTP mode enabled)
6. **Data Exposure** - Sensitive test/bug data logged or backed up insecurely

---

## Authentication & Authorization

### API Token Management

**Storage & Configuration:**

See [config.py documentation](../../src/testio_mcp/config.py) for complete configuration details.

**Quick Reference:**
- **Storage:** `.env` file (NOT committed to git)
- **Validation:** Pydantic validates token on startup
- **Rotation:** Manual for MVP (see [AUTH_STRATEGY.md](AUTH_STRATEGY.md#incident-response-plan))

**Security Requirements:**
```bash
# .env file permissions
chmod 600 .env

# Verify token is configured
grep TESTIO_CUSTOMER_API_TOKEN .env
```



---

### Authorization Scope

**TestIO Customer API Token Permissions:**
- Read-only access to products, tests, bugs
- No write permissions (can't create/modify/delete)
- Scoped to customer account (can't access other customers)

**Principle of Least Privilege:**
- Use dedicated API token for MCP server (not admin token)
- Request minimum permissions from TestIO
- Rotate tokens regularly

---

## Input Validation

### Parameter Validation (Pydantic)

**Framework:** All tool inputs validated via Pydantic models.

See [TECH-STACK.md - Pydantic section](TECH-STACK.md) for complete validation patterns and examples.

**Security Benefits:**
- ✅ Prevents SQL injection (no raw queries)
- ✅ Prevents path traversal (no file access)
- ✅ Prevents parameter pollution (strict typing)
- ✅ Clear error messages for invalid input

**Example:**
```python
from pydantic import BaseModel, Field

class GetTestBugsInput(BaseModel):
    test_id: str = Field(pattern=r"^\d+$")  # Only digits
    page_size: int = Field(ge=1, le=1000)  # 1-1000 only
```

---

### Date Range Validation

**Prevent DoS via huge date ranges:**
```python
from datetime import datetime, timedelta

def validate_date_range(start_date: str, end_date: str) -> None:
    """Validate date range is reasonable (max 1 year)."""
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)

    # Check order
    if end < start:
        raise ValueError("end_date must be after start_date")

    # Check range
    days = (end - start).days
    if days > 365:
        raise ValueError(
            f"Date range {days} days exceeds maximum 365 days. "
            "Reduce range to prevent performance issues."
        )
```

---

## Output Sanitization

### Bug Descriptions (User-Generated Content)

**Risk:** Bug titles/descriptions may contain:
- HTML/JavaScript (XSS risk if rendered in browser)
- Markdown injection (if AI client renders markdown)
- SQL-like syntax (confuse parsing)
- Excessive length (DoS)

**Mitigation:**

**1. MCP Protocol Handles JSON Encoding**
```json
{
  "bug_title": "<script>alert('XSS')</script>",
  "description": "Click here: [evil](javascript:void(0))"
}
```
→ JSON encoding escapes special characters automatically
→ AI clients (Claude) sanitize before display

**2. Truncate Long Content**
```python
def sanitize_bug_description(description: str, max_length: int = 1000) -> str:
    """Truncate and sanitize bug description."""
    if len(description) > max_length:
        return description[:max_length] + "... (truncated)"
    return description
```

**3. Strip Control Characters (Optional)**
```python
import re

def strip_control_chars(text: str) -> str:
    """Remove control characters (except newlines/tabs)."""
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
```

**4. Don't Execute User Content**
- Never use `eval()` or `exec()` on user input
- Never render bug descriptions as HTML without escaping
- Never execute commands based on bug content

---

## Secrets Management

### MVP: Environment Variables

**.env File:**
```bash
# TestIO API Configuration
TESTIO_CUSTOMER_API_BASE_URL=https://api.test.io/customer/v2
TESTIO_CUSTOMER_API_TOKEN=abc123...xyz789
```

**Generate Secret Key:**
```bash
openssl rand -hex 32
```

**Never:**
- ❌ Commit `.env` to git
- ❌ Share `.env` via email/Slack
- ❌ Store tokens in code
- ❌ Log tokens (even at debug level)

---

### Future: Production Secrets Management

**Option 1: AWS Secrets Manager**
```python
import boto3

def get_api_token() -> str:
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='testio/api/token')
    return json.loads(response['SecretString'])['token']
```

**Option 2: HashiCorp Vault**
```python
import hvac

def get_api_token() -> str:
    client = hvac.Client(url='https://vault.company.com')
    client.token = os.getenv('VAULT_TOKEN')
    secret = client.secrets.kv.v2.read_secret_version(path='testio/api')
    return secret['data']['data']['token']
```

**Option 3: Environment Variables (Container Orchestration)**
```yaml
# kubernetes deployment.yaml
env:
  - name: TESTIO_CUSTOMER_API_TOKEN
    valueFrom:
      secretKeyRef:
        name: testio-secrets
        key: api-token
```

---

## Rate Limiting & Abuse Prevention

### Semaphore-Based Rate Limiting

**Prevents abuse:**
```python
# Global semaphore (ADR-002)
MAX_CONCURRENT_API_REQUESTS = 10

# Even if user makes 1000 requests, only 10 hit API concurrently
# Others queue gracefully (no API overwhelm)
```

**Future: Per-User Rate Limiting**
```python
from collections import defaultdict
import time

class RateLimiter:
    """Token bucket rate limiter per user."""

    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.buckets: dict[str, list[float]] = defaultdict(list)

    async def allow_request(self, user_id: str) -> bool:
        """Check if user is within rate limit."""
        now = time.time()
        minute_ago = now - 60

        # Remove old timestamps
        self.buckets[user_id] = [
            ts for ts in self.buckets[user_id] if ts > minute_ago
        ]

        # Check limit
        if len(self.buckets[user_id]) >= self.rpm:
            return False  # Rate limit exceeded

        # Allow request
        self.buckets[user_id].append(now)
        return True
```

---

## Logging & Auditing

### What to Log ✅

**Request Metadata:**
```python
logger.info(
    "MCP tool called",
    extra={
        "tool": "get_test_status",
        "test_id": test_id,
        "user": "user@company.com",  # If multi-tenant
        "duration_ms": duration * 1000,
        "cache_hit": cache_hit,
    }
)
```

**Errors:**
```python
logger.error(
    "API request failed",
    extra={
        "endpoint": "exploratory_tests/123",
        "status_code": 429,
        "error": "Rate limit exceeded",
    }
)
```

**Security Events:**
```python
logger.warning(
    "Invalid continuation token",
    extra={
        "token_prefix": token[:10],  # Only log prefix
        "error": "Signature mismatch",
    }
)
```

---

### What NOT to Log ❌

**API Tokens:**
```python
# ❌ NEVER
logger.debug(f"Using token: {settings.TESTIO_CUSTOMER_API_TOKEN}")

# ✅ Safe
logger.debug(f"Using token: {settings.TESTIO_CUSTOMER_API_TOKEN[:8]}***")
```

**Full Responses (May Contain PII):**
```python
# ❌ Risky
logger.debug(f"API response: {json.dumps(response)}")

# ✅ Safe (log summary only)
logger.debug(f"API response: {len(response.get('bugs', []))} bugs")
```

**User Input (May Contain Sensitive Data):**
```python
# ❌ Risky
logger.debug(f"User query: {user_input}")

# ✅ Safe (log metadata)
logger.debug(f"User query length: {len(user_input)} chars")
```

---

## Data Privacy & Compliance

### Data at Rest

**SQLite Database (Current):**
- **Persistence:** Data survives server restarts
- **Location:** `~/.testio-mcp/cache.db` (configurable via `TESTIO_DB_PATH`)
- **File Permissions:** Should be 600 (user read/write only)
- **Encryption:** Not encrypted by default (plaintext on disk)
- **WAL Mode:** Write-Ahead Logging enabled for concurrent reads
- **Backup Security:** VACUUM operations and backups should be secured

**Security Checklist:**
```bash
# Verify database file permissions
ls -la ~/.testio-mcp/cache.db
# Should show: -rw------- (600)

# Set correct permissions if needed
chmod 600 ~/.testio-mcp/cache.db
chmod 700 ~/.testio-mcp/  # Directory permissions
```

**SQL Injection Prevention:**

See [SERVICE_LAYER_SUMMARY.md - Repository Pattern](SERVICE_LAYER_SUMMARY.md) for complete data access patterns.

**Security Guarantees:**
- ✅ All queries use parameterized statements (via aiosqlite)
- ✅ Repository pattern enforces safe query construction
- ✅ No raw SQL from user input

**Quick Example:**
```python
# ✅ SAFE - Parameterized query
await conn.execute("SELECT * FROM tests WHERE id = ?", (test_id,))

# ❌ NEVER - String interpolation
await conn.execute(f"SELECT * FROM tests WHERE id = {test_id}")
```

**Multi-Tenant Isolation:**
- `customer_id` column on all tables
- Repository queries filter by `customer_id` automatically
- Prevents cross-tenant data access

**Future Enhancements:**
- **SQLCipher:** Encrypt database file at rest
- **OS-level encryption:** FileVault (macOS), BitLocker (Windows), LUKS (Linux)
- **Field-level encryption:** Encrypt sensitive fields before storage
- **Key management:** Integrate with AWS KMS or HashiCorp Vault

---

### Data in Transit

**HTTPS Enforcement:**
```python
# httpx client configuration
client = httpx.AsyncClient(
    base_url="https://api.test.io/customer/v2",  # HTTPS only
    verify=True,  # Verify SSL certificates
)
```

**Certificate Validation:**
- Always verify SSL certificates (never set `verify=False`)
- Use system CA bundle for certificate validation
- Alert on certificate expiration

---

### HTTP Transport Mode Security

**Current Implementation (STORY-023a):**
- **Default Binding:** localhost:8080 (not exposed to network)
- **No Authentication:** HTTP endpoint has no auth (localhost-only assumption)
- **Multiple Clients:** Allows Claude Code + Cursor + Inspector simultaneously
- **Single Process:** Prevents SQLite database lock conflicts

**Security Posture:**
```python
# server.py - HTTP mode configuration
uvicorn.run(
    app,
    host="127.0.0.1",  # ✅ Localhost only (not 0.0.0.0)
    port=8080,
    log_level="info"
)
```

**Risks:**
- ✅ **Low:** Localhost binding prevents network exposure
- ⚠️ **Medium:** No authentication on HTTP endpoint
- ⚠️ **Medium:** Any local process can connect to port 8080
- ⚠️ **Low:** CORS not configured (assume same-origin only)

**Recommended Security Measures:**

**1. Localhost-Only Binding (REQUIRED):**
```python
# ✅ SAFE - Localhost only
host="127.0.0.1"  # IPv4 localhost
host="::1"        # IPv6 localhost

# ❌ DANGEROUS - Network exposed
host="0.0.0.0"    # Binds to all interfaces (NEVER use in production)
```

**2. Port Security:**
- Use non-privileged port (1024-65535)
- Default: 8080 (configurable)
- Consider firewall rules if needed

**3. Future: Add Authentication (Multi-User Deployment):**
```python
# Future: JWT authentication for HTTP mode
@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # Validate JWT
    user = validate_jwt(token)
    request.state.user = user
    return await call_next(request)
```

**4. CORS Policy (If Needed):**
```python
# Only if exposing to browser clients
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["POST"],  # MCP uses POST only
    allow_headers=["Content-Type"],
)
```

**Security Checklist (HTTP Mode):**
- [ ] Verify binding to localhost (not 0.0.0.0)
- [ ] Confirm port is not exposed via firewall
- [ ] Document that HTTP mode is localhost-only
- [ ] Add authentication if deploying in multi-user environment
- [ ] Monitor for unauthorized access attempts

---

### Data Retention

**Current (SQLite Database):**
- **Persistence:** Data retained indefinitely until manually deleted
- **Background Sync:** Updates existing data every 5 minutes (configurable)
- **Data Growth:** Database grows as new tests/bugs are synced
- **Manual Cleanup:** Use CLI commands for data management:
  ```bash
  # Clear all data (destructive)
  testio-mcp sync --nuke --yes

  # Clear specific product data
  testio-mcp sync --nuke --yes --product-ids 598

  # View database size and stats
  testio-mcp sync --status
  ```

**GDPR/CCPA Compliance:**
- **Right to Erasure:** Delete customer data via `customer_id` filter
  ```sql
  DELETE FROM tests WHERE customer_id = ?;
  DELETE FROM products WHERE customer_id = ?;
  DELETE FROM bugs WHERE test_id IN (SELECT id FROM tests WHERE customer_id = ?);
  ```
- **Data Minimization:** Only sync required product IDs (configure via `TESTIO_PRODUCT_IDS`)
- **Purpose Limitation:** Data used only for test status reporting (read-only operations)
- **Storage Limitation:** Implement data retention policy (e.g., auto-delete tests older than 90 days)

**Recommended Data Retention Policy:**
```python
# Future: Auto-delete old data
async def cleanup_old_data(max_age_days: int = 90):
    """Delete tests older than max_age_days."""
    cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
    async with cache.get_connection() as conn:
        await conn.execute(
            "DELETE FROM tests WHERE end_at < ?",
            (cutoff_date.isoformat(),)
        )
```

**Backup & Recovery:**
- Database file can be backed up via standard file copy
- VACUUM operation compacts database and reclaims space
- Consider automated backups for production deployments

---

## Dependency Security

### Dependency Scanning

**Tools:**
- **pip-audit:** Scan for known vulnerabilities
- **safety:** Python dependency checker
- **Dependabot:** Automated dependency updates (GitHub)

**Pre-Commit Hook:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pypa/pip-audit
    rev: v2.6.1
    hooks:
      - id: pip-audit
        args: [--require-hashes, --disable-pip]
```

**Run Manually:**
```bash
pip-audit --desc
```

---

### Pinning Dependencies

**requirements.txt:**
```
# Pin exact versions for reproducibility
fastmcp==1.2.3
httpx==0.25.0
pydantic==2.4.2
pydantic-settings==2.0.3

# Or use hash checking
fastmcp==1.2.3 \
    --hash=sha256:abc123...
```

**Update Process:**
1. Review release notes for security fixes
2. Update in development environment
3. Run tests
4. Update production

---

## Security Checklist

Before deploying to production:

**Authentication & Secrets:**
- [ ] API token stored securely (not in git)
- [ ] `.env` file in `.gitignore`
- [ ] Secret key generated (for token signing, if needed)
- [ ] SSL certificate validation enabled

**Database Security (SQLite):**
- [ ] Database file permissions set to 600 (user read/write only)
- [ ] Database directory permissions set to 700
- [ ] All queries use parameterized statements (no SQL injection)
- [ ] Multi-tenant isolation enforced via `customer_id` filtering
- [ ] Database backup strategy defined (if needed)
- [ ] Data retention policy documented

**HTTP Transport Mode (if enabled):**
- [ ] Server binds to localhost only (127.0.0.1, NOT 0.0.0.0)
- [ ] Port not exposed via firewall
- [ ] Authentication added (if multi-user deployment)
- [ ] CORS policy configured (if needed)

**Input Validation & Rate Limiting:**
- [ ] Input validation with Pydantic
- [ ] Rate limiting configured (semaphore)
- [ ] Date range limits enforced (max 1 year)
- [ ] Response size limits enforced (pagination)
- [ ] Continuation tokens validated (optional: signed)

**Logging & Monitoring:**
- [ ] Logging configured (no sensitive data logged)
- [ ] API tokens never logged (even at debug level)
- [ ] Error messages don't leak sensitive info
- [ ] Audit logging for security events

**Dependencies & Code Quality:**
- [ ] Dependencies scanned for vulnerabilities (pip-audit)
- [ ] Pre-commit hooks configured (detect-secrets)
- [ ] Code reviewed for security issues
- [ ] Penetration test completed (if production)

---

## Incident Response

### If API Token is Compromised

**Immediate Actions:**
1. Revoke token in TestIO dashboard
2. Generate new token
3. Update `.env` file
4. Restart MCP server
5. Review API usage logs for suspicious activity

**Investigate:**
- How was token leaked? (git commit, email, log file?)
- What data was accessed?
- When did compromise occur?

**Prevent Recurrence:**
- Add pre-commit hook to scan for secrets
- Use secrets management tool (Vault, AWS Secrets Manager)
- Rotate tokens regularly (e.g., every 90 days)

---

### If Suspicious Activity Detected

**Signs:**
- Unusual API error rates (429, 401, 403)
- Unexpected queries to sensitive endpoints
- High volume of requests from single user
- Requests outside normal business hours

**Actions:**
1. Review logs for suspicious patterns
2. Identify affected users/data
3. Temporarily disable access if needed
4. Investigate root cause
5. Implement additional controls (rate limiting, IP allowlist)

---

## Security Resources

### Tools

- **pip-audit:** https://pypi.org/project/pip-audit/
- **safety:** https://pyup.io/safety/
- **bandit:** Python security linter
- **pre-commit:** https://pre-commit.com/

### Best Practices

- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **Python Security Best Practices:** https://python.readthedocs.io/en/stable/library/security_warnings.html
- **API Security:** https://github.com/OWASP/API-Security

### TestIO Documentation

- API Authentication: (Internal - see project brief)
- Token Management: (Internal)

---

## Future Enhancements

### Post-MVP Security Improvements

1. **Multi-Factor Authentication (MFA)**
   - Require MFA for API token generation
   - Add MFA for server admin operations

2. **Audit Logging**
   - Log all API calls with user attribution
   - Immutable audit log (write-only, no deletes)
   - Export to SIEM (Splunk, ELK)

3. **Encryption at Rest**
   - Encrypt SQLite database file (SQLCipher or OS-level encryption)
   - Encrypt sensitive fields before database storage (e.g., bug descriptions with PII)
   - Key management: Integrate with AWS KMS or HashiCorp Vault
   - Encrypt logs with sensitive data

4. **IP Allowlisting**
   - Restrict API access to known IP ranges
   - Block requests from untrusted networks

5. **Anomaly Detection**
   - ML-based anomaly detection for API usage
   - Alert on unusual query patterns

6. **Penetration Testing**
   - Regular security audits
   - Third-party penetration testing
   - Bug bounty program

---

**Document Version:** 1.1
**Last Updated:** 2025-11-18 (Updated for SQLite-First Architecture)
**Owner:** Architect (Winston)
**Next Review:** After MVP launch

**Changelog:**
- **v1.1 (2025-11-18):** Updated for SQLite-first architecture (STORY-021, STORY-023 refactoring)
  - **Data at Rest:** In-memory cache → SQLite database security (file permissions, SQL injection prevention, multi-tenant isolation)
  - **Data Retention:** TTL-based expiration → SQLite persistence with GDPR compliance guidance
  - **HTTP Transport Mode:** Added security section for localhost binding, authentication, CORS
  - **Security Checklist:** Added SQLite-specific items and HTTP mode checks
  - **Future Enhancements:** Redis encryption → SQLite encryption (SQLCipher, OS-level)
- **v1.0 (2025-11-04):** Initial security guidelines

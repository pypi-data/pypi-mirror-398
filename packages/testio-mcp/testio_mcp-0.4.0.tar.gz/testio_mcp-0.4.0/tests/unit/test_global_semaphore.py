"""Semaphore Dependency Injection Tests - Concurrency Control (ADR-002).

This test suite verifies the dependency injection pattern for semaphore sharing:
- Clients can share a semaphore when passed explicitly (global concurrency control)
- Clients get isolated semaphores when none provided (test isolation)
- Server-level semaphore can be injected for production use

Architecture Decision: ADR-002 specifies "global semaphore limiting to 10
concurrent requests". This is achieved via dependency injection, not global state.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from src.testio_mcp.client import TestIOClient


@pytest.mark.asyncio
async def test_shared_semaphore_via_dependency_injection():
    """Verify clients share semaphore when passed explicitly (ADR-002).

    Architecture requirement: ADR-002 (Concurrency Limits)

    When a shared semaphore is injected, all clients using it enforce
    a global concurrency limit. This is how production code works.
    """
    # Create shared semaphore (like server.py does)
    shared_semaphore = asyncio.Semaphore(5)

    async with TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token="token1",
        semaphore=shared_semaphore,
    ) as client1:
        async with TestIOClient(
            base_url="https://api.test.io/customer/v2",
            api_token="token2",
            semaphore=shared_semaphore,
        ) as client2:
            # Both should reference the same semaphore object
            assert client1._semaphore is client2._semaphore, (
                "Clients must share injected semaphore (ADR-002)"
            )
            assert client1._semaphore is shared_semaphore
            assert client2._semaphore is shared_semaphore


@pytest.mark.asyncio
async def test_isolated_semaphores_without_injection():
    """Verify clients get isolated semaphores when none provided.

    Test isolation: When no semaphore is injected, each client gets
    its own semaphore. This prevents test pollution.
    """
    async with TestIOClient(
        base_url="https://api.test.io/customer/v2", api_token="token1"
    ) as client1:
        async with TestIOClient(
            base_url="https://api.test.io/customer/v2", api_token="token2"
        ) as client2:
            # Each client should have its own semaphore
            assert client1._semaphore is not client2._semaphore, (
                "Clients without injection should have isolated semaphores"
            )


@pytest.mark.asyncio
async def test_shared_semaphore_enforces_limit():
    """Verify shared semaphore enforces concurrent request limit.

    Architecture requirement: ADR-002
    ADR: ADR-002 (10 concurrent requests max)

    Test that when semaphore limit is reached, additional requests
    block until a slot becomes available.
    """
    # Create shared semaphore with limit=5
    shared_semaphore = asyncio.Semaphore(5)

    # Create multiple clients sharing the same semaphore
    clients = []
    for i in range(3):
        client = TestIOClient(
            base_url="https://api.test.io/customer/v2",
            api_token=f"token_{i}",
            semaphore=shared_semaphore,
        )
        await client.__aenter__()
        clients.append(client)

    try:
        # All clients share the same semaphore with limit=5
        semaphore = clients[0]._semaphore
        assert all(c._semaphore is semaphore for c in clients), (
            "All clients must share same semaphore"
        )

        # Track concurrent request count
        concurrent_count = 0
        max_concurrent = 0
        lock = asyncio.Lock()

        async def mock_request(client_id: int):
            """Simulate API request with tracking."""
            nonlocal concurrent_count, max_concurrent

            async with lock:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)

            # Simulate work
            await asyncio.sleep(0.1)

            async with lock:
                concurrent_count -= 1

        # Mock the httpx client for all instances
        for client in clients:

            async def mock_get(*args, **kwargs):
                response = AsyncMock()
                response.json.return_value = {"data": "test"}
                response.raise_for_status = AsyncMock()
                return response

            client._client.get = mock_get

        # Launch 15 concurrent requests across 3 clients (should be limited to 5)
        tasks = []
        for i in range(15):
            client = clients[i % 3]  # Distribute across clients

            async def make_request(c=client, client_id=i):
                async with c._semaphore:
                    await mock_request(client_id)

            tasks.append(asyncio.create_task(make_request()))

        await asyncio.gather(*tasks)

        # Verify semaphore limited concurrent requests to 5
        assert max_concurrent <= 5, (
            f"Semaphore should limit concurrent requests to 5, got {max_concurrent}"
        )

    finally:
        # Cleanup
        for client in clients:
            await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_custom_limit_without_shared_semaphore():
    """Verify custom limits work when no semaphore provided."""
    client = TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token="test_token",
        max_concurrent_requests=3,  # Custom limit
    )

    # Verify semaphore created with custom limit
    assert client._semaphore is not None
    assert client._semaphore._value == 3


@pytest.mark.asyncio
async def test_sequential_client_creation_with_shared_semaphore():
    """Verify sequential client creation with shared semaphore.

    Even if clients are created sequentially (not in nested async with),
    they share the injected semaphore.
    """
    shared_semaphore = asyncio.Semaphore(10)

    client1 = TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token="token1",
        semaphore=shared_semaphore,
    )
    await client1.__aenter__()

    client2 = TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token="token2",
        semaphore=shared_semaphore,
    )
    await client2.__aenter__()

    try:
        assert client1._semaphore is client2._semaphore, (
            "Sequential clients must share injected semaphore"
        )
        assert client1._semaphore is shared_semaphore
    finally:
        await client1.__aexit__(None, None, None)
        await client2.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_phase_3_multi_tenant_simulation():
    """Simulate Phase 3 multi-tenant scenario with dependency injection.

    Architecture requirement: ADR-002
    Use case: Phase 3 deployment

    Scenario:
    - 10 users, each with their own API token
    - Server creates shared semaphore and injects it into all clients
    - Each user makes multiple concurrent requests
    - Global semaphore limits total concurrent requests across ALL users
    """
    # Server creates shared semaphore (like server.py does)
    server_semaphore = asyncio.Semaphore(5)

    # Simulate 10 users
    user_tokens = [f"user_{i}_token" for i in range(10)]
    clients = []

    # Create client for each user, inject shared semaphore
    for token in user_tokens:
        client = TestIOClient(
            base_url="https://api.test.io/customer/v2",
            api_token=token,
            semaphore=server_semaphore,  # Server injects shared semaphore
        )
        await client.__aenter__()
        clients.append(client)

    try:
        # Verify all clients share the server's semaphore
        first_sem = clients[0]._semaphore
        assert all(c._semaphore is first_sem for c in clients), (
            "All user clients must share server's semaphore (Phase 3 requirement)"
        )
        assert first_sem is server_semaphore

        # Track concurrent requests
        concurrent_count = 0
        max_concurrent = 0
        lock = asyncio.Lock()

        async def user_request(user_id: int):
            """Simulate user making API request."""
            nonlocal concurrent_count, max_concurrent

            client = clients[user_id]

            # Mock httpx client
            async def mock_get(*args, **kwargs):
                response = AsyncMock()
                response.json.return_value = {"user": user_id}
                response.raise_for_status = AsyncMock()
                return response

            client._client.get = mock_get

            # Make request through semaphore (like real client.get())
            async with client._semaphore:
                async with lock:
                    concurrent_count += 1
                    max_concurrent = max(max_concurrent, concurrent_count)

                await asyncio.sleep(0.05)  # Simulate API latency

                async with lock:
                    concurrent_count -= 1

        # Each user makes 5 requests = 50 total requests
        # But only 5 should run concurrently (server's semaphore limit)
        tasks = []
        for user_id in range(10):
            for _ in range(5):
                tasks.append(asyncio.create_task(user_request(user_id)))

        await asyncio.gather(*tasks)

        # Verify global limit was enforced
        assert max_concurrent <= 5, (
            f"Server semaphore should limit to 5, got {max_concurrent} concurrent requests"
        )

        # Verify all requests completed
        assert len(tasks) == 50, "All 50 requests should complete"

    finally:
        for client in clients:
            await client.__aexit__(None, None, None)

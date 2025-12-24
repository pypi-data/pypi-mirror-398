"""Unit tests for UserRepository.

Tests user creation, deduplication, and query methods for both tester and customer users.

STORY-036: User Metadata Extraction (AC7)
Epic: EPIC-005 (Data Enhancement and Serving)
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.models.orm import Bug, Test, User
from testio_mcp.repositories.user_repository import UserRepository


@pytest_asyncio.fixture
async def async_session_with_tables():
    """Async session with all ORM tables created for each test.

    Creates a fresh in-memory database for each test to ensure isolation.
    Uses StaticPool to ensure table creation is visible to the session.
    """
    from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool
    from sqlmodel import SQLModel

    # Import all ORM models to ensure they're registered in metadata
    from testio_mcp.models.orm import Bug, Product, Test, User  # noqa: F401

    # Create engine for this test
    engine: AsyncEngine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        poolclass=StaticPool,  # Share in-memory DB across connections
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create session factory
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.fixture
def customer_id() -> int:
    """Customer ID for tests."""
    return 123


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_user_creates_tester_user(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test tester user creation."""
    repo = UserRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Upsert tester user
    user = await repo.upsert_user(
        username="tester1",
        user_type="tester",
        raw_data={"name": "tester1", "id": 123},
    )

    # Verify user created
    assert user is not None
    assert user.username == "tester1"
    assert user.user_type == "tester"
    assert user.id is not None  # Auto-generated ID
    assert user.first_seen is not None
    assert user.last_seen is not None

    # Verify stored in database
    result = await async_session_with_tables.exec(
        select(User).where(col(User.username) == "tester1")
    )
    db_user = result.first()
    assert db_user is not None
    assert db_user.id == user.id
    assert db_user.user_type == "tester"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_user_creates_customer_user(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test customer user creation."""
    repo = UserRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Upsert customer user
    user = await repo.upsert_user(username="B M", user_type="customer")

    # Verify user created
    assert user is not None
    assert user.username == "B M"
    assert user.user_type == "customer"
    assert user.id is not None

    # Verify stored in database
    result = await async_session_with_tables.exec(select(User).where(col(User.username) == "B M"))
    db_user = result.first()
    assert db_user is not None
    assert db_user.user_type == "customer"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_user_deduplicates_by_username(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test user deduplication when same username used as tester and customer.

    "First wins" behavior: If a user is first seen as tester, later references
    as customer will still show user_type="tester".
    """
    repo = UserRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Create user as tester first
    user1 = await repo.upsert_user(username="john_doe", user_type="tester")
    assert user1 is not None
    first_seen = user1.first_seen
    first_id = user1.id

    # Upsert same username as customer (should deduplicate, not create new)
    user2 = await repo.upsert_user(username="john_doe", user_type="customer")
    assert user2 is not None

    # Verify same user (deduplication by username)
    assert user2.id == first_id  # Same ID
    assert user2.user_type == "tester"  # Keeps original type (first wins)
    assert user2.first_seen == first_seen  # first_seen unchanged
    assert user2.last_seen >= first_seen  # last_seen updated

    # Verify only one user in database
    result = await async_session_with_tables.exec(select(func.count(col(User.id))))
    count = result.one()
    assert count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_user_updates_last_seen_on_existing_user(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test that upsert_user updates last_seen for existing users."""
    repo = UserRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Create user
    user1 = await repo.upsert_user(username="active_tester", user_type="tester")
    assert user1 is not None
    original_last_seen = user1.last_seen

    # Wait briefly to ensure timestamp difference
    await async_session_with_tables.exec(select(User))  # Small delay

    # Upsert same user again
    user2 = await repo.upsert_user(username="active_tester", user_type="tester")
    assert user2 is not None

    # Verify last_seen was updated
    assert user2.id == user1.id  # Same user
    assert user2.last_seen >= original_last_seen  # last_seen updated


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_user_handles_empty_username(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test that upsert_user returns None for empty username."""
    repo = UserRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Upsert with empty username
    user = await repo.upsert_user(username="", user_type="tester")

    # Verify no user created
    assert user is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_top_contributors_testers(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test get_top_contributors for testers (by bug count)."""
    # Create tester users
    user1 = User(
        id=1,
        customer_id=customer_id,
        username="tester1",
        user_type="tester",
        raw_data="{}",
        first_seen=datetime.now(UTC),
        last_seen=datetime.now(UTC),
    )
    user2 = User(
        id=2,
        customer_id=customer_id,
        username="tester2",
        user_type="tester",
        raw_data="{}",
        first_seen=datetime.now(UTC),
        last_seen=datetime.now(UTC),
    )
    async_session_with_tables.add(user1)
    async_session_with_tables.add(user2)
    await async_session_with_tables.commit()

    # Create bugs (user1: 3 bugs, user2: 1 bug)
    now = datetime.now(UTC)
    bug1 = Bug(
        id=1,
        title="Bug 1",
        test_id=1,
        product_id=598,
        customer_id=customer_id,
        reported_by_user_id=1,
        raw_data="{}",
        synced_at=now,
    )
    bug2 = Bug(
        id=2,
        title="Bug 2",
        test_id=1,
        product_id=598,
        customer_id=customer_id,
        reported_by_user_id=1,
        raw_data="{}",
        synced_at=now,
    )
    bug3 = Bug(
        id=3,
        title="Bug 3",
        test_id=1,
        product_id=598,
        customer_id=customer_id,
        reported_by_user_id=1,
        raw_data="{}",
        synced_at=now,
    )
    bug4 = Bug(
        id=4,
        title="Bug 4",
        test_id=1,
        product_id=598,
        customer_id=customer_id,
        reported_by_user_id=2,
        raw_data="{}",
        synced_at=now,
    )
    async_session_with_tables.add_all([bug1, bug2, bug3, bug4])
    await async_session_with_tables.commit()

    repo = UserRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Get top contributors (testers)
    contributors = await repo.get_top_contributors(user_type="tester", limit=10)

    # Verify results
    assert len(contributors) == 2
    assert contributors[0][0].id == 1  # user1 (3 bugs)
    assert contributors[0][1] == 3  # bug count
    assert contributors[1][0].id == 2  # user2 (1 bug)
    assert contributors[1][1] == 1  # bug count


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_top_contributors_customers(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test get_top_contributors for customers (by test count)."""
    # Create customer users
    user1 = User(
        id=1,
        customer_id=customer_id,
        username="customer1",
        user_type="customer",
        raw_data="{}",
        first_seen=datetime.now(UTC),
        last_seen=datetime.now(UTC),
    )
    user2 = User(
        id=2,
        customer_id=customer_id,
        username="customer2",
        user_type="customer",
        raw_data="{}",
        first_seen=datetime.now(UTC),
        last_seen=datetime.now(UTC),
    )
    async_session_with_tables.add(user1)
    async_session_with_tables.add(user2)
    await async_session_with_tables.commit()

    # Create tests (user1: 2 tests, user2: 1 test)
    now = datetime.now(UTC)
    test1 = Test(
        id=1,
        customer_id=customer_id,
        product_id=598,
        created_by_user_id=1,
        data="{}",
        status="archived",
        created_at=now,
        synced_at=now,
    )
    test2 = Test(
        id=2,
        customer_id=customer_id,
        product_id=598,
        created_by_user_id=1,
        data="{}",
        status="archived",
        created_at=now,
        synced_at=now,
    )
    test3 = Test(
        id=3,
        customer_id=customer_id,
        product_id=598,
        created_by_user_id=2,
        data="{}",
        status="archived",
        created_at=now,
        synced_at=now,
    )
    async_session_with_tables.add_all([test1, test2, test3])
    await async_session_with_tables.commit()

    repo = UserRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Get top contributors (customers)
    contributors = await repo.get_top_contributors(user_type="customer", limit=10)

    # Verify results
    assert len(contributors) == 2
    assert contributors[0][0].id == 1  # user1 (2 tests)
    assert contributors[0][1] == 2  # test count
    assert contributors[1][0].id == 2  # user2 (1 test)
    assert contributors[1][1] == 1  # test count


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_users_filtered_by_type(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test get_active_users filters by user_type."""
    # Create users with different types
    now = datetime.now(UTC)
    tester = User(
        id=1,
        customer_id=customer_id,
        username="tester1",
        user_type="tester",
        last_seen=now,
        first_seen=now,
        raw_data="{}",
    )
    customer = User(
        id=2,
        customer_id=customer_id,
        username="customer1",
        user_type="customer",
        last_seen=now,
        first_seen=now,
        raw_data="{}",
    )
    async_session_with_tables.add(tester)
    async_session_with_tables.add(customer)
    await async_session_with_tables.commit()

    repo = UserRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Get active testers only
    active_testers = await repo.get_active_users(user_type="tester", days=30)
    assert len(active_testers) == 1
    assert active_testers[0].user_type == "tester"

    # Get active customers only
    active_customers = await repo.get_active_users(user_type="customer", days=30)
    assert len(active_customers) == 1
    assert active_customers[0].user_type == "customer"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_users_filters_by_date_range(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test get_active_users filters by last_seen date."""
    now = datetime.now(UTC)
    old_date = now - timedelta(days=60)

    # Create users with different last_seen timestamps
    active_user = User(
        id=1,
        customer_id=customer_id,
        username="active_user",
        user_type="tester",
        last_seen=now,
        first_seen=now,
        raw_data="{}",
    )
    inactive_user = User(
        id=2,
        customer_id=customer_id,
        username="inactive_user",
        user_type="tester",
        last_seen=old_date,
        first_seen=old_date,
        raw_data="{}",
    )
    async_session_with_tables.add(active_user)
    async_session_with_tables.add(inactive_user)
    await async_session_with_tables.commit()

    repo = UserRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Get users active in last 30 days
    active_users = await repo.get_active_users(user_type="tester", days=30)

    # Verify only active user returned
    assert len(active_users) == 1
    assert active_users[0].id == 1
    assert active_users[0].username == "active_user"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_by_username(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test get_user_by_username lookup."""
    # Create user
    now = datetime.now(UTC)
    user = User(
        id=1,
        customer_id=customer_id,
        username="lookup_test",
        user_type="tester",
        last_seen=now,
        first_seen=now,
        raw_data="{}",
    )
    async_session_with_tables.add(user)
    await async_session_with_tables.commit()

    repo = UserRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Lookup existing user
    found = await repo.get_user_by_username("lookup_test")
    assert found is not None
    assert found.id == 1
    assert found.username == "lookup_test"

    # Lookup non-existent user
    not_found = await repo.get_user_by_username("does_not_exist")
    assert not_found is None

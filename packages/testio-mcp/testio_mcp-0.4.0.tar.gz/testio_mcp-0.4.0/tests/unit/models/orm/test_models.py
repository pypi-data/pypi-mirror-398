"""
Unit tests for ORM models.

Tests model instantiation, field types, relationships, and schema compatibility.
"""

import json
from datetime import datetime

import pytest
from sqlmodel import Session, create_engine, select

from testio_mcp.models.orm import Bug, Product, SyncEvent, SyncMetadata, Test


@pytest.fixture
def engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    # Import SQLModel to create tables
    from sqlmodel import SQLModel

    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create database session for testing."""
    with Session(engine) as session:
        yield session


class TestProductModel:
    """Tests for Product model."""

    def test_product_instantiation(self):
        """Test Product model can be instantiated with valid data."""
        product = Product(
            id=123,
            customer_id=456,
            data=json.dumps({"name": "Test Product", "type": "website"}),
            last_synced=datetime(2025, 11, 22, 10, 0, 0),
        )

        assert product.id == 123
        assert product.customer_id == 456
        assert product.data == json.dumps({"name": "Test Product", "type": "website"})
        assert product.last_synced == datetime(2025, 11, 22, 10, 0, 0)

    def test_product_table_name(self):
        """Test Product has correct table name."""
        assert Product.__tablename__ == "products"

    def test_product_nullable_fields(self):
        """Test Product allows nullable fields."""
        product = Product(customer_id=456, data=json.dumps({"name": "Test Product"}))

        assert product.id is None
        assert product.last_synced is None

    def test_product_persistence(self, session):
        """Test Product can be saved and retrieved from database."""
        product = Product(
            id=123,
            customer_id=456,
            title="Test Product",
            data=json.dumps({"name": "Test Product"}),
        )

        session.add(product)
        session.commit()

        # Retrieve product
        statement = select(Product).where(Product.id == 123)
        result = session.exec(statement).first()

        assert result is not None
        assert result.id == 123
        assert result.customer_id == 456


class TestTestModel:
    """Tests for Test model."""

    def test_test_instantiation(self):
        """Test Test model can be instantiated with valid data."""
        test = Test(
            id=789,
            customer_id=456,
            product_id=123,
            data=json.dumps({"title": "Test Case"}),
            status="running",
            start_at=datetime(2025, 11, 22, 11, 0, 0),
            end_at=datetime(2025, 11, 22, 12, 0, 0),
            synced_at=datetime(2025, 11, 22, 13, 0, 0),
            bugs_synced_at=datetime(2025, 11, 22, 13, 30, 0),
        )

        assert test.id == 789
        assert test.customer_id == 456
        assert test.product_id == 123
        assert test.status == "running"
        # STORY-054: created_at removed (not provided by API)
        assert test.bugs_synced_at == datetime(2025, 11, 22, 13, 30, 0)

    def test_test_table_name(self):
        """Test Test has correct table name."""
        assert Test.__tablename__ == "tests"

    def test_test_nullable_fields(self):
        """Test Test allows nullable timestamp fields."""
        test = Test(
            customer_id=456,
            product_id=123,
            data=json.dumps({"title": "Test Case"}),
            status="running",
        )

        assert test.id is None
        # STORY-054: created_at removed (not provided by API)
        assert test.start_at is None
        assert test.end_at is None
        assert test.synced_at is None
        assert test.bugs_synced_at is None

    def test_test_relationship_to_bugs(self, session):
        """Test Test.bugs relationship navigation."""
        # Create test
        test = Test(
            id=789,
            customer_id=456,
            product_id=123,
            data=json.dumps({"title": "Test Case"}),
            status="running",
        )
        session.add(test)
        session.commit()

        # Create bugs
        bug1 = Bug(
            id=1,
            customer_id=456,
            test_id=789,
            title="Bug 1",
            raw_data=json.dumps({"severity": "high"}),
        )
        bug2 = Bug(
            id=2,
            customer_id=456,
            test_id=789,
            title="Bug 2",
            raw_data=json.dumps({"severity": "low"}),
        )
        session.add(bug1)
        session.add(bug2)
        session.commit()

        # Refresh test to load relationships
        session.refresh(test)

        # Verify relationship
        assert len(test.bugs) == 2
        assert test.bugs[0].title in ["Bug 1", "Bug 2"]
        assert test.bugs[1].title in ["Bug 1", "Bug 2"]


class TestBugModel:
    """Tests for Bug model."""

    def test_bug_instantiation(self):
        """Test Bug model can be instantiated with valid data."""
        bug = Bug(
            id=1,
            customer_id=456,
            test_id=789,
            title="Critical bug",
            severity="high",
            status="open",
            raw_data=json.dumps({"description": "Bug details"}),
            synced_at=datetime(2025, 11, 22, 13, 0, 0),
        )

        assert bug.id == 1
        assert bug.customer_id == 456
        assert bug.test_id == 789
        assert bug.title == "Critical bug"
        assert bug.severity == "high"
        assert bug.status == "open"

    def test_bug_table_name(self):
        """Test Bug has correct table name."""
        assert Bug.__tablename__ == "bugs"

    def test_bug_nullable_fields(self):
        """Test Bug allows nullable fields."""
        bug = Bug(
            customer_id=456,
            test_id=789,
            title="Bug",
            raw_data=json.dumps({}),
        )

        assert bug.id is None
        assert bug.severity is None
        assert bug.status is None
        assert bug.synced_at is None

    def test_bug_foreign_key(self, session):
        """Test Bug has foreign key to Test."""
        # Create test first
        test = Test(
            id=789,
            customer_id=456,
            product_id=123,
            data=json.dumps({"title": "Test Case"}),
            status="running",
        )
        session.add(test)
        session.commit()

        # Create bug
        bug = Bug(
            id=1,
            customer_id=456,
            test_id=789,
            title="Bug",
            raw_data=json.dumps({}),
        )
        session.add(bug)
        session.commit()

        # Verify relationship
        statement = select(Bug).where(Bug.test_id == 789)
        result = session.exec(statement).first()

        assert result is not None
        assert result.test_id == 789


class TestSyncEventModel:
    """Tests for SyncEvent model."""

    def test_sync_event_instantiation(self):
        """Test SyncEvent model can be instantiated with valid data."""
        event = SyncEvent(
            id=1,
            event_type="initial_sync",
            started_at="2025-11-22T10:00:00Z",
            completed_at="2025-11-22T10:05:00Z",
            status="success",
            products_synced=10,
            tests_discovered=50,
            tests_refreshed=5,
            duration_seconds=300.5,
            error_message=None,
            trigger_source="startup",
        )

        assert event.id == 1
        assert event.event_type == "initial_sync"
        assert event.status == "success"
        assert event.products_synced == 10
        assert event.tests_discovered == 50
        assert event.duration_seconds == 300.5
        assert event.trigger_source == "startup"

    def test_sync_event_table_name(self):
        """Test SyncEvent has correct table name."""
        assert SyncEvent.__tablename__ == "sync_events"

    def test_sync_event_nullable_fields(self):
        """Test SyncEvent allows nullable fields."""
        event = SyncEvent(
            event_type="background_refresh",
            started_at="2025-11-22T10:00:00Z",
            status="running",
        )

        assert event.id is None
        assert event.completed_at is None
        assert event.products_synced is None
        assert event.tests_discovered is None
        assert event.tests_refreshed is None
        assert event.duration_seconds is None
        assert event.error_message is None
        assert event.trigger_source is None


class TestSyncMetadataModel:
    """Tests for SyncMetadata model."""

    def test_sync_metadata_instantiation(self):
        """Test SyncMetadata model can be instantiated with valid data."""
        metadata = SyncMetadata(key="schema_version", value=json.dumps({"version": 4}))

        assert metadata.key == "schema_version"
        assert metadata.value == json.dumps({"version": 4})

    def test_sync_metadata_table_name(self):
        """Test SyncMetadata has correct table name."""
        assert SyncMetadata.__tablename__ == "sync_metadata"

    def test_sync_metadata_nullable_value(self):
        """Test SyncMetadata allows nullable value."""
        metadata = SyncMetadata(key="test_key")

        assert metadata.key == "test_key"
        assert metadata.value is None

    def test_sync_metadata_persistence(self, session):
        """Test SyncMetadata can be saved and retrieved."""
        metadata = SyncMetadata(key="schema_version", value="4")

        session.add(metadata)
        session.commit()

        # Retrieve metadata
        statement = select(SyncMetadata).where(SyncMetadata.key == "schema_version")
        result = session.exec(statement).first()

        assert result is not None
        assert result.key == "schema_version"
        assert result.value == "4"


class TestSchemaCompatibility:
    """Tests to verify models match existing schema.py."""

    def test_all_models_have_correct_table_names(self):
        """Verify all models have table names matching schema.py."""
        assert Product.__tablename__ == "products"
        assert Test.__tablename__ == "tests"
        assert Bug.__tablename__ == "bugs"
        assert SyncEvent.__tablename__ == "sync_events"
        assert SyncMetadata.__tablename__ == "sync_metadata"

    def test_product_fields_match_schema(self):
        """Verify Product fields match schema.py definition."""
        product = Product(customer_id=1, data="{}")

        # Check all expected fields exist
        assert hasattr(product, "id")
        assert hasattr(product, "customer_id")
        assert hasattr(product, "data")
        assert hasattr(product, "last_synced")

    def test_test_fields_match_schema(self):
        """Verify Test fields match schema.py definition."""
        test = Test(customer_id=1, product_id=1, data="{}", status="running")

        # Check all expected fields exist
        assert hasattr(test, "id")
        assert hasattr(test, "customer_id")
        assert hasattr(test, "product_id")
        assert hasattr(test, "data")
        assert hasattr(test, "status")
        # STORY-054: created_at removed (always NULL, not from API)
        assert hasattr(test, "title")  # New field from STORY-054
        assert hasattr(test, "start_at")
        assert hasattr(test, "end_at")
        assert hasattr(test, "synced_at")
        assert hasattr(test, "bugs_synced_at")

    def test_bug_fields_match_schema(self):
        """Verify Bug fields match schema.py definition."""
        bug = Bug(customer_id=1, test_id=1, title="Bug", raw_data="{}")

        # Check all expected fields exist
        assert hasattr(bug, "id")
        assert hasattr(bug, "customer_id")
        assert hasattr(bug, "test_id")
        assert hasattr(bug, "title")
        assert hasattr(bug, "severity")
        assert hasattr(bug, "status")
        assert hasattr(bug, "raw_data")
        assert hasattr(bug, "synced_at")
        # Removed: acceptance_state and created_at (never populated by API)

    def test_sync_event_fields_match_schema(self):
        """Verify SyncEvent fields match schema.py definition."""
        event = SyncEvent(event_type="test", started_at="2025-11-22", status="success")

        # Check all expected fields exist
        assert hasattr(event, "id")
        assert hasattr(event, "event_type")
        assert hasattr(event, "started_at")
        assert hasattr(event, "completed_at")
        assert hasattr(event, "status")
        assert hasattr(event, "products_synced")
        assert hasattr(event, "tests_discovered")
        assert hasattr(event, "tests_refreshed")
        assert hasattr(event, "duration_seconds")
        assert hasattr(event, "error_message")
        assert hasattr(event, "trigger_source")

    def test_sync_metadata_fields_match_schema(self):
        """Verify SyncMetadata fields match schema.py definition."""
        metadata = SyncMetadata(key="test")

        # Check all expected fields exist
        assert hasattr(metadata, "key")
        assert hasattr(metadata, "value")

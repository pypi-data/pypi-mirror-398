import json
import sqlite3
from pathlib import Path

import alembic.config
import alembic.command
from sqlalchemy import create_engine, text

# Configuration
DB_PATH = "testio_mcp_test.db"
ALEMBIC_CFG = alembic.config.Config("alembic.ini")
ALEMBIC_CFG.set_main_option("sqlalchemy.url", f"sqlite:///{DB_PATH}")

def setup_db():
    """Create a fresh database and run migrations up to the previous revision."""
    if Path(DB_PATH).exists():
        Path(DB_PATH).unlink()

    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.connect() as connection:
        ALEMBIC_CFG.attributes["connection"] = connection
        alembic.command.upgrade(ALEMBIC_CFG, "f63655d178ae")  # pragma: allowlist secret

        # Insert test data
        # We can use the same connection or a new one, but let's use sqlite3 for simplicity as before
        # or just use sqlalchemy connection

        # Insert a test with test_environment in data
        test_data = json.dumps({
            "id": 101,
            "title": "Test with Env",
            "test_environment": {"id": 1, "title": "Production"}
        })
        connection.execute(text(
            "INSERT INTO tests (id, customer_id, product_id, status, data) VALUES (:id, :cid, :pid, :status, :data)"
        ), {"id": 101, "cid": 1, "pid": 1, "status": "running", "data": test_data})

        # Insert a test WITHOUT test_environment
        test_data_no_env = json.dumps({
            "id": 102,
            "title": "Test without Env"
        })
        connection.execute(text(
            "INSERT INTO tests (id, customer_id, product_id, status, data) VALUES (:id, :cid, :pid, :status, :data)"
        ), {"id": 102, "cid": 1, "pid": 1, "status": "running", "data": test_data_no_env})

        # Insert a bug with known=true in raw_data
        bug_data_known = json.dumps({
            "id": 201,
            "title": "Known Bug",
            "known": True
        })
        connection.execute(text(
            "INSERT INTO bugs (id, customer_id, test_id, title, raw_data) VALUES (:id, :cid, :tid, :title, :raw)"
        ), {"id": 201, "cid": 1, "tid": 101, "title": "Known Bug", "raw": bug_data_known})

        # Insert a bug with known=false in raw_data
        bug_data_unknown = json.dumps({
            "id": 202,
            "title": "Unknown Bug",
            "known": False
        })
        connection.execute(text(
            "INSERT INTO bugs (id, customer_id, test_id, title, raw_data) VALUES (:id, :cid, :tid, :title, :raw)"
        ), {"id": 202, "cid": 1, "tid": 101, "title": "Unknown Bug", "raw": bug_data_unknown})

        # Insert a bug WITHOUT known field (should default to False)
        bug_data_missing = json.dumps({
            "id": 203,
            "title": "Missing Known Field"
        })
        connection.execute(text(
            "INSERT INTO bugs (id, customer_id, test_id, title, raw_data) VALUES (:id, :cid, :tid, :title, :raw)"
        ), {"id": 203, "cid": 1, "tid": 101, "title": "Missing Known Field", "raw": bug_data_missing})

        connection.commit()
    print("✅ Database setup with test data")

def verify_upgrade():
    """Run upgrade and verify backfill."""
    print("\nRunning upgrade...")
    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.connect() as connection:
        ALEMBIC_CFG.attributes["connection"] = connection
        alembic.command.upgrade(ALEMBIC_CFG, "head")

        # Verify Test 101 (Has Env)
        result = connection.execute(text("SELECT test_environment FROM tests WHERE id = 101")).scalar()
        env = json.loads(result)
        assert env["id"] == 1
        assert env["title"] == "Production"
        print("✅ Test 101: test_environment backfilled correctly")

        # Verify Test 102 (No Env)
        result = connection.execute(text("SELECT test_environment FROM tests WHERE id = 102")).scalar()
        assert result is None
        print("✅ Test 102: test_environment is None as expected")

        # Verify Bug 201 (Known=True)
        result = connection.execute(text("SELECT known FROM bugs WHERE id = 201")).scalar()
        assert result == 1  # SQLite stores True as 1
        print("✅ Bug 201: known=True backfilled correctly")

        # Verify Bug 202 (Known=False)
        result = connection.execute(text("SELECT known FROM bugs WHERE id = 202")).scalar()
        assert result == 0
        print("✅ Bug 202: known=False backfilled correctly")

        # Verify Bug 203 (Missing Known -> Default False)
        result = connection.execute(text("SELECT known FROM bugs WHERE id = 203")).scalar()
        assert result == 0
        print("✅ Bug 203: known defaulted to False correctly")

def verify_downgrade():
    """Run downgrade and verify columns removed."""
    print("\nRunning downgrade...")
    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.connect() as connection:
        ALEMBIC_CFG.attributes["connection"] = connection
        alembic.command.downgrade(ALEMBIC_CFG, "-1")

        # Verify columns are gone
        try:
            connection.execute(text("SELECT test_environment FROM tests"))
            print("❌ test_environment column still exists!")
        except Exception:
            print("✅ test_environment column removed")

        try:
            connection.execute(text("SELECT known FROM bugs"))
            print("❌ known column still exists!")
        except Exception:
            print("✅ known column removed")

if __name__ == "__main__":
    try:
        setup_db()
        verify_upgrade()
        verify_downgrade()
        print("\n🎉 Verification Successful!")
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        exit(1)
    finally:
        if Path(DB_PATH).exists():
            Path(DB_PATH).unlink()

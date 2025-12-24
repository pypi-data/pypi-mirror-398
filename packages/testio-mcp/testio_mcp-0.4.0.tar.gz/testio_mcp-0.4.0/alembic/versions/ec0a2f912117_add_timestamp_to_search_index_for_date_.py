"""Add timestamp to search_index for date filtering (STORY-065)

Add timestamp column to FTS5 search_index for date range filtering.
Since FTS5 doesn't support ALTER TABLE, we drop and recreate the table.

Timestamps:
- Tests: end_at (never null, used for time filtering)
- Bugs: reported_at (used for time filtering)
- Features: NULL (excluded from time filtering)
- Products: NULL (excluded from time filtering)

Revision ID: ec0a2f912117
Revises: aae371b62afd
Create Date: 2025-11-29 14:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ec0a2f912117"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "aae371b62afd"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Recreates FTS5 table with timestamp column (FTS5 doesn't support ALTER TABLE).
    """
    # 1. Drop existing triggers
    op.execute("DROP TRIGGER IF EXISTS bugs_ad")
    op.execute("DROP TRIGGER IF EXISTS bugs_au")
    op.execute("DROP TRIGGER IF EXISTS bugs_ai")
    op.execute("DROP TRIGGER IF EXISTS tests_ad")
    op.execute("DROP TRIGGER IF EXISTS tests_au")
    op.execute("DROP TRIGGER IF EXISTS tests_ai")
    op.execute("DROP TRIGGER IF EXISTS features_ad")
    op.execute("DROP TRIGGER IF EXISTS features_au")
    op.execute("DROP TRIGGER IF EXISTS features_ai")
    op.execute("DROP TRIGGER IF EXISTS products_ad")
    op.execute("DROP TRIGGER IF EXISTS products_au")
    op.execute("DROP TRIGGER IF EXISTS products_ai")

    # 2. Drop existing FTS5 table
    op.execute("DROP TABLE IF EXISTS search_index")

    # 3. Create FTS5 virtual table with timestamp column
    op.execute("""
        CREATE VIRTUAL TABLE search_index USING fts5(
            entity_type UNINDEXED,
            entity_id UNINDEXED,
            product_id UNINDEXED,
            timestamp UNINDEXED,
            title,
            content,
            tokenize='porter unicode61 remove_diacritics 2',
            prefix='2 3'
        )
    """)

    # 4. Create triggers for products table (timestamp = NULL)
    op.execute("""
        CREATE TRIGGER products_ai AFTER INSERT ON products BEGIN
            INSERT INTO search_index(entity_type, entity_id, product_id, timestamp, title, content)
            VALUES (
                'product',
                NEW.id,
                NEW.id,
                NULL,
                NEW.title,
                NEW.title
            );
        END
    """)

    op.execute("""
        CREATE TRIGGER products_au AFTER UPDATE ON products BEGIN
            UPDATE search_index
            SET
                product_id = NEW.id,
                timestamp = NULL,
                title = NEW.title,
                content = NEW.title
            WHERE entity_type = 'product' AND entity_id = OLD.id;
        END
    """)

    op.execute("""
        CREATE TRIGGER products_ad AFTER DELETE ON products BEGIN
            DELETE FROM search_index
            WHERE entity_type = 'product' AND entity_id = OLD.id;
        END
    """)

    # 5. Create triggers for features table (timestamp = NULL)
    op.execute("""
        CREATE TRIGGER features_ai AFTER INSERT ON features BEGIN
            INSERT INTO search_index(entity_type, entity_id, product_id, timestamp, title, content)
            VALUES (
                'feature',
                NEW.id,
                NEW.product_id,
                NULL,
                NEW.title,
                NEW.title || ' ' ||
                COALESCE(NEW.description, '') || ' ' ||
                COALESCE(NEW.howtofind, '') || ' ' ||
                COALESCE(NEW.user_stories, '')
            );
        END
    """)

    op.execute("""
        CREATE TRIGGER features_au AFTER UPDATE ON features BEGIN
            UPDATE search_index
            SET
                product_id = NEW.product_id,
                timestamp = NULL,
                title = NEW.title,
                content = NEW.title || ' ' ||
                          COALESCE(NEW.description, '') || ' ' ||
                          COALESCE(NEW.howtofind, '') || ' ' ||
                          COALESCE(NEW.user_stories, '')
            WHERE entity_type = 'feature' AND entity_id = OLD.id;
        END
    """)

    op.execute("""
        CREATE TRIGGER features_ad AFTER DELETE ON features BEGIN
            DELETE FROM search_index
            WHERE entity_type = 'feature' AND entity_id = OLD.id;
        END
    """)

    # 6. Create triggers for tests table (timestamp = end_at)
    op.execute("""
        CREATE TRIGGER tests_ai AFTER INSERT ON tests BEGIN
            INSERT INTO search_index(entity_type, entity_id, product_id, timestamp, title, content)
            VALUES (
                'test',
                NEW.id,
                NEW.product_id,
                NEW.end_at,
                COALESCE(NEW.title, ''),
                COALESCE(NEW.title, '') || ' ' ||
                COALESCE(NEW.goal, '') || ' ' ||
                COALESCE(NEW.instructions, '') || ' ' ||
                COALESCE(NEW.out_of_scope, '')
            );
        END
    """)

    op.execute("""
        CREATE TRIGGER tests_au AFTER UPDATE ON tests BEGIN
            UPDATE search_index
            SET
                product_id = NEW.product_id,
                timestamp = NEW.end_at,
                title = COALESCE(NEW.title, ''),
                content = COALESCE(NEW.title, '') || ' ' ||
                          COALESCE(NEW.goal, '') || ' ' ||
                          COALESCE(NEW.instructions, '') || ' ' ||
                          COALESCE(NEW.out_of_scope, '')
            WHERE entity_type = 'test' AND entity_id = OLD.id;
        END
    """)

    op.execute("""
        CREATE TRIGGER tests_ad AFTER DELETE ON tests BEGIN
            DELETE FROM search_index
            WHERE entity_type = 'test' AND entity_id = OLD.id;
        END
    """)

    # 7. Create triggers for bugs table (timestamp = reported_at)
    op.execute("""
        CREATE TRIGGER bugs_ai AFTER INSERT ON bugs BEGIN
            INSERT INTO search_index(entity_type, entity_id, product_id, timestamp, title, content)
            SELECT
                'bug',
                NEW.id,
                tests.product_id,
                NEW.reported_at,
                NEW.title,
                NEW.title || ' ' ||
                COALESCE(NEW.steps, '') || ' ' ||
                COALESCE(NEW.actual_result, '') || ' ' ||
                COALESCE(NEW.expected_result, '')
            FROM tests
            WHERE tests.id = NEW.test_id;
        END
    """)

    op.execute("""
        CREATE TRIGGER bugs_au AFTER UPDATE ON bugs BEGIN
            UPDATE search_index
            SET
                timestamp = NEW.reported_at,
                title = NEW.title,
                content = NEW.title || ' ' ||
                          COALESCE(NEW.steps, '') || ' ' ||
                          COALESCE(NEW.actual_result, '') || ' ' ||
                          COALESCE(NEW.expected_result, '')
            WHERE entity_type = 'bug' AND entity_id = OLD.id;
        END
    """)

    op.execute("""
        CREATE TRIGGER bugs_ad AFTER DELETE ON bugs BEGIN
            DELETE FROM search_index
            WHERE entity_type = 'bug' AND entity_id = OLD.id;
        END
    """)

    # 8. Populate index from existing data with timestamps
    # Products (timestamp = NULL)
    op.execute("""
        INSERT INTO search_index(entity_type, entity_id, product_id, timestamp, title, content)
        SELECT
            'product',
            id,
            id,
            NULL,
            title,
            title
        FROM products
    """)

    # Features (timestamp = NULL)
    op.execute("""
        INSERT INTO search_index(entity_type, entity_id, product_id, timestamp, title, content)
        SELECT
            'feature',
            id,
            product_id,
            NULL,
            title,
            title || ' ' ||
            COALESCE(description, '') || ' ' ||
            COALESCE(howtofind, '') || ' ' ||
            COALESCE(user_stories, '')
        FROM features
    """)

    # Tests (timestamp = end_at)
    op.execute("""
        INSERT INTO search_index(entity_type, entity_id, product_id, timestamp, title, content)
        SELECT
            'test',
            id,
            product_id,
            end_at,
            COALESCE(title, ''),
            COALESCE(title, '') || ' ' ||
            COALESCE(goal, '') || ' ' ||
            COALESCE(instructions, '') || ' ' ||
            COALESCE(out_of_scope, '')
        FROM tests
    """)

    # Bugs (timestamp = reported_at)
    op.execute("""
        INSERT INTO search_index(entity_type, entity_id, product_id, timestamp, title, content)
        SELECT
            'bug',
            bugs.id,
            tests.product_id,
            bugs.reported_at,
            bugs.title,
            bugs.title || ' ' ||
            COALESCE(bugs.steps, '') || ' ' ||
            COALESCE(bugs.actual_result, '') || ' ' ||
            COALESCE(bugs.expected_result, '')
        FROM bugs
        JOIN tests ON tests.id = bugs.test_id
    """)


def downgrade() -> None:
    """Downgrade schema.

    Reverts to previous FTS5 table without timestamp column.
    """
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS bugs_ad")
    op.execute("DROP TRIGGER IF EXISTS bugs_au")
    op.execute("DROP TRIGGER IF EXISTS bugs_ai")
    op.execute("DROP TRIGGER IF EXISTS tests_ad")
    op.execute("DROP TRIGGER IF EXISTS tests_au")
    op.execute("DROP TRIGGER IF EXISTS tests_ai")
    op.execute("DROP TRIGGER IF EXISTS features_ad")
    op.execute("DROP TRIGGER IF EXISTS features_au")
    op.execute("DROP TRIGGER IF EXISTS features_ai")
    op.execute("DROP TRIGGER IF EXISTS products_ad")
    op.execute("DROP TRIGGER IF EXISTS products_au")
    op.execute("DROP TRIGGER IF EXISTS products_ai")

    # Drop FTS5 table
    op.execute("DROP TABLE IF EXISTS search_index")

    # Recreate original FTS5 table without timestamp
    op.execute("""
        CREATE VIRTUAL TABLE search_index USING fts5(
            entity_type UNINDEXED,
            entity_id UNINDEXED,
            product_id UNINDEXED,
            title,
            content,
            tokenize='porter unicode61 remove_diacritics 2',
            prefix='2 3'
        )
    """)

    # Recreate original triggers (without timestamp)
    # Products
    op.execute("""
        CREATE TRIGGER products_ai AFTER INSERT ON products BEGIN
            INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
            VALUES ('product', NEW.id, NEW.id, NEW.title, NEW.title);
        END
    """)
    op.execute("""
        CREATE TRIGGER products_au AFTER UPDATE ON products BEGIN
            UPDATE search_index SET product_id = NEW.id, title = NEW.title, content = NEW.title
            WHERE entity_type = 'product' AND entity_id = OLD.id;
        END
    """)
    op.execute("""
        CREATE TRIGGER products_ad AFTER DELETE ON products BEGIN
            DELETE FROM search_index WHERE entity_type = 'product' AND entity_id = OLD.id;
        END
    """)

    # Features
    op.execute("""
        CREATE TRIGGER features_ai AFTER INSERT ON features BEGIN
            INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
            VALUES ('feature', NEW.id, NEW.product_id, NEW.title,
                    NEW.title || ' ' || COALESCE(NEW.description, '') || ' ' ||
                    COALESCE(NEW.howtofind, '') || ' ' || COALESCE(NEW.user_stories, ''));
        END
    """)
    op.execute("""
        CREATE TRIGGER features_au AFTER UPDATE ON features BEGIN
            UPDATE search_index SET product_id = NEW.product_id, title = NEW.title,
                   content = NEW.title || ' ' || COALESCE(NEW.description, '') || ' ' ||
                             COALESCE(NEW.howtofind, '') || ' ' || COALESCE(NEW.user_stories, '')
            WHERE entity_type = 'feature' AND entity_id = OLD.id;
        END
    """)
    op.execute("""
        CREATE TRIGGER features_ad AFTER DELETE ON features BEGIN
            DELETE FROM search_index WHERE entity_type = 'feature' AND entity_id = OLD.id;
        END
    """)

    # Tests
    op.execute("""
        CREATE TRIGGER tests_ai AFTER INSERT ON tests BEGIN
            INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
            VALUES ('test', NEW.id, NEW.product_id, COALESCE(NEW.title, ''),
                    COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.goal, '') || ' ' ||
                    COALESCE(NEW.instructions, '') || ' ' || COALESCE(NEW.out_of_scope, ''));
        END
    """)
    op.execute("""
        CREATE TRIGGER tests_au AFTER UPDATE ON tests BEGIN
            UPDATE search_index SET product_id = NEW.product_id, title = COALESCE(NEW.title, ''),
                   content = COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.goal, '') || ' ' ||
                             COALESCE(NEW.instructions, '') || ' ' || COALESCE(NEW.out_of_scope, '')
            WHERE entity_type = 'test' AND entity_id = OLD.id;
        END
    """)
    op.execute("""
        CREATE TRIGGER tests_ad AFTER DELETE ON tests BEGIN
            DELETE FROM search_index WHERE entity_type = 'test' AND entity_id = OLD.id;
        END
    """)

    # Bugs
    op.execute("""
        CREATE TRIGGER bugs_ai AFTER INSERT ON bugs BEGIN
            INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
            SELECT 'bug', NEW.id, tests.product_id, NEW.title,
                   NEW.title || ' ' || COALESCE(NEW.steps, '') || ' ' ||
                   COALESCE(NEW.actual_result, '') || ' ' || COALESCE(NEW.expected_result, '')
            FROM tests WHERE tests.id = NEW.test_id;
        END
    """)
    op.execute("""
        CREATE TRIGGER bugs_au AFTER UPDATE ON bugs BEGIN
            UPDATE search_index SET title = NEW.title,
                   content = NEW.title || ' ' || COALESCE(NEW.steps, '') || ' ' ||
                             COALESCE(NEW.actual_result, '') || ' ' ||
                             COALESCE(NEW.expected_result, '')
            WHERE entity_type = 'bug' AND entity_id = OLD.id;
        END
    """)
    op.execute("""
        CREATE TRIGGER bugs_ad AFTER DELETE ON bugs BEGIN
            DELETE FROM search_index WHERE entity_type = 'bug' AND entity_id = OLD.id;
        END
    """)

    # Repopulate original data
    op.execute("""
        INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
        SELECT 'product', id, id, title, title FROM products
    """)
    op.execute("""
        INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
        SELECT 'feature', id, product_id, title,
               title || ' ' || COALESCE(description, '') || ' ' ||
               COALESCE(howtofind, '') || ' ' || COALESCE(user_stories, '')
        FROM features
    """)
    op.execute("""
        INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
        SELECT 'test', id, product_id, COALESCE(title, ''),
               COALESCE(title, '') || ' ' || COALESCE(goal, '') || ' ' ||
               COALESCE(instructions, '') || ' ' || COALESCE(out_of_scope, '')
        FROM tests
    """)
    op.execute("""
        INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
        SELECT 'bug', bugs.id, tests.product_id, bugs.title,
               bugs.title || ' ' || COALESCE(bugs.steps, '') || ' ' ||
               COALESCE(bugs.actual_result, '') || ' ' || COALESCE(bugs.expected_result, '')
        FROM bugs JOIN tests ON tests.id = bugs.test_id
    """)

"""Add FTS5 search index (STORY-064)

Create FTS5 virtual table for full-text search across products, features, tests, and bugs.
Includes triggers for automatic index maintenance and initial data population.

Revision ID: aae371b62afd
Revises: 061ba7016275
Create Date: 2025-11-29 13:31:20.495939

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aae371b62afd"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "061ba7016275"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Creates FTS5 virtual table, triggers for automatic updates, and populates from existing data.
    """
    # 1. Create FTS5 virtual table with column weights
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

    # 2. Create triggers for products table
    op.execute("""
        CREATE TRIGGER products_ai AFTER INSERT ON products BEGIN
            INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
            VALUES (
                'product',
                NEW.id,
                NEW.id,
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

    # 3. Create triggers for features table
    op.execute("""
        CREATE TRIGGER features_ai AFTER INSERT ON features BEGIN
            INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
            VALUES (
                'feature',
                NEW.id,
                NEW.product_id,
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

    # 4. Create triggers for tests table
    op.execute("""
        CREATE TRIGGER tests_ai AFTER INSERT ON tests BEGIN
            INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
            VALUES (
                'test',
                NEW.id,
                NEW.product_id,
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

    # 5. Create triggers for bugs table
    op.execute("""
        CREATE TRIGGER bugs_ai AFTER INSERT ON bugs BEGIN
            INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
            SELECT
                'bug',
                NEW.id,
                tests.product_id,
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

    # 6. Populate index from existing data (set-based, faster than triggers)
    # Products
    op.execute("""
        INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
        SELECT
            'product',
            id,
            id,
            title,
            title
        FROM products
    """)

    # Features
    op.execute("""
        INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
        SELECT
            'feature',
            id,
            product_id,
            title,
            title || ' ' ||
            COALESCE(description, '') || ' ' ||
            COALESCE(howtofind, '') || ' ' ||
            COALESCE(user_stories, '')
        FROM features
    """)

    # Tests
    op.execute("""
        INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
        SELECT
            'test',
            id,
            product_id,
            COALESCE(title, ''),
            COALESCE(title, '') || ' ' ||
            COALESCE(goal, '') || ' ' ||
            COALESCE(instructions, '') || ' ' ||
            COALESCE(out_of_scope, '')
        FROM tests
    """)

    # Bugs (join with tests to get product_id)
    op.execute("""
        INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
        SELECT
            'bug',
            bugs.id,
            tests.product_id,
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

    Drops all triggers and the FTS5 virtual table.
    """
    # Drop triggers (in reverse order of creation)
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

    # Drop FTS5 virtual table
    op.execute("DROP TABLE IF EXISTS search_index")

"""sync items and items_fts

Revision ID: 20240603_fts_items_sync
Revises: 20240603_fts_items
Create Date: 2025-06-03 12:10:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = '20240603_fts_items_sync'
down_revision: Union[str, None] = '20240603_fts_items'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("INSERT INTO items_fts(rowid, name) SELECT id, name FROM items;")
    op.execute("""
    CREATE TRIGGER items_ai AFTER INSERT ON items BEGIN
      INSERT INTO items_fts(rowid, name) VALUES (new.id, new.name);
    END;
    """)
    op.execute("""
    CREATE TRIGGER items_au AFTER UPDATE ON items BEGIN
      UPDATE items_fts SET name = new.name WHERE rowid = new.id;
    END;
    """)
    op.execute("""
    CREATE TRIGGER items_ad AFTER DELETE ON items BEGIN
      DELETE FROM items_fts WHERE rowid = old.id;
    END;
    """)

def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS items_ai;")
    op.execute("DROP TRIGGER IF EXISTS items_au;")
    op.execute("DROP TRIGGER IF EXISTS items_ad;")
    op.execute("DELETE FROM items_fts;")
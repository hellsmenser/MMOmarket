"""create items_fts FTS5 table

Revision ID: 20240603_fts_items
Revises: 697a8a72f07f
Create Date: 2025-06-03 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20240603_fts_items'
down_revision: Union[str, None] = '697a8a72f07f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("CREATE VIRTUAL TABLE items_fts USING fts5(name);")

def downgrade() -> None:
    op.execute("DROP TABLE items_fts;")
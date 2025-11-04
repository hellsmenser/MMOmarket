"""extend daily_price_stats materialized view

Revision ID: b1f0e1d3c111
Revises: a785e1095a77
Create Date: 2025-11-04 19:20:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b1f0e1d3c111'
down_revision: Union[str, None] = '2d790a8c2c99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Recreate MV with extended columns (volume, max_price) and correct timestamp column name
    op.execute("DROP MATERIALIZED VIEW IF EXISTS daily_price_stats;")
    op.execute(
        """
        CREATE MATERIALIZED VIEW daily_price_stats AS
        SELECT
            item_id,
            currency,
            date_trunc('day', timestamp) AS day,
            COUNT(*)::int AS volume,
            AVG(price)::bigint AS avg_price,
            MIN(price)::bigint AS min_price,
            MAX(price)::bigint AS max_price
        FROM price_history
        GROUP BY item_id, currency, date_trunc('day', timestamp);
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_price_stats_key
        ON daily_price_stats (item_id, currency, day);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_daily_price_stats_day
        ON daily_price_stats (day);
        """
    )

def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS daily_price_stats;")


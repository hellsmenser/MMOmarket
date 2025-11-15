"""irq MV

Revision ID: e53fbac2bc1a
Revises: b1f0e1d3c111
Create Date: 2025-11-15 23:42:30.446637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e53fbac2bc1a'
down_revision: Union[str, None] = 'b1f0e1d3c111'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP INDEX IF EXISTS idx_daily_price_stats_key;")
    op.execute("DROP INDEX IF EXISTS idx_daily_price_stats_day;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS daily_price_stats;")

    op.execute(
        """
        CREATE MATERIALIZED VIEW daily_price_stats AS
        WITH raw AS (
            SELECT
                item_id,
                currency,
                price,
                date_trunc('day', timestamp) AS day
            FROM price_history
        ),
        
        stats AS (
            SELECT
                item_id,
                currency,
                day,
                (percentile_cont(0.25) WITHIN GROUP (ORDER BY price)) AS q1,
                (percentile_cont(0.75) WITHIN GROUP (ORDER BY price)) AS q3
            FROM raw
            GROUP BY item_id, currency, day
        ),
        
        joined AS (
            SELECT
                r.item_id,
                r.currency,
                r.day,
                r.price,
                s.q1,
                s.q3,
                s.q3 + 1.5 * (s.q3 - s.q1) AS iqr3
            FROM raw r
            JOIN stats s
                ON r.item_id = s.item_id
               AND r.currency = s.currency
               AND r.day = s.day
        ),
        
        filtered AS (
            SELECT *
            FROM joined
            WHERE price <= iqr3
        )
        
        SELECT
            item_id,
            currency,
            day,
            COUNT(*)::int AS volume,
            AVG(price)::bigint AS avg_price,
            MIN(price)::bigint AS min_price,
            MAX(price)::bigint AS max_price
        FROM filtered
        GROUP BY item_id, currency, day;
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX idx_daily_price_stats_key
        ON daily_price_stats (item_id, currency, day);
        """
    )
    op.execute(
        """
        CREATE INDEX idx_daily_price_stats_day
        ON daily_price_stats (day);
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
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

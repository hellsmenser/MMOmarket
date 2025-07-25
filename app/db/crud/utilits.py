from sqlalchemy import over, func, case, select


def get_quartiled_query(base_query, partition_by=None, order_by=None, label="quartile"):
    if partition_by is None:
        partition_by = []
    if order_by is None:
        raise ValueError("order_by должен быть указан")
    return base_query.add_columns(
        over(func.ntile(4), partition_by=partition_by, order_by=order_by).label(label)
    )

def get_iqr_query(quartiled, q_label="quartile", price_col="price"):
    return select(
        func.min(case((getattr(quartiled.c, q_label) == 1, getattr(quartiled.c, price_col)))).label("q1"),
        func.max(case((getattr(quartiled.c, q_label) == 3, getattr(quartiled.c, price_col)))).label("q3")
    )
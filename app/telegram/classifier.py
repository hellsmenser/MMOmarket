import logging
from collections import deque
from typing import Optional

from app.db.schemas.price import PriceCreate


def classify_from_history(
        price: PriceCreate,
        buffer: dict[int, deque[int]],
        tolerance: float = 0.35
) -> Optional[str]:
    if not buffer:
        return None

    item = price.item
    if not item or not item.modifications:
        return None

    try:
        levels = sorted([int(m) for m in item.modifications if str(m).strip().isdigit()])
    except ValueError:
        return None

    if len(levels) <= 1:
        return None

    price_value = price.price
    bands = {}

    for level in levels:
        vals = list(buffer.get(level, []))
        if not vals:
            continue
        center = sum(vals) / len(vals)
        delta = center * tolerance
        bands[level] = (center - delta, center + delta)

    if not bands:
        return None

    matches = [level for level, (low, high) in bands.items() if low <= price_value <= high]
    if len(matches) == 1:
        return str(matches[0])
    elif len(matches) > 1:
        return f"{min(matches)}-{max(matches)}"

    sorted_levels = sorted(bands.keys())
    for i in range(len(sorted_levels) - 1):
        _, high = bands[sorted_levels[i]]
        low, _ = bands[sorted_levels[i + 1]]
        if high < price_value < low:
            return f"{sorted_levels[i]}-{sorted_levels[i + 1]}"

    min_level = min(bands.keys())
    max_level = max(bands.keys())
    min_band = min(b[0] for b in bands.values())
    max_band = max(b[1] for b in bands.values())

    if price.source == "private_trade" and item.category.name == "Доспехи":
        if price_value < min_band or price_value > max_band:
            return "Сет"

    if price_value < min_band:
        return str(min_level)
    if price_value > max_band:
        return str(max_level)

    return None

from typing import Optional

def classify_from_history(
    price,
    buffer: list[tuple[int, int]],
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

    per_level_prices = {level: [] for level in levels}
    for mod, val in buffer:
        if mod in per_level_prices:
            per_level_prices[mod].append(val)

    for level, vals in per_level_prices.items():
        if not vals:
            continue
        else:
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

    if price_value < min(b[0] for b in bands.values()):
        return f"<{min(bands.keys())}"
    if price_value > max(b[1] for b in bands.values()):
        return f">{max(bands.keys())}"

    return None
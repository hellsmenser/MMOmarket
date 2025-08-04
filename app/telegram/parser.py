import re
from datetime import datetime

def parse_price_message(text: str) -> dict | None:
    # Determine trade type
    if "Всемирной Торговли" in text:
        currency = "coin"
        source = "world_trade"
    elif "Комиссионную Торговлю" in text:
        currency = "adena"
        source = "auction_house"
    elif "личной торговой лавке" in text:
        currency = "adena"
        source = "private_store"
    else:
        currency = "unknown"
        source = "unknown"

    # Item name
    name_match = re.search(r'Предмет\s+"(.+?)"', text)
    if not name_match:
        return None
    name = name_match.group(1).strip()

    # Price
    price_match = re.search(r'Цена:\s*([\d\s]+)', text)
    if not price_match:
        return None
    price = int(price_match.group(1).replace(" ", ""))

    return {
        "item_name": name,
        "enchant_level": None,
        "price": price,
        "currency": currency,
        "source": source
    }

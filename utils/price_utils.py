import re
from typing import Dict, Optional, List


def parse_price_isk(value) -> Optional[int]:
    """Parse a price-like value into integer ISK.

    Accepts values like:
    - "2.144 kr"
    - "2144"
    - "9592 kr kr"
    - text that contains "... 5.899 kr ..."
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        if value <= 0:
            return None
        return int(round(float(value)))

    text = str(value).strip()
    if not text:
        return None

    # Prefer number groups that are explicitly tied to "kr"
    currency_matches = re.findall(r"(\d[\d\.,\s]*)\s*kr", text, flags=re.IGNORECASE)
    if currency_matches:
        text = currency_matches[0]

    digits = re.sub(r"\D", "", text)
    if not digits:
        return None

    amount = int(digits)
    if amount <= 0:
        return None

    return amount


def format_price_isk(value) -> Optional[str]:
    amount = parse_price_isk(value)
    if amount is None:
        return None
    return f"{amount} kr"


def is_valid_set_number(value: str) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(re.fullmatch(r"\d{5,6}", text))


def extract_set_number(text: str) -> Optional[str]:
    if not text:
        return None
    text_value = str(text)
    match = re.search(r"LEGO\s*-?\s*(\d{5,6})", text_value, flags=re.IGNORECASE)
    if not match:
        match = re.search(r"\b(\d{6}|\d{5})\b", text_value)
    if not match:
        return None
    set_number = match.group(1)
    return set_number if is_valid_set_number(set_number) else None


def extract_parts_count(text: str) -> Optional[int]:
    if not text:
        return None
    match = re.search(r"\b(\d{1,5})\s*(?:Partar|parts|pieces)\b", str(text), flags=re.IGNORECASE)
    if not match:
        return None
    parts = int(match.group(1))
    return parts if parts > 0 else None


def enrich_with_lego_data(product: Dict, lego_data: Dict[str, Dict], title_fallback: Optional[str] = None) -> Dict:
    set_number = product.get('lego_set_number')
    if is_valid_set_number(set_number) and set_number in lego_data:
        product.update(lego_data[set_number])
        return product

    text_for_parts = title_fallback or product.get('name') or ''
    parts = extract_parts_count(text_for_parts)
    if parts:
        product['num_parts'] = str(parts)
    else:
        product.setdefault('num_parts', '-1')
    return product


def dedupe_products(products: List[Dict], key_fields: List[str]) -> List[Dict]:
    seen = set()
    deduped = []
    for product in products:
        key = tuple(str(product.get(field) or '').strip() for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(product)
    return deduped
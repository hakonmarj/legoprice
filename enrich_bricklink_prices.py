import json
import os
import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Optional, Tuple
from utils.exchange_rate_utils import fetch_usd_to_isk

try:
    import requests
except Exception:
    requests = None

try:
    from requests_oauthlib import OAuth1
except Exception:
    OAuth1 = None


BRICKLINK_BASE = "https://api.bricklink.com/api/store/v1"


def load_dotenv_file(path: Path):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def to_bricklink_item_no(set_number: str) -> str:
    value = (set_number or "").strip()
    if not value:
        return value
    if "-" in value:
        return value
    return f"{value}-1"


def load_products(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_products(path: Path, products):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(products, handle, ensure_ascii=False, indent=2)


def fetch_bricklink_price_guide(set_number: str, auth) -> Optional[dict]:
    item_no = to_bricklink_item_no(set_number)
    endpoint = f"{BRICKLINK_BASE}/items/SET/{item_no}/price"
    params = {
        "guide_type": "sold",
        "new_or_used": "N",
        "currency_code": "USD",
        "vat": "N",
    }
    response = requests.get(endpoint, auth=auth, params=params, timeout=20)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data") or {}
    return {
        "bricklink_6m_avg_price_new_usd": data.get("avg_price"),
        "bricklink_6m_qty_avg_price_new_usd": data.get("qty_avg_price"),
        "bricklink_6m_sales_count_new": data.get("unit_quantity"),
        "bricklink_6m_items_sold_new": data.get("total_quantity"),
        "bricklink_6m_min_price_new_usd": data.get("min_price"),
        "bricklink_6m_max_price_new_usd": data.get("max_price"),
    }


def fetch_bricklink_item_metadata(set_number: str, auth) -> Optional[dict]:
    item_no = to_bricklink_item_no(set_number)
    endpoint = f"{BRICKLINK_BASE}/items/SET/{item_no}"
    response = requests.get(endpoint, auth=auth, timeout=20)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data") or {}
    return {
        "bricklink_name": data.get("name"),
        "bricklink_image_url": data.get("image_url"),
        "bricklink_thumbnail_url": data.get("thumbnail_url"),
        "bricklink_category_id": data.get("category_id"),
    }


def fetch_bricklink_categories(auth) -> Dict[str, str]:
    endpoint = f"{BRICKLINK_BASE}/categories"
    response = requests.get(endpoint, auth=auth, timeout=25)
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data") or []

    category_map: Dict[str, str] = {}
    for item in data:
        category_id = str(item.get("category_id") or "").strip()
        category_name = (item.get("category_name") or "").strip()
        if category_id and category_name:
            category_map[category_id] = category_name
    return category_map


def fetch_bricklink_for_set(set_number: str, auth) -> Tuple[str, Optional[dict], Optional[str]]:
    try:
        guide = fetch_bricklink_price_guide(set_number, auth)
        metadata = fetch_bricklink_item_metadata(set_number, auth)
    except Exception as exc:
        return "failed", None, f"{type(exc).__name__}: {exc}"

    if not guide:
        return "missing", None, None

    payload = dict(guide)
    if metadata:
        payload.update(metadata)
    return "enriched", payload, None


def preflight_check(auth) -> Tuple[bool, str]:
    endpoint = f"{BRICKLINK_BASE}/items/SET/75192-1"
    try:
        response = requests.get(endpoint, auth=auth, timeout=20)
    except Exception as exc:
        return False, f"Network/SSL error during BrickLink preflight: {type(exc).__name__}: {exc}"

    if response.status_code in (200, 404):
        return True, "BrickLink auth/network preflight OK"

    body_preview = response.text[:300].replace("\n", " ")
    return False, f"BrickLink preflight failed: HTTP {response.status_code} - {body_preview}"


def clear_bricklink_fields(product: dict):
    fields = [
        "bricklink_6m_avg_price_new_usd",
        "bricklink_6m_qty_avg_price_new_usd",
        "bricklink_6m_sales_count_new",
        "bricklink_6m_items_sold_new",
        "bricklink_6m_min_price_new_usd",
        "bricklink_6m_max_price_new_usd",
        "bricklink_name",
        "bricklink_image_url",
        "bricklink_thumbnail_url",
        "bricklink_category_id",
        "bricklink_6m_avg_price_new_isk",
        "lowest_price_vs_bricklink_avg_ratio",
    ]
    for field in fields:
        product[field] = None
    product["display_image_url"] = product.get("img_url")


def parse_args():
    parser = argparse.ArgumentParser(description="Enrich aggregated LEGO products with BrickLink sold/new data.")
    parser.add_argument(
        "path",
        nargs="?",
        default="data/aggregated_products.json",
        help="Path to aggregated products JSON (default: data/aggregated_products.json)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=6,
        help="Number of concurrent BrickLink requests by set (default: 6)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if requests is None or OAuth1 is None:
        print("⚠️ Missing dependencies. Install with: pip install requests requests-oauthlib")
        return 1

    load_dotenv_file(Path(".env"))

    consumer_key = os.getenv("BRICKLINK_CONSUMER_KEY")
    consumer_secret = os.getenv("BRICKLINK_CONSUMER_SECRET")
    token = os.getenv("BRICKLINK_TOKEN") or os.getenv("BRICKLINK_TOKEN_VALUE")
    token_secret = os.getenv("BRICKLINK_TOKEN_SECRET")

    if not all([consumer_key, consumer_secret, token, token_secret]):
        print("⚠️ BrickLink credentials not set. Cannot run BrickLink enrichment.")
        print("Required env vars: BRICKLINK_CONSUMER_KEY, BRICKLINK_CONSUMER_SECRET, BRICKLINK_TOKEN (or BRICKLINK_TOKEN_VALUE), BRICKLINK_TOKEN_SECRET")
        print("Tip: put them in a local .env file in this project root.")
        return 1

    output_path = Path(args.path)
    products = load_products(output_path)

    auth = OAuth1(consumer_key, consumer_secret, token, token_secret, signature_type="auth_header")

    ok, message = preflight_check(auth)
    print(message)
    if not ok:
        return 1

    usd_to_isk = fetch_usd_to_isk()
    if usd_to_isk:
        print(f"Using live USD→ISK exchange rate: {usd_to_isk:.4f}")
    else:
        print("⚠️ Could not fetch live USD→ISK exchange rate. Ratio fields will be unavailable.")

    try:
        category_map = fetch_bricklink_categories(auth)
        print(f"Loaded {len(category_map)} BrickLink categories.")
    except Exception as exc:
        print(f"⚠️ Failed to load BrickLink categories: {type(exc).__name__}: {exc}")
        category_map = {}

    set_to_indexes: Dict[str, list] = {}
    for index, product in enumerate(products):
        set_number = str(product.get("lego_set_number") or "").strip()
        if not set_number:
            clear_bricklink_fields(product)
            continue
        set_to_indexes.setdefault(set_number, []).append(index)

    set_numbers = list(set_to_indexes.keys())
    total_sets = len(set_numbers)
    if total_sets == 0:
        save_products(output_path, products)
        print("⚠️ No valid lego_set_number values found.")
        return 0

    workers = max(1, min(args.workers, 16))
    print(f"Starting BrickLink bulk enrichment for {total_sets} unique set numbers with {workers} workers...")

    results_by_set: Dict[str, Tuple[str, Optional[dict], Optional[str]]] = {}
    processed_sets = 0
    enriched_sets = 0
    missing_sets = 0
    failed_sets = 0
    error_samples = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(fetch_bricklink_for_set, set_number, auth): set_number for set_number in set_numbers}
        for future in as_completed(future_map):
            set_number = future_map[future]
            status, payload, error = future.result()
            results_by_set[set_number] = (status, payload, error)

            processed_sets += 1
            if status == "enriched":
                enriched_sets += 1
            elif status == "missing":
                missing_sets += 1
            else:
                failed_sets += 1
                if error and len(error_samples) < 5:
                    error_samples.append(f"{set_number}: {error}")

            if processed_sets % 25 == 0 or processed_sets == total_sets:
                print(
                    f"Processed {processed_sets}/{total_sets} unique sets "
                    f"(enriched: {enriched_sets}, missing: {missing_sets}, failed: {failed_sets})"
                )

            time.sleep(0.01)

    for set_number, indexes in set_to_indexes.items():
        status, payload, _ = results_by_set.get(set_number, ("failed", None, "missing result"))
        for idx in indexes:
            product = products[idx]
            if status == "enriched" and payload:
                product.update(payload)
                category_id = str(product.get("bricklink_category_id") or "").strip()
                category_name = category_map.get(category_id)
                current_theme = str(product.get("theme") or "").strip()
                if category_name and (not current_theme or current_theme.lower().startswith("theme ")):
                    product["theme"] = category_name

                avg_usd = product.get("bricklink_6m_avg_price_new_usd")
                lowest_isk = product.get("lowest_price_isk")
                try:
                    avg_usd_num = float(avg_usd)
                    lowest_isk_num = float(lowest_isk)
                except (TypeError, ValueError):
                    avg_usd_num = None
                    lowest_isk_num = None

                if usd_to_isk and avg_usd_num and avg_usd_num > 0:
                    avg_isk = avg_usd_num * usd_to_isk
                    product["bricklink_6m_avg_price_new_isk"] = avg_isk
                    if lowest_isk_num and lowest_isk_num > 0:
                        product["lowest_price_vs_bricklink_avg_ratio"] = lowest_isk_num / avg_isk
                    else:
                        product["lowest_price_vs_bricklink_avg_ratio"] = None
                else:
                    product["bricklink_6m_avg_price_new_isk"] = None
                    product["lowest_price_vs_bricklink_avg_ratio"] = None

                product["display_image_url"] = product.get("bricklink_image_url") or product.get("img_url")
            else:
                clear_bricklink_fields(product)

    save_products(output_path, products)

    if error_samples:
        print("Sample BrickLink errors:")
        for sample in error_samples:
            print(f" - {sample}")

    print(f"✅ BrickLink enrichment complete: {output_path} updated")
    print(f"Summary: unique sets={total_sets}, enriched={enriched_sets}, missing={missing_sets}, failed={failed_sets}")

    if enriched_sets == 0 and failed_sets > 0:
        print("⚠️ No sets enriched. Check credentials and BrickLink API access for this token pair.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import requests
except Exception:
    requests = None


def parse_isk(value):
    if value is None:
        return None
    text = str(value)
    digits = re.sub(r"\D", "", text)
    return int(digits) if digits else None


def to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize(item):
    return {
        "legoSetNumber": str(item.get("lego_set_number") or "").strip(),
        "name": item.get("name"),
        "theme": item.get("theme"),
        "numParts": to_int(item.get("num_parts")),
        "displayImageUrl": item.get("display_image_url"),
        "bricklinkImageUrl": item.get("bricklink_image_url"),
        "bricklinkThumbnailUrl": item.get("bricklink_thumbnail_url"),
        "bricklinkName": item.get("bricklink_name"),
        "bricklinkCategoryId": to_int(item.get("bricklink_category_id")),
        "coolshopUrl": item.get("coolshop_url"),
        "kubbabudinUrl": item.get("kubbabudin_url"),
        "booztUrl": item.get("boozt_url"),
        "hagkaupUrl": item.get("hagkaup_url"),
        "kidsworldUrl": item.get("kidsworld_url"),
        "elkoUrl": item.get("elko_url"),
        "lowestPriceIsk": parse_isk(item.get("lowest_price") or item.get("lowest_price_isk")),
        "lowestPriceStore": item.get("lowest_price_store"),
        "coolshopPriceIsk": parse_isk(item.get("coolshop_price")),
        "kubbabudinPriceIsk": parse_isk(item.get("kubbabudin_price")),
        "booztPriceIsk": parse_isk(item.get("boozt_price")),
        "hagkaupPriceIsk": parse_isk(item.get("hagkaup_price")),
        "kidsworldPriceIsk": parse_isk(item.get("kidsworld_price")),
        "elkoPriceIsk": parse_isk(item.get("elko_price")),
        "piecesPerKr": to_float(item.get("pieces_per_kr")),
        "bricklink6mAvgPriceNewUsd": to_float(item.get("bricklink_6m_avg_price_new_usd")),
        "bricklink6mAvgPriceNewIsk": to_float(item.get("bricklink_6m_avg_price_new_isk")),
        "lowestPriceVsBricklinkAvgRatio": to_float(item.get("lowest_price_vs_bricklink_avg_ratio")),
        "bricklink6mSalesCountNew": to_int(item.get("bricklink_6m_sales_count_new")),
    }


def main():
    parser = argparse.ArgumentParser(description="Push aggregated_products.json into backend API")
    parser.add_argument("path", nargs="?", default="data/aggregated_products.json")
    parser.add_argument(
        "--api-base-url",
        default=os.getenv("BACKEND_API_URL", "http://localhost:8080"),
        help="Backend API base URL (default: BACKEND_API_URL or http://localhost:8080)",
    )
    args = parser.parse_args()

    if requests is None:
        print("⚠️ requests is not installed")
        return 1

    path = Path(args.path)
    if not path.exists():
        print(f"⚠️ Missing file: {path}")
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    payload = {
        "products": [normalize(item) for item in data if str(item.get("lego_set_number") or "").strip()]
    }

    endpoint = args.api_base_url.rstrip("/") + "/api/ingest/products"
    response = requests.post(endpoint, json=payload, timeout=120)
    if response.status_code >= 400:
        print(f"⚠️ Ingest API failed: HTTP {response.status_code} {response.text[:500]}")
        return 1

    print(f"✅ Pushed {len(payload['products'])} products to API: {endpoint}")
    print(response.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
ingest.py – read aggregated_products.json into the Postgres database.

Usage (standalone):
    python -m backend.ingest

Called automatically by run_all.py after aggregation if DATABASE_URL is set.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, date
from pathlib import Path


def _parse_isk(value) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    digits = re.sub(r"\D", "", text)
    return int(digits) if digits else None


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def run(json_path: str = "data/aggregated_products.json") -> bool:
    try:
        from backend.database import SessionLocal, init_db
        from backend.models import Product, PriceSnapshot
    except Exception as exc:
        print(f"⚠️  Could not import backend modules: {exc}")
        return False

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        print("⚠️  DATABASE_URL not set – skipping database ingest.")
        return False

    path = Path(json_path)
    if not path.exists():
        print(f"⚠️  {json_path} not found – skipping ingest.")
        return False

    try:
        products_json = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"⚠️  Could not read {json_path}: {exc}")
        return False

    try:
        init_db()
    except Exception as exc:
        print(f"⚠️  DB init failed: {exc}")
        return False

    db = SessionLocal()
    today = date.today()
    ingested = 0
    skipped = 0

    try:
        for item in products_json:
            set_num = str(item.get("lego_set_number") or "").strip()
            if not set_num:
                continue

            # Upsert product metadata
            product = db.get(Product, set_num)
            if product is None:
                product = Product(lego_set_number=set_num)
                db.add(product)

            product.name = item.get("name") or product.name
            product.theme = item.get("theme") or product.theme
            product.num_parts = _to_int(item.get("num_parts")) or product.num_parts
            product.display_image_url = item.get("display_image_url") or product.display_image_url
            product.bricklink_image_url = item.get("bricklink_image_url") or product.bricklink_image_url
            product.bricklink_thumbnail_url = (
                item.get("bricklink_thumbnail_url") or product.bricklink_thumbnail_url
            )
            product.bricklink_name = item.get("bricklink_name") or product.bricklink_name
            product.bricklink_category_id = (
                _to_int(item.get("bricklink_category_id")) or product.bricklink_category_id
            )
            product.updated_at = datetime.utcnow()

            # Store URLs (update whenever available)
            for store in ("coolshop", "kubbabudin", "boozt", "hagkaup", "kidsworld", "elko"):
                url = item.get(f"{store}_url")
                if url:
                    setattr(product, f"{store}_url", url)

            # Skip if we already have a snapshot for today
            existing = (
                db.query(PriceSnapshot)
                .filter(
                    PriceSnapshot.lego_set_number == set_num,
                    PriceSnapshot.captured_at >= datetime.combine(today, datetime.min.time()),
                )
                .first()
            )
            if existing:
                skipped += 1
                continue

            snapshot = PriceSnapshot(
                lego_set_number=set_num,
                captured_at=datetime.utcnow(),
                lowest_price_isk=_parse_isk(item.get("lowest_price")),
                lowest_price_store=item.get("lowest_price_store"),
                coolshop_price_isk=_parse_isk(item.get("coolshop_price")),
                kubbabudin_price_isk=_parse_isk(item.get("kubbabudin_price")),
                boozt_price_isk=_parse_isk(item.get("boozt_price")),
                hagkaup_price_isk=_parse_isk(item.get("hagkaup_price")),
                kidsworld_price_isk=_parse_isk(item.get("kidsworld_price")),
                elko_price_isk=_parse_isk(item.get("elko_price")),
                pieces_per_kr=_to_float(item.get("pieces_per_kr")),
                bricklink_6m_avg_price_new_usd=_to_float(item.get("bricklink_6m_avg_price_new_usd")),
                bricklink_6m_avg_price_new_isk=_to_float(item.get("bricklink_6m_avg_price_new_isk")),
                lowest_price_vs_bricklink_avg_ratio=_to_float(
                    item.get("lowest_price_vs_bricklink_avg_ratio")
                ),
                bricklink_6m_sales_count_new=_to_int(item.get("bricklink_6m_sales_count_new")),
            )
            db.add(snapshot)
            ingested += 1

        db.commit()
        print(f"✅ Ingest complete: {ingested} new snapshots, {skipped} already had today's data.")
        return True

    except Exception as exc:
        db.rollback()
        print(f"⚠️  Ingest failed: {exc}")
        return False

    finally:
        db.close()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/aggregated_products.json"
    ok = run(path)
    sys.exit(0 if ok else 1)

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import PriceHistoryEntry, ProductSummary

router = APIRouter(prefix="/api", tags=["products"])

_STORE_KEYS = [
    "coolshop",
    "kubbabudin",
    "boozt",
    "hagkaup",
    "kidsworld",
    "elko",
]


@router.get("/products", response_model=List[ProductSummary])
def list_products(db: Session = Depends(get_db)):
    """
    Return all products with their most recent per-store prices plus a
    6-month historical low comparison.
    """
    six_months_ago = datetime.utcnow() - timedelta(days=180)

    # ── Latest snapshot per product (DISTINCT ON is efficient on Postgres) ──
    latest_rows = db.execute(
        text(
            """
            SELECT DISTINCT ON (ps.lego_set_number)
                p.lego_set_number,
                p.name,
                p.theme,
                p.num_parts,
                p.display_image_url,
                p.bricklink_image_url,
                p.bricklink_thumbnail_url,
                p.bricklink_name,
                p.coolshop_url,
                p.kubbabudin_url,
                p.boozt_url,
                p.hagkaup_url,
                p.kidsworld_url,
                p.elko_url,
                ps.captured_at,
                ps.lowest_price_isk,
                ps.lowest_price_store,
                ps.coolshop_price_isk,
                ps.kubbabudin_price_isk,
                ps.boozt_price_isk,
                ps.hagkaup_price_isk,
                ps.kidsworld_price_isk,
                ps.elko_price_isk,
                ps.pieces_per_kr,
                ps.bricklink_6m_avg_price_new_usd,
                ps.bricklink_6m_avg_price_new_isk,
                ps.lowest_price_vs_bricklink_avg_ratio,
                ps.bricklink_6m_sales_count_new
            FROM products p
            JOIN price_snapshots ps
              ON ps.lego_set_number = p.lego_set_number
            ORDER BY ps.lego_set_number, ps.captured_at DESC
            """
        )
    ).mappings().all()

    # ── 6-month low (store that had the minimum price) per product ──
    low_rows = db.execute(
        text(
            """
            SELECT DISTINCT ON (lego_set_number)
                lego_set_number,
                lowest_price_isk  AS six_month_low_isk,
                lowest_price_store AS six_month_low_store
            FROM price_snapshots
            WHERE captured_at >= :cutoff
              AND lowest_price_isk IS NOT NULL
            ORDER BY lego_set_number, lowest_price_isk ASC
            """
        ),
        {"cutoff": six_months_ago},
    ).mappings().all()

    low_by_set = {r["lego_set_number"]: r for r in low_rows}

    results: List[ProductSummary] = []
    for row in latest_rows:
        six_m = low_by_set.get(row["lego_set_number"])
        six_month_low_isk = six_m["six_month_low_isk"] if six_m else None
        six_month_low_store = six_m["six_month_low_store"] if six_m else None

        diff_pct: float | None = None
        if six_month_low_isk and row["lowest_price_isk"]:
            diff_pct = (row["lowest_price_isk"] - six_month_low_isk) / six_month_low_isk * 100

        results.append(
            ProductSummary(
                lego_set_number=row["lego_set_number"],
                name=row["name"],
                theme=row["theme"],
                num_parts=row["num_parts"],
                display_image_url=row["display_image_url"],
                bricklink_image_url=row["bricklink_image_url"],
                bricklink_thumbnail_url=row["bricklink_thumbnail_url"],
                bricklink_name=row["bricklink_name"],
                coolshop_url=row["coolshop_url"],
                kubbabudin_url=row["kubbabudin_url"],
                boozt_url=row["boozt_url"],
                hagkaup_url=row["hagkaup_url"],
                kidsworld_url=row["kidsworld_url"],
                elko_url=row["elko_url"],
                lowest_price_isk=row["lowest_price_isk"],
                lowest_price_store=row["lowest_price_store"],
                coolshop_price_isk=row["coolshop_price_isk"],
                kubbabudin_price_isk=row["kubbabudin_price_isk"],
                boozt_price_isk=row["boozt_price_isk"],
                hagkaup_price_isk=row["hagkaup_price_isk"],
                kidsworld_price_isk=row["kidsworld_price_isk"],
                elko_price_isk=row["elko_price_isk"],
                pieces_per_kr=row["pieces_per_kr"],
                bricklink_6m_avg_price_new_usd=row["bricklink_6m_avg_price_new_usd"],
                bricklink_6m_avg_price_new_isk=row["bricklink_6m_avg_price_new_isk"],
                lowest_price_vs_bricklink_avg_ratio=row["lowest_price_vs_bricklink_avg_ratio"],
                bricklink_6m_sales_count_new=row["bricklink_6m_sales_count_new"],
                six_month_low_isk=six_month_low_isk,
                six_month_low_store=six_month_low_store,
                price_diff_from_six_month_low_pct=diff_pct,
            )
        )

    return results


@router.get("/products/{set_number}/history", response_model=List[PriceHistoryEntry])
def get_price_history(
    set_number: str,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Return per-store price snapshots for the last `days` days (default 30)."""
    if days < 1 or days > 365:
        raise HTTPException(status_code=422, detail="days must be between 1 and 365")

    cutoff = datetime.utcnow() - timedelta(days=days)

    rows = db.execute(
        text(
            """
            SELECT
                captured_at,
                lowest_price_isk,
                lowest_price_store,
                coolshop_price_isk,
                kubbabudin_price_isk,
                boozt_price_isk,
                hagkaup_price_isk,
                kidsworld_price_isk,
                elko_price_isk
            FROM price_snapshots
            WHERE lego_set_number = :set_number
              AND captured_at >= :cutoff
            ORDER BY captured_at ASC
            """
        ),
        {"set_number": set_number, "cutoff": cutoff},
    ).mappings().all()

    return [PriceHistoryEntry(**dict(r)) for r in rows]

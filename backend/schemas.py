from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


def _to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class PriceHistoryEntry(BaseModel):
    captured_at: datetime
    lowest_price_isk: Optional[int] = None
    lowest_price_store: Optional[str] = None
    coolshop_price_isk: Optional[int] = None
    kubbabudin_price_isk: Optional[int] = None
    boozt_price_isk: Optional[int] = None
    hagkaup_price_isk: Optional[int] = None
    kidsworld_price_isk: Optional[int] = None
    elko_price_isk: Optional[int] = None

    model_config = {"from_attributes": True, "alias_generator": _to_camel, "populate_by_name": True}


class ProductSummary(BaseModel):
    lego_set_number: str
    name: Optional[str] = None
    theme: Optional[str] = None
    num_parts: Optional[int] = None
    display_image_url: Optional[str] = None
    bricklink_image_url: Optional[str] = None
    bricklink_thumbnail_url: Optional[str] = None
    bricklink_name: Optional[str] = None

    # Current snapshot prices
    lowest_price_isk: Optional[int] = None
    lowest_price_store: Optional[str] = None
    coolshop_price_isk: Optional[int] = None
    kubbabudin_price_isk: Optional[int] = None
    boozt_price_isk: Optional[int] = None
    hagkaup_price_isk: Optional[int] = None
    kidsworld_price_isk: Optional[int] = None
    elko_price_isk: Optional[int] = None

    # Store product page URLs
    coolshop_url: Optional[str] = None
    kubbabudin_url: Optional[str] = None
    boozt_url: Optional[str] = None
    hagkaup_url: Optional[str] = None
    kidsworld_url: Optional[str] = None
    elko_url: Optional[str] = None

    # Value metrics
    pieces_per_kr: Optional[float] = None
    bricklink_6m_avg_price_new_usd: Optional[float] = None
    bricklink_6m_avg_price_new_isk: Optional[float] = None
    lowest_price_vs_bricklink_avg_ratio: Optional[float] = None
    bricklink_6m_sales_count_new: Optional[int] = None

    # 6-month historical comparison
    six_month_low_isk: Optional[int] = None
    six_month_low_store: Optional[str] = None
    price_diff_from_six_month_low_pct: Optional[float] = None

    model_config = {"from_attributes": True, "alias_generator": _to_camel, "populate_by_name": True}

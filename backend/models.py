from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Product(Base):
    __tablename__ = "products"

    lego_set_number = Column(String(20), primary_key=True)
    name = Column(Text)
    theme = Column(Text)
    num_parts = Column(Integer)
    display_image_url = Column(Text)
    bricklink_image_url = Column(Text)
    bricklink_thumbnail_url = Column(Text)
    bricklink_name = Column(Text)
    bricklink_category_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Per-store product page URLs (rarely change, stored on product level)
    coolshop_url = Column(Text)
    kubbabudin_url = Column(Text)
    boozt_url = Column(Text)
    hagkaup_url = Column(Text)
    kidsworld_url = Column(Text)
    elko_url = Column(Text)

    snapshots: list["PriceSnapshot"] = relationship(
        "PriceSnapshot",
        back_populates="product",
        order_by="PriceSnapshot.captured_at",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lego_set_number = Column(
        String(20),
        ForeignKey("products.lego_set_number", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Current lowest across all stores
    lowest_price_isk = Column(Integer)
    lowest_price_store = Column(String(50))

    # Per-store prices (ISK)
    coolshop_price_isk = Column(Integer)
    kubbabudin_price_isk = Column(Integer)
    boozt_price_isk = Column(Integer)
    hagkaup_price_isk = Column(Integer)
    kidsworld_price_isk = Column(Integer)
    elko_price_isk = Column(Integer)

    # Derived metrics
    pieces_per_kr = Column(Float)
    bricklink_6m_avg_price_new_usd = Column(Float)
    bricklink_6m_avg_price_new_isk = Column(Float)
    lowest_price_vs_bricklink_avg_ratio = Column(Float)
    bricklink_6m_sales_count_new = Column(Integer)

    product: "Product" = relationship("Product", back_populates="snapshots")

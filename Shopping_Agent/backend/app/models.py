"""SQLAlchemy ORM models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from .database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    store_url = Column(String(500), nullable=False)
    product_id = Column(String(100), nullable=True)
    title = Column(String(500), nullable=False)
    handle = Column(String(300), nullable=True)
    vendor = Column(String(200), nullable=True)
    product_type = Column(String(200), nullable=True)
    tags = Column(JSON, nullable=True)           # list of strings
    price_min = Column(Float, nullable=True)
    price_max = Column(Float, nullable=True)
    currency = Column(String(10), default="USD")
    image_url = Column(Text, nullable=True)
    product_url = Column(Text, nullable=True)
    available = Column(String(10), nullable=True)  # "true"/"false"/"unknown"
    description = Column(Text, nullable=True)
    variants = Column(JSON, nullable=True)        # raw variant list
    rank_score = Column(Float, nullable=True)
    crawled_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Product id={self.id} title={self.title!r}>"

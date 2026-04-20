"""CRUD helpers — thin wrappers around SQLAlchemy session."""
from typing import List, Optional
from sqlalchemy.orm import Session
from . import models


def upsert_products(db: Session, products: List[dict]) -> List[models.Product]:
    """Insert products; skip duplicates by (store_url, handle)."""
    saved: List[models.Product] = []
    for p in products:
        existing = (
            db.query(models.Product)
            .filter(
                models.Product.store_url == p.get("store_url"),
                models.Product.handle == p.get("handle"),
            )
            .first()
        )
        if existing:
            # refresh price / availability
            existing.price_min = p.get("price_min")
            existing.price_max = p.get("price_max")
            existing.available = p.get("available")
            existing.rank_score = p.get("rank_score")
            db.commit()
            db.refresh(existing)
            saved.append(existing)
        else:
            obj = models.Product(**p)
            db.add(obj)
            db.commit()
            db.refresh(obj)
            saved.append(obj)
    return saved


def get_products(
    db: Session,
    store_url: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[models.Product]:
    q = db.query(models.Product)
    if store_url:
        q = q.filter(models.Product.store_url == store_url)
    return q.order_by(models.Product.rank_score.desc().nullslast()).offset(skip).limit(limit).all()


def get_product_by_id(db: Session, product_id: int) -> Optional[models.Product]:
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def delete_products_by_store(db: Session, store_url: str) -> int:
    count = db.query(models.Product).filter(models.Product.store_url == store_url).delete()
    db.commit()
    return count

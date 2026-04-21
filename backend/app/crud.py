from sqlalchemy.orm import Session
from .models import Product


def upsert_products(db: Session, products: list[dict]) -> int:
    inserted = 0
    for item in products:
        existing = (
            db.query(Product)
            .filter(
                Product.source_url == item["source_url"],
                Product.handle == item["handle"],
            )
            .first()
        )

        if existing:
            existing.title = item["title"]
            existing.price = item["price"]
            existing.currency = item.get("currency", "USD")
            existing.image_url = item.get("image_url")
            existing.tags = ",".join(item.get("tags", []))
            existing.product_url = item["product_url"]
        else:
            db.add(
                Product(
                    vendor=item["vendor"],
                    title=item["title"],
                    handle=item["handle"],
                    product_url=item["product_url"],
                    image_url=item.get("image_url"),
                    price=item["price"],
                    currency=item.get("currency", "USD"),
                    tags=",".join(item.get("tags", [])),
                    source_url=item["source_url"],
                )
            )
            inserted += 1

    db.commit()
    return inserted


def list_products(db: Session, limit: int = 100) -> list[Product]:
    return db.query(Product).order_by(Product.created_at.desc()).limit(limit).all()

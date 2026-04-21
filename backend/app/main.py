import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .agents import ShoppingMainAgent
from .crud import list_products, upsert_products
from .database import Base, engine, get_db
from .schemas import ProductOut, SearchRequest, SearchResponse

load_dotenv()

app = FastAPI(title="AI Shopping Assistant", version="1.0.0")
Base.metadata.create_all(bind=engine)

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

main_agent = ShoppingMainAgent()

frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def index():
    index_file = frontend_dir / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_file)


@app.post("/api/search", response_model=SearchResponse)
def search_products(payload: SearchRequest, db: Session = Depends(get_db)):
    if payload.budget_min > payload.budget_max:
        raise HTTPException(status_code=400, detail="budget_min cannot exceed budget_max")

    host = (urlparse(str(payload.shopify_store_url)).hostname or "").lower()
    if host in {"shopify.com", "www.shopify.com"}:
        raise HTTPException(
            status_code=400,
            detail=(
                "Use a Shopify vendor storefront URL (example: https://allbirds.com or "
                "https://storename.myshopify.com), not shopify.com marketing pages."
            ),
        )

    crawled, ranked = main_agent.run(
        product_name=payload.product_name,
        occasion=payload.occasion,
        budget_min=payload.budget_min,
        budget_max=payload.budget_max,
        preferences=payload.preferences,
        shopify_store_url=str(payload.shopify_store_url),
    )

    if crawled:
        upsert_products(db, crawled)

    results = [
        ProductOut(
            title=item["title"],
            vendor=item["vendor"],
            price=item["price"],
            currency=item.get("currency", "USD"),
            product_url=item["product_url"],
            image_url=item.get("image_url"),
            tags=item.get("tags", []),
            score=item.get("score", 0.0),
        )
        for item in ranked
    ]

    return SearchResponse(
        query=payload.product_name,
        occasion=payload.occasion,
        budget_min=payload.budget_min,
        budget_max=payload.budget_max,
        total_crawled=len(crawled),
        total_matched=len(results),
        results=results,
    )


@app.get("/api/products", response_model=list[ProductOut])
def get_products(limit: int = 100, db: Session = Depends(get_db)):
    items = list_products(db, limit=min(max(limit, 1), 500))
    return [
        ProductOut(
            title=p.title,
            vendor=p.vendor,
            price=p.price,
            currency=p.currency,
            product_url=p.product_url,
            image_url=p.image_url,
            tags=[t.strip() for t in (p.tags or "").split(",") if t.strip()],
            score=0.0,
        )
        for p in items
    ]

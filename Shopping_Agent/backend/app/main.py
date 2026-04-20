"""FastAPI application entry-point."""
from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from .database import engine, get_db, Base
from .models import Product
from .schemas import SearchRequest, SearchResponse, ProductOut, HealthResponse
from .agents import shopping_agent
from .crud import get_products, get_product_by_id

# ── Initialise tables ──────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Shopping Assistant",
    description="Crawl Shopify stores, rank products, return best matches.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static frontend ────────────────────────────────────────────────────────
_PUBLIC = Path(__file__).resolve().parents[2] / "public"

if _PUBLIC.exists():
    app.mount("/static", StaticFiles(directory=str(_PUBLIC)), name="static")


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_ui():
    index = _PUBLIC / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return HTMLResponse("<h2>Frontend not found – open /docs to use the API.</h2>")


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"
    return HealthResponse(status="ok", database=db_status)


@app.post("/api/search", response_model=SearchResponse, tags=["Shopping"])
async def search(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Main endpoint — crawls the given Shopify store, ranks products by the
    user query, persists results to PostgreSQL, and returns the best matches.
    """
    try:
        result = await shopping_agent(request, db)
        return result
    except Exception as exc:
        logger.exception("Agent error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/products", response_model=List[ProductOut], tags=["Shopping"])
def list_products(
    store_url: Optional[str] = Query(None, description="Filter by store URL"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return cached products from the database."""
    return get_products(db, store_url=store_url, skip=skip, limit=limit)


@app.get("/api/products/{product_id}", response_model=ProductOut, tags=["Shopping"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = get_product_by_id(db, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p

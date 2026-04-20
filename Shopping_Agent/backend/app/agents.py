"""Shopping sub-agent: orchestrates crawl → rank → persist pipeline.

This module is the "brain" of the assistant. Keeping it separate makes it
easy to swap in an LLM later (OpenAI function-calling, LangChain, etc.).
"""
from __future__ import annotations
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from .crawler_adapter import run_crawl
from .ranking import rank_products
from .crud import upsert_products, get_products
from .schemas import SearchRequest

logger = logging.getLogger(__name__)


async def shopping_agent(
    request: SearchRequest,
    db: Session,
) -> dict:
    """
    Full pipeline:
      1. Crawl the Shopify store  (I/O-bound, runs in thread-pool)
      2. Rank all products against the user query
      3. Upsert into PostgreSQL
      4. Return top-N results

    Returns a dict shaped for :class:`~app.schemas.SearchResponse`.
    """
    store_url = request.shopify_store_url
    logger.info(
        "Agent started | store=%s query=%r", store_url, request.product_name
    )

    # ── 1. Crawl ───────────────────────────────────────────────────────────
    raw_products: List[dict] = await run_crawl(store_url)
    total_crawled = len(raw_products)
    logger.info("Crawled %d products from %s", total_crawled, store_url)

    if not raw_products:
        return {
            "query":          request.product_name,
            "store":          store_url,
            "total_crawled":  0,
            "total_matched":  0,
            "results":        [],
        }

    # ── 2. Rank ────────────────────────────────────────────────────────────
    ranked = rank_products(
        products    = raw_products,
        product_name= request.product_name,
        occasion    = request.occasion,
        budget_min  = request.budget_min,
        budget_max  = request.budget_max,
        preferences = request.preferences,
    )

    # ── 3. Persist (top results + any scoring > 0) ─────────────────────────
    to_save = [p for p in ranked if (p.get("rank_score") or 0) > 0]
    if not to_save:
        to_save = ranked          # save everything if nothing scored

    saved = upsert_products(db, to_save)
    logger.info("Persisted %d products to DB", len(saved))

    # ── 4. Return top-N ────────────────────────────────────────────────────
    limit = min(request.limit or 20, len(saved))
    top = sorted(saved, key=lambda p: p.rank_score or 0, reverse=True)[:limit]

    return {
        "query":         request.product_name,
        "store":         store_url,
        "total_crawled": total_crawled,
        "total_matched": len(saved),
        "results":       top,
    }

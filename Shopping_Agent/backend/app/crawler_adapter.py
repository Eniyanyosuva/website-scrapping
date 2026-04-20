"""Crawler adapter — thin bridge between the spider and FastAPI.

Runs the blocking HTTP crawl in a thread pool so it doesn't block the
asyncio event loop.
"""
from __future__ import annotations
import asyncio
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor

from .scraper.shopify_spider import crawl_shopify_store

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=4)


async def run_crawl(store_url: str) -> List[dict]:
    """Async wrapper: crawl the store in a background thread."""
    loop = asyncio.get_event_loop()
    logger.info("Starting async crawl for: %s", store_url)
    products = await loop.run_in_executor(
        _executor, crawl_shopify_store, store_url
    )
    return products

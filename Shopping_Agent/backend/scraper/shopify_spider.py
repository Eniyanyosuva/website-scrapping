"""Shopify spider — fetches /products.json pages and yields flat product dicts.

Shopify exposes a public REST endpoint on every storefront:
  GET  /products.json?limit=250&page=<N>

No API key required.  We paginate until we receive an empty page.
"""
from __future__ import annotations
import logging
from typing import Iterator, List
import requests

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ShoppingAgentBot/1.0; "
        "+https://github.com/shopping-agent)"
    ),
    "Accept": "application/json",
}
_PAGE_LIMIT = 250       # Shopify max per page
_MAX_PAGES  = 20        # safety cap ≈ 5 000 products


def _parse_variants(variants: list) -> tuple[float | None, float | None, str]:
    """Return (price_min, price_max, available) from a variant list."""
    prices = []
    available = "false"
    for v in variants:
        try:
            prices.append(float(v.get("price", 0)))
        except (TypeError, ValueError):
            pass
        if v.get("available"):
            available = "true"
    if not prices:
        return None, None, available
    return min(prices), max(prices), available


def crawl_shopify_store(store_url: str) -> List[dict]:
    """
    Crawl a Shopify store and return a list of normalised product dicts.

    Parameters
    ----------
    store_url : str
        Root URL of the Shopify store, e.g. ``https://allbirds.com``
    """
    store_url = store_url.rstrip("/")
    products: List[dict] = []

    for page in range(1, _MAX_PAGES + 1):
        url = f"{store_url}/products.json?limit={_PAGE_LIMIT}&page={page}"
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as exc:
            logger.warning("Request failed [page=%d]: %s", page, exc)
            break
        except ValueError as exc:
            logger.warning("JSON parse error [page=%d]: %s", page, exc)
            break

        page_products = data.get("products", [])
        if not page_products:
            logger.info("Empty page %d — stopping crawl.", page)
            break

        for raw in page_products:
            price_min, price_max, available = _parse_variants(
                raw.get("variants") or []
            )

            # Best image
            images = raw.get("images") or []
            image_url = images[0].get("src") if images else None

            # Strip HTML from body_html
            description = _strip_html(raw.get("body_html") or "")

            products.append(
                {
                    "store_url":    store_url,
                    "product_id":   str(raw.get("id", "")),
                    "title":        raw.get("title", "Unknown"),
                    "handle":       raw.get("handle"),
                    "vendor":       raw.get("vendor"),
                    "product_type": raw.get("product_type"),
                    "tags":         raw.get("tags") or [],
                    "price_min":    price_min,
                    "price_max":    price_max,
                    "currency":     "USD",
                    "image_url":    image_url,
                    "product_url":  f"{store_url}/products/{raw.get('handle')}",
                    "available":    available,
                    "description":  description[:1000] if description else None,
                    "variants":     raw.get("variants") or [],
                    "rank_score":   None,
                }
            )

        logger.info("Page %d: %d products so far.", page, len(products))

        # If we received fewer than the limit we're on the last page
        if len(page_products) < _PAGE_LIMIT:
            break

    logger.info("Crawl complete: %d total products from %s", len(products), store_url)
    return products


def _strip_html(html: str) -> str:
    """Very lightweight HTML tag remover (no external dep)."""
    import re
    clean = re.sub(r"<[^>]+>", " ", html)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean

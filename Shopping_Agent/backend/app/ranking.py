"""Heuristic ranking engine.

Score formula (all weights tunable here):
  - keyword match in title/tags/type  →  up to 40 pts
  - price within budget               →  up to 30 pts
  - occasion / preference match       →  up to 20 pts
  - availability bonus                →  10 pts
"""
from __future__ import annotations
import re
from typing import List, Optional


# ── Weights ────────────────────────────────────────────────────────────────
W_KEYWORD   = 40.0
W_PRICE     = 30.0
W_PREF      = 20.0
W_AVAILABLE = 10.0


def _tokenise(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _keyword_score(product: dict, keywords: List[str]) -> float:
    """Fraction of keywords found in title + tags + type, scaled to W_KEYWORD."""
    if not keywords:
        return W_KEYWORD * 0.5          # neutral if no query
    haystack = " ".join([
        product.get("title") or "",
        " ".join(product.get("tags") or []),
        product.get("product_type") or "",
        product.get("vendor") or "",
    ]).lower()
    tokens = _tokenise(haystack)
    matched = sum(1 for kw in keywords if kw in tokens)
    return W_KEYWORD * (matched / len(keywords))


def _price_score(
    product: dict,
    budget_min: Optional[float],
    budget_max: Optional[float],
) -> float:
    """Full score if price inside budget; partial if outside; 0 if way off."""
    price = product.get("price_min")
    if price is None:
        return W_PRICE * 0.3            # unknown price – small penalty

    if budget_min is None and budget_max is None:
        return W_PRICE * 0.5            # no budget given – neutral

    lo = budget_min or 0.0
    hi = budget_max or float("inf")

    if lo <= price <= hi:
        return W_PRICE                  # perfectly in budget
    if price < lo:
        ratio = price / lo if lo > 0 else 1
        return W_PRICE * max(0.0, ratio)
    # price > hi
    over = (price - hi) / hi if hi > 0 else 1
    return W_PRICE * max(0.0, 1 - over)


def _preference_score(product: dict, preferences: List[str]) -> float:
    """Match user free-text prefs against product text."""
    if not preferences:
        return W_PREF * 0.5
    haystack = " ".join([
        product.get("title") or "",
        product.get("description") or "",
        " ".join(product.get("tags") or []),
    ]).lower()
    pref_tokens = [t for p in preferences for t in _tokenise(p)]
    matched = sum(1 for t in pref_tokens if t in haystack)
    return W_PREF * (matched / len(pref_tokens)) if pref_tokens else W_PREF * 0.5


def _availability_score(product: dict) -> float:
    avail = str(product.get("available", "")).lower()
    if avail == "true":
        return W_AVAILABLE
    if avail == "false":
        return 0.0
    return W_AVAILABLE * 0.5


def rank_products(
    products: List[dict],
    product_name: str,
    occasion: Optional[str],
    budget_min: Optional[float],
    budget_max: Optional[float],
    preferences: Optional[List[str]],
) -> List[dict]:
    """Scores every product and returns sorted list (highest first)."""
    keywords = _tokenise(product_name or "")
    if occasion:
        keywords += _tokenise(occasion)

    prefs = preferences or []

    for p in products:
        score = (
            _keyword_score(p, keywords)
            + _price_score(p, budget_min, budget_max)
            + _preference_score(p, prefs)
            + _availability_score(p)
        )
        p["rank_score"] = round(score, 4)

    return sorted(products, key=lambda x: x["rank_score"], reverse=True)

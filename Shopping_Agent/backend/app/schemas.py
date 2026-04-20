"""Pydantic request / response schemas."""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, field_validator


# ── Request ────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    product_name: str
    occasion: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    preferences: Optional[List[str]] = []
    shopify_store_url: str          # e.g. "https://allbirds.com"
    limit: Optional[int] = 20

    @field_validator("shopify_store_url", mode="before")
    @classmethod
    def normalise_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if not v.startswith("http"):
            v = "https://" + v
        return v


# ── Response ───────────────────────────────────────────────────────────────

class ProductOut(BaseModel):
    id: int
    store_url: str
    title: str
    vendor: Optional[str]
    product_type: Optional[str]
    tags: Optional[List[str]]
    price_min: Optional[float]
    price_max: Optional[float]
    currency: Optional[str]
    image_url: Optional[str]
    product_url: Optional[str]
    available: Optional[str]
    description: Optional[str]
    rank_score: Optional[float]
    crawled_at: datetime

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    query: str
    store: str
    total_crawled: int
    total_matched: int
    results: List[ProductOut]


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str = "1.0.0"

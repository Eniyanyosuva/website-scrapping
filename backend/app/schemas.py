from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class SearchRequest(BaseModel):
    product_name: str = Field(..., min_length=2, max_length=120)
    occasion: str = Field(default="general", max_length=120)
    budget_min: float = Field(default=0, ge=0)
    budget_max: float = Field(..., gt=0)
    preferences: List[str] = Field(default_factory=list)
    shopify_store_url: HttpUrl


class ProductOut(BaseModel):
    title: str
    vendor: str
    price: float
    currency: str
    product_url: str
    image_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    score: float = 0.0


class SearchResponse(BaseModel):
    query: str
    occasion: str
    budget_min: float
    budget_max: float
    total_crawled: int
    total_matched: int
    results: List[ProductOut]

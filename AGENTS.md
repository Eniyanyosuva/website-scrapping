# AGENTS.md - Shopping Assistant

## Objective
Build an AI-powered shopping assistant that finds Shopify products based on:

- product name
- occasion
- budget range
- user preferences

## Agent Design

### Main Agent (`ShoppingMainAgent`)
- Accepts user query from API.
- Calls the sub-agent tool to crawl vendor products.
- Runs ranking on crawled products.
- Returns top matches to API layer.

Input fields:
- `product_name`
- `occasion`
- `budget_min`
- `budget_max`
- `preferences`
- `shopify_store_url`

### Sub-Agent (`CrawlerSubAgent`)
- Uses Scrapy tool adapter (`crawl_shopify_products`).
- Crawls Shopify store via `/products.json`.
- Extracts normalized product records:
  - title
  - vendor
  - handle
  - product_url
  - image_url
  - price
  - tags
  - source_url

### Tool Layer
- `crawler_adapter.py` runs Scrapy spider as subprocess.
- `shopify_spider.py` performs paginated extraction.
- `ranking.py` scores products by:
  - budget fit
  - product-title relevance
  - occasion/tag relevance
  - preference token overlap

## API Flow
1. Client sends `POST /api/search`.
2. Main agent triggers crawler sub-agent.
3. Products are stored/updated in PostgreSQL.
4. Ranked top results are returned to client.

## Key Files
- `backend/app/agents.py`
- `backend/app/crawler_adapter.py`
- `backend/scraper/shopify_spider.py`
- `backend/app/ranking.py`
- `backend/app/main.py`

## Run
From `backend/`:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

# AI Shopping Assistant (FastAPI + Scrapy + PostgreSQL)

An AI-powered shopping assistant that:

- Accepts a user query (`product`, `occasion`, `budget`, preferences)
- Uses a sub-agent tool to crawl Shopify vendor websites
- Extracts and stores product data in PostgreSQL
- Ranks and returns best matches
- Exposes API endpoints and a simple frontend UI

## Tech Stack

- Python 3.11+
- FastAPI
- Scrapy
- PostgreSQL
- SQLAlchemy

## Project Structure

```text
Shopping_Agent/
  backend/
    app/
      agents.py
      crawler_adapter.py
      crud.py
      database.py
      main.py
      models.py
      ranking.py
      schemas.py
    scraper/
      shopify_spider.py
    requirements.txt
  frontend/
    index.html
    styles.css
    app.js
  .env.example
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Create PostgreSQL database (example):

```sql
CREATE DATABASE shopping_agent;
```

4. Copy `.env.example` to `.env` and update credentials.

5. Run API (recommended from project root):

```bash
cd C:\Users\benju\Desktop\Shopping_Agent
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

6. Open UI:

`http://localhost:8000/`

## API

- `GET /health` - health check
- `POST /api/search` - crawl + extract + rank
- `GET /api/products` - list cached products in DB

### Example Search Request

```json
{
  "product_name": "running shoes",
  "occasion": "casual",
  "budget_min": 40,
  "budget_max": 120,
  "preferences": ["black", "lightweight"],
  "shopify_store_url": "https://allbirds.com"
}
```

## Notes

- The crawler uses Shopify's public `/products.json` endpoint.
- Ranking is heuristic and easy to tune in `backend/app/ranking.py`.
- This starter is intentionally modular so you can plug in LLM calls later.
"# Shopping-agent-" 

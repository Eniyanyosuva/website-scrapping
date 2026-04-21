import scrapy
from urllib.parse import urlparse


class ShopifyProductsSpider(scrapy.Spider):
    name = "shopify_products"

    custom_settings = {
        "LOG_ENABLED": False,
    }

    def __init__(self, store_url: str, query: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        parsed = urlparse(store_url)
        self.store_origin = f"{parsed.scheme}://{parsed.netloc}"
        self.query = query.lower().strip()
        self.next_page = 1

    def start_requests(self):
        url = f"{self.store_origin}/products.json?limit=250&page={self.next_page}"
        yield scrapy.Request(url=url, callback=self.parse_products)

    def parse_products(self, response):
        payload = response.json()
        products = payload.get("products", [])
        if not products:
            return

        for product in products:
            title = product.get("title", "")
            tags = [t.strip() for t in (product.get("tags", "") or "").split(",") if t.strip()]

            if self.query and self.query not in title.lower() and all(
                self.query not in t.lower() for t in tags
            ):
                continue

            variants = product.get("variants", [])
            if not variants:
                continue

            price_text = variants[0].get("price", "0")
            try:
                price = float(price_text)
            except ValueError:
                price = 0.0

            image_url = None
            image_block = product.get("image")
            if image_block and isinstance(image_block, dict):
                image_url = image_block.get("src")

            yield {
                "vendor": product.get("vendor") or urlparse(self.store_origin).netloc,
                "title": title,
                "handle": product.get("handle", ""),
                "product_url": f"{self.store_origin}/products/{product.get('handle', '')}",
                "image_url": image_url,
                "price": price,
                "currency": "USD",
                "tags": tags,
                "source_url": self.store_origin,
            }

        self.next_page += 1
        next_url = f"{self.store_origin}/products.json?limit=250&page={self.next_page}"
        yield scrapy.Request(url=next_url, callback=self.parse_products)

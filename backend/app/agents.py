from .crawler_adapter import crawl_shopify_products
from .ranking import rank_products


class CrawlerSubAgent:
    def crawl_vendor_site(self, store_url: str, product_query: str) -> list[dict]:
        return crawl_shopify_products(store_url=store_url, query=product_query)


class ShoppingMainAgent:
    def __init__(self):
        self.subagent = CrawlerSubAgent()

    def run(
        self,
        product_name: str,
        occasion: str,
        budget_min: float,
        budget_max: float,
        preferences: list[str],
        shopify_store_url: str,
    ) -> tuple[list[dict], list[dict]]:
        crawled = self.subagent.crawl_vendor_site(shopify_store_url, product_name)
        ranked = rank_products(
            crawled,
            product_name=product_name,
            occasion=occasion,
            preferences=preferences,
            budget_min=budget_min,
            budget_max=budget_max,
            top_k=10,
        )
        return crawled, ranked

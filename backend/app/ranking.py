def rank_products(
    products: list[dict],
    product_name: str,
    occasion: str,
    preferences: list[str],
    budget_min: float,
    budget_max: float,
    top_k: int = 10,
) -> list[dict]:
    product_tokens = set(product_name.lower().split())
    occasion_tokens = set(occasion.lower().split())
    pref_tokens = {token.lower() for token in preferences}

    ranked: list[dict] = []
    for p in products:
        title_tokens = set(str(p.get("title", "")).lower().split())
        tag_tokens = {t.lower() for t in p.get("tags", [])}
        price = float(p.get("price", 0))
        score = 0.0

        if budget_min <= price <= budget_max:
            score += 5.0
            middle = (budget_min + budget_max) / 2
            spread = max((budget_max - budget_min) / 2, 1)
            score += max(0.0, 3.0 - abs(price - middle) / spread)
        else:
            score -= 5.0

        score += 2.0 * len(product_tokens.intersection(title_tokens))
        score += 1.5 * len(occasion_tokens.intersection(title_tokens.union(tag_tokens)))
        score += 1.2 * len(pref_tokens.intersection(title_tokens.union(tag_tokens)))

        p["score"] = round(score, 3)
        ranked.append(p)

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:top_k]

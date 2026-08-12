import httpx
from typing import Any

DAMASCO_API = "https://damasco.vtexcommercestable.com.br/api/catalog_system/pub/products/search"
STORE_NAME = "Damasco"
STORE_KEY = "damasco"


async def search_products(query: str, max_results: int = 50) -> list[dict[str, Any]]:
    headers = {
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    products: list[dict] = []
    offset = 0
    tokens = [t for t in query.lower().split() if t]
    ft_term = tokens[0] if tokens else query
    async with httpx.AsyncClient(timeout=20.0) as client:
        while len(products) < max_results:
            params = {
                "ft": ft_term,
                "q": query,
                "_from": offset,
                "_to": offset + 49,
            }
            r = await client.get(DAMASCO_API, params=params, headers=headers)
            r.raise_for_status()
            batch: list[dict] = r.json()
            if not batch:
                break
            added = 0
            for item in batch:
                if _matches_query(item, tokens):
                    products.append(item)
                    added += 1
            if added == 0 and offset > 0:
                break
            offset += 50

    return [_parse_product(p) for p in products[:max_results]]


def _matches_query(item: dict, tokens: list[str]) -> bool:
    if not tokens:
        return True
    name = (item.get("productName", "")).lower()
    return all(t in name for t in tokens)


async def fetch_catalog(max_results: int = 2000) -> list[dict[str, Any]]:
    headers = {
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    products: list[dict] = []
    offset = 0
    async with httpx.AsyncClient(timeout=20.0) as client:
        while len(products) < max_results:
            params = {"_from": offset, "_to": offset + 49}
            r = await client.get(DAMASCO_API, params=params, headers=headers)
            r.raise_for_status()
            batch: list[dict] = r.json()
            if not batch:
                break
            products.extend(batch)
            offset += 50

    return [_parse_product(p) for p in products[:max_results]]


STORE_URL = "https://www.damascovzla.com"


def _parse_product(raw: dict) -> dict:
    product_name = raw.get("productName", "")
    brand = raw.get("brand", "")
    link = raw.get("link", "")
    categories = raw.get("categories", [])

    image_url = None
    price = None
    list_price = None
    images: list[str] = []

    items = raw.get("items", [])
    if items:
        images = [img.get("imageUrl") for img in items[0].get("images", []) if img.get("imageUrl")]
        if images:
            image_url = images[0]

        sellers = items[0].get("sellers", [])
        if sellers:
            offer = sellers[0].get("commertialOffer", {})
            price = offer.get("Price")
            list_price = offer.get("ListPrice")

    category = ""
    if categories:
        cat_parts = [c.strip("/") for c in categories if c]
        category = cat_parts[-1] if cat_parts else ""

    if link:
        if link.startswith("http"):
            from urllib.parse import urlparse
            link = urlparse(link).path
        product_url = f"{STORE_URL}{link}"
    else:
        product_url = None

    return {
        "name": product_name,
        "brand": brand,
        "category": category,
        "description": raw.get("description") or None,
        "image_url": image_url,
        "images": images,
        "product_url": product_url,
        "store": STORE_KEY,
        "store_name": STORE_NAME,
        "price_usd": float(price) if price is not None else None,
        "list_price_usd": float(list_price) if list_price is not None else None,
        "in_stock": price is not None,
    }

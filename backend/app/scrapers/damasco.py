import httpx
from typing import Any

DAMASCO_API = "https://damasco.vtexcommercestable.com.br/api/catalog_system/pub/products/search"
STORE_NAME = "Damasco"
STORE_KEY = "damasco"


async def search_products(query: str, max_results: int = 24) -> list[dict[str, Any]]:
    params = {
        "q": query,
        "_from": 0,
        "_to": max_results - 1,
    }
    headers = {
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(DAMASCO_API, params=params, headers=headers)
        r.raise_for_status()
        products: list[dict] = r.json()

    return [_parse_product(p) for p in products]


STORE_URL = "https://www.damascovzla.com"


def _parse_product(raw: dict) -> dict:
    product_name = raw.get("productName", "")
    brand = raw.get("brand", "")
    link = raw.get("link", "")
    categories = raw.get("categories", [])

    image_url = None
    price = None
    list_price = None

    items = raw.get("items", [])
    if items:
        images = items[0].get("images", [])
        if images:
            image_url = images[0].get("imageUrl")

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
        "image_url": image_url,
        "product_url": product_url,
        "store": STORE_KEY,
        "store_name": STORE_NAME,
        "price_usd": float(price) if price is not None else None,
        "list_price_usd": float(list_price) if list_price is not None else None,
        "in_stock": price is not None,
    }

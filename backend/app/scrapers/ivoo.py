"""Ivoo scraper using Magento 2 GraphQL API."""
import re
import httpx
from typing import Any

STORE_NAME = "Ivoo"
STORE_KEY = "ivoo"
GRAPHQL_URL = "https://nuweapp.com/graphql"
PRODUCT_BASE = "https://www.ivoo.com"


SEARCH_QUERY = """
query searchProducts($search: String!, $pageSize: Int!) {
    products(search: $search, pageSize: $pageSize) {
        total_count
        items {
            sku
            name
            url_key
            url_suffix
            price_range {
                minimum_price {
                    final_price { value currency }
                    regular_price { value currency }
                }
            }
            image { url label }
            stock_status
        }
    }
}
"""


def _parse_graphql_price(price_info: dict) -> tuple[float | None, float | None]:
    minimum = price_info.get("minimum_price", {})
    final = minimum.get("final_price", {})
    regular = minimum.get("regular_price", {})

    price = float(final["value"]) if final.get("value") is not None else None
    list_price = float(regular["value"]) if regular.get("value") is not None else None

    return price, list_price


async def search_products(query: str, max_results: int = 24) -> list[dict[str, Any]]:
    payload = {
        "query": SEARCH_QUERY,
        "variables": {"search": query, "pageSize": max_results},
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(GRAPHQL_URL, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return []

    products = data.get("data", {}).get("products", {})
    items = products.get("items", [])
    results = []

    for item in items:
        name = item.get("name", "")
        if not name or len(name) < 3:
            continue

        price, list_price = _parse_graphql_price(item.get("price_range", {}))

        url_key = item.get("url_key", "")
        url_suffix = item.get("url_suffix", ".html")
        product_url = f"{PRODUCT_BASE}/{url_key}{url_suffix}" if url_key else ""

        img_data = item.get("image", {}) or {}
        image_url = img_data.get("url", "")

        results.append({
            "name": name,
            "brand": "",
            "category": "",
            "image_url": image_url,
            "product_url": product_url,
            "store": STORE_KEY,
            "store_name": STORE_NAME,
            "price_usd": price,
            "list_price_usd": list_price,
            "in_stock": item.get("stock_status") == "IN_STOCK",
        })

    return results


CATALOG_QUERY = """
query catalogProducts($page: Int!, $pageSize: Int!) {
    products(filter: { category_id: { eq: "2" } }, currentPage: $page, pageSize: $pageSize) {
        total_count
        items {
            sku
            name
            url_key
            url_suffix
            price_range {
                minimum_price {
                    final_price { value currency }
                    regular_price { value currency }
                }
            }
            image { url label }
            stock_status
        }
    }
}
"""


async def fetch_catalog(max_results: int = 1000) -> list[dict[str, Any]]:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    results: list[dict[str, Any]] = []
    page = 1
    page_size = 50

    async with httpx.AsyncClient(timeout=20.0) as client:
        while len(results) < max_results:
            payload = {
                "query": CATALOG_QUERY,
                "variables": {"page": page, "pageSize": page_size},
            }
            try:
                r = await client.post(GRAPHQL_URL, json=payload, headers=headers)
                r.raise_for_status()
                data = r.json()
            except Exception:
                break

            products = data.get("data", {}).get("products", {})
            items = products.get("items", [])
            if not items:
                break
            total = products.get("total_count", 0)

            for item in items:
                name = item.get("name", "")
                if not name or len(name) < 3:
                    continue
                price, list_price = _parse_graphql_price(item.get("price_range", {}))
                url_key = item.get("url_key", "")
                url_suffix = item.get("url_suffix", ".html")
                product_url = f"{PRODUCT_BASE}/{url_key}{url_suffix}" if url_key else ""
                img_data = item.get("image", {}) or {}
                results.append({
                    "name": name,
                    "brand": "",
                    "category": "",
                    "image_url": img_data.get("url", ""),
                    "product_url": product_url,
                    "store": STORE_KEY,
                    "store_name": STORE_NAME,
                    "price_usd": price,
                    "list_price_usd": list_price,
                    "in_stock": item.get("stock_status") == "IN_STOCK",
                })

            if len(results) >= total or len(results) >= max_results:
                break
            page += 1

    return results[:max_results]

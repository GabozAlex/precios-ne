import re
import httpx
from bs4 import BeautifulSoup
from typing import Any

STORE_NAME = "Multimax"
STORE_KEY = "multimax"
SEARCH_URL = "https://multimax.com.ve/buscar?q={query}"
BASE_URL = "https://multimax.com.ve"


async def search_products(query: str, max_results: int = 50) -> list[dict[str, Any]]:
    base_url = SEARCH_URL.format(query=query.replace(" ", "+"))

    try:
        results: list[dict[str, Any]] = []
        page = 1
        while len(results) < max_results:
            url = f"{base_url}&page={page}"
            batch = await _scrape_httpx(url, max_results - len(results))
            if not batch:
                break
            seen = {p["name"] for p in results}
            batch = [p for p in batch if p["name"] not in seen]
            if not batch:
                break
            results.extend(batch)
            page += 1
        return results[:max_results]
    except Exception:
        return []


def _parse_price(text: str) -> float | None:
    cleaned = text.replace("$", "").replace(" ", "").replace(",", ".")
    match = re.search(r"(\d+\.?\d*)", cleaned)
    if match:
        return float(match.group(1))
    return None


async def _scrape_httpx(url: str, max_results: int) -> list[dict[str, Any]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html",
    }

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")
    results = []
    seen_names = set()

    price_spans = soup.select('[class*="tabular-nums"]')

    for span in price_spans:
        price_text = span.get("data-price") or span.get_text()
        price = _parse_price(price_text)
        if price is None:
            continue

        card = span.find_parent(
            lambda t: t.name == "div" and "text-card-foreground" in " ".join(t.get("class", []))
        )
        if not card:
            continue

        link = card.select_one('a[href*="/producto/"][title]')
        if not link:
            continue

        name = link.get("title")
        if not name or len(name) < 5 or name in seen_names:
            continue
        seen_names.add(name)

        href = link.get("href", "")
        product_url = href if href.startswith("http") else f"{BASE_URL}{href}"

        img = card.select_one("picture img")
        image_url = img.get("src", "") if img else ""

        results.append({
            "name": name,
            "brand": "",
            "category": "",
            "image_url": image_url,
            "product_url": product_url,
            "store": STORE_KEY,
            "store_name": STORE_NAME,
            "price_usd": price,
            "list_price_usd": None,
            "in_stock": True,
        })

        if len(results) >= max_results:
            break

    return results

"""Daka scraper: extract products from SSR search results page, filter by query."""
import asyncio
import re
import unicodedata
import urllib.parse
import httpx
from bs4 import BeautifulSoup
from typing import Any

STORE_NAME = "Daka"
STORE_KEY = "daka"
STORE_URL = "https://tiendasdaka.com/ve"
BASE_URL = "https://tiendasdaka.com"
RESULTS_URL = "https://tiendasdaka.com/ve/results/{slug}?q={query}"

CATALOG_URLS = [
    "https://tiendasdaka.com/ve/store/aires-y-ventilacion",
    "https://tiendasdaka.com/ve/store/audio-y-video",
    "https://tiendasdaka.com/ve/store/deportes-y-aire-libre",
    "https://tiendasdaka.com/ve/store/electrodomesticos",
    "https://tiendasdaka.com/ve/store/equipaje-y-accesorios",
    "https://tiendasdaka.com/ve/store/ferreteria",
    "https://tiendasdaka.com/ve/store/hogar-y-muebles",
    "https://tiendasdaka.com/ve/store/juguetes-y-hobbies",
    "https://tiendasdaka.com/ve/store/oficina-y-papeleria",
    "https://tiendasdaka.com/ve/store/tecnologia",
]


def _slugify(query: str) -> str:
    return (
        unicodedata.normalize("NFD", query.lower())
        .encode("ascii", "ignore")
        .decode()
        .strip()
        .replace(".", "")
    )


def _parse_price(text: str) -> float | None:
    cleaned = text.replace("US$", "").replace("Bs.", "").replace(" ", "").strip()
    if not cleaned:
        return None
    cleaned = cleaned.replace(".", "").replace(",", ".")
    match = re.search(r"(\d+\.?\d*)", cleaned)
    if match:
        return float(match.group(1))
    return None


async def search_products(query: str, max_results: int = 50) -> list[dict[str, Any]]:
    base_url = RESULTS_URL.format(
        slug=_slugify(query),
        query=urllib.parse.quote(query),
    )

    try:
        results: list[dict[str, Any]] = []
        page = 1
        while len(results) < max_results:
            url = f"{base_url}&page={page}"
            batch = await _scrape_httpx(url, max_results - len(results), query)
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


async def fetch_catalog(max_results: int = 2000) -> list[dict[str, Any]]:
    try:
        results: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        for base_url in CATALOG_URLS:
            if len(results) >= max_results:
                break
            page = 1
            while len(results) < max_results:
                url = f"{base_url}?page={page}"
                batch = await _scrape_httpx(url, max_results - len(results), "")
                new_batch = [p for p in batch if p["name"] not in seen_names]
                for p in new_batch:
                    seen_names.add(p["name"])
                results.extend(new_batch)
                if not new_batch or len(batch) == 0:
                    break
                page += 1
                await asyncio.sleep(0.5)

        return results[:max_results]
    except Exception:
        return []


async def _scrape_httpx(url: str, max_results: int, query: str) -> list[dict[str, Any]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html",
    }

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")
    results = []
    seen = set()

    wrappers = soup.select('[data-testid="product-wrapper"]')

    for wrapper in wrappers:
        links = wrapper.select("a[href*='/ve/products/']")
        if len(links) < 2:
            continue

        name_link = links[1]
        spans = name_link.select("span")
        brand = spans[0].get_text(strip=True) if spans else ""
        name = spans[1].get_text(strip=True) if len(spans) > 1 else name_link.get_text(strip=True)

        if not name or len(name) < 3:
            continue

        name_lower = name.lower()
        tokens = [t for t in query.lower().split() if t]
        if any(t not in name_lower for t in tokens):
            continue

        if name in seen:
            continue
        seen.add(name)

        img_link = links[0]
        img = img_link.select_one("img")
        image_url = ""
        if img:
            src = img.get("src", "")
            if src.startswith("/_next/image"):
                parsed = urllib.parse.urlparse(src)
                qs = urllib.parse.parse_qs(parsed.query)
                image_url = qs.get("url", [""])[0]
            elif src:
                image_url = src

        href = name_link.get("href", "")
        product_url = href if href.startswith("http") else f"{BASE_URL}{href}"

        price_el = wrapper.select_one('[data-testid="price"]')
        price = _parse_price(price_el.get_text()) if price_el else None

        if price is None:
            continue

        results.append({
            "name": name,
            "brand": brand,
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

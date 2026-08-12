import re
import httpx
from bs4 import BeautifulSoup
from typing import Any

STORE_NAME = "Multimax"
STORE_KEY = "multimax"
SEARCH_URL = "https://multimax.com.ve/buscar?q={query}"
BASE_URL = "https://multimax.com.ve"

CATALOG_URLS = [
    "https://multimax.com.ve/aires-acondicionados",
    "https://multimax.com.ve/audio-y-tv",
    "https://multimax.com.ve/calzado",
    "https://multimax.com.ve/celulares-y-tablets",
    "https://multimax.com.ve/cocina",
    "https://multimax.com.ve/cuidado-personal",
    "https://multimax.com.ve/electrodomesticos",
    "https://multimax.com.ve/ferreteria",
    "https://multimax.com.ve/hogar",
    "https://multimax.com.ve/lavado",
    "https://multimax.com.ve/lenceria-de-hogar",
    "https://multimax.com.ve/oportunidades",
    "https://multimax.com.ve/refrigeracion",
    "https://multimax.com.ve/tecnologia",
    "https://multimax.com.ve/televisores",
    "https://multimax.com.ve/variedades",
]


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


async def fetch_catalog(max_results: int = 4000) -> list[dict[str, Any]]:
    try:
        results: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        for base_url in CATALOG_URLS:
            if len(results) >= max_results:
                break
            page = 1
            while len(results) < max_results:
                url = f"{base_url}?page={page}"
                batch = await _scrape_httpx(url, max_results - len(results))
                new_batch = [p for p in batch if p["name"] not in seen_names]
                for p in new_batch:
                    seen_names.add(p["name"])
                results.extend(new_batch)
                if not new_batch or len(batch) == 0:
                    break
                page += 1

        return results[:max_results]
    except Exception:
        return []


def _parse_price(text: str) -> float | None:
    cleaned = text.replace("$", "").replace("BS.", "").replace("USD", "").replace(" ", "").strip()
    if not cleaned:
        return None
    cleaned = cleaned.replace(".", "").replace(",", ".")  # quitar miles, coma->punto
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


async def fetch_detail(product_url: str) -> tuple[str | None, list[str]]:
    """Fetch a product detail page: description + image gallery."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html",
    }

    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            r = await client.get(product_url, headers=headers)
            r.raise_for_status()
    except Exception:
        return None, []

    soup = BeautifulSoup(r.text, "lxml")

    meta = soup.select_one('meta[name="description"]')
    description = (meta.get("content") or "").strip() if meta else ""

    images: list[str] = []
    for img in soup.select('img[src*="medios/productos/"]'):
        src = img.get("src", "")
        if "-medium." not in src:
            continue
        if src not in images:
            images.append(src)

    return (description or None, images)

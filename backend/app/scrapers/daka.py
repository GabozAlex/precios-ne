"""Daka scraper: extract products from SSR store page, filter by query."""
import re
from bs4 import BeautifulSoup
from typing import Any

STORE_NAME = "Daka"
STORE_KEY = "daka"
STORE_URL = "https://daka.tiendasdaka.com/ve/store"
BASE_URL = "https://daka.tiendasdaka.com"


def _parse_price(text: str) -> float | None:
    cleaned = text.replace("US$", "").replace(",", "").replace(" ", "")
    match = re.search(r"(\d+\.?\d*)", cleaned)
    if match:
        return float(match.group(1))
    return None


async def search_products(query: str, max_results: int = 24) -> list[dict[str, Any]]:
    from playwright.async_api import async_playwright

    browser = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1920, "height": 1080})

            await page.goto(STORE_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            html = await page.content()
            soup = BeautifulSoup(html, "lxml")
            results = []
            seen = set()

            wrappers = soup.select('[data-testid="product-wrapper"]')

            for wrapper in wrappers:
                links = wrapper.select("a[href*='/ve/products/']")
                if len(links) < 2:
                    continue

                name_link = links[1]
                brand_el = name_link.select_one("p")
                name_el = name_link.select_one("p:last-child")
                name = name_el.get_text(strip=True) if name_el else name_link.get_text(strip=True)
                brand = brand_el.get_text(strip=True) if brand_el else ""

                if not name or len(name) < 3:
                    continue

                if query.lower() not in name.lower():
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
                        import urllib.parse
                        parsed = urllib.parse.urlparse(src)
                        qs = urllib.parse.parse_qs(parsed.query)
                        image_url = qs.get("url", [""])[0]
                    elif src:
                        image_url = src

                href = name_link.get("href", "")
                product_url = href if href.startswith("http") else f"{BASE_URL}{href}"

                price_el = wrapper.select_one('[data-testid="price"]')
                price = _parse_price(price_el.get_text()) if price_el else None

                if price is not None:
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

    except Exception:
        return []
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass

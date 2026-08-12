import asyncio
import re
import unicodedata
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from rapidfuzz import fuzz
from sqlalchemy import select, desc, exists, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from .database import get_db
from .models import Product, Price, PriceHistory, Store
from .scrapers import damasco, multimax, daka, ivoo

router = APIRouter(prefix="/api", tags=["api"])


def _parse_price(raw_price) -> float | None:
    try:
        return float(raw_price)
    except (TypeError, ValueError):
        return None


def _dedup_by_store(results: list[dict]) -> list[dict]:
    best: dict[tuple[str, str], dict] = {}
    for r in results:
        if not r.get("price_usd"):
            continue
        key = (r.get("name", ""), r.get("store", ""))
        existing = best.get(key)
        if existing is None:
            best[key] = r
        else:
            try:
                cur = float(existing.get("price_usd", 0) or 0)
                new = float(r.get("price_usd", 0) or 0)
            except (TypeError, ValueError):
                continue
            if new < cur:
                best[key] = r
    return list(best.values())


def _normalize_name(name: str) -> str:
    text = (name or "").lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    for token in (
        "damasco", "multimax", "tiendas daka", "daka", "ivoo",
        "da+co", "da&co", "da co", "marca",
    ):
        text = text.replace(token, " ")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


_CLUSTER_THRESHOLD = 82


def _cluster_products(products: list["ProductOut"]) -> list["ProductOut"]:
    """Agrupa el mismo producto físico (nombres similares) entre tiendas."""
    clusters: list[dict] = []
    for p in products:
        norm = _normalize_name(p.name)
        best_idx, best_score = -1, 0.0
        for i, c in enumerate(clusters):
            score = fuzz.WRatio(norm, c["norm"])
            if score > best_score:
                best_score, best_idx = score, i
        if best_idx >= 0 and best_score >= _CLUSTER_THRESHOLD:
            clusters[best_idx]["members"].append(p)
        else:
            clusters.append({"norm": norm, "members": [p]})

    out: list[ProductOut] = []
    for c in clusters:
        best_by_store: dict[str, PriceOut] = {}
        for m in c["members"]:
            for price in m.prices:
                existing = best_by_store.get(price.store)
                if existing is None or (
                    price.price_usd is not None
                    and (existing.price_usd is None or price.price_usd < existing.price_usd)
                ):
                    best_by_store[price.store] = price
        price_list = sorted(
            best_by_store.values(),
            key=lambda x: x.price_usd if x.price_usd is not None else float("inf"),
        )
        rep = min(
            c["members"],
            key=lambda m: m.best_price.price_usd
            if m.best_price and m.best_price.price_usd is not None
            else float("inf"),
        )
        out.append(ProductOut(
            id=rep.id,
            name=rep.name,
            brand=rep.brand,
            category=rep.category,
            image_url=rep.image_url,
            images=rep.images or [],
            description=rep.description,
            best_price=price_list[0] if price_list else None,
            prices=price_list,
        ))
    return out


async def _upsert_scraper_results(
    db: AsyncSession,
    all_results: list[dict],
    now: datetime,
) -> dict:
    grouped: dict[str, dict] = {}
    for r in all_results:
        price = _parse_price(r.get("price_usd"))
        if price is None:
            continue

        images = r.get("images") or []
        description = r.get("description")

        product_stmt = select(Product).where(Product.name == r["name"]).limit(1)
        product_result = await db.execute(product_stmt)
        existing = product_result.scalar_one_or_none()

        if existing:
            product_id = existing.id
            if images and not existing.images:
                existing.images = images
            if description and not existing.description:
                existing.description = description
        else:
            new_product = Product(
                name=r["name"],
                brand=r.get("brand"),
                category=r.get("category"),
                image_url=r.get("image_url"),
                images=images or [],
                description=description,
            )
            db.add(new_product)
            await db.flush()
            product_id = new_product.id

        await db.execute(
            Price.__table__.delete().where(
                Price.product_id == product_id,
                Price.store == r["store"],
            )
        )

        price_entry = Price(
            product_id=product_id,
            store=r["store"],
            store_name=r["store_name"],
            price_usd=price,
            product_url=r.get("product_url"),
            in_stock=r.get("in_stock", True),
            scraped_at=now,
        )
        db.add(price_entry)

        history_entry = PriceHistory(
            product_id=product_id,
            store=r["store"],
            price_usd=price,
            recorded_at=now,
        )
        db.add(history_entry)

        key = str(product_id)
        if key not in grouped:
            grouped[key] = {
                "id": key,
                "name": r["name"],
                "brand": r.get("brand"),
                "category": r.get("category"),
                "image_url": r.get("image_url"),
                "images": images or [],
                "description": description,
                "prices": [],
            }
        grouped[key]["prices"].append(r)

    await db.commit()

    out_products = []
    for pid, data in grouped.items():
        price_list = sorted(data["prices"], key=lambda x: _parse_price(x.get("price_usd")) or 0)
        prices_out = [
            PriceOut(
                store=p["store"],
                store_name=p["store_name"],
                price_usd=_parse_price(p.get("price_usd")),
                product_url=p.get("product_url"),
                in_stock=p.get("in_stock", True),
                scraped_at=now.isoformat(),
            )
            for p in price_list
        ]
        out_products.append(ProductOut(
            id=data["id"],
            name=data["name"],
            brand=data["brand"],
            category=data["category"],
            image_url=data["image_url"],
            images=data.get("images") or [],
            description=data.get("description"),
            best_price=prices_out[0] if prices_out else None,
            prices=prices_out,
        ))

    out_products.sort(key=lambda p: p.best_price.price_usd if p.best_price and p.best_price.price_usd is not None else float("inf"))
    return {"products": out_products, "total": len(out_products)}


class PriceOut(BaseModel):
    store: str
    store_name: str
    price_usd: float | None
    product_url: str | None
    in_stock: bool
    scraped_at: str | None = None


class ProductOut(BaseModel):
    id: str
    name: str
    brand: str | None
    category: str | None
    image_url: str | None
    images: list[str] = []
    description: str | None = None
    best_price: PriceOut | None
    prices: list[PriceOut]


class SearchResult(BaseModel):
    query: str
    total_results: int
    products: list[ProductOut]
    cached: bool
    scraped_at: str | None = None


class ProductsPage(BaseModel):
    total: int
    page: int
    page_size: int
    products: list[ProductOut]


class StoreOut(BaseModel):
    id: str
    name: str
    website: str
    active: bool
    last_scrape: str | None = None


@router.get("/search", response_model=SearchResult)
async def search(
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    force_refresh: bool = Query(False, description="Ignorar caché"),
    store: str = Query("", description="Filtrar por tienda (damasco, multimax, daka, ivoo)"),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    if not force_refresh:
        cutoff = now.timestamp() - 3600
        stmt = (
            select(Price)
            .join(Product)
            .where(Product.name.ilike(f"%{q}%"))
            .where(Price.scraped_at >= datetime.fromtimestamp(cutoff, tz=timezone.utc))
            .limit(24)
        )
        if store:
            stmt = stmt.where(Price.store == store)
        result = await db.execute(stmt)
        cached_prices = result.scalars().all()

        if cached_prices:
            product_ids = list(set(p.product_id for p in cached_prices))
            products_stmt = select(Product).where(Product.id.in_(product_ids))
            products_result = await db.execute(products_stmt)
            products = products_result.scalars().all()

            product_map = {p.id: p for p in products}
            grouped: dict = {}
            for price in cached_prices:
                prod = product_map.get(price.product_id)
                if not prod:
                    continue
                if prod.id not in grouped:
                    grouped[prod.id] = {"product": prod, "prices": []}
                grouped[prod.id]["prices"].append(price)

            out = []
            for pid, data in grouped.items():
                prod = data["product"]
                price_list = sorted(data["prices"], key=lambda x: x.price_usd or 0)
                prices_out = [
                    PriceOut(
                        store=p.store,
                        store_name=p.store_name,
                        price_usd=float(p.price_usd) if p.price_usd is not None else None,
                        product_url=p.product_url,
                        in_stock=p.in_stock,
                        scraped_at=p.scraped_at.isoformat() if p.scraped_at else None,
                    )
                    for p in price_list
                ]
                out.append(ProductOut(
                    id=str(prod.id),
                    name=prod.name,
                    brand=prod.brand,
                    category=prod.category,
                    image_url=prod.image_url,
                    images=prod.images or [],
                    description=prod.description,
                    best_price=prices_out[0] if prices_out else None,
                    prices=prices_out,
                ))

            out = _cluster_products(out)
            out.sort(key=lambda p: p.best_price.price_usd if p.best_price and p.best_price.price_usd is not None else float("inf"))

            return SearchResult(
                query=q,
                total_results=len(out),
                products=out,
                cached=True,
                scraped_at=cached_prices[0].scraped_at.isoformat() if cached_prices else None,
            )

    scraper_results = await asyncio.gather(
        damasco.search_products(q, 50),
        multimax.search_products(q, 50),
        daka.search_products(q, 50),
        ivoo.search_products(q, 50),
        return_exceptions=True,
    )

    all_results: list[dict] = []
    for res in scraper_results:
        if isinstance(res, Exception):
            continue
        all_results.extend(res)

    if store:
        all_results = [r for r in all_results if r.get("store") == store]

    all_results = _dedup_by_store(all_results)
    saved = await _upsert_scraper_results(db, all_results, now)
    saved_products = _cluster_products(saved["products"])
    saved_products.sort(
        key=lambda p: p.best_price.price_usd
        if p.best_price and p.best_price.price_usd is not None
        else float("inf")
    )

    return SearchResult(
        query=q,
        total_results=len(saved_products),
        products=saved_products,
        cached=False,
        scraped_at=now.isoformat(),
    )


@router.get("/suggest")
async def suggest(
    q: str = Query(..., min_length=1, max_length=80, description="Prefijo/texto de búsqueda"),
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Product.name)
        .where(Product.name.ilike(f"%{q}%"))
        .distinct()
        .order_by(Product.name)
        .limit(limit)
    )
    result = await db.execute(stmt)
    names = result.scalars().all()
    return {"suggestions": list(names)}


@router.get("/products", response_model=ProductsPage)
async def list_products(
    db: AsyncSession = Depends(get_db),
    q: str = Query("", description="Filtrar por nombre"),
    store: str = Query("", description="Filtrar por tienda (damasco, multimax, daka, ivoo)"),
    limit: int = Query(50, ge=1, le=200, description="Tamaño de página"),
    offset: int = Query(0, ge=0, description="Desplazamiento"),
):
    prod_stmt = select(Product)
    if q:
        prod_stmt = prod_stmt.where(Product.name.ilike(f"%{q}%"))
    if store:
        prod_stmt = prod_stmt.where(
            exists().where(and_(Price.product_id == Product.id, Price.store == store))
        )

    total = await db.scalar(select(func.count()).select_from(prod_stmt.subquery()))
    total = int(total or 0)

    prod_stmt = prod_stmt.order_by(Product.created_at.desc()).offset(offset).limit(limit)
    products_result = await db.execute(prod_stmt)
    products = products_result.scalars().all()

    prices_stmt = (
        select(Price)
        .where(Price.product_id.in_([p.id for p in products]))
        .order_by(Price.price_usd)
    )
    prices_result = await db.execute(prices_stmt)
    prices = prices_result.scalars().all()

    grouped: dict = {}
    for price in prices:
        grouped.setdefault(price.product_id, []).append(price)

    out = []
    for prod in products:
        price_list = sorted(grouped.get(prod.id, []), key=lambda x: x.price_usd or 0)
        prices_out = [
            PriceOut(
                store=p.store,
                store_name=p.store_name,
                price_usd=float(p.price_usd) if p.price_usd is not None else None,
                product_url=p.product_url,
                in_stock=p.in_stock,
                scraped_at=p.scraped_at.isoformat() if p.scraped_at else None,
            )
            for p in price_list
        ]
        out.append(ProductOut(
            id=str(prod.id),
            name=prod.name,
            brand=prod.brand,
            category=prod.category,
            image_url=prod.image_url,
            images=prod.images or [],
            description=prod.description,
            best_price=prices_out[0] if prices_out else None,
            prices=prices_out,
        ))

    return ProductsPage(
        total=total,
        page=offset // limit + 1 if limit else 1,
        page_size=limit,
        products=out,
    )


@router.get("/products/{product_id}")
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(404, "Producto no encontrado")

    prices_stmt = (
        select(Price)
        .where(Price.product_id == product.id)
        .order_by(Price.price_usd)
    )
    prices_result = await db.execute(prices_stmt)
    prices = prices_result.scalars().all()

    history_stmt = (
        select(PriceHistory)
        .where(PriceHistory.product_id == product.id)
        .order_by(desc(PriceHistory.recorded_at))
        .limit(50)
    )
    history_result = await db.execute(history_stmt)
    history = history_result.scalars().all()

    store = prices[0].store if prices else None
    if store in ("multimax", "daka") and (not product.images or not product.description):
        scraper = multimax if store == "multimax" else daka
        url = next((p.product_url for p in prices), None)
        if url:
            try:
                description, images = await scraper.fetch_detail(url)
                if description and not product.description:
                    product.description = description
                if images and not product.images:
                    product.images = images
                await db.commit()
            except Exception:
                pass

    return {
        "id": str(product.id),
        "name": product.name,
        "brand": product.brand,
        "category": product.category,
        "image_url": product.image_url,
        "images": product.images or [],
        "description": product.description,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "current_prices": [
            {
                "store": p.store,
                "store_name": p.store_name,
                "price_usd": float(p.price_usd) if p.price_usd is not None else None,
                "product_url": p.product_url,
                "in_stock": p.in_stock,
                "scraped_at": p.scraped_at.isoformat() if p.scraped_at else None,
            }
            for p in prices
        ],
        "price_history": [
            {
                "store": h.store,
                "price_usd": float(h.price_usd) if h.price_usd is not None else None,
                "recorded_at": h.recorded_at.isoformat() if h.recorded_at else None,
            }
            for h in history
        ],
    }


@router.get("/stores", response_model=list[StoreOut])
async def list_stores(db: AsyncSession = Depends(get_db)):
    stmt = select(Store).order_by(Store.name)
    result = await db.execute(stmt)
    stores = result.scalars().all()

    if not stores:
        default_stores = [
            Store(id="damasco", name="Damasco", website="https://www.damascovzla.com", active=True),
            Store(id="multimax", name="Multimax", website="https://multimax.com.ve", active=True),
            Store(id="daka", name="Daka", website="https://tiendasdaka.com/ve", active=True),
            Store(id="ivoo", name="Ivoo", website="https://www.ivoo.com", active=True),
        ]
        for s in default_stores:
            db.add(s)
        await db.commit()
        stores = default_stores

    return [
        StoreOut(
            id=s.id,
            name=s.name,
            website=s.website,
            active=s.active,
            last_scrape=s.last_scrape.isoformat() if s.last_scrape else None,
        )
        for s in stores
    ]


@router.api_route("/sync/catalog", methods=["GET", "POST"])
async def sync_catalog(
    store: str = Query("", description="Sincronizar una sola tienda (damasco, multimax, daka, ivoo)"),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    store_names = {"damasco": "Damasco", "multimax": "Multimax", "daka": "Daka", "ivoo": "Ivoo"}
    store_websites = {
        "damasco": "https://www.damascovzla.com",
        "multimax": "https://multimax.com.ve",
        "daka": "https://tiendasdaka.com/ve",
        "ivoo": "https://www.ivoo.com",
    }

    targets = [store] if store in store_names else list(store_names.keys())

    scrapers_map = {
        "damasco": lambda: damasco.fetch_catalog(2000),
        "multimax": lambda: multimax.fetch_catalog(4000),
        "daka": lambda: daka.fetch_catalog(2000),
        "ivoo": lambda: ivoo.fetch_catalog(1000),
    }

    tasks = [scrapers_map[s]() for s in targets]
    syncs = await asyncio.gather(*tasks, return_exceptions=True)

    all_results: list[dict] = []
    summary: dict[str, int] = {}

    for res, store_key in zip(syncs, targets):
        if isinstance(res, Exception):
            summary[store_key] = 0
            continue
        all_results.extend(res)
        summary[store_key] = len(res)

    all_results = _dedup_by_store(all_results)
    saved = await _upsert_scraper_results(db, all_results, now)

    for store_key in summary:
        stmt = select(Store).where(Store.id == store_key)
        result = await db.execute(stmt)
        s_obj = result.scalar_one_or_none()
        if s_obj:
            s_obj.last_scrape = now
        else:
            db.add(Store(
                id=store_key,
                name=store_names[store_key],
                website=store_websites[store_key],
                active=True,
                last_scrape=now,
            ))
    await db.commit()

    return {
        "message": f"Catálogo sincronizado{f' para {store}' if store else ''}",
        "timestamp": now.isoformat(),
        "stores": summary,
        "total_products": saved["total"],
    }

import asyncio
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
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

        product_stmt = select(Product).where(Product.name == r["name"]).limit(1)
        product_result = await db.execute(product_stmt)
        existing = product_result.scalar_one_or_none()

        if existing:
            product_id = existing.id
        else:
            new_product = Product(
                name=r["name"],
                brand=r.get("brand"),
                category=r.get("category"),
                image_url=r.get("image_url"),
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
    best_price: PriceOut | None
    prices: list[PriceOut]


class SearchResult(BaseModel):
    query: str
    total_results: int
    products: list[ProductOut]
    cached: bool
    scraped_at: str | None = None


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
                    best_price=prices_out[0] if prices_out else None,
                    prices=prices_out,
                ))

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

    saved = await _upsert_scraper_results(db, all_results, now)

    return SearchResult(
        query=q,
        total_results=saved["total"],
        products=saved["products"],
        cached=False,
        scraped_at=now.isoformat(),
    )


@router.get("/products", response_model=list[ProductOut])
async def list_products(
    db: AsyncSession = Depends(get_db),
    q: str = Query("", description="Filtrar por nombre"),
    store: str = Query("", description="Filtrar por tienda (damasco, multimax, daka, ivoo)"),
):
    stmt = (
        select(Price)
        .join(Product)
        .order_by(Price.price_usd)
    )
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    if store:
        stmt = stmt.where(Price.store == store)
    result = await db.execute(stmt)
    prices = result.scalars().all()

    product_ids = list(set(p.product_id for p in prices))
    products_stmt = select(Product).where(Product.id.in_(product_ids))
    products_result = await db.execute(products_stmt)
    products = products_result.scalars().all()
    product_map = {p.id: p for p in products}

    grouped: dict = {}
    for price in prices:
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
            best_price=prices_out[0] if prices_out else None,
            prices=prices_out,
        ))

    out.sort(key=lambda p: p.best_price.price_usd if p.best_price and p.best_price.price_usd is not None else float("inf"))
    return out


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

    return {
        "id": str(product.id),
        "name": product.name,
        "brand": product.brand,
        "category": product.category,
        "image_url": product.image_url,
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


@router.post("/sync/catalog")
async def sync_catalog(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)

    syncs = await asyncio.gather(
        damasco.fetch_catalog(2000),
        multimax.fetch_catalog(4000),
        daka.fetch_catalog(2000),
        ivoo.fetch_catalog(1000),
        return_exceptions=True,
    )

    store_names = {"damasco": "Damasco", "multimax": "Multimax", "daka": "Daka", "ivoo": "Ivoo"}
    store_websites = {
        "damasco": "https://www.damascovzla.com",
        "multimax": "https://multimax.com.ve",
        "daka": "https://tiendasdaka.com/ve",
        "ivoo": "https://www.ivoo.com",
    }
    all_results: list[dict] = []
    summary: dict[str, int] = {}

    for res, store_key in zip(syncs, ("damasco", "multimax", "daka", "ivoo")):
        if isinstance(res, Exception):
            summary[store_key] = 0
            continue
        all_results.extend(res)
        summary[store_key] = len(res)

    saved = await _upsert_scraper_results(db, all_results, now)

    for store_key in summary:
        stmt = select(Store).where(Store.id == store_key)
        result = await db.execute(stmt)
        store = result.scalar_one_or_none()
        if store:
            store.last_scrape = now
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
        "message": "Catálogo sincronizado",
        "timestamp": now.isoformat(),
        "stores": summary,
        "total_products": saved["total"],
    }

from app.router import ProductOut, PriceOut, _cluster_products


def _product(pid: str, name: str, store: str, price: float) -> ProductOut:
    price_out = PriceOut(
        store=store,
        store_name=store,
        price_usd=price,
        product_url=None,
        in_stock=True,
    )
    return ProductOut(
        id=pid,
        name=name,
        brand=None,
        category=None,
        image_url=None,
        images=[],
        description=None,
        best_price=price_out,
        prices=[price_out],
    )


class TestClusterProducts:
    def test_merges_same_product_across_stores(self):
        items = [
            _product("1", "Nevera Da+Co DCRT13 127L", "damasco", 288.0),
            _product("2", "Nevera Damasco DCRT13 127L", "multimax", 299.99),
        ]
        clustered = _cluster_products(items)
        assert len(clustered) == 1
        assert len(clustered[0].prices) == 2
        assert clustered[0].best_price.price_usd == 288.0

    def test_keeps_different_products_separate(self):
        items = [
            _product("1", "Nevera Da+Co DCRT13 127L", "damasco", 288.0),
            _product("3", "Televisor Smart LG 43", "daka", 240.0),
            _product("5", "Licuadora Oster 1.5L", "damasco", 45.0),
        ]
        clustered = _cluster_products(items)
        assert len(clustered) == 3

    def test_dedupes_price_per_store(self):
        items = [
            _product("1", "Nevera Da+Co DCRT13 127L", "damasco", 288.0),
            _product("2", "Nevera Damasco DCRT13 127L", "damasco", 275.0),
        ]
        clustered = _cluster_products(items)
        assert len(clustered) == 1
        assert len(clustered[0].prices) == 1
        assert clustered[0].prices[0].price_usd == 275.0

    def test_uses_lowest_price_product_as_representative(self):
        items = [
            _product("1", "Nevera Damasco DCRT13 127L", "multimax", 299.99),
            _product("2", "Nevera Da+Co DCRT13 127L", "damasco", 288.0),
        ]
        clustered = _cluster_products(items)
        assert clustered[0].id == "2"
        assert clustered[0].name.startswith("Nevera Da+Co")
        assert clustered[0].best_price.price_usd == 288.0
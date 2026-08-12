from app.scrapers import multimax, daka, damasco, ivoo


class TestMultimaxParsePrice:
    def test_thousands_and_decimals(self):
        assert multimax._parse_price("$1.000,00") == 1000.0

    def test_decimals_with_comma(self):
        assert multimax._parse_price("$299,99") == 299.99

    def test_million_with_decimals(self):
        assert multimax._parse_price("1.000.000,50") == 1000000.5

    def test_bolivares(self):
        assert multimax._parse_price("Bs. 250,75") == 250.75

    def test_thousands_only(self):
        assert multimax._parse_price("1.000") == 1000.0

    def test_usd_prefix(self):
        assert multimax._parse_price("USD 300,0") == 300.0

    def test_empty(self):
        assert multimax._parse_price("") is None
        assert multimax._parse_price("   ") is None
        assert multimax._parse_price("Sin precio") is None


class TestDakaParsePrice:
    def test_thousands_and_decimals(self):
        assert daka._parse_price("$1.000,00") == 1000.0

    def test_usds(self):
        assert daka._parse_price("US$299,99") == 299.99

    def test_empty(self):
        assert daka._parse_price("") is None


class TestDamascoParseProduct:
    def test_parses_images_and_description(self):
        raw = {
            "productName": "Nevera Damasco DC187 187 Litros",
            "brand": "DAMASCO",
            "link": "/nevera/p",
            "categories": ["/Electrodomésticos/Refrigeración/"],
            "description": (
                "Nevera de dos puertas con tecnología de ahorro energético, "
                "capacidad de 187 litros."
            ),
            "items": [
                {
                    "images": [
                        {"imageUrl": "https://img/1.jpg"},
                        {"imageUrl": "https://img/2.jpg"},
                    ],
                    "sellers": [
                        {
                            "commertialOffer": {"Price": 288.0, "ListPrice": 320.0}
                        }
                    ],
                }
            ],
        }
        result = damasco._parse_product(raw)
        assert result["description"] == raw["description"]
        assert result["images"] == ["https://img/1.jpg", "https://img/2.jpg"]
        assert result["image_url"] == "https://img/1.jpg"
        assert result["price_usd"] == 288.0
        assert result["list_price_usd"] == 320.0
        assert result["in_stock"] is True


class TestIvooParsePrice:
    def test_parses_price_range(self):
        price_info = {
            "minimum_price": {
                "final_price": {"value": 250.5, "currency": "USD"},
                "regular_price": {"value": 290.0, "currency": "USD"},
            }
        }
        price, list_price = ivoo._parse_graphql_price(price_info)
        assert price == 250.5
        assert list_price == 290.0

    def test_missing_regular_price(self):
        price_info = {
            "minimum_price": {"final_price": {"value": None, "currency": "USD"}}
        }
        price, list_price = ivoo._parse_graphql_price(price_info)
        assert price is None
        assert list_price is None
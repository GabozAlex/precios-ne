# Tareas para el Backend (precios-ne)

Estas tareas son requeridas por mejoras/pulidos del **frontend** y no pueden resolverse solo modificando el cliente.

## 1. Bug crítico: parsing de precios en Multimax (prioridad alta)

**Archivo:** `backend/app/scrapers/multimax.py` — función `_parse_price`

**Problema:** en Venezuela los precios usan `.` como separador
de miles y `,` como decimal (ej: `1.000,00`). El scraper reemplaza la
coma **antes** de borrar los puntos, por lo que:

- Entrada: `"$1.000,00"`
- Después de `.replace(",", ".")`: `"$1.000.00"`
- Regex `(\d+\.?\d*)` atrapa `"1.000"` → `float("1.000")` = **1.0**

Cuando un producto cuesta **1.000,00 USD** se graba **1.00** y el
frontend muestra **$1.00** en vez de **$1.000,00**.

**Fix esperado** (igual al scraper de Daka que ya funciona bien):

```python
def _parse_price(text: str) -> float | None:
    cleaned = text.replace("$", "").replace("BS.", "").replace("USD", "").replace(" ", "").strip()
    if not cleaned:
        return None
    cleaned = cleaned.replace(".", "").replace(",", ".")  # borrar miles, coma->punto
    match = re.search(r"(\d+\.?\d*)", cleaned)
    if match:
        return float(match.group(1))
    return None
```

> Nota: `daka.py` ya usa el orden correcto. `ivoo.py` recibe `value` numérico directamente de GraphQL, OK.

## 2. Exponer descripción y galería de imágenes (prioridad media)

**Archivo:** scrapers + `backend/app/models.py` + `backend/app/router.py`

El frontend quiere abrir un modal de detalle de producto que muestre
la **descripción** y **varias imágenes** del producto. Hoy en la DB
solo se guarda `image_url` (una) y no hay descripción.

**Cambios requeridos:**

1. **Scrapers** (`damasco.py`, `multimax.py`, `daka.py`, `ivoo.py`):
   - Capturar una lista `images: list[str]` (galería).
   - Capturar `description: str | None`.

2. **`models.py`**:
   - Tabla `products`: añadir columnas
     - `images` → `Text` o JSON (PostgreSQL `ARRAY`/`JSON`), con default `[]`.
     - `description` → `Text` nullable.

3. **`router.py`**:
   - `_upsert_scraper_results`: guardar `images` y `description`.
   - `GET /api/products/{id}`: incluir `images` y `description` en la
     respuesta JSON.
   - `GET /api/products` y `GET /api/search`: incluir `images`/`description`
     en `ProductOut` (el frontend los usa para el modal).

## 3. (Opcional) Endpoint de sugerencias/autocompletado (prioridad baja)

**Archivo:** `backend/app/router.py`

El frontend podría añadir autocompletado al `SearchBar`. Requeriría:

- `GET /api/suggest?q=...` → retorna lista de nombres de productos
  distintos que empiecen con o contengan `q` (ej: 10 resultados).

Esto mejora UX pero no es bloqueante.

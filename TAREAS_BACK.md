# Tareas del Backend (precios-ne) — Estado

Todas las tareas documentadas originalmente fueron resueltas. Estado al 12/08/2026:

## 1. Bug crítico: parsing de precios en Multimax ✅ Resuelto

**Archivo:** `backend/app/scrapers/multimax.py` — función `_parse_price`

Ahora quita los miles (`.`) **antes** de convertir la coma (`,`) en decimal,
igual que `daka.py`:

- `"$1.000,00"` → `1000.0` (antes daba `1.0`)
- `"1.000.000,50"` → `1000000.5`
- `""` / `"Sin precio"` → `None`

Cubierto por `backend/tests/test_parse_price.py`.

## 2. Descripción y galería de imágenes ✅ Resuelto

- `products` ahora tiene columnas `images` (JSON, default `[]`) y `description` (Text).
- **Damasco** (API VTEX) y **Ivoo** (GraphQL Magento): capturan `description` e
  `images` directamente durante el scrape.
- **Multimax** y **Daka**: sus páginas exigirían una request extra por producto,
  por eso la captura es **perezosa**: `GET /api/products/{id}` visita la página
  de detalle (`scrapers/*.py::fetch_detail`) y cachea `description` + `images`
  en la DB.
- La API expone `images` y `description` en:
  - `/api/search`
  - `/api/products`
  - `/api/products/{id}`

### Migración de base de datos (PRODUCCIÓN — importante)

La DB de Render/Supabase ya existe con el esquema viejo. Antes de desplegar el
nuevo código, correr UNA VEZ la migración:

```bash
cd backend
DATABASE_URL="<TU_URL>?ssl=require" .venv/bin/alembic -c alembic.ini upgrade head
```

La migración (`alembic/versions/0001_*.py`) solo agrega `images`/`description`.
Bases nuevas no la necesitan (el `create_all` del arranque ya crea el esquema
completo). No ejecutar `alembic upgrade` sobre una base recién creada por
`create_all` (fallaría por columnas duplicadas).

**Equivalente en SQL plano (Supabase):**

```sql
-- ejecutar UNA vez contra la DB de producción
ALTER TABLE products ADD COLUMN images JSON DEFAULT '[]';
ALTER TABLE products ADD COLUMN description TEXT;
```

Si prefieres no instalar Alembic en producción, el SQL de arriba es suficiente.
En ese caso, no uses `alembic` después para otras migraciones o marcá la base
como al día con `alembic stamp 0001`.

## 3. Sugerencias / autocompletado ✅ Resuelto

- `GET /api/suggest?q=...` → `{"suggestions": [...]}` (nombres distintos que
  contienen `q`, 10 por defecto).
- `SearchBar` del frontend usa el endpoint con debounce (300 ms) y dropdown.

## Mejoras adicionales resueltas

- **Paginación server** en `GET /api/products` (`limit`/`offset`) → responde
  `{ total, page, page_size, products }`. El frontend de `/productos` pagina en
  servidor (antes paginaba en cliente el catálogo completo).
- **`StoreStatusBar` dinámico**: consume `GET /api/stores` y muestra el estado
  real de cada tienda (gris = inactiva).
- **Agrupación ligera entre tiendas**: `rapidfuzz` agrupa en tiempo de
  búsqueda el mismo producto físico con nombres distintos (normaliza marca y
  términos tipo "da+co"). Umbral WRatio ≥ 82, sin cambios de esquema.
- **Limpieza**: eliminado el código fantasma `ivuu` en `router.py`.
- **Tests**: `backend/tests/` (parsing de precios + clustering), 17 casos.
- **Alembic**: setup en `backend/alembic/` (env async compatible con
  `postgresql+asyncpg` y `sqlite+aiosqlite`).
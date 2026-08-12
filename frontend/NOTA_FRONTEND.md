# NOTA para quien maneja el FRONTEND

> Nota dejada por el equipo de **backend** (12/08/2026). Lee esto antes de
> seguir tocando el front: aquí están los cambios que hicimos y lo que debes
> ajustar.

## 1. Contrato de API actualizado (el backend YA responde así)

El backend cambió. Asegúrate de consumir:

| Endpoint | Cambio |
|----------|--------|
| `GET /api/products` | Ahora **paginado**: `?limit=50&offset=0` → `{ "total", "page", "page_size", "products" }`. Ya NO devuelve un array simple. |
| `GET /api/search` | `ProductOut` ahora incluye **`images: string[]`** y **`description: string \| null`**. |
| `GET /api/products/{id}` | Incluye `images` y `description`. Ojo: para **Multimax** y **Daka** `images`/`description` pueden llegar vacíos en la búsqueda y se rellenan **bajo demanda** al llamar a este endpoint (visita la página del producto y cachea). |
| `GET /api/suggest` | **NUEVO**: `?q=nevera` → `{ "suggestions": ["...", ...] }` (10 por defecto). Para autocompletado. |
| `GET /api/stores` | Sin cambios (para el estado de tiendas). |
| `GET /api/search?q=X` | Los resultados vienen **agrupados** por similitud (rapidfuzz ≥ 82) — un mismo producto de varias tiendas aparece en UN solo card con varios precios. |

## 2. Archivos del front que ya tocamos (para que sepas)

Modificamos parte del front para consumir el contrato nuevo. Si prefieres
reescribirlos desde cero, aquí está la lista:

- `src/lib/types.ts` — añadido `ProductsPage` y `images`/`description` en `ProductResult`.
- `src/lib/api.ts` — `listProducts` acepta `limit`/`offset` y devuelve `ProductsPage`; `getSuggestions()`; `getStores()`.
- `src/lib/useProducts.ts` — carga paginada (server) con `{total, ...}`.
- `src/lib/useStores.ts` — **NUEVO**: hook que trae `/api/stores` para el estado de tiendas.
- `src/components/SearchBar.tsx` — dropdown de sugerencias usando `/api/suggest` (debounce 300 ms).
- `src/components/StoreStatusBar.tsx` + `StoreIcon.tsx` — dinámicos (estado real de cada tienda; prop `active` para grisar las inactivas).
- `src/app/productos/page.tsx` — paginación **server** (antes paginaba en cliente el catálogo completo).
- `src/app/resultados/page.tsx` — typo corregido en el contador de resultados.

## 3. Pendiente tuyo (revisar / completar)

- El **modal de detalle** (`ProductModal.tsx`) ya usa `images`/`description` de
  `getProduct(id)`. Para Multimax/Daka la primera apertura puede tardar un poco
  (el backend va a buscar la descripción/galería a la página del producto y la
  cachea). Verifica que el "Cargando descripción..." se vea bien.
- Si el producto aún no tiene descripción, el modal muestra el mensaje "(El
  backend aún no expone la descripción...)" — **ajústalo** a un texto neutro.
- Confirma que `productos` (paginado) y `resultados` (agrupado) reciben bien el
  nuevo formato de respuesta.

## 4. Migración de base de datos (backend ya la dejó lista)

Las columnas `images` y `description` de la tabla `products` se agregan con una
migración Alembic (`backend/alembic/versions/0001_*.py`). El comando y el SQL
plano de respaldo están en `TAREAS_BACK.md`. No necesitas hacer nada desde el
front, pero ten en cuenta que hasta que se corra la migración en producción el
backend no responde `images`/`description`.
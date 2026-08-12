# PreciosNE — Comparador de Precios Nueva Esparta

---

## 1. Resumen del Proyecto

**PreciosNE** es un comparador de precios en línea diseñado para el estado **Nueva Esparta, Venezuela**. Su objetivo es permitir que los usuarios busquen un producto (electrodomésticos, tecnología, hogar, etc.) y vean en tiempo real cuál de las tiendas participantes lo ofrece al **mejor precio**, ahorrando tiempo y dinero al evitar recorrer físicamente cada establecimiento.

---

## 2. Problema que Resuelve

En Venezuela, los precios de un mismo producto pueden variar significativamente entre distintas tiendas, incluso dentro de un mismo estado. Factores como:

- Inflación y devaluación constante
- Diferencias en proveedores y costos de importación
- Promociones exclusivas por tienda
- Falta de plataformas centralizadas de comparación

Hacen que el consumidor tenga que visitar múltiples tiendas (físicas o virtuales) para encontrar el mejor precio. **PreciosNE** resuelve esto centralizando la información de precios de las principales tiendas de Nueva Esparta en un solo lugar.

---

## 3. Tiendas Participantes

| Tienda | Sucursales en Nueva Esparta | Rubro |
|--------|-----------------------------|-------|
| **Damasco** | Porlamar, La Asunción, Pampatar | Electrodomésticos, tecnología, hogar |
| **Multimax** | Margarita (Costa Azul), Porlamar (CC Ciudad Traki) | Electrodomésticos, tecnología, línea blanca |
| **Daka** | Porlamar, Margarita | Electrodomésticos, tecnología, electrónica |
| **Ivoo** | Porlamar, Margarita | Tecnología, electrodomésticos, entretenimiento |

*Nota: Aunque estas tiendas tienen presencia nacional, el proyecto se enfoca inicialmente en verificar disponibilidad y precios en el estado Nueva Esparta.*

---

## 4. Stack Tecnológico

### Backend — Render (Python)

| Componente | Tecnología |
|------------|-----------|
| Framework | **FastAPI** — API REST rápida, moderna, con documentación automática (Swagger) |
| ORM | **SQLAlchemy 2 (async)** — Mapeo objeto-relacional |
| DB | **Supabase (PostgreSQL)** — Base de datos relacional en la nube |
| Migraciones | **Alembic** — Control de versiones del esquema de base de datos |
| Scraping API | **httpx** — Cliente HTTP async (Damasco VTEX, Ivoo Magento GraphQL) |
| Scraping HTML | **httpx + BeautifulSoup (lxml)** — SSR de Multimax y Daka |
| Agrupación | **rapidfuzz** — agrupa el mismo producto entre tiendas |
| Async | **asyncio** — Operaciones concurrentes para scrapear múltiples tiendas |
| Scheduler | **cron-job.org → `POST /api/sync/catalog`** — actualización periódica del catálogo |
| Contenedor | **Docker** — imagen Python 3.12 desplegada en Render |

### Frontend — Vercel (Next.js)

| Componente | Tecnología |
|------------|-----------|
| Framework | **Next.js 14+** (App Router) — SSR + Static Generation |
| Estilos | **Tailwind CSS** — Diseño responsive rápido |
| Lenguaje | **TypeScript** — Tipado estático |
| Despliegue | **Vercel** — Integración continua desde Git |

---

## 5. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      USUARIO                                │
│              (Navegador web / móvil)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   FRONTEND (Vercel)                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ SearchBar    │  │ ProductCard  │  │ PriceTable        │  │
│  │ (búsqueda)   │  │ (por tienda) │  │ (comparativa)     │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
│                     Next.js + Tailwind                      │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS / REST
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (Render)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              FastAPI (Python 3.12)                   │  │
│  │  /api/search?q=nevera  →  busca + scrapea + agrupa   │  │
│  │  /api/products{e?limit=}  →  paginado                │  │
│  │  /api/products/{id}  →  historial + detalle (lazy)   │  │
│  │  /api/suggest?q= →  autocompletado                   │  │
│  │  /api/sync/catalog?store= →  sincronización (cron)   │  │
│  └──────────────────────────────────────────────────────┘  │
│          ┌───────────────┼───────────────┐                  │
│          ▼               ▼               ▼                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  DAMASCO   │  │ MULTIMAX   │  │   DAKA     │           │
│  │ (API VTEX) │  │ (httpx/BS4)│  │ (httpx/BS4)│           │
│  └────────────┘  └────────────┘  └────────────┘           │
│  ┌────────────┐                                            │
│  │   IVOO     │                                            │
│  │(GraphQL)   │                                            │
│  └────────────┘                                            │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           PostgreSQL (Supabase)                       │  │
│  │  products ── prices ── price_history ── stores       │  │
│  │  Caché de resultados para búsquedas repetidas        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de una búsqueda

1. El usuario escribe "nevera" en el frontend
2. Next.js hace un `GET /api/search?q=nevera` al backend
3. FastAPI busca en caché (PostgreSQL) si ya hay resultados recientes (< 1 hora)
4. Si no hay caché válida:
   - Scrapea Damasco (API directa, ~500ms)
   - Scrapea Multimax (Playwright, ~3s)
   - Scrapea Daka (Playwright, ~3s)
   - Scrapea Ivoo (Playwright, ~3s)
   - Todos en paralelo con asyncio
5. Normaliza los nombres de producto (ej. "Nevera Da+Co DCRT13 127L")
6. Agrupa productos similares por nombre y especificaciones
7. Ordena resultados por precio ascendente
8. Guarda en DB para caché
9. Devuelve JSON al frontend
10. Next.js renderiza las cards comparativas

---

## 6. Modelo de Datos

```sql
-- Productos únicos (normalizados)
CREATE TABLE products (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    brand       TEXT,
    category    TEXT,
    image_url   TEXT,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Precios por tienda
CREATE TABLE prices (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id  UUID REFERENCES products(id) ON DELETE CASCADE,
    store       TEXT NOT NULL CHECK (store IN ('damasco','multimax','daka','ivoo')),
    store_name  TEXT NOT NULL,
    price_usd   DECIMAL(10,2) NOT NULL,
    product_url TEXT,
    in_stock    BOOLEAN DEFAULT TRUE,
    scraped_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, store, scraped_at)
);

-- Historial de cambios de precio
CREATE TABLE price_history (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id  UUID REFERENCES products(id) ON DELETE CASCADE,
    store       TEXT NOT NULL,
    price_usd   DECIMAL(10,2) NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Tiendas scraping
CREATE TABLE stores (
    id          TEXT PRIMARY KEY,   -- 'damasco', 'multimax', etc.
    name        TEXT NOT NULL,
    website     TEXT NOT NULL,
    active      BOOLEAN DEFAULT TRUE,
    last_scrape TIMESTAMP
);
```

---

## 7. Scrapers — Estrategia Detallada

### 7.1 Damasco (API VTEX) — Sin Playwright

Damasco usa **VTEX** como plataforma de e-commerce. VTEX expone una API pública de búsqueda:

```
GET https://damasco.vtexcommercestable.com.br/api/catalog_system/pub/products/search
  ?q={término}
  &_from=0
  &_to=23
  &O=OrderByPriceASC
```

**Headers necesarios:**
```
Accept: application/json
```

**Respuesta JSON** con campos:
- `productName`: "Nevera Damasco DCRT13 127L"
- `productReference`: "D0006031"
- `items[0].sellers[0].commertialOffer.Price`: 288.00
- `items[0].sellers[0].commertialOffer.ListPrice`: 320.00
- `items[0].images[0].imageUrl`: "https://..."
- `link`: "/nevera-2-ptas-127l-da-co-dcrt13/p"
- `brand`: "DAMASCO"

**Ventajas:** Rápido, sin JavaScript, sin bloqueo, datos estructurados.

### 7.2 Multimax (SSR via httpx + BeautifulSoup)

Multimax renderiza en servidor (Astro). Estrategia:

1. `GET https://multimax.com.ve/buscar?q={query}&page={n}` con httpx
2. Parsear con BeautifulSoup los `span[class*=tabular-nums]` (precio) y los
   `a[href*="/producto/"][title]` (nombre/enlace)
3. Extraer: nombre, precio (formato venezolano `1.000,00`), imagen, enlace
4. Para el catálogo usa las URLs de categoría de `CATALOG_URLS`
5. El detalle (`description` + galería) se obtiene bajo demanda:
   `fetch_detail()` visita la página del producto y extrae el `meta[description]`
   y las imágenes `cdn.multimax.com.ve/medios/productos/*-medium.webp`

### 7.3 Daka (SSR via httpx + BeautifulSoup)

Daka usa rutas como:
- `https://tiendasdaka.com/ve/store/electrodomesticos`
- `https://tiendasdaka.com/ve/results/{slug}?q={query}&page={n}`

Estrategia:
1. HTTP GET con httpx (SSR) + BeautifulSoup sobre `[data-testid="product-wrapper"]`
2. Extraer nombre, marca, precio (USD y Bs), imagen (`/_next/image`), enlace
3. Manejar paginación si es necesario
4. El detalle se obtiene bajo demanda con `fetch_detail()`: la sección
   "Descripción" de la página y las imágenes de producto
   (`*.cloudfront.net/<SKU>_<N>-<hash>.webp`)

### 7.4 Ivoo (Magento 2 GraphQL)

Ivoo expone GraphQL público en `nuweapp.com/graphql`. Estrategia:

1. `POST nuweapp.com/graphql` con la query `searchProducts` (o `catalogProducts`)
2. Campos: `name`, `price_range.minimum_price`, `image`, `media_gallery`,
   `description.html`, `url_key`, `stock_status`
3. Sin navegador, respuestas JSON estructuradas

---

## 8. API Endpoints — Especificación

### `GET /api/search`

Busca un producto en todas las tiendas.

**Parámetros:**
| Query | Tipo | Descripción |
|-------|------|-------------|
| `q` | string (obligatorio) | Término de búsqueda |
| `force_refresh` | boolean (opcional) | Ignorar caché y forzar scraping |

**Respuesta:**
```json
{
  "query": "nevera",
  "total_results": 24,
  "products": [
    {
      "name": "Nevera Damasco DCRT13 127L",
      "brand": "DAMASCO",
      "image_url": "https://...",
      "best_price": {
        "store": "damasco",
        "price_usd": 288.00,
        "product_url": "https://damascovzla.com/nevera-2-ptas-127l-da-co-dcrt13/p",
        "in_stock": true
      },
      "prices": [
        {
          "store": "damasco",
          "store_name": "Damasco",
          "price_usd": 288.00,
          "product_url": "...",
          "in_stock": true
        },
        {
          "store": "multimax",
          "store_name": "Multimax",
          "price_usd": 299.99,
          "product_url": "...",
          "in_stock": true
        },
        {
          "store": "daka",
          "store_name": "Daka",
          "price_usd": 305.00,
          "product_url": "...",
          "in_stock": false
        }
      ],
      "price_difference_percent": 5.9
    }
  ],
  "cached": false,
  "scraped_at": "2026-06-27T10:30:00Z"
}
```

### `GET /api/products/{id}`

Historial de precios de un producto específico.

### `GET /api/stores`

Lista las tiendas configuradas y su estado.

### `GET /api/suggest`

Autocompletado: `?q=nevera` → `{"suggestions": ["NEVERA DAMASCO ...", ...]}` (10).

### `GET /api/products` (paginado)

`?q=&store=&limit=50&offset=0` → `{ "total": 123, "page": 1, "page_size": 50, "products": [...] }`.

> Todos los `ProductOut` incluyen `images: string[]` y `description` (los de
> Multimax/Daka se llenan bajo demanda al abrir `GET /api/products/{id}`).
> Los resultados de `/api/search` agrupan por similitud (rapidfuzz ≥ 82) el
> mismo producto entre tiendas.

---

## 9. Frontend — Componentes

### Página principal (`/`)
- `SearchBar`: Input de búsqueda con debounce y autocompletado
- `StoreStatusBar`: Indicadores de qué tiendas están disponibles

### Resultados (`/resultados?q=nevera`)
- `ProductGrid`: Grid de productos encontrados
- `ProductCard`: Card individual con:
  - Imagen del producto
  - Nombre
  - Marca
  - Tabla de precios por tienda (ordenados de menor a mayor)
  - Badge "Mejor precio" 🏆
  - Diferencia porcentual vs el más caro
- `Filters`: Filtros por tienda, rango de precio, marca

### Componentes reutilizables
- `PriceBadge`: Muestra precio con formato USD
- `StoreIcon`: Logo/ícono de cada tienda
- `LoadingSkeleton`: Esqueleto de carga mientras se scrapea
- `ErrorState`: Mensaje si una tienda no responde

---

## 10. Cacheo y Actualización

| Estrategia | Detalle |
|------------|---------|
| **TTL de caché** | 1 hora para resultados de búsqueda |
| **Actualización programada** | Cada 6 horas, el scheduler actualiza precios de productos populares |
| **Forzar actualización** | Botón "Actualizar precios" en frontend |
| **Límite de scraping** | Máximo 1 solicitud por tienda cada 5 minutos para evitar bloqueo |

---

## 11. Consideraciones Técnicas

### Anti-bloqueo en scraping
- Rotación de User-Agent
- Retry con backoff exponencial (3 intentos)
- Timeout de 10s por solicitud
- Respetar `robots.txt`
- Headers de navegador real

### Normalización de productos
Usar similitud de texto (fuzzy matching) para agrupar el mismo producto en distintas tiendas:
- Ej: "Nevera Damasco DCRT13 127L" ≈ "Nevera Da+Co 127L DCRT13"
- Algoritmo: `difflib.SequenceMatcher` o `rapidfuzz`

### Rendimiento
- Scraping concurrente con `asyncio.gather()`
- Timeout total por búsqueda: 15s
- Si una tienda falla, mostrar "No disponible" sin bloquear las demás

---

## 12. Despliegue

### Render (Backend)
```yaml
# render.yaml (deploy por Git)
services:
  - type: web
    name: precios-ne
    runtime: docker
    rootDir: backend
    plan: free
    healthCheckPath: /docs
```

### Vercel (Frontend)
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs"
}
```

Variables de entorno:
- `DATABASE_URL` — Conexión a Supabase (PostgreSQL) con `?ssl=require`
- `CORS_ORIGINS` — Orígenes permitidos separados por coma
- `NEXT_PUBLIC_API_URL` — URL pública del backend en Render

---

## 13. Posibles Expansiones Futuras

- [ ] Agregar más tiendas (Traki, Farmatodo, EPA, etc.)
- [ ] Alertas de precios (notificación cuando baje de X)
- [ ] Historial gráfico de precios en el tiempo
- [ ] Soporte para otras monedas (Bs., EUR)
- [ ] App móvil (React Native / Flutter)
- [ ] Modo oscuro
- [ ] Comparación por código de barras / SKU
- [ ] API pública para desarrolladores

---

## 14. Roadmap

| Fase | Descripción | Estado |
|------|-------------|--------|
| **Fase 1** | Backend: modelo DB + scraper Damasco + endpoint search | ✅ Completado |
| **Fase 2** | Scrapers Multimax, Daka, Ivoo | ✅ Completado |
| **Fase 3** | Frontend Next.js: página principal + resultados | ✅ Completado |
| **Fase 4** | Scheduler (cron → sync/catalog) + caché + refinamientos + deploy | ✅ Completado |
| **Fase 5** | Pruebas con usuarios en Nueva Esparta | ⏳ Pendiente |

---

## 15. Autores

Proyecto desarrollado como iniciativa personal para facilitar el acceso a información de precios en el estado Nueva Esparta, Venezuela.

---

*Documento generado el 27 de junio de 2026.*

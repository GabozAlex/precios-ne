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

### Backend — Railway (Python)

| Componente | Tecnología |
|------------|-----------|
| Framework | **FastAPI** — API REST rápida, moderna, con documentación automática (Swagger) |
| ORM | **SQLAlchemy** — Mapeo objeto-relacional para PostgreSQL |
| DB | **PostgreSQL** — Base de datos relacional en Railway |
| Scraping API | **httpx** — Cliente HTTP async para APIs REST (Damasco) |
| Scraping Dinámico | **Playwright** — Navegador headless para sitios con JavaScript (Multimax, Daka, Ivoo) |
| Async | **asyncio** — Operaciones concurrentes para scrapear múltiples tiendas |
| Scheduler | **APScheduler** — Actualización periódica automática de precios |
| Migraciones | **Alembic** — Control de versiones del esquema de base de datos |
| Contenedor | **Docker** — Imagen con Python + Chromium para Playwright |

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
│                    BACKEND (Railway)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              FastAPI (Python 3.12)                   │  │
│  │  /api/search?q=nevera  →  busca + scrapea + ordena  │  │
│  │  /api/products/{id}   →  historial de precios       │  │
│  │  /api/refresh         →  fuerza actualización       │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│          ┌───────────────┼───────────────┐                  │
│          ▼               ▼               ▼                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  DAMASCO   │  │ MULTIMAX   │  │   DAKA     │           │
│  │ (API VTEX) │  │(Playwright)│  │(Playwright)│           │
│  └────────────┘  └────────────┘  └────────────┘           │
│  ┌────────────┐                                            │
│  │   IVOO     │                                            │
│  │(Playwright)│                                            │
│  └────────────┘                                            │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              PostgreSQL (Railway)                    │  │
│  │  products ── price_history ── stores                 │  │
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

### 7.2 Multimax (Playwright)

Multimax usa un sitio con renderizado híbrido. La estrategia:

1. Playwright navega a `https://multimax.com.ve/`
2. Espera que cargue el DOM completo
3. Extrae todos los productos visibles de la página principal
4. Para buscar un producto específico, usa la URL de categorías:
   - `https://multimax.com.ve/categoria-producto/refrigeracion/`
   - `https://multimax.com.ve/categoria-producto/lavado/`
5. Extrae: nombre, precio (selector `.price`), imagen, enlace
6. Si el sitio carga vía JavaScript, esperar por `networkidle`

### 7.3 Daka (Playwright)

Daka tiene rutas como:
- `https://daka.tiendasdaka.com/ve/store/electrodomesticos`
- `https://daka.tiendasdaka.com/ve/store/search?q=nevera`

Estrategia:
1. Navegar a URL de búsqueda
2. Esperar que carguen los productos (pueden tardar por JS)
3. Extraer nombre, precio (USD y Bs), imagen, enlace
4. Manejar paginación si es necesario

### 7.4 Ivoo (Playwright)

Ivoo es una SPA (Single Page Application). Estrategia:
1. Navegar a `https://www.ivoo.com/searchpage`
2. Esperar que la app React renderice completamente
3. Usar selectores para encontrar productos
4. Extraer datos

**Alternativa:** Revisar si la app móvil de Ivoo expone una API que podamos usar directamente (endpoints como `api.ivoo.com`).

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

### Railway (Backend)
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y chromium chromium-driver
RUN pip install -r requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
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
- `DATABASE_URL` — Conexión a PostgreSQL en Railway
- `NEXT_PUBLIC_API_URL` — URL del backend en Railway

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
| **Fase 1** | Backend: modelo DB + scraper Damasco + endpoint search | ⏳ Pendiente |
| **Fase 2** | Scrapers Multimax, Daka, Ivoo con Playwright | ⏳ Pendiente |
| **Fase 3** | Frontend Next.js: página principal + resultados | ⏳ Pendiente |
| **Fase 4** | Scheduler + caché + refinamientos + deploy | ⏳ Pendiente |
| **Fase 5** | Pruebas con usuarios en Nueva Esparta | ⏳ Pendiente |

---

## 15. Autores

Proyecto desarrollado como iniciativa personal para facilitar el acceso a información de precios en el estado Nueva Esparta, Venezuela.

---

*Documento generado el 27 de junio de 2026.*

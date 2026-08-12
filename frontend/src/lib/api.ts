const API_URL = 'https://precios-ne.onrender.com'

export interface PriceInfo {
  store: string
  store_name: string
  price_usd: number | null
  product_url: string | null
  in_stock: boolean
  scraped_at: string | null
}

export interface ProductResult {
  id: string
  name: string
  brand: string | null
  category: string | null
  image_url: string | null
  best_price: PriceInfo | null
  prices: PriceInfo[]
}

export interface SearchResponse {
  query: string
  total_results: number
  products: ProductResult[]
  cached: boolean
  scraped_at: string | null
}

export async function searchProducts(
  q: string,
  forceRefresh = false
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q })
  if (forceRefresh) params.set('force_refresh', 'true')

  const res = await fetch(`${API_URL}/api/search?${params}`)

  if (!res.ok) {
    throw new Error(`Error ${res.status}: ${res.statusText}`)
  }

  return res.json()
}

export async function listProducts(q = '', store = ''): Promise<ProductResult[]> {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  if (store) params.set('store', store)
  const query = params.toString()
  const res = await fetch(`${API_URL}/api/products${query ? `?${query}` : ''}`)
  if (!res.ok) throw new Error(`Error ${res.status}`)
  return res.json()
}

export async function getProduct(id: string) {
  const res = await fetch(`${API_URL}/api/products/${id}`)
  if (!res.ok) throw new Error(`Error ${res.status}`)
  return res.json()
}

export async function getStores() {
  const res = await fetch(`${API_URL}/api/stores`)
  if (!res.ok) throw new Error(`Error ${res.status}`)
  return res.json()
}

export async function syncCatalog() {
  const res = await fetch(`${API_URL}/api/sync/catalog`, {
    method: 'POST',
  })
  if (!res.ok) throw new Error(`Error ${res.status}`)
  return res.json()
}

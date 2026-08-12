import {
  SearchResponse,
  ProductResult,
  StoreInfo,
  CatalogSyncResponse,
  PriceInfo,
} from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://precios-ne.onrender.com'

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })

  if (!res.ok) {
    let message = `Error ${res.status}: ${res.statusText}`
    try {
      const data = await res.json()
      if (data?.detail) message = data.detail
    } catch {}
    throw new Error(message)
  }

  if (res.status === 204 || res.headers.get('content-length') === '0') {
    return null as T
  }

  return res.json()
}

export async function searchProducts(
  q: string,
  forceRefresh = false,
  store = '',
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q })
  if (forceRefresh) params.set('force_refresh', 'true')
  if (store) params.set('store', store)

  return apiFetch<SearchResponse>(`/api/search?${params}`)
}

export async function listProducts(q = '', store = ''): Promise<ProductResult[]> {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  if (store) params.set('store', store)
  const query = params.toString()

  return apiFetch<ProductResult[]>(`/api/products${query ? `?${query}` : ''}`)
}

export async function getProduct(id: string): Promise<{
  id: string
  name: string
  brand: string | null
  category: string | null
  image_url: string | null
  created_at: string | null
  current_prices: PriceInfo[]
  price_history: { store: string; price_usd: number | null; recorded_at: string | null }[]
}> {
  return apiFetch(`/api/products/${id}`)
}

export async function getStores(): Promise<StoreInfo[]> {
  return apiFetch<StoreInfo[]>('/api/stores')
}

export async function syncCatalog(): Promise<CatalogSyncResponse> {
  return apiFetch<CatalogSyncResponse>('/api/sync/catalog', { method: 'POST' })
}

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

export interface StoreInfo {
  id: string
  name: string
  website: string
  active: boolean
  last_scrape: string | null
}

export interface CatalogSyncResponse {
  message: string
  timestamp: string
  stores: Record<string, number>
  total_products: number
}

export type StoreKey = 'damasco' | 'multimax' | 'daka' | 'ivoo'

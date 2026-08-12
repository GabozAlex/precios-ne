import { useState, useCallback } from 'react'
import { listProducts } from '@/lib/api'
import type { ProductResult } from '@/lib/types'

interface ProductsState {
  products: ProductResult[]
  loading: boolean
  error: string | null
}

export function useProducts() {
  const [state, setState] = useState<ProductsState>({
    products: [],
    loading: false,
    error: null,
  })

  const load = useCallback(async (q = '', store = '') => {
    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const products = await listProducts(q, store)
      setState({ products, loading: false, error: null })
    } catch (err) {
      setState({
        products: [],
        loading: false,
        error: err instanceof Error ? err.message : 'Error al cargar productos',
      })
    }
  }, [])

  return { ...state, load }
}

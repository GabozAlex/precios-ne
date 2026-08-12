import { useState, useCallback, useRef } from 'react'
import { listProducts } from '@/lib/api'
import type { ProductResult } from '@/lib/types'

interface ProductsState {
  products: ProductResult[]
  total: number
  loading: boolean
  error: string | null
}

export function useProducts() {
  const [state, setState] = useState<ProductsState>({
    products: [],
    total: 0,
    loading: false,
    error: null,
  })
  const controllerRef = useRef<AbortController | null>(null)

  const load = useCallback(async (q = '', store = '', limit = 24, offset = 0) => {
    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller

    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const page = await listProducts(q, store, limit, offset, controller.signal)
      if (controller.signal.aborted) return
      setState({
        products: page.products,
        total: page.total,
        loading: false,
        error: null,
      })
    } catch (err) {
      if (controller.signal.aborted) return
      setState({
        products: [],
        total: 0,
        loading: false,
        error: err instanceof Error ? err.message : 'Error al cargar productos',
      })
    }
  }, [])

  return { ...state, load }
}
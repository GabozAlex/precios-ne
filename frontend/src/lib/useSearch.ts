import { useState, useCallback, useRef } from 'react'
import { searchProducts } from '@/lib/api'
import type { SearchResponse } from '@/lib/types'

interface SearchState {
  data: SearchResponse | null
  loading: boolean
  error: string | null
}

export function useSearch() {
  const [state, setState] = useState<SearchState>({
    data: null,
    loading: false,
    error: null,
  })
  const controllerRef = useRef<AbortController | null>(null)

  const search = useCallback(async (q: string, forceRefresh = false) => {
    if (!q) return

    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller

    setState((prev) => ({
      data: forceRefresh && prev.data?.query === q ? prev.data : null,
      loading: true,
      error: null,
    }))

    try {
      const data = await searchProducts(q, forceRefresh, '', controller.signal)
      if (controller.signal.aborted) return
      setState({ data, loading: false, error: null })
    } catch (err) {
      if (controller.signal.aborted) return
      setState((prev) => ({
        data: prev.data,
        loading: false,
        error: err instanceof Error ? err.message : 'Error inesperado',
      }))
    }
  }, [])

  return { ...state, search }
}
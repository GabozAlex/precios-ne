import { useState, useCallback } from 'react'
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

  const search = useCallback(async (q: string, forceRefresh = false) => {
    if (!q) return
    setState({ data: null, loading: true, error: null })
    try {
      const data = await searchProducts(q, forceRefresh)
      setState({ data, loading: false, error: null })
    } catch (err) {
      setState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Error inesperado',
      })
    }
  }, [])

  return { ...state, search }
}

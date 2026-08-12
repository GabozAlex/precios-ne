import { useState, useEffect, useCallback } from 'react'
import { getStores } from '@/lib/api'
import type { StoreInfo } from '@/lib/types'

interface StoresState {
  stores: StoreInfo[]
  loading: boolean
  error: string | null
}

export function useStores() {
  const [state, setState] = useState<StoresState>({
    stores: [],
    loading: true,
    error: null,
  })

  const load = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const stores = await getStores()
      setState({ stores, loading: false, error: null })
    } catch (err) {
      setState({
        stores: [],
        loading: false,
        error: err instanceof Error ? err.message : 'Error al cargar tiendas',
      })
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return { ...state, load }
}
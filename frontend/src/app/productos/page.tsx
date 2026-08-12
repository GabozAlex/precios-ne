'use client'

import { useEffect, useState, Suspense } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { useProducts } from '@/lib/useProducts'
import { syncCatalog } from '@/lib/api'
import ProductCard from '@/components/ProductCard'
import LoadingSkeleton from '@/components/LoadingSkeleton'
import ErrorState from '@/components/ErrorState'
import { STORES, getStoreMeta } from '@/lib/stores'
import type { StoreKey } from '@/lib/types'

const PAGE_SIZE = 24

function ProductosContent() {
  const searchParams = useSearchParams()
  const storeParam = (searchParams.get('store') || '') as StoreKey
  const { products, total, loading, error, load } = useProducts()
  const [q, setQ] = useState('')
  const [debouncedQ, setDebouncedQ] = useState('')
  const [page, setPage] = useState(1)
  const [syncing, setSyncing] = useState(false)
  const [syncMsg, setSyncMsg] = useState<string | null>(null)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQ(q), 300)
    return () => clearTimeout(timer)
  }, [q])

  useEffect(() => {
    setPage(1)
  }, [storeParam])

  useEffect(() => {
    load(debouncedQ.trim(), storeParam, PAGE_SIZE, (page - 1) * PAGE_SIZE)
  }, [debouncedQ, storeParam, page, load])

  const handleSync = async () => {
    setSyncing(true)
    setSyncMsg(null)
    try {
      const res = await syncCatalog()
      const detail = Object.entries(res.stores || {})
        .map(([k, v]) => `${getStoreMeta(k).label}: ${v}`)
        .join(', ')
      setSyncMsg(`Catálogo actualizado: ${res.total_products} productos (${detail})`)
    } catch (err) {
      setSyncMsg(`Error al actualizar: ${err instanceof Error ? err.message : 'desconocido'}`)
    } finally {
      setSyncing(false)
      load(q.trim(), storeParam, PAGE_SIZE, (page - 1) * PAGE_SIZE)
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <Link href="/" className="text-blue-600 hover:underline text-sm">
            &larr; Inicio
          </Link>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {syncing ? 'Actualizando…' : 'Actualizar ahora'}
          </button>
        </div>
        <h2 className="text-2xl font-bold mt-2">
          {storeParam
            ? `Productos de ${STORES[storeParam]?.label || storeParam}`
            : 'Todos los productos'}
        </h2>
        {syncMsg && <p className="text-sm text-gray-600 mt-2">{syncMsg}</p>}
      </div>

      <input
        type="search"
        placeholder="Filtrar productos..."
        value={q}
        onChange={(e) => {
          setQ(e.target.value)
          setPage(1)
        }}
        className="w-full border border-gray-300 rounded-lg px-4 py-2 mb-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
      />

      {loading && <LoadingSkeleton count={6} variant="grid" />}

      {error && <ErrorState message={error} onRetry={() => load(q.trim(), storeParam, PAGE_SIZE, (page - 1) * PAGE_SIZE)} />}

      {!loading && !error && (
        <>
          <p className="text-sm text-gray-500 mb-4">
            {total} producto{total !== 1 ? 's' : ''}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} compact />
            ))}
          </div>
          {total === 0 && (
            <div className="text-center py-16">
              <p className="text-gray-500">
                {q
                  ? `No hay productos que coincidan con "${q}"`
                  : 'No hay productos en la base de datos. Realizá una búsqueda o presioná "Actualizar ahora".'}
              </p>
            </div>
          )}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <button
                onClick={() => setPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm disabled:opacity-40"
              >
                &larr; Anterior
              </button>
              <span className="text-sm text-gray-600">
                Página {currentPage} de {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm disabled:opacity-40"
              >
                Siguiente &rarr;
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default function ProductosPage() {
  return (
    <div>
      <Suspense fallback={
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mt-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 animate-pulse"
            >
              <div className="flex gap-3">
                <div className="w-16 h-16 bg-gray-200 rounded-lg" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-3/4" />
                  <div className="h-3 bg-gray-200 rounded w-1/3" />
                </div>
              </div>
            </div>
          ))}
        </div>
      }>
        <ProductosContent />
      </Suspense>
    </div>
  )
}

'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useSearch } from '@/lib/useSearch'
import type { ProductResult } from '@/lib/types'
import ProductCard from '@/components/ProductCard'
import ProductModal from '@/components/ProductModal'
import LoadingSkeleton from '@/components/LoadingSkeleton'
import ErrorState from '@/components/ErrorState'

function ResultadosContent() {
  const searchParams = useSearchParams()
  const q = searchParams.get('q') || ''
  const { data, loading, error, search } = useSearch()
  const products = data?.products ?? []
  const [modalProduct, setModalProduct] = useState<ProductResult | null>(null)

  useEffect(() => {
    if (q && !data && !loading) {
      search(q)
    }
  }, [q, data, loading, search])

  if (!q) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500">Ingresa un término de búsqueda</p>
        <Link href="/" className="text-blue-600 hover:underline mt-2 inline-block">
          Volver
        </Link>
      </div>
    )
  }

  const isLoadingInitial = (loading || !data) && products.length === 0

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link href="/" className="text-blue-600 hover:underline text-sm">
            &larr; Nueva búsqueda
          </Link>
          <h2 className="text-2xl font-bold mt-2">
            Resultados para: <span className="text-blue-600">{q}</span>
          </h2>
        </div>
        <button
          onClick={() => search(q, true)}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium underline"
        >
          Actualizar precios
        </button>
      </div>

      {isLoadingInitial && <LoadingSkeleton count={3} variant="list" />}

      {!isLoadingInitial && error && <ErrorState message={error} onRetry={() => search(q)} />}

      {!isLoadingInitial && !error && (
        <>
          <p className="text-sm text-gray-500 mb-4">
            {products.length} producto{products.length !== 1 ? 's' : ''} encontrado
            {products.length !== 1 ? 's' : ''}
            {data?.cached ? ' (resultados en caché)' : ''}
          </p>
          {data?.scraped_at && (
            <p className="text-xs text-gray-400 mb-4">
              Actualizado: {new Date(data.scraped_at).toLocaleString('es-VE')}
            </p>
          )}
          {products.length === 0 ? (
            <div className="text-center py-16">
              <p className="text-gray-500">
                No se encontraron productos para &quot;{q}&quot;
              </p>
            </div>
          ) : (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {products.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              onViewDetails={() => setModalProduct(product)}
            />
          ))}
        </div>
      )}

      {modalProduct && (
        <ProductModal product={modalProduct} onClose={() => setModalProduct(null)} />
      )}
    </>
      )}
    </div>
  )
}

export default function ResultadosPage() {
  return (
    <Suspense fallback={
      <div className="space-y-4">
        <div className="mb-6 flex items-center justify-between">
          <div className="h-5 bg-gray-200 rounded w-40 animate-pulse" />
        </div>
        <LoadingSkeleton count={3} variant="list" />
      </div>
    }>
      <ResultadosContent />
    </Suspense>
  )
}

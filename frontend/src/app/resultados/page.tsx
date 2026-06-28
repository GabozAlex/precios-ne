'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { searchProducts, type ProductResult } from '@/lib/api'

const STORE_COLORS: Record<string, string> = {
  damasco: 'bg-store-damasco',
  multimax: 'bg-store-multimax',
  daka: 'bg-store-daka',
  ivoo: 'bg-store-ivoo',
}

const STORE_LABELS: Record<string, string> = {
  damasco: 'Damasco',
  multimax: 'Multimax',
  daka: 'Daka',
  ivoo: 'Ivoo',
}

function formatPrice(price: number | null) {
  if (price === null) return '—'
  return `$${price.toFixed(2)}`
}

function ProductCard({ product }: { product: ProductResult }) {
  const sorted = [...product.prices].sort(
    (a, b) => (a.price_usd ?? Infinity) - (b.price_usd ?? Infinity)
  )
  const bestPrice = sorted[0]

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 relative">
      {bestPrice && (
        <span className="absolute top-3 right-3 text-[10px] bg-green-500 text-white px-2 py-0.5 rounded-full font-bold uppercase tracking-wide">
          Mejor precio
        </span>
      )}
      <div className="flex gap-4">
        {product.image_url && (
          <img
            src={product.image_url}
            alt={product.name}
            className="w-24 h-24 object-contain rounded-lg bg-gray-50"
          />
        )}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-lg truncate">{product.name}</h3>
          {product.brand && (
            <p className="text-sm text-gray-500">{product.brand}</p>
          )}
          {product.category && (
            <p className="text-xs text-gray-400 mt-1">{product.category}</p>
          )}
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {sorted.map((price) => (
          <div
            key={`${price.store}-${price.price_usd}`}
            className={`flex items-center justify-between p-3 rounded-lg ${
              price === bestPrice
                ? 'bg-green-50 ring-1 ring-green-300'
                : 'bg-gray-50'
            }`}
          >
            <div className="flex items-center gap-2">
              <span
                className={`inline-block w-3 h-3 rounded-full ${
                  STORE_COLORS[price.store] || 'bg-gray-400'
                }`}
              />
              <span className="font-medium text-sm">
                {STORE_LABELS[price.store] || price.store_name}
              </span>
              {price === bestPrice && (
                <span className="text-[10px] bg-green-500 text-white px-2 py-0.5 rounded-full font-bold uppercase tracking-wide">
                  Mejor precio
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              <span className="font-bold text-lg">
                {formatPrice(price.price_usd)}
              </span>
              {price.product_url ? (
                <a
                  href={price.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:underline"
                >
                  Ir
                </a>
              ) : (
                <span className="text-xs text-gray-400">N/D</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function ResultadosPageWrapper() {
  return (
    <Suspense fallback={
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 animate-pulse">
            <div className="flex gap-4">
              <div className="w-24 h-24 bg-gray-200 rounded-lg" />
              <div className="flex-1 space-y-2">
                <div className="h-5 bg-gray-200 rounded w-3/4" />
                <div className="h-4 bg-gray-200 rounded w-1/4" />
              </div>
            </div>
          </div>
        ))}
      </div>
    }>
      <ResultadosPage />
    </Suspense>
  )
}

function ResultadosPage() {
  const searchParams = useSearchParams()
  const q = searchParams.get('q') || ''
  const [products, setProducts] = useState<ProductResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!q) return
    setLoading(true)
    setError(null)
    searchProducts(q)
      .then((res) => {
        const sorted = [...res.products].sort(
          (a, b) => (a.best_price?.price_usd ?? Infinity) - (b.best_price?.price_usd ?? Infinity)
        )
        setProducts(sorted)
      })
      .catch((err) => {
        setError(err.message)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [q])

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
        <Link href="/productos" className="text-blue-600 hover:underline text-sm">
          Ver todos &rarr;
        </Link>
      </div>

      {loading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 animate-pulse"
            >
              <div className="flex gap-4">
                <div className="w-24 h-24 bg-gray-200 rounded-lg" />
                <div className="flex-1 space-y-2">
                  <div className="h-5 bg-gray-200 rounded w-3/4" />
                  <div className="h-4 bg-gray-200 rounded w-1/4" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="text-center py-16">
          <p className="text-red-600">Error: {error}</p>
        </div>
      )}

      {!loading && !error && (
        <>
          <p className="text-sm text-gray-500 mb-4">
            {products.length} producto{products.length !== 1 ? 's' : ''} encontrado{products.length !== 1 ? 's' : ''}
          </p>
          <div className="space-y-4">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
          {products.length === 0 && (
            <div className="text-center py-16">
              <p className="text-gray-500">
                No se encontraron productos para &quot;{q}&quot;
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}

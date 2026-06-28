'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { listProducts, type ProductResult } from '@/lib/api'

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
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 relative">
      {bestPrice && (
        <span className="absolute top-2 right-2 text-[10px] bg-green-500 text-white px-2 py-0.5 rounded-full font-bold uppercase tracking-wide">
          Mejor precio
        </span>
      )}
      <div className="flex gap-3">
        {product.image_url && (
          <img
            src={product.image_url}
            alt={product.name}
            className="w-16 h-16 object-contain rounded-lg bg-gray-50 shrink-0"
          />
        )}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-sm truncate">{product.name}</h3>
          {product.brand && (
            <p className="text-xs text-gray-500">{product.brand}</p>
          )}
        </div>
      </div>

      <div className="mt-3 space-y-1.5">
        {sorted.slice(0, 3).map((price) => (
          <div
            key={`${price.store}-${price.price_usd}`}
            className={`flex items-center justify-between p-2 rounded-md ${
              price === bestPrice ? 'bg-green-50 ring-1 ring-green-300' : 'bg-gray-50'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <span
                className={`inline-block w-2.5 h-2.5 rounded-full ${
                  STORE_COLORS[price.store] || 'bg-gray-400'
                }`}
              />
              <span className="text-xs font-medium">
                {STORE_LABELS[price.store] || price.store_name}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm">
                {formatPrice(price.price_usd)}
              </span>
              {price.product_url && (
                <a
                  href={price.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[10px] text-blue-600 hover:underline"
                >
                  Ir
                </a>
              )}
            </div>
          </div>
        ))}
        {sorted.length > 3 && (
          <p className="text-[10px] text-gray-400 text-center">
            +{sorted.length - 3} tienda{sorted.length - 3 !== 1 ? 's' : ''} más
          </p>
        )}
      </div>
    </div>
  )
}

export default function ProductosPage() {
  const [products, setProducts] = useState<ProductResult[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    setLoading(true)
    listProducts()
      .then(setProducts)
      .catch(() => setProducts([]))
      .finally(() => setLoading(false))
  }, [])

  const filtered = filter
    ? products.filter((p) => p.name.toLowerCase().includes(filter.toLowerCase()))
    : products

  return (
    <div>
      <div className="mb-6">
        <Link href="/" className="text-blue-600 hover:underline text-sm">
          &larr; Inicio
        </Link>
        <h2 className="text-2xl font-bold mt-2">Todos los productos</h2>
      </div>

      <input
        type="text"
        placeholder="Filtrar productos..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="w-full border border-gray-300 rounded-lg px-4 py-2 mb-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
      />

      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 animate-pulse">
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
      )}

      {!loading && (
        <>
          <p className="text-sm text-gray-500 mb-4">
            {filtered.length} producto{filtered.length !== 1 ? 's' : ''}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {filtered.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
          {filtered.length === 0 && (
            <div className="text-center py-16">
              <p className="text-gray-500">
                {filter
                  ? `No hay productos que coincidan con "${filter}"`
                  : 'No hay productos en la base de datos. Realizá una búsqueda primero.'}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}

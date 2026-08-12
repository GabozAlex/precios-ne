'use client'

import { useEffect, useState } from 'react'
import Image from 'next/image'
import PriceRow, { formatPriceRow } from '@/components/PriceRow'
import type { ProductResult } from '@/lib/types'
import { getProduct } from '@/lib/api'
import { getStoreMeta } from '@/lib/stores'

interface ProductDetail {
  id: string
  name: string
  brand: string | null
  category: string | null
  image_url: string | null
  description?: string | null
  images?: string[]
  current_prices: ProductResult['prices']
  price_history: { store: string; price_usd: number | null; recorded_at: string | null }[]
}

interface ProductModalProps {
  product: ProductResult
  onClose: () => void
}

export default function ProductModal({ product, onClose }: ProductModalProps) {
  const [detail, setDetail] = useState<ProductDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const sorted = [...product.prices].sort(
    (a, b) => (a.price_usd ?? Infinity) - (b.price_usd ?? Infinity),
  )
  const best = sorted[0]

  useEffect(() => {
    const fetchDetail = async () => {
      setLoading(true)
      try {
        const res = await getProduct(product.id)
        setDetail({
          ...res,
          image_url: res.image_url ?? product.image_url,
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error')
      } finally {
        setLoading(false)
      }
    }
    fetchDetail()
  }, [product.id, product.image_url])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  const history = detail?.price_history ?? []
  const historyByStore: Record<string, { date: string; price: number | null }[]> = {}
  history.forEach((h) => {
    const key = h.store
    if (!historyByStore[key]) historyByStore[key] = []
    historyByStore[key].push({ date: h.recorded_at ?? '', price: h.price_usd ?? null })
  })

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-2xl font-bold">{product.name}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-700 text-xl font-bold leading-none"
            aria-label="Cerrar"
          >
            ×
          </button>
        </div>

        <div className="p-6">
          {product.brand && (
            <p className="text-sm text-gray-500 mb-1">{product.brand}</p>
          )}
          {product.category && (
            <p className="text-xs text-gray-400 mb-3">{product.category}</p>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              {product.image_url && (
                <div className="relative aspect-square rounded-lg bg-gray-50 overflow-hidden">
                  <Image
                    src={product.image_url}
                    alt={product.name}
                    fill
                    className="object-contain p-2"
                    unoptimized
                  />
                </div>
              )}
              {detail?.images && detail.images.length > 1 && (
                <div className="grid grid-cols-5 gap-2 mt-3">
                  {detail.images.slice(0, 5).map((img, i) => (
                    <div key={i} className="relative aspect-square rounded bg-gray-50 overflow-hidden">
                      <Image
                        src={img}
                        alt={`${product.name} ${i + 1}`}
                        fill
                        className="object-cover"
                        unoptimized
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-sm text-gray-500 mb-2">
                  Precios disponibles
                </h3>
                <div className="space-y-2">
                  {sorted.map((price) => (
                    <PriceRow
                      key={`${price.store}-${price.price_usd}`}
                      price={price}
                    />
                  ))}
                </div>
                {best && (
                  <p className="text-green-600 font-bold mt-2">
                    Mejor precio: {formatPriceRow(best.price_usd)}
                  </p>
                )}
              </div>

              {(detail?.description || error || loading) && (
                <div>
                  <h3 className="font-semibold text-sm text-gray-500 mb-2">
                    Descripción
                  </h3>
                  {loading && (
                    <p className="text-sm text-gray-400 animate-pulse">
                      Cargando descripción...
                    </p>
                  )}
                  {error && (
                    <p className="text-xs text-gray-400">
                      (Descripción no disponible aún)
                    </p>
                  )}
                  {detail?.description && (
                    <p className="text-sm text-gray-700">{detail.description}</p>
                  )}
                  {!loading && !error && !detail?.description && (
                    <p className="text-xs text-gray-400">
                      (El backend aún no expone la descripción de este producto)
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>

          {history.length > 0 && (
            <div className="mt-6">
              <h3 className="font-semibold text-sm text-gray-500 mb-2">
                Historial de precios
              </h3>
              <div className="space-y-3">
                {Object.entries(historyByStore).map(([storeKey, entries]) => {
                  const meta = getStoreMeta(storeKey)
                  const bars = entries.filter((e) => e.price != null)
                  if (bars.length === 0) return null
                  const min = Math.min(...bars.map((e) => e.price!))
                  const max = Math.max(...bars.map((e) => e.price!))

                  return (
                    <div key={storeKey} className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`inline-block w-3 h-3 rounded-full ${meta.colorClass}`} />
                        <span className="text-sm font-medium">{meta.label}</span>
                      </div>
                      <div className="flex items-end gap-1 h-16">
                        {bars.slice(0, 12).map((e, i) => {
                          const height =
                            max === min ? 100 : ((e.price! - min) / (max - min)) * 100
                          const date = new Date(e.date)
                          const isValidDate = !isNaN(date.getTime())
                          const dateLabel = isValidDate
                            ? date.toLocaleDateString('es-VE', { month: 'short', day: 'numeric' })
                            : ''
                          const title = `${formatPriceRow(e.price)}${
                            isValidDate ? ` · ${date.toLocaleDateString('es-VE')}` : ''
                          }`
                          return (
                            <div
                              key={i}
                              className="flex-1 min-w-[32px] flex flex-col justify-end"
                              title={title}
                            >
                              <div
                                className={`w-full rounded-t ${meta.colorClass} opacity-70`}
                                style={{ height: `${height}%`, minHeight: '4px' }}
                              />
                              {dateLabel && (
                                <span className="text-[8px] text-gray-400 mt-1 truncate">
                                  {dateLabel}
                                </span>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

import PriceRow from '@/components/PriceRow'
import Image from 'next/image'
import type { ProductResult } from '@/lib/types'
import { formatPriceRow } from '@/components/PriceRow'

interface ProductCardProps {
  product: ProductResult
  compact?: boolean
  onViewDetails?: () => void
}

export default function ProductCard({ product, compact = false, onViewDetails }: ProductCardProps) {
  const sorted = [...product.prices].sort(
    (a, b) =>
      (a.price_usd ?? Infinity) - (b.price_usd ?? Infinity),
  )
  const bestPrice = sorted[0]

  return (
    <div
      className={`bg-white rounded-2xl shadow-md border border-gray-200 transition-shadow hover:shadow-lg flex flex-col ${
        compact ? 'p-4' : 'p-6'
      }`}
    >
      <div className="w-full flex flex-col items-center">
        <div className={`relative rounded-xl bg-gray-50 shrink-0 ${
          compact ? 'w-24 h-24' : 'w-36 h-36'
        }`}>
          {product.image_url ? (
            <Image
              src={product.image_url}
              alt={product.name}
              fill
              sizes={compact ? '96px' : '144px'}
              className="object-contain p-2 rounded-xl"
              unoptimized
            />
          ) : (
            <span className="absolute inset-0 flex items-center justify-center text-gray-300 text-3xl">
              ?
            </span>
          )}
        </div>

        <div className="w-full min-w-0 mt-4 text-center">
          <h3 className={`font-semibold truncate ${compact ? 'text-base' : 'text-xl'}`}>
            {product.name}
          </h3>
          {product.brand && (
            <p className={`text-gray-500 ${compact ? 'text-xs' : 'text-sm'}`}>
              {product.brand}
            </p>
          )}
          {!compact && product.category && (
            <p className="text-xs text-gray-400 mt-1">{product.category}</p>
          )}
          {!compact && bestPrice && (
            <p className="text-green-600 font-bold mt-1">
              Desde {formatPriceRow(bestPrice.price_usd)}
            </p>
          )}
        </div>
      </div>

      {!compact && onViewDetails && (
        <button
          onClick={onViewDetails}
          className="mt-4 w-full px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
        >
          Ver detalle y precios
        </button>
      )}

      <div className="mt-4 space-y-2 flex-1 flex flex-col justify-end">
        {sorted.slice(0, compact ? 3 : sorted.length).map((price) => (
          <PriceRow
            key={`${price.store}-${price.price_usd}`}
            price={price}
            compact={compact}
          />
        ))}
        {compact && sorted.length > 3 && (
          <p className="text-[10px] text-gray-400 text-center">
            +{sorted.length - 3} tienda{sorted.length - 3 !== 1 ? 's' : ''} más
          </p>
        )}
      </div>
    </div>
  )
}
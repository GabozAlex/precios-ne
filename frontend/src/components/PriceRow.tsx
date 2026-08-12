import StoreIcon from '@/components/StoreIcon'
import type { PriceInfo } from '@/lib/types'

interface PriceRowProps {
  price: PriceInfo
  compact?: boolean
}

function formatPrice(price: number | null) {
  if (price === null || price === undefined) return '—'
  return `$${price.toFixed(2)}`
}

export default function PriceRow({ price, compact = false }: PriceRowProps) {
  const isAvailable = price.in_stock

  return (
    <div className="flex items-center justify-between rounded-lg p-3 bg-gray-50">
      <div className="flex items-center gap-2">
        <StoreIcon store={price.store} size="sm" showDot showLabel={false} />
        {!compact && (
          <span className="font-medium text-sm">
            {price.store_name || price.store}
          </span>
        )}
        {!isAvailable && (
          <span className="text-[10px] text-red-500 font-medium">Sin stock</span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <span className={`font-bold ${compact ? 'text-sm' : 'text-lg'}`}>
          {formatPrice(price.price_usd)}
        </span>
        {price.product_url && (
          <a
            href={price.product_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`rounded px-3 py-1 font-medium ${
              compact
                ? 'text-xs bg-blue-50 text-blue-700 hover:bg-blue-100'
                : 'text-sm bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            Ver en tienda
          </a>
        )}
      </div>
    </div>
  )
}

export { formatPrice as formatPriceRow }

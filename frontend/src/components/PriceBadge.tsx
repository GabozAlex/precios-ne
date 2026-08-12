import type { PriceInfo } from '@/lib/types'

interface PriceBadgeProps {
  price: PriceInfo
  isBest?: boolean
  showLink?: boolean
  size?: 'sm' | 'md'
}

function formatPrice(price: number | null) {
  if (price === null || price === undefined) return '—'
  return `$${price.toFixed(2)}`
}

export default function PriceBadge({ price, isBest = false, showLink = true, size = 'md' }: PriceBadgeProps) {
  const textSize = size === 'sm' ? 'text-sm' : 'text-lg'
  const isAvailable = price.in_stock
  const colorClass = isBest ? 'text-green-600' : 'text-gray-900'

  return (
    <div className="flex items-center justify-between gap-2">
      <span className={`font-bold ${textSize} ${colorClass}`}>
        {formatPrice(price.price_usd)}
      </span>
      {showLink && price.product_url && (
        <a
          href={price.product_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
        >
          Ver
        </a>
      )}
      {!isAvailable && (
        <span className="text-[10px] text-red-500 font-medium">Sin stock</span>
      )}
    </div>
  )
}

export { formatPrice }

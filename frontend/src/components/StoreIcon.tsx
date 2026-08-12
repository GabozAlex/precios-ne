import { getStoreMeta, type StoreMeta } from '@/lib/stores'
import type { StoreKey } from '@/lib/types'

const STORE_DOT_CLASSES: Record<StoreKey, string> = {
  damasco: 'bg-store-damasco ring-2 ring-store-damasco/20',
  multimax: 'bg-store-multimax ring-2 ring-store-multimax/20',
  daka: 'bg-store-daka ring-2 ring-store-daka/20',
  ivoo: 'bg-store-ivoo ring-2 ring-store-ivoo/20',
}

const STORE_LABEL_CLASSES: Record<StoreKey, string> = {
  damasco: 'text-store-damasco-foreground',
  multimax: 'text-store-multimax-foreground',
  daka: 'text-store-daka-foreground',
  ivoo: 'text-store-ivoo-foreground',
}

interface StoreIconProps {
  store: string
  size?: 'sm' | 'md'
  showDot?: boolean
  showLabel?: boolean
  active?: boolean
}

export default function StoreIcon({
  store,
  size = 'md',
  showDot = true,
  showLabel = false,
  active = true,
}: StoreIconProps) {
  const meta: StoreMeta = getStoreMeta(store)
  const storeKey = (meta.key as StoreKey) ?? null
  const sizeClasses = {
    sm: 'w-4 h-4 shrink-0',
    md: 'w-6 h-6 shrink-0',
  }
  const isActive = active !== false
  const dotClass = !isActive
    ? 'bg-gray-300 ring-2 ring-gray-200'
    : storeKey
    ? STORE_DOT_CLASSES[storeKey]
    : 'bg-gray-400 ring-2 ring-gray-200'
  const labelClass = !isActive
    ? 'text-gray-400'
    : storeKey
    ? `${STORE_LABEL_CLASSES[storeKey]}`
    : 'text-gray-700'

  return (
    <div className="inline-flex items-center gap-1.5">
      <span className={`inline-block rounded-full ${sizeClasses[size]} ${dotClass}`} />
      {showLabel && (
        <span className={`text-xs font-semibold ${labelClass}`}>
          {meta.label}
        </span>
      )}
    </div>
  )
}

export { getStoreMeta }
export type { StoreMeta }
export type { StoreKey }

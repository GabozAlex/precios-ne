'use client'

import StoreIcon from '@/components/StoreIcon'
import { STORE_KEYS } from '@/lib/stores'
import { useStores } from '@/lib/useStores'
import type { StoreKey } from '@/lib/types'

interface StoreStatusBarProps {
  activeOnly?: boolean
}

export default function StoreStatusBar({ activeOnly = false }: StoreStatusBarProps) {
  const { stores } = useStores()

  const statusMap: Record<string, boolean> = {}
  stores.forEach((s) => {
    statusMap[s.id] = s.active
  })

  const visible = STORE_KEYS.filter((k) => {
    const isActive = statusMap[k] ?? true
    return !activeOnly || isActive
  })

  return (
    <div className="flex items-center justify-center gap-6 flex-wrap">
      {visible.map((store: StoreKey) => (
        <StoreIcon
          key={store}
          store={store}
          size="md"
          showDot
          showLabel
          active={statusMap[store] ?? true}
        />
      ))}
    </div>
  )
}
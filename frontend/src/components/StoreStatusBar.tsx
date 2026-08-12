import StoreIcon from '@/components/StoreIcon'
import { STORE_KEYS } from '@/lib/stores'

interface StoreStatusBarProps {
  activeOnly?: boolean
}

export default function StoreStatusBar({ activeOnly = true }: StoreStatusBarProps) {
  const stores = STORE_KEYS

  return (
    <div className="flex items-center justify-center gap-6 flex-wrap">
      {stores.map((store) => (
        <StoreIcon key={store} store={store} size="md" showDot showLabel />
      ))}
    </div>
  )
}

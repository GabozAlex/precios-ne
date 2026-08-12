interface LoadingSkeletonProps {
  count?: number
  variant?: 'list' | 'grid'
  gridCols?: string
}

export default function LoadingSkeleton({
  count = 3,
  variant = 'list',
  gridCols = 'sm:grid-cols-2 md:grid-cols-3',
}: LoadingSkeletonProps) {
  const items = Array.from({ length: count })

  return variant === 'grid' ? (
    <div className={`grid grid-cols-1 ${gridCols} gap-4`}>
      {items.map((_, i) => (
        <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
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
  ) : (
    <div className="space-y-4">
      {items.map((_, i) => (
        <div
          key={i}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 animate-pulse"
        >
          <div className="flex gap-4">
            <div className="w-24 h-24 bg-gray-200 rounded-lg" />
            <div className="flex-1 space-y-2">
              <div className="h-5 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-1/4" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

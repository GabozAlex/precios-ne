import Link from 'next/link'

interface ErrorStateProps {
  message: string
  actionLabel?: string
  actionHref?: string
  onRetry?: () => void
}

export default function ErrorState({ message, actionLabel, actionHref, onRetry }: ErrorStateProps) {
  return (
    <div className="text-center py-16">
      <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-red-100 mb-4">
        <span className="text-2xl" role="img" aria-label="error">
          ⚠️
        </span>
      </div>
      <p className="text-red-600 mb-4 max-w-sm mx-auto">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium underline"
        >
          Reintentar
        </button>
      )}
      {actionHref && actionLabel && (
        <Link href={actionHref} className="text-sm text-blue-600 hover:text-blue-800 font-medium underline">
          {actionLabel}
        </Link>
      )}
    </div>
  )
}

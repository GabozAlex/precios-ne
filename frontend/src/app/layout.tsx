import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'

export const metadata: Metadata = {
  title: 'PreciosNE — Compara precios en Nueva Esparta',
  description: 'Encuentra el mejor precio en Damasco, Multimax, Daka e Ivoo para cualquier producto en Nueva Esparta, Venezuela.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-3">
            <Link href="/" className="text-2xl font-bold text-blue-600">
              PreciosNE
            </Link>
            <span className="text-sm text-gray-500 hidden sm:inline">
              Comparador de precios · Nueva Esparta
            </span>
          </div>
        </header>
        <main className="max-w-6xl mx-auto px-4 py-8">
          {children}
        </main>
        <footer className="border-t border-gray-200 py-6 text-center text-sm text-gray-500">
          PreciosNE — Comparador de precios de tiendas en Nueva Esparta, Venezuela
        </footer>
      </body>
    </html>
  )
}

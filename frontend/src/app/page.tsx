import SearchBar from '@/components/SearchBar'
import StoreStatusBar from '@/components/StoreStatusBar'
import Link from 'next/link'

export default function Home() {
  return (
    <div className="flex flex-col items-center gap-8 pt-16">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">
          ¿Buscas el mejor precio?
        </h1>
        <p className="text-lg text-gray-600 max-w-xl">
          Compara precios de electrodomésticos, tecnología y hogar entre
          <strong> Damasco</strong>, <strong>Multimax</strong>,{' '}
          <strong>Daka</strong> e <strong>Ivoo</strong> en Nueva Esparta.
        </p>
      </div>

      <StoreStatusBar />

      <SearchBar />

      <Link
        href="/productos"
        className="text-sm text-blue-600 hover:underline mt-2"
      >
        Ver todos los productos &rarr;
      </Link>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full max-w-2xl mt-4">
        {[
          { name: 'Damasco', key: 'damasco', color: 'bg-store-damasco' },
          { name: 'Multimax', key: 'multimax', color: 'bg-store-multimax' },
          { name: 'Daka', key: 'daka', color: 'bg-store-daka' },
          { name: 'Ivoo', key: 'ivoo', color: 'bg-store-ivoo' },
        ].map((store) => (
          <Link
            key={store.name}
            href={`/productos?store=${store.key}`}
            className={`${store.color} text-white rounded-lg p-4 text-center font-semibold shadow hover:opacity-80 transition-opacity`}
          >
            {store.name}
          </Link>
        ))}
      </div>

      <p className="text-sm text-gray-400 mt-4">
        Resultados en tiempo real · Precios en USD
      </p>
    </div>
  )
}

import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'best-price': '#16a34a',
        'store-damasco': '#e11d48',
        'store-multimax': '#2563eb',
        'store-daka': '#ca8a04',
        'store-ivoo': '#7c3aed',
      },
    },
  },
  plugins: [],
}

export default config

import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
      extend: {
        colors: {
          'store-damasco': '#e11d48',
          'store-damasco-foreground': '#7f1d1d',
          'store-multimax': '#2563eb',
          'store-multimax-foreground': '#1e3a8a',
          'store-daka': '#ca8a04',
          'store-daka-foreground': '#78350f',
          'store-ivoo': '#7c3aed',
          'store-ivoo-foreground': '#312e81',
        },
      },
  },
  plugins: [],
}

export default config

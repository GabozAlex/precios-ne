/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '*.vtexcommercestable.com.br',
      },
      {
        protocol: 'https',
        hostname: '*.damasco*.com',
      },
      {
        protocol: 'https',
        hostname: 'www.damascovzla.com',
      },
      {
        protocol: 'https',
        hostname: 'multimax.com.ve',
      },
      {
        protocol: 'https',
        hostname: 'tiendasdaka.com',
      },
      {
        protocol: 'https',
        hostname: '*.ivoo.com',
      },
      {
        protocol: 'https',
        hostname: 'www.ivoo.com',
      },
      {
        protocol: 'https',
        hostname: '*.cloudfront.net',
      },
      {
        protocol: 'https',
        hostname: '*.tiendasdaka.com',
      },
    ],
  },
}

module.exports = nextConfig

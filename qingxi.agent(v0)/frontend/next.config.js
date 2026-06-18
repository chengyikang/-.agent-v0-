/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // 允许跨域请求到后端API
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig

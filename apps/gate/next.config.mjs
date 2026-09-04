/** @type {import('next').NextConfig} */
const nextConfig = {
  // This app is authenticated and writes to GitHub. It must never be cached or
  // indexed, and it shares no runtime with the published convo pages, which are
  // a separate static project so their 2 MB budget and read-time purity hold.
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Robots-Tag', value: 'noindex, nofollow' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Cache-Control', value: 'no-store' },
        ],
      },
    ]
  },
}

export default nextConfig

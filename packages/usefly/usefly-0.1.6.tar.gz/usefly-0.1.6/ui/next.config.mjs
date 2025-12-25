/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',           // Enable static export
  distDir: 'out',             // Output to ui/out/
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,        // Required for static export
  },
  trailingSlash: true,        // Better for static hosting
  reactStrictMode: false,
}

export default nextConfig

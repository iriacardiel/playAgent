/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',              // ⬅️ enables .next/standalone for tiny runtime images
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },
};

export default nextConfig;

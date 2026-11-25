import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
  allowedDevOrigins: [
    "192.168.0.102",
    "192.168.0.102:3000",
    "localhost",
    "127.0.0.1",
    "*.trycloudflare.com",
  ],
};

export default nextConfig;

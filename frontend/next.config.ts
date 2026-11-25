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
  // /api/* is forwarded to the backend by src/proxy.ts (BACKEND_URL is read at request time)
  allowedDevOrigins: [
    "192.168.0.102",
    "192.168.0.102:3000",
    "localhost",
    "127.0.0.1",
    "*.trycloudflare.com",
  ],
};

export default nextConfig;

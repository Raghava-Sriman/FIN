import { NextResponse, type NextRequest } from "next/server";

/**
 * Forwards every /api/* request to the FastAPI backend, so the browser only ever talks to this
 * origin (session cookies stay first-party, no CORS).
 *
 * Server-side environment variables (never sent to the browser):
 *   BACKEND_URL            Backend origin, e.g. https://finsight-backend.up.railway.app
 *                          (defaults to http://127.0.0.1:8000 for local development)
 *   FINSIGHT_PROXY_SECRET  Shared secret the backend requires on every request in production
 */

const CLIENT_IP_HEADER = "x-finsight-client-ip";
const PROXY_SECRET_HEADER = "x-finsight-proxy-secret";

export const config = {
  matcher: "/api/:path*",
};

export function proxy(request: NextRequest) {
  const backend = process.env.BACKEND_URL || "http://127.0.0.1:8000";
  const target = new URL(`${request.nextUrl.pathname}${request.nextUrl.search}`, backend);

  const headers = new Headers(request.headers);
  // Never trust these from the browser: always overwrite (or remove) them here
  headers.delete(PROXY_SECRET_HEADER);
  headers.delete(CLIENT_IP_HEADER);

  // On Vercel, x-forwarded-for is set by the platform to the visitor's address
  const clientIp = (request.headers.get("x-forwarded-for") || "").split(",")[0].trim();
  if (clientIp) headers.set(CLIENT_IP_HEADER, clientIp);

  const secret = process.env.FINSIGHT_PROXY_SECRET;
  if (secret) headers.set(PROXY_SECRET_HEADER, secret);

  return NextResponse.rewrite(target, { request: { headers } });
}

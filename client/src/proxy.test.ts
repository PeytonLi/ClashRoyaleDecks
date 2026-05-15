import { unstable_doesMiddlewareMatch as doesProxyMatch } from "next/experimental/testing/server";
import { NextRequest, NextResponse } from "next/server";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { config, proxy } from "./proxy";

const auth0Mock = vi.hoisted(() => ({
  middleware: vi.fn(),
}));

vi.mock("@/lib/auth0", () => ({
  auth0: {
    middleware: auth0Mock.middleware,
  },
}));

describe("Auth0 proxy", () => {
  beforeEach(() => {
    auth0Mock.middleware.mockReset();
  });

  it("matches app and auth routes while excluding static assets and metadata", () => {
    expect(doesProxyMatch({ config, nextConfig: {}, url: "/recommend" })).toBe(true);
    expect(doesProxyMatch({ config, nextConfig: {}, url: "/auth/login" })).toBe(true);
    expect(doesProxyMatch({ config, nextConfig: {}, url: "/auth/logout" })).toBe(true);
    expect(doesProxyMatch({ config, nextConfig: {}, url: "/_next/static/chunk.js" })).toBe(false);
    expect(doesProxyMatch({ config, nextConfig: {}, url: "/_next/image" })).toBe(false);
    expect(doesProxyMatch({ config, nextConfig: {}, url: "/favicon.ico" })).toBe(false);
    expect(doesProxyMatch({ config, nextConfig: {}, url: "/sitemap.xml" })).toBe(false);
    expect(doesProxyMatch({ config, nextConfig: {}, url: "/robots.txt" })).toBe(false);
  });

  it("returns the response from Auth0 middleware", async () => {
    const request = new NextRequest("https://example.com/recommend");
    const authResponse = NextResponse.next();

    auth0Mock.middleware.mockResolvedValue(authResponse);

    await expect(proxy(request)).resolves.toBe(authResponse);
    expect(auth0Mock.middleware).toHaveBeenCalledWith(request);
  });
});

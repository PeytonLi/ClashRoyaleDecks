import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Home from "./page";

const auth0Mock = vi.hoisted(() => ({
  getSession: vi.fn(),
}));

vi.mock("@/lib/auth0", () => ({
  auth0: {
    getSession: auth0Mock.getSession,
  },
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

const textContent = (html: string) => html.replace(/<[^>]*>/g, "");

describe("Home authentication actions", () => {
  beforeEach(() => {
    auth0Mock.getSession.mockReset();
  });

  it("shows Auth0 login and signup links when the visitor is not authenticated", async () => {
    auth0Mock.getSession.mockResolvedValue(null);

    const html = renderToStaticMarkup(await Home());

    expect(html).toContain('href="/auth/login"');
    expect(html).toContain('href="/auth/login?screen_hint=signup"');
  });

  it("shows the authenticated user's email and logout link", async () => {
    auth0Mock.getSession.mockResolvedValue({
      user: {
        email: "player@example.com",
        name: "Arena Player",
      },
    });

    const html = renderToStaticMarkup(await Home());

    expect(textContent(html)).toContain("Logged in as player@example.com");
    expect(html).toContain('href="/auth/logout"');
    expect(html).not.toContain('href="/auth/login"');
    expect(html).not.toContain('href="/auth/login?screen_hint=signup"');
  });
});

import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Home from "./page";

const authMock = vi.hoisted(() => ({
  auth: vi.fn(),
}));

vi.mock("@/auth", () => ({
  auth: authMock.auth,
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

vi.mock("next-auth/react", () => ({
  useSession: () => ({
    data: null,
    status: "unauthenticated",
  }),
}));

const textContent = (html: string) => html.replace(/<[^>]*>/g, "");

describe("Home authentication actions", () => {
  beforeEach(() => {
    authMock.auth.mockReset();
  });

  it("shows sign-in and sign-up links when the visitor is not authenticated", async () => {
    authMock.auth.mockResolvedValue(null);

    const html = renderToStaticMarkup(await Home());

    expect(html).toContain('href="/login"');
    expect(html).toContain('href="/signup"');
  });

  it("shows the authenticated user's email and logout link", async () => {
    authMock.auth.mockResolvedValue({
      user: {
        email: "player@example.com",
        name: "Arena Player",
      },
    });

    const html = renderToStaticMarkup(await Home());

    expect(textContent(html)).toContain("Logged in as player@example.com");
    expect(html).toContain('href="/api/auth/signout"');
    expect(html).not.toContain('href="/login"');
    expect(html).not.toContain('href="/signup"');
  });
});

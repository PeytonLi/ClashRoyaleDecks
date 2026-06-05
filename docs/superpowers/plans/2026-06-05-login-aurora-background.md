# Login Aurora Background Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an interactive dual-aurora-orb background to the login page where two large, blurred gradient blobs (royal blue + CR red) lazily drift and are gently attracted toward the user's mouse cursor.

**Architecture:** A `LoginBackground` client component owns mouse tracking via a `useEffect` + `requestAnimationFrame` loop that lerps two blob positions toward the cursor at different speeds. Blob positions are written directly to CSS custom properties on a wrapper `div` so React state is never involved in the animation hot path, keeping it jank-free. The login `page.tsx` wraps the entire page in this component.

**Tech Stack:** React 19 (Next.js App Router), TypeScript, CSS custom properties, `requestAnimationFrame`, Tailwind CSS v4.

---

## File Map

| Action  | Path                                           | Responsibility                                      |
|---------|------------------------------------------------|-----------------------------------------------------|
| Create  | `client/src/app/login/LoginBackground.tsx`     | Client component: mouse tracking, blob animation    |
| Modify  | `client/src/app/login/page.tsx`                | Wrap children in `LoginBackground`                  |

---

### Task 1: Create the `LoginBackground` client component

**Files:**
- Create: `client/src/app/login/LoginBackground.tsx`

The component renders two absolutely-positioned blob `div`s whose positions are driven by CSS custom properties (`--bx`, `--by`, `--rx`, `--ry`). A `requestAnimationFrame` loop lerps each blob toward the mouse at a slightly different speed so they feel independent.

- [ ] **Step 1: Create `LoginBackground.tsx`**

```tsx
"use client";

import { useEffect, useRef } from "react";

export default function LoginBackground({
  children,
}: {
  children: React.ReactNode;
}) {
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap) return;

    // target positions (updated on mousemove)
    let mx = window.innerWidth / 2;
    let my = window.innerHeight / 2;

    // current positions (lerped each frame)
    let bx = mx * 0.3;   // blue blob starts top-left area
    let by = my * 0.6;
    let rx = mx * 1.5;   // red blob starts bottom-right area
    let ry = my * 1.2;

    const onMove = (e: MouseEvent) => {
      mx = e.clientX;
      my = e.clientY;
    };

    window.addEventListener("mousemove", onMove);

    let rafId: number;

    const tick = () => {
      // blue blob lerps faster — feels more "eager"
      bx += (mx - bx) * 0.04;
      by += (my - by) * 0.04;
      // red blob lerps slower — feels heavier/lazier
      rx += (mx - rx) * 0.018;
      ry += (my - ry) * 0.018;

      wrap.style.setProperty("--bx", `${bx}px`);
      wrap.style.setProperty("--by", `${by}px`);
      wrap.style.setProperty("--rx", `${rx}px`);
      wrap.style.setProperty("--ry", `${ry}px`);

      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);

    return () => {
      window.removeEventListener("mousemove", onMove);
      cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <div ref={wrapRef} className="relative min-h-screen overflow-hidden" style={{ background: "#060810" }}>
      {/* Blue aurora blob */}
      <div
        aria-hidden
        className="pointer-events-none fixed"
        style={{
          width: "700px",
          height: "700px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(59,130,246,0.22) 0%, rgba(37,99,235,0.10) 40%, transparent 70%)",
          filter: "blur(60px)",
          transform: "translate(calc(var(--bx, 30%) - 350px), calc(var(--by, 40%) - 350px))",
          transition: "none",
          zIndex: 0,
        }}
      />

      {/* Red aurora blob */}
      <div
        aria-hidden
        className="pointer-events-none fixed"
        style={{
          width: "600px",
          height: "600px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(240,68,68,0.18) 0%, rgba(185,28,28,0.08) 40%, transparent 70%)",
          filter: "blur(70px)",
          transform: "translate(calc(var(--rx, 70%) - 300px), calc(var(--ry, 60%) - 300px))",
          transition: "none",
          zIndex: 0,
        }}
      />

      {/* Content */}
      <div className="relative z-10 flex min-h-screen flex-col">
        {children}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify the file was created with no TypeScript errors**

Run from `client/`:
```bash
npx tsc --noEmit
```
Expected: no errors for the new file (there may be pre-existing errors elsewhere — those are fine).

---

### Task 2: Wire `LoginBackground` into the login page

**Files:**
- Modify: `client/src/app/login/page.tsx`

- [ ] **Step 1: Update `page.tsx` to wrap in `LoginBackground`**

Replace the full file content with:

```tsx
import Navbar from "../../components/Navbar";
import UnifiedAuthForm from "./UnifiedAuthForm";
import LoginBackground from "./LoginBackground";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ callbackUrl?: string }>;
}) {
  const params = await searchParams;
  const callbackUrl = params.callbackUrl?.startsWith("/")
    ? params.callbackUrl
    : "/recommend";
  const googleEnabled = Boolean(
    process.env.AUTH_GOOGLE_ID && process.env.AUTH_GOOGLE_SECRET,
  );

  return (
    <LoginBackground>
      <Navbar />
      <main className="page-frame flex grow items-center justify-center py-10">
        <UnifiedAuthForm
          callbackUrl={callbackUrl}
          googleEnabled={googleEnabled}
        />
      </main>
    </LoginBackground>
  );
}
```

Note: The inline `style` background override added in the previous session's `div` is replaced by `LoginBackground`'s own `#060810` background — remove it from any wrappers if it still exists.

- [ ] **Step 2: Start the dev server and verify visually**

```bash
cd client && pnpm dev
```

Open `http://localhost:3000/login`. You should see:
- Deep navy `#060810` background
- Two large soft glowing blobs — one blue-tinted, one red-tinted
- Moving the mouse causes both blobs to slowly follow, the blue one slightly faster
- The login card sits on top, unaffected

- [ ] **Step 3: Check reduced-motion compliance**

The global `globals.css` already has:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    ...
  }
}
```

`requestAnimationFrame` is not an animation/transition so it's not affected by this rule. To respect reduced-motion preference, add this inside the `useEffect` in `LoginBackground.tsx` before starting the RAF loop:

```tsx
const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (prefersReduced) return; // skip animation, blobs stay at initial positions
```

Add this check right after the initial position variable declarations and before the `onMove` listener.

- [ ] **Step 4: Commit**

```bash
git add client/src/app/login/LoginBackground.tsx client/src/app/login/page.tsx
git commit -m "feat: add interactive aurora blob background to login page"
```

---

## Self-Review

**Spec coverage:**
- [x] Two aurora blobs — one blue, one red
- [x] Blobs lazily drift (separate lerp speeds: 0.04 vs 0.018)
- [x] Attracted to mouse cursor via rAF lerp loop
- [x] Behind the login card (z-index layering via wrapper)
- [x] Reduced-motion respected

**Placeholder scan:** None found — all steps have complete code.

**Type consistency:** `wrapRef` typed as `HTMLDivElement`, CSS property names (`--bx`, `--by`, `--rx`, `--ry`) consistent across useEffect and JSX style props.

"use client";

import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

export default function LoginBackground({ children }: { children: ReactNode }) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const blueBlobRef = useRef<HTMLDivElement>(null);
  const redBlobRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const wrap = wrapRef.current;
    const blueBlob = blueBlobRef.current;
    const redBlob = redBlobRef.current;
    if (!wrap || !blueBlob || !redBlob) return;

    const mql = window.matchMedia("(prefers-reduced-motion: reduce)");
    let prefersReduced = mql.matches;

    let mx = window.innerWidth / 2;
    let my = window.innerHeight / 2;
    let bx = mx * 0.3;
    let by = my * 0.6;
    let rx = mx * 1.5;
    let ry = my * 1.2;
    let rafId = 0;
    let cancelled = false;

    const setWillChange = (active: boolean) => {
      const value = active ? "transform" : "auto";
      blueBlob.style.willChange = value;
      redBlob.style.willChange = value;
    };

    const tick = () => {
      if (cancelled) return;
      bx += (mx - bx) * 0.04;
      by += (my - by) * 0.04;
      rx += (mx - rx) * 0.018;
      ry += (my - ry) * 0.018;
      wrap.style.setProperty("--bx", `${bx}px`);
      wrap.style.setProperty("--by", `${by}px`);
      wrap.style.setProperty("--rx", `${rx}px`);
      wrap.style.setProperty("--ry", `${ry}px`);
      rafId = requestAnimationFrame(tick);
    };

    const onMove = (e: MouseEvent) => {
      mx = e.clientX;
      my = e.clientY;
    };

    const startAnimation = () => {
      setWillChange(true);
      window.addEventListener("mousemove", onMove);
      rafId = requestAnimationFrame(tick);
    };

    const stopAnimation = () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("mousemove", onMove);
      setWillChange(false);
    };

    const onReducedChange = (e: MediaQueryListEvent) => {
      prefersReduced = e.matches;
      if (prefersReduced) {
        stopAnimation();
      } else if (!document.hidden) {
        startAnimation();
      }
    };

    const onVisibilityChange = () => {
      if (document.hidden) {
        cancelAnimationFrame(rafId);
      } else if (!prefersReduced) {
        rafId = requestAnimationFrame(tick);
      }
    };

    mql.addEventListener("change", onReducedChange);
    document.addEventListener("visibilitychange", onVisibilityChange);

    if (!prefersReduced) {
      startAnimation();
    }

    return () => {
      cancelled = true;
      stopAnimation();
      mql.removeEventListener("change", onReducedChange);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, []);

  return (
    <div ref={wrapRef} className="relative min-h-screen overflow-hidden" style={{ background: "#060810" }}>
      {/* Blue aurora blob */}
      <div
        ref={blueBlobRef}
        aria-hidden={true}
        className="pointer-events-none fixed"
        style={{
          width: "700px",
          height: "700px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(59,130,246,0.22) 0%, rgba(37,99,235,0.10) 40%, transparent 70%)",
          filter: "blur(60px)",
          transform: "translate(calc(var(--bx, 50vw) - 350px), calc(var(--by, 40vh) - 350px))",
          zIndex: 0,
        }}
      />

      {/* Red aurora blob */}
      <div
        ref={redBlobRef}
        aria-hidden={true}
        className="pointer-events-none fixed"
        style={{
          width: "600px",
          height: "600px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(240,68,68,0.18) 0%, rgba(185,28,28,0.08) 40%, transparent 70%)",
          filter: "blur(70px)",
          transform: "translate(calc(var(--rx, 60vw) - 300px), calc(var(--ry, 60vh) - 300px))",
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

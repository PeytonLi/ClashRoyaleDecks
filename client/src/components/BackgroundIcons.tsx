"use client";

import { useEffect, useRef } from "react";

type Icon = {
  type: "crown" | "sword";
  x: number;        // 0–1 fraction of viewport width
  y: number;        // 0–1 fraction of viewport height
  size: number;     // base size in px
  opacity: number;
  angle: number;    // initial rotation (radians)
  depth: number;    // parallax depth 0–1
  phaseX: number;
  phaseY: number;
  freqX: number;
  freqY: number;
  ampX: number;
  ampY: number;
};

function seeded(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 0xffffffff;
  };
}

function drawCrown(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  size: number,
  opacity: number,
) {
  ctx.save();
  ctx.globalAlpha = opacity;
  ctx.lineWidth = Math.max(0.8, size * 0.08);
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.shadowColor = "rgba(245,181,63,0.5)";
  ctx.shadowBlur = size * 0.3;
  ctx.strokeStyle = "#f5b53f";

  const w = size * 0.9;
  const h = size * 0.75;
  const bY = cy + h * 0.25;   // base bar y
  const bH = h * 0.18;        // base bar height

  // Base bar
  ctx.beginPath();
  ctx.rect(cx - w / 2, bY, w, bH);
  ctx.stroke();

  // Crown peaks path
  ctx.beginPath();
  ctx.moveTo(cx - w / 2, bY);
  ctx.lineTo(cx - w / 2, cy - h * 0.05);       // left upright
  ctx.lineTo(cx - w / 4, cy - h * 0.42);        // left peak
  ctx.lineTo(cx - w / 9, cy - h * 0.08);        // left valley
  ctx.lineTo(cx,          cy - h * 0.62);        // center peak (tallest)
  ctx.lineTo(cx + w / 9, cy - h * 0.08);        // right valley
  ctx.lineTo(cx + w / 4, cy - h * 0.42);        // right peak
  ctx.lineTo(cx + w / 2, cy - h * 0.05);        // right upright
  ctx.lineTo(cx + w / 2, bY);
  ctx.stroke();

  // Three jewel dots at peaks
  ctx.fillStyle = "#f5b53f";
  const dotR = Math.max(0.8, size * 0.06);
  [
    [cx - w / 4, cy - h * 0.42],
    [cx,         cy - h * 0.62],
    [cx + w / 4, cy - h * 0.42],
  ].forEach(([dx, dy]) => {
    ctx.beginPath();
    ctx.arc(dx, dy, dotR, 0, Math.PI * 2);
    ctx.fill();
  });

  ctx.restore();
}

function drawSword(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  size: number,
  opacity: number,
  angle: number,
) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(angle);
  ctx.globalAlpha = opacity;
  ctx.lineCap = "round";
  ctx.strokeStyle = "#4f8ef7";
  ctx.shadowColor = "rgba(79,142,247,0.5)";
  ctx.shadowBlur = size * 0.3;

  const h = size;

  // Blade
  ctx.lineWidth = Math.max(0.8, h * 0.07);
  ctx.beginPath();
  ctx.moveTo(0, -h * 0.5);
  ctx.lineTo(0, h * 0.22);
  ctx.stroke();

  // Blade tip (small angled lines to make a point)
  ctx.lineWidth = Math.max(0.6, h * 0.06);
  ctx.beginPath();
  ctx.moveTo(-h * 0.06, -h * 0.35);
  ctx.lineTo(0, -h * 0.5);
  ctx.lineTo(h * 0.06, -h * 0.35);
  ctx.stroke();

  // Crossguard
  ctx.lineWidth = Math.max(1, h * 0.1);
  ctx.beginPath();
  ctx.moveTo(-h * 0.28, h * 0.12);
  ctx.lineTo(h * 0.28, h * 0.12);
  ctx.stroke();

  // Grip / handle (slightly wider)
  ctx.lineWidth = Math.max(1, h * 0.13);
  ctx.beginPath();
  ctx.moveTo(0, h * 0.22);
  ctx.lineTo(0, h * 0.48);
  ctx.stroke();

  // Pommel dot
  ctx.fillStyle = "#4f8ef7";
  ctx.beginPath();
  ctx.arc(0, h * 0.5, Math.max(1, h * 0.07), 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}

export default function BackgroundIcons() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const mql = window.matchMedia("(prefers-reduced-motion: reduce)");
    const prefersReduced = mql.matches;

    // Deterministic icon layout
    const rand = seeded(137);
    const icons: Icon[] = Array.from({ length: 46 }, () => ({
      type: rand() > 0.48 ? "crown" : "sword",
      x: rand(),
      y: rand(),
      size: 13 + rand() * 18,
      opacity: 0.10 + rand() * 0.16,
      angle: rand() * Math.PI * 2,
      depth: 0.15 + rand() * 0.85,
      phaseX: rand() * Math.PI * 2,
      phaseY: rand() * Math.PI * 2,
      freqX: 0.00018 + rand() * 0.00055,
      freqY: 0.00018 + rand() * 0.00055,
      ampX: 8 + rand() * 22,
      ampY: 8 + rand() * 22,
    }));

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();

    // Shared render function — draws all icons for a given time + mouse offset
    const render = (now: number, offX = 0, offY = 0) => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const icon of icons) {
        const dx = Math.sin(now * icon.freqX + icon.phaseX) * icon.ampX;
        const dy = Math.cos(now * icon.freqY + icon.phaseY) * icon.ampY;
        const px = icon.x * canvas.width  + dx + offX * icon.depth * 45;
        const py = icon.y * canvas.height + dy + offY * icon.depth * 45;
        if (icon.type === "crown") {
          drawCrown(ctx, px, py, icon.size, icon.opacity);
        } else {
          drawSword(ctx, px, py, icon.size, icon.opacity, icon.angle);
        }
      }
    };

    // Reduced-motion: render one static frame, no rAF loop
    if (prefersReduced) {
      render(0);
      const onResize = () => { resize(); render(0); };
      window.addEventListener("resize", onResize);
      return () => window.removeEventListener("resize", onResize);
    }

    let mx = window.innerWidth / 2;
    let my = window.innerHeight / 2;
    let smx = mx;
    let smy = my;
    let rafId = 0;
    let cancelled = false;

    const onResize = () => resize();
    const onMove = (e: MouseEvent) => { mx = e.clientX; my = e.clientY; };

    window.addEventListener("resize", onResize);
    window.addEventListener("mousemove", onMove);

    const tick = (now: number) => {
      if (cancelled) return;
      smx += (mx - smx) * 0.04;
      smy += (my - smy) * 0.04;
      const offX = (smx / window.innerWidth  - 0.5) * 2;
      const offY = (smy / window.innerHeight - 0.5) * 2;
      render(now, offX, offY);
      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("mousemove", onMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden={true}
      className="pointer-events-none fixed inset-0"
      style={{ zIndex: 0 }}
    />
  );
}

import React, {useLayoutEffect, useRef} from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import type {BgSpec} from './types';

/**
 * Backdrop option 2, "dot wave": a port of the dot-field-wave from video-talkcraft `template/motion-systems/backdrop.tsx`.
 * Main mounts it when `bg: 'dots'` is set in `src/config.ts`. It replaces option 1, the fog Fog plus star field StarField (the two never stack).
 * - Deterministic frame by frame: t = frame / fps × speed (talkcraft's default speed is 1.5). A diagonal wavefront sweeps across every 14 s (÷speed ≈ 9.3 s).
 * - Scaled uniformly from a 960×540 design grid to cover 1280×720: dot spacing 36 → 48px on screen, radius 1.5–2 → 2–2.7px. Base color #0b0c11, dot color #cfe0ff.
 *   Opacity (0.2 + 0.6k²) × radial edge falloff, where k is the normalized distance to the wavefront. A static noise layer (overlay .06) prevents color banding.
 * - Follows BgSpec: inside a range, `stars:'none'` skips the whole layer and returns to pure black (matches the star option: 10 frames before the opening, 40 frames before the closing). The `fog` field has no effect with this option.
 * - The dots are a static texture in screen space and do not follow any camera move. scripts/frame_metrics.py removes them from its measurements using the same grid coordinates (`bg` is read from the config automatically).
 */
const DW = 960, DH = 540;
export const DOT_STEP = 36, DOT_X0 = 24, DOT_Y0 = 18; // design-grid origin and spacing (frame_metrics.py uses the same constants to recover screen coordinates)
const GRAIN_URL =
  "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .5 0'/></filter><rect width='160' height='160' filter='url(%23n)'/></svg>\")";

const drawDots = (ctx: CanvasRenderingContext2D, t: number) => {
  ctx.fillStyle = '#0b0c11';
  ctx.fillRect(-DW, -DH, DW * 3, DH * 3);
  const phase = ((t % 14) / 14) * 1700 - 300;
  for (let y = DOT_Y0; y < DH; y += DOT_STEP) {
    for (let x = DOT_X0; x < DW; x += DOT_STEP) {
      const d = Math.abs(x + y * 0.6 - phase);
      const k = Math.max(0, 1 - d / 280);
      const kk = k * k;
      const edge = Math.min(1, Math.max(0, 1.25 - Math.hypot((x - 480) / 560, (y - 270) / 360)));
      ctx.globalAlpha = (0.2 + 0.6 * kk) * edge;
      ctx.fillStyle = '#cfe0ff';
      ctx.beginPath();
      ctx.arc(x, y, 1.5 + 0.5 * kk, 0, 6.283);
      ctx.fill();
    }
  }
  ctx.globalAlpha = 1;
};

const DotCanvas: React.FC<{t: number}> = ({t}) => {
  const {width, height} = useVideoConfig();
  const ref = useRef<HTMLCanvasElement>(null);
  useLayoutEffect(() => {
    const c = ref.current;
    if (!c) return;
    const ctx = c.getContext('2d');
    if (!ctx) return;
    const s = Math.max(width / DW, height / DH);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, width, height);
    ctx.setTransform(s, 0, 0, s, (width - DW * s) / 2, (height - DH * s) / 2);
    drawDots(ctx, t);
  }, [t, width, height]);
  return <canvas ref={ref} width={width} height={height} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}} />;
};

export const DotFieldBg: React.FC<{specs: BgSpec[]; speed?: number; grain?: boolean}> = ({specs, speed = 1.5, grain = true}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const N = frame + 1;
  let show = true;
  for (const s of specs) {
    if (N >= s.from && N <= s.to && s.stars === 'none') show = false;
  }
  if (!show) return null;
  const t = (frame / fps) * speed;
  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden', background: '#0b0b0f'}}>
      <DotCanvas t={t} />
      {grain ? <div style={{position: 'absolute', inset: 0, backgroundImage: GRAIN_URL, backgroundSize: '160px 160px', opacity: 0.06, mixBlendMode: 'overlay', pointerEvents: 'none'}} /> : null}
    </div>
  );
};

import React from 'react';
import {useCurrentFrame} from 'remotion';
import {rnd} from './easing';
import type {BgSpec} from './types';
import {Fog, FOG_DEFAULT_ON} from './Fog';

/**
 * Background star-particle layer. Deterministic: position, velocity and lifetime are all set by (seed, star index, cycle number). Each frame is a pure function, with no re-rolling.
 * Measured (blob tracking on verify_seg_06/07/08): about 45 stars per frame (threshold 40; about 60 by eye), drift |v| 0.4–3.2 px/frame (mean 1.7) in random directions,
 * brightness 40–250 flickering frame to frame (one star went 77→86→87→111→92→104→54→71), 1–3px core with soft edges, lifetime ≥60 frames.
 * seg_23: 6–25 visible per frame, lifetime 10–30 frames, rising to peak over 4–6 frames then easing out, with batch refreshes. seg_24: most drift left (−1.5…−4.5, −1.5…+3) px/frame, with parallax by size.
 * Three variants: 'drift' (default, random direction at 0.4–3.2), 'fast' (seg_24 leftward parallax at 1.5–4.5), 'still' (no movement, only twinkling), 'none'.
 */
export type StarVariant = 'drift' | 'fast' | 'still' | 'none';
export type StarFieldProps = {
  variant: StarVariant;
  count: number; // particles alive at once (default 45)
  speed: number; // speed multiplier (1 = measured distribution)
  lifetime: [number, number]; // lifetime range in frames
  twinkle: number; // per-frame brightness jitter amplitude (0.3 = ±30%)
  size: [number, number]; // core diameter in px
  brightness: [number, number]; // peak brightness, 0–255
  seed: number;
  region: [number, number, number, number]; // spawn region x, y, w, h
  opacity: number;
};
// Main session (QC v1 RQ1): the final-cut star density was about 50% of the original, and there were no bright 255-level stars → count 45→80, peak cap 200→255
export const STAR_DEFAULT: StarFieldProps = {variant: 'drift', count: 80, speed: 1, lifetime: [60, 200], twinkle: 0.3, size: [2, 4], brightness: [35, 255], seed: 7, region: [0, 0, 1280, 687], opacity: 1};

type Star = {x: number; y: number; s: number; a: number};
/** Pure function: returns every visible star for a given frame number (reusable for Canvas or tests). */
export const starsAt = (frame: number, p: StarFieldProps): Star[] => {
  if (p.variant === 'none') return [];
  const out: Star[] = [];
  const [rx, ry, rw, rh] = p.region;
  for (let i = 0; i < p.count; i++) {
    const L = Math.round(p.lifetime[0] + (p.lifetime[1] - p.lifetime[0]) * rnd(p.seed, i, 1));
    const phase = Math.floor(rnd(p.seed, i, 2) * L);
    const tt = frame + phase;
    const cyc = Math.floor(tt / L);
    const age = tt - cyc * L;
    // each cycle regenerates the spawn point, velocity, size and peak brightness
    const x0 = rx + rnd(p.seed, i, cyc, 3) * rw;
    const y0 = ry + rnd(p.seed, i, cyc, 4) * rh;
    const size = p.size[0] + (p.size[1] - p.size[0]) * rnd(p.seed, i, cyc, 5);
    const peak = p.brightness[0] + (p.brightness[1] - p.brightness[0]) * Math.pow(rnd(p.seed, i, cyc, 6), 2); // skewed dim: f13060 measured 10 stars, 7 of which peaked at 35–90
    let vx = 0, vy = 0;
    if (p.variant === 'drift') {
      const ang = rnd(p.seed, i, cyc, 7) * Math.PI * 2;
      const sp = 0.4 * Math.pow(3.2 / 0.4, rnd(p.seed, i, cyc, 8)); // log-uniform 0.4–3.2, mean ≈1.3–1.7
      vx = Math.cos(ang) * sp * p.speed;
      vy = Math.sin(ang) * sp * p.speed;
    } else if (p.variant === 'fast') {
      const sn = (size - p.size[0]) / (p.size[1] - p.size[0]); // bigger ones move faster (parallax)
      vx = -(1.5 + 3.0 * (0.4 * sn + 0.6 * rnd(p.seed, i, cyc, 7))) * p.speed;
      vy = (-1.5 + 4.5 * rnd(p.seed, i, cyc, 8)) * p.speed;
    }
    const x = x0 + vx * age;
    const y = y0 + vy * age;
    if (x < -4 || x > 1284 || y < -4 || y > 724) continue;
    // envelope: rise to peak over the first 5 frames, ease out over the last 12
    const rise = Math.min(1, age / 5);
    const fall = Math.min(1, (L - age) / 12);
    const env = Math.min(rise, fall);
    // per-frame twinkle: deterministic noise of ±twinkle (brightness only, position is not re-rolled)
    const tw = 1 + p.twinkle * (rnd(p.seed, i, frame, 9) * 2 - 1);
    const a = Math.min(1, Math.max(0, (peak / 255) * env * tw)) * p.opacity;
    if (a < 0.03) continue;
    out.push({x, y, s: size, a});
  }
  return out;
};

export const StarField: React.FC<Partial<StarFieldProps> & {frame?: number}> = (props) => {
  const cur = useCurrentFrame();
  const p: StarFieldProps = {...STAR_DEFAULT, ...props};
  const frame = props.frame ?? cur;
  const stars = starsAt(frame, p);
  return (
    <div style={{position: 'absolute', inset: 0, pointerEvents: 'none'}}>
      {stars.map((s, k) => (
        <div
          key={k}
          style={{
            position: 'absolute',
            left: s.x - s.s / 2,
            top: s.y - s.s / 2,
            width: s.s,
            height: s.s,
            borderRadius: '50%',
            background: '#fff',
            opacity: s.a,
            boxShadow: `0 0 ${Math.max(2, s.s * 1.3)}px rgba(255,255,255,0.8)`, // the original blobs at threshold 35 have 5–11px area and peak mostly at 35–90: soft and dim
          }}
        />
      ))}
    </div>
  );
};

/** Backdrop track: looks up the BgSpec for the original-footage frame (later specs take priority) and renders the fog and stars. N = original-footage frame number. If nothing overrides it, the default is drift with fog on. */
export const BgTrack: React.FC<{specs: BgSpec[]; defaultStars?: Partial<StarFieldProps>; defaultFog?: boolean}> = ({specs, defaultStars, defaultFog = FOG_DEFAULT_ON}) => {
  const N = useCurrentFrame() + 1;
  let stars: Partial<StarFieldProps> = {...defaultStars};
  let fog = defaultFog;
  for (const s of specs) {
    if (N < s.from || N > s.to) continue;
    if (s.stars !== undefined) stars = typeof s.stars === 'string' ? {variant: s.stars} : {...s.stars};
    if (s.fog !== undefined) fog = s.fog;
  }
  return (
    <>
      {fog ? <Fog /> : null}
      <StarField {...stars} />
    </>
  );
};

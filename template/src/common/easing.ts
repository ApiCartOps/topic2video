// Shared easing for the recommendation-system piece (summarized from measurements on seg_25/26/27). All functions are pure with no side effects. n = frames since the start (N − f0).
export const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

/** Bottom-up slide progress 0→1: 1 − (1 − n/N)^p. Measured on seg_25: the offsets Δ305 / icon group Δ320 / upward arrow Δ172 all match (1−n/22)^2.5 exactly.
 *  It is more accurate than an exponential k^n (exponential tails are off by more than 10px). Usage: y = yEnd + Δ·(1 − slideIn(n)), or y = yEnd + Δ·powOutRemain(n). */
export const slideIn = (n: number, N = 22, p = 2.5) => 1 - Math.pow(1 - clamp01(n / N), p);
/** Remaining amount of a power ease-out (1 − n/N)^p. Multiply it by the displacement Δ. seg_27 funnel-layer rise uses N=28, p=2.5. The balance beam uses N=21, p=3 (easeOutCubic). */
export const powOutRemain = (n: number, N = 22, p = 2.5) => Math.pow(1 - clamp01(n / N), p);
/** Exponential ease-out 1 − k^n (seg_20 horizontal label slide, k≈0.92; seg_26 opening reflow, k≈0.78). Returns progress 0→1. */
export const expOut = (k: number) => (n: number) => (n <= 0 ? 0 : 1 - Math.pow(k, n));
/** Power ease-in t^p (accelerating exit. seg_26 measured powers 1.7–2.0: KL group Δ≈0.69·t², top capsule Δ≈0.37·t^1.71). t∈[0,1].
 *  If you write it as "Δ = c·t^p" (t in frames), use Math.pow(n, p) times the coefficient directly. */
export const powIn = (p: number) => (t: number) => Math.pow(clamp01(t), p);
/** Power easeInOut: t<0.5 → 0.5·(2t)^p; otherwise 1 − 0.5·(2−2t)^p. seg_25 full-page scroll uses p=2.5, N=43 (cubic-bezier(0.6,0,0.4,1) is a close approximation). */
export const easeInOutPow = (p = 2.5) => (t: number) => {
  t = clamp01(t);
  return t < 0.5 ? 0.5 * Math.pow(2 * t, p) : 1 - 0.5 * Math.pow(2 - 2 * t, p);
};
export const easeOutCubic = (t: number) => 1 - Math.pow(1 - clamp01(t), 3);
export const easeInOutCubic = easeInOutPow(3);
export const easeOutQuad = (t: number) => 1 - Math.pow(1 - clamp01(t), 2);

/** Evaluates a CSS cubic-bezier(x1,y1,x2,y2) (Newton iteration, with bisection as a fallback). Takes t∈[0,1] and returns progress. */
export const cubicBezier = (x1: number, y1: number, x2: number, y2: number) => {
  const A = (a1: number, a2: number) => 1 - 3 * a2 + 3 * a1;
  const B = (a1: number, a2: number) => 3 * a2 - 6 * a1;
  const C = (a1: number) => 3 * a1;
  const calc = (u: number, a1: number, a2: number) => ((A(a1, a2) * u + B(a1, a2)) * u + C(a1)) * u;
  const slope = (u: number, a1: number, a2: number) => 3 * A(a1, a2) * u * u + 2 * B(a1, a2) * u + C(a1);
  return (t: number) => {
    t = clamp01(t);
    if (t === 0 || t === 1) return t;
    let u = t;
    for (let i = 0; i < 8; i++) {
      const s = slope(u, x1, x2);
      if (Math.abs(s) < 1e-6) break;
      u -= (calc(u, x1, x2) - t) / s;
    }
    if (u < 0 || u > 1 || Math.abs(calc(u, x1, x2) - t) > 1e-4) {
      let lo = 0, hi = 1;
      for (let i = 0; i < 40; i++) {
        u = (lo + hi) / 2;
        if (calc(u, x1, x2) < t) lo = u; else hi = u;
      }
    }
    return calc(u, y1, y2);
  };
};
/** 21-frame scale-in curve cubic-bezier(0.10,0.10,0.35,1) (the values recorded in the analysis). Usage: scale = s0 + (s1−s0)·BEZ_SCALE_IN(n/21). */
export const BEZ_SCALE_IN = cubicBezier(0.1, 0.1, 0.35, 1);

/** Emphasis scale pulse (two measurements on seg_25): scale 1 → peak (1.11–1.147) → 1, with up frames, hold frames, and down frames, easeInOut, no opacity change.
 *  Connector lines and arrows do not take part. It syncs with the subtitle start (starts 2 frames after the subtitle). Returns 1 when n<0 or after the end. */
export const emphasisPulse = (
  n: number,
  {peak = 1.11, up = 13, hold = 4, down = 13, ease = easeInOutPow(2.5)}: {peak?: number; up?: number; hold?: number; down?: number; ease?: (t: number) => number} = {},
) => {
  if (n <= 0) return 1;
  if (n < up) return 1 + (peak - 1) * ease(n / up);
  if (n < up + hold) return peak;
  if (n < up + hold + down) return peak - (peak - 1) * ease((n - up - hold) / down);
  return 1;
};

/**
 * Linear interpolation over keyframes (t is an original-footage frame number or a relative frame).
 * ⚠ First-value trap: when t is before the first keyframe, it returns the **first value** (not 0). A curve that only takes effect mid-shot must start with [shot start frame, starting value].
 *   Otherwise the first half of the shot stays fixed at the first keyframe's value. When t is past the last keyframe, it returns the last value.
 * Optional ease: eases the normalized progress within each segment (linear by default).
 */
export const kf = (t: number, pairs: Array<[number, number]>, ease: (u: number) => number = (u) => u) => {
  if (pairs.length === 0) return 0;
  if (t <= pairs[0][0]) return pairs[0][1];
  for (let i = 1; i < pairs.length; i++) {
    const [t0, v0] = pairs[i - 1];
    const [t1, v1] = pairs[i];
    if (t <= t1) return t1 === t0 ? v1 : v0 + (v1 - v0) * ease((t - t0) / (t1 - t0));
  }
  return pairs[pairs.length - 1][1];
};
/** Stepped hold: t before the first frame → first value. Otherwise, the value of the latest keyframe ≤ t (used for hard-cut sequences and glitch state machines). */
export const stepKf = (t: number, pairs: Array<[number, number]>) => {
  if (pairs.length === 0) return 0;
  if (t < pairs[0][0]) return pairs[0][1];
  for (let i = pairs.length - 1; i >= 0; i--) if (t >= pairs[i][0]) return pairs[i][1];
  return pairs[0][1];
};
/** Deterministic pseudo-random value in [0,1) (from any number of numeric seeds), for particles and jitter in each group. Math.random is not allowed. */
export const rnd = (...seeds: number[]) => {
  let h = 2166136261;
  for (const s of seeds) {
    h ^= Math.floor(s * 1000003) & 0xffffffff;
    h = Math.imul(h, 16777619);
  }
  h ^= h >>> 13;
  h = Math.imul(h, 0x5bd1e995);
  h ^= h >>> 15;
  return ((h >>> 0) % 100000) / 100000;
};

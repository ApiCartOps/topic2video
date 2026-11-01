import React from 'react';
import {FONT_ORB} from './common/lib';
import {clamp01, easeInOutPow} from './common';
import {CText, PURPLE, PURPLE_LIGHT, WHITE, GLOW_PURPLE, abs} from './ui';

/**
 * Light effects / highlight moments / depth / camera primitives (upgraded from the helper files of the sample's groups in 《RAG 与知识库》; rules in reference/composition-and-light.md).
 * Shot components use `import {…} from '../../fx'`. All are pure functions. The shot computes the animation from N and passes it in, or passes N/f0 and the component computes relative frames itself.
 * Quick reference:
 *   LightBar / LightSweep  purple light bars sweeping across (highlight-moment opening, three rounds)
 *   StageLine              central stage line: widens → breathes → white flash for 3 frames on the beat frame, then disappears
 *   GhostText              white-outline silhouette of the protagonist's text, fading in at 10% (preview)
 *   HaloRing               purple halo under a subject (white outer and inner outlines, purple gradient, dashed ripples). Can be split into front and back halves to sandwich the subject
 *   HeroGlow               double-layer purple soft glow for any rectangular protagonist, with a 30-frame breath
 *   BigNumber / countTo    large number (Orbitron, purple hard shadow, white light), tabular, can count
 *   Sparkle / GradBall     four-point star / bright-top black ball
 *   TiltPlane              tilted plane (depth layer)
 *   CameraRig / camAt      camera for a fixed push-in, pan, or full-page scroll (world coordinates → screen)
 *   SET_PIECE / setPiece   standard relative frames for an entrance-type highlight moment
 */

// ---- light bars ----
/** Single light bar: a purple gradient bar on black with a violet outer glow and a white core. alpha is the overall opacity */
export const LightBar: React.FC<{x: number; y: number; w: number; h: number; alpha?: number; color?: string; core?: boolean}> = ({x, y, w, h, alpha = 0.3, color = PURPLE_LIGHT, core = true}) => (
  <div style={{...abs(x, y, w, h), opacity: alpha}}>
    <div style={{position: 'absolute', inset: 0, borderRadius: h / 2, background: `linear-gradient(90deg, transparent 0%, ${color} 16%, ${color} 84%, transparent 100%)`, boxShadow: `0 0 ${h * 2.4}px ${h * 0.9}px rgba(102,45,248,.6)`}} />
    {core ? <div style={{position: 'absolute', left: w * 0.18, right: w * 0.18, top: h * 0.3, height: h * 0.4, borderRadius: h, background: 'linear-gradient(90deg, transparent 0%, #FFFFFF 28%, #FFFFFF 72%, transparent 100%)', boxShadow: '0 0 6px 1px rgba(255,255,255,.75)'}} /> : null}
  </div>
);
/** Light bar x: over n frames, sweeps from the left (−w) to 1280+w (easeInOut 1.6) */
export const sweepX = (n: number, w: number, len = 16) => -w + (1280 + 2 * w) * easeInOutPow(1.6)(clamp01(n / len));
/** Default three light bars [y, h, w, frame offset] (sample SC08) */
export const SWEEP_BARS: Array<[number, number, number, number]> = [[292, 6, 420, 0], [334, 10, 560, 2], [378, 6, 380, 4]];
/**
 * One or more sweep rounds: rounds gives the start frame of each round (the sample has 3 rounds, 18 frames apart, back to back). alphas gives each round's opacity. dy shifts everything vertically (to line the light up with the protagonist's center).
 * Each round has 3 bars with a 2-frame stagger over 16 frames. The tail ends on (1−t^6), so nothing disappears abruptly.
 */
export const LightSweep: React.FC<{N: number; rounds: number[]; alphas?: number[]; bars?: Array<[number, number, number, number]>; dy?: number; len?: number}> = ({N, rounds, alphas = [0.6, 0.55, 0.55], bars = SWEEP_BARS, dy = 0, len = 16}) => (
  <>
    {rounds.map((t0, k) =>
      bars.map(([y, h, w, off], i) => {
        const n = N - t0 - off;
        if (n < 0 || n > len) return null;
        return <LightBar key={`${k}-${i}`} x={sweepX(n, w, len)} y={y + dy - h / 2} w={w} h={h} alpha={(alphas[k] ?? 0.55) * (1 - Math.pow(clamp01(n / len), 6))} />;
      }),
    )}
  </>
);

// ---- stage line ----
/**
 * Central line: from frame f0, widens to w over 14 frames (power 2.5 ease-out). After that its alpha breathes at .45±.15. From flashAt, it flashes white for 3 frames (.95/.7/.35), then disappears.
 * Usage: the protagonist's GlitchIn beat frame = flashAt.
 */
export const StageLine: React.FC<{N: number; f0: number; flashAt?: number; cx?: number; cy?: number; w?: number; h?: number}> = ({N, f0, flashAt = Infinity, cx = 640, cy = 331, w = 720, h = 3}) => {
  const n = N - f0;
  if (n < 0) return null;
  const flash = N >= flashAt ? N - flashAt : -1;
  if (flash >= 3) return null;
  const lineW = w * (1 - Math.pow(1 - clamp01(n / 14), 2.5));
  const breathe = 0.45 + 0.15 * Math.sin(n * 0.28);
  return (
    <div style={{position: 'absolute', left: cx - lineW / 2, top: cy - h / 2, width: lineW, height: h, borderRadius: h, background: flash >= 0 ? WHITE : `linear-gradient(90deg, transparent, ${PURPLE_LIGHT} 20%, ${PURPLE_LIGHT} 80%, transparent)`, opacity: flash >= 0 ? [0.95, 0.7, 0.35][flash] : breathe, boxShadow: flash >= 0 ? '0 0 30px 8px rgba(255,255,255,.55)' : '0 0 18px 4px rgba(102,45,248,.5)'}} />
  );
};

// ---- ghost outline ----
/** Protagonist text with a white outline, transparent fill and a purple haze outline. The caller sets opacity (sample: (0.1+0.02·sin)·fadeIn(n,12). It stays as a base during the glitch and is removed at the pulse) */
export const GhostText: React.FC<{cx: number; cy: number; size: number; family?: string; weight?: number; letterSpacing?: number; opacity: number; dy?: number; scaleX?: number; children: React.ReactNode}> = ({cx, cy, size, family, weight = 400, letterSpacing = 8, opacity, dy = -4, scaleX = 1, children}) => {
  if (opacity <= 0) return null;
  return (
    <CText cx={cx} cy={cy} size={size} weight={weight} family={family} letterSpacing={letterSpacing} color="transparent" dy={dy} scaleX={scaleX} opacity={opacity} shadow="0 0 22px rgba(161,117,241,.95)" style={{WebkitTextStroke: `2px ${WHITE}`}}>
      {children}
    </CText>
  );
};
/** Standard opacity for a ghost outline: fades in to 0.10 over 12 frames from f0 and breathes. Removed at frame until */
export const ghostOpacity = (N: number, f0: number, until: number) => {
  const n = N - f0;
  if (n < 0 || N >= until) return 0;
  return (0.1 + 0.02 * Math.sin(n * 0.35)) * clamp01(n / 12);
};

// ---- halo ----
const ellipsePerim = (rx: number, ry: number) => Math.PI * (3 * (rx + ry) - Math.sqrt((3 * rx + ry) * (rx + 3 * ry)));
let haloSeq = 0;
/**
 * Purple halo under the subject (sample SC44 "moat"): outer ring rxo×ryo, inner ring rxi×ryi. p is the white-outline draw-on progress 0→1. fillOp is the opacity of the purple gradient fill.
 * phase is the dash phase of the ripples (sample floor(n/2)*5). half='back' draws only the back half (above cy), 'front' only the front half. Draw back, then the subject, then front, and the subject appears to stand inside the ring.
 */
export const HaloRing: React.FC<{cx?: number; cy?: number; rxo?: number; ryo?: number; rxi?: number; ryi?: number; p?: number; fillOp?: number; phase?: number; half?: 'back' | 'front' | 'both'; opacity?: number; ripples?: boolean}> = ({cx = 640, cy = 428, rxo = 335, ryo = 78, rxi = 245, ryi = 44, p = 1, fillOp = 0.85, phase = 0, half = 'both', opacity = 1, ripples = true}) => {
  const idRef = React.useRef<string | undefined>(undefined);
  if (!idRef.current) idRef.current = `halo-${haloSeq++}`;
  const id = idRef.current;
  const pe = 1 - Math.pow(1 - clamp01(p), 2);
  const PO = ellipsePerim(rxo, ryo), PI = ellipsePerim(rxi, ryi);
  const e = (rx: number, ry: number) => `M ${cx - rx} ${cy} a ${rx} ${ry} 0 1 0 ${rx * 2} 0 a ${rx} ${ry} 0 1 0 ${-rx * 2} 0 Z`;
  const ring = `${e(rxo, ryo)} ${e(rxi, ryi)}`;
  const clip = half === 'back' ? `url(#${id}-back)` : half === 'front' ? `url(#${id}-front)` : undefined;
  return (
    <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: 'drop-shadow(0 0 3px rgba(255,255,255,0.45))', opacity}}>
      <defs>
        <linearGradient id={`${id}-g`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#3A1E8C" />
          <stop offset="55%" stopColor={PURPLE} />
          <stop offset="100%" stopColor="#8F62F5" />
        </linearGradient>
        <clipPath id={`${id}-back`}><rect x={0} y={0} width={1280} height={cy} /></clipPath>
        <clipPath id={`${id}-front`}><rect x={0} y={cy} width={1280} height={720 - cy} /></clipPath>
      </defs>
      <g clipPath={clip}>
        <path d={ring} fill={`url(#${id}-g)`} fillRule="evenodd" opacity={fillOp} />
        <ellipse cx={cx} cy={cy} rx={rxo} ry={ryo} fill="none" stroke={WHITE} strokeWidth={2.5} strokeDasharray={PO} strokeDashoffset={PO * (1 - pe)} />
        <ellipse cx={cx} cy={cy} rx={rxi} ry={ryi} fill="none" stroke={WHITE} strokeWidth={2.5} strokeDasharray={PI} strokeDashoffset={PI * (1 - pe)} />
        {ripples ? [0.3, 0.55, 0.8].map((t, i) => (
          <ellipse key={i} cx={cx} cy={cy} rx={rxi + (rxo - rxi) * t} ry={ryi + (ryo - ryi) * t} fill="none" stroke={PURPLE_LIGHT} strokeWidth={1.6} strokeDasharray="16 22" strokeDashoffset={phase * (i % 2 ? -1 : 1) + i * 9} opacity={0.55 * fillOp} />
        )) : null}
      </g>
    </svg>
  );
};

// ---- protagonist glow ----
/** Adds a double-layer purple soft glow to a rectangular protagonist. Place it beneath the protagonist, at the same position and size. When N is passed, it breathes ±15% on a 30-frame cycle. k is the strength 0→1 (for a fade-in over 8 frames on activation). */
export const HeroGlow: React.FC<{x: number; y: number; w: number; h: number; r?: number; N?: number; k?: number; color?: string}> = ({x, y, w, h, r = 16, N, k = 1, color}) => {
  const breathe = N === undefined ? 1 : 1 + 0.15 * Math.sin((2 * Math.PI * N) / 30);
  const a = clamp01(k) * breathe;
  if (a <= 0.01) return null;
  const glow = color ? `0 0 ${(12 * a).toFixed(0)}px ${(3 * a).toFixed(0)}px ${color}59, 0 0 ${(42 * a).toFixed(0)}px ${(14 * a).toFixed(0)}px ${color}73` : GLOW_PURPLE;
  return <div style={{...abs(x, y, w, h), borderRadius: r, boxShadow: glow, opacity: color ? 1 : a}} />;
};

// ---- large numbers ----
export const fmtInt = (v: number) => Math.round(v).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
/** Counts from a to b over len frames (power 2 ease-out). Returns a rounded string with thousands separators */
export const countTo = (n: number, a: number, b: number, len = 20) => fmtInt(a + (b - a) * (1 - Math.pow(1 - clamp01(n / len), 2)));
/** Large number: Orbitron tabular, 6px purple hard shadow, and a purple soft glow (the same heavy treatment as the video title). unit is the small text below */
export const BigNumber: React.FC<{cx: number; cy: number; value: string | number; size?: number; color?: string; family?: string; weight?: number; letterSpacing?: number; shadow?: string; unit?: string; unitSize?: number; unitColor?: string; opacity?: number; dy?: number}> = ({cx, cy, value, size = 110, color = WHITE, family = FONT_ORB, weight = 700, letterSpacing = 2, shadow = `6px 6px 0 ${PURPLE}, 0 0 28px rgba(102,45,248,.45)`, unit, unitSize = 24, unitColor = '#A0A0A1', opacity = 1, dy = -2}) => (
  <>
    <CText cx={cx} cy={cy} size={size} weight={weight} family={family} color={color} letterSpacing={letterSpacing} opacity={opacity} dy={dy} shadow={shadow} style={{fontVariantNumeric: 'tabular-nums'}}>
      {value}
    </CText>
    {unit ? <CText cx={cx} cy={cy + size * 0.62 + unitSize / 2} size={unitSize} weight={600} color={unitColor} opacity={opacity}>{unit}</CText> : null}
  </>
);

// ---- small pieces ----
/** Four-point sparkle, r = outer radius */
export const Sparkle: React.FC<{cx: number; cy: number; r: number; opacity?: number; color?: string}> = ({cx, cy, r, opacity = 1, color = WHITE}) => {
  const k = 0.28;
  const d = `M0,${-r} C0,${-r * k} ${r * k},0 ${r},0 C${r * k},0 0,${r * k} 0,${r} C0,${r * k} ${-r * k},0 ${-r},0 C${-r * k},0 0,${-r * k} 0,${-r} Z`;
  return (
    <svg width={r * 2 + 8} height={r * 2 + 8} viewBox={`${-r - 4} ${-r - 4} ${r * 2 + 8} ${r * 2 + 8}`} style={{position: 'absolute', left: cx - r - 4, top: cy - r - 4, opacity, overflow: 'visible'}}>
      <path d={d} fill={color} />
    </svg>
  );
};
/** Black ball with a bright top (for nodes, or a ball running around a ring) */
export const GradBall: React.FC<{cx: number; cy: number; r: number; stroke?: number}> = ({cx, cy, r, stroke = 2.5}) => (
  <div style={{...abs(cx - r, cy - r, 2 * r, 2 * r), borderRadius: '50%', boxSizing: 'border-box', border: `${stroke}px solid #FFF`, background: 'linear-gradient(180deg, #F0F0F0 0%, #E8E8E8 3%, #919191 11.7%, #787878 20%, #5B5B5B 28%, #313131 40%, #0F0F0F 50%, #000 58%, #000 100%)'}} />
);

// ---- depth: tilted plane ----
/**
 * Tilted plane (for HNSW layers and spatial layers): a w×h plane centered at (cx,cy), turned into a lying parallelogram by skewX(skew°) scaleY(sy).
 * children are positioned absolutely in plane coordinates (origin top left, size w×h) and deform with the plane. Stacking several: 90px between layers, and the layers further back have opacity 0.6.
 */
export const TiltPlane: React.FC<{cx: number; cy: number; w?: number; h?: number; skew?: number; sy?: number; stroke?: string; sw?: number; fill?: string; opacity?: number; children?: React.ReactNode}> = ({cx, cy, w = 420, h = 260, skew = -20, sy = 0.5, stroke = WHITE, sw = 2, fill = 'rgba(0,0,0,.85)', opacity = 1, children}) => (
  <div style={{...abs(cx - w / 2, cy - h / 2, w, h), transform: `scaleY(${sy}) skewX(${skew}deg)`, transformOrigin: '50% 50%', opacity}}>
    <div style={{position: 'absolute', inset: 0, boxSizing: 'border-box', border: `${sw}px solid ${stroke}`, background: fill, filter: 'drop-shadow(0 0 2px rgba(255,255,255,.35))'}} />
    {children}
  </div>
);

// ---- camera ----
export type CamKey = {f: number; x: number; y: number; s: number};
/** Camera keyframe interpolation: easeInOutPow(2.5) between keys. Before the first key it stays on the first frame, and after the last it stays on the last frame. This avoids the first-value trap: the first frame must be set to the shot's starting state */
export const camAt = (N: number, keys: CamKey[], ease = easeInOutPow(2.5)) => {
  if (N <= keys[0].f) return keys[0];
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1], b = keys[i];
    if (N <= b.f) {
      const t = ease(clamp01((N - a.f) / Math.max(1, b.f - a.f)));
      return {f: N, x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, s: a.s + (b.s - a.s) * t};
    }
  }
  return keys[keys.length - 1];
};
/**
 * Camera: children use world coordinates (they coincide with the canvas when the default camera is x=640, y=360, s=1). A fixed push-in is the same (x,y) with a changing s (1→1.33 over 30–40 frames).
 * Pan or full-page scroll changes (x,y). A carry-over uses the same keys at the end of one shot and the start of the next. Scale also enlarges box-shadows and outlines, so past 1.4 the outlines look heavy.
 */
export const CameraRig: React.FC<{N: number; keys: CamKey[]; children: React.ReactNode; style?: React.CSSProperties}> = ({N, keys, children, style}) => {
  const c = camAt(N, keys);
  return (
    <div style={{position: 'absolute', inset: 0, transformOrigin: '0 0', transform: `translate(640px,360px) scale(${c.s.toFixed(4)}) translate(${(-c.x).toFixed(2)}px,${(-c.y).toFixed(2)}px)`, ...style}}>
      {children}
    </div>
  );
};

// ---- standard highlight-moment timing ----
/** Relative frames for an entrance-type highlight moment (T0 = the shot's start or clear frame, T1 = the protagonist's beat frame. Sample SC08: T0=1013, T1=1080) */
export const SET_PIECE = {
  sweeps: [4, 22, 40], // starts of the three LightSweep rounds (relative to T0)
  line: 18, // StageLine start (relative to T0)
  ghost: 37, // GhostText start (relative to T0)
  pulse: 12, // emphasisPulse start (relative to T1)
  sub: 16, // Chinese subtitle slideUp Δ80/22 (relative to T1)
  pills: 24, // word-by-word labels, SoftIn with a 2-frame stagger (relative to T1)
  minLen: 90, // minimum shot length in frames for a highlight moment
};
export const setPiece = (T0: number, T1: number) => ({
  sweeps: SET_PIECE.sweeps.map((d) => T0 + d),
  line: T0 + SET_PIECE.line,
  ghost: T0 + SET_PIECE.ghost,
  flash: T1,
  pulse: T1 + SET_PIECE.pulse,
  sub: T1 + SET_PIECE.sub,
  pills: T1 + SET_PIECE.pills,
});

// ---- circular glow spot / vignette / protagonist combinations (from G1's g1ui.tsx, moved into the shared layer for reuse) ----
/** Circular purple glow spot (radial-gradient). For large light areas under or behind a graphic protagonist. It suits circular or human protagonists (Gauge, PersonIcon, rings) better than HeroGlow's rectangular box-shadow. When N is passed, it breathes ±15% on a 30-frame cycle. k is the strength 0→1 */
export const GlowBlob: React.FC<{cx: number; cy: number; r: number; N?: number; k?: number; alpha?: number}> = ({cx, cy, r, N, k = 1, alpha = 0.34}) => {
  const breathe = N === undefined ? 1 : 1 + 0.15 * Math.sin((2 * Math.PI * N) / 30);
  const a = clamp01(k) * breathe * alpha;
  if (a <= 0.005) return null;
  return <div style={{position: 'absolute', left: cx - r, top: cy - r, width: 2 * r, height: 2 * r, borderRadius: '50%', background: `radial-gradient(circle, rgba(102,45,248,${a.toFixed(3)}) 0%, rgba(102,45,248,${(a * 0.55).toFixed(3)}) 34%, rgba(102,45,248,0) 70%)`}} />;
};
/** Screen-space top and bottom vignette (fades in over 18 frames in sync with a push-in): k 0→1. Place it outside CameraRig (screen space, does not move with the camera).
 *  The top band starts at y=top (100) with height topH (100) by default, and **does not darken the HUD capsule (y 28–100)**. The bottom band is 560–687 and stops at the progress bar. The bar is semi-transparent, so darkening behind it would darken the bar too (QC v1 C1). */
export const Vignette: React.FC<{k: number; alpha?: number; top?: number; topH?: number}> = ({k, alpha = 0.4, top = 100, topH = 100}) => {
  if (k <= 0.005) return null;
  const a = (alpha * clamp01(k)).toFixed(3);
  return (
    <>
      <div style={{position: 'absolute', left: 0, top, width: 1280, height: topH, background: `linear-gradient(180deg, rgba(0,0,0,${a}) 0%, rgba(0,0,0,0) 100%)`}} />
      <div style={{position: 'absolute', left: 0, top: 560, width: 1280, height: 127, background: `linear-gradient(0deg, rgba(0,0,0,${a}) 0%, rgba(0,0,0,0) 100%)`}} />
    </>
  );
};

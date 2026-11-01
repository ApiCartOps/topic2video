import React from 'react';
import {FONT_HEAVY, FONT_TECH, FONT_MONO, FONT_ORB, TEXT_DY} from './common/lib';
import {GlitchIn, powOutRemain, BEZ_SCALE_IN, clamp01, rnd} from './common';

/**
 * Shared graphics primitives and palette (black fill with a 2–3px white outline; purple = current focus; orange-red = metric or warning; grey = not in focus; green = correct). Shot components import them with `import {…} from '../../ui'`.
 * Every component is a pure function with absolute positioning (canvas 1280×720). The caller computes the animation from N and passes it in (opacity, p, s, and so on).
 */
// ---- palette ----
export const PURPLE = '#6630F8'; // standard capsule purple (102,48,248)
export const PURPLE_LIGHT = '#A175F1'; // light purple (highlight end, or after crossing the progress bar)
export const PURPLE_TECH = '#6530F4'; // purple for English technical terms
export const PURPLE_DEEP = '#5A3AD5'; // deep purple (curves, hard shadows)
export const PURPLE_PALE = '#E6DCFF';
export const ORANGE = '#F05F41'; // orange-red: metric numbers, the other side, emphasis
export const CORAL = '#F16043';
export const RED_DEEP = '#EC081F'; // deep red warning block
export const GREEN = '#8FF740'; // green check
export const GREY = '#A0A0A1'; // inactive
export const GREY_MID = '#747474';
export const GREY_LINE = '#4A4A4A'; // grid lines
export const GREY_LIGHT = '#D4D4D4';
export const WHITE = '#FFFFFF';
export const MAGENTA = '#D100D6';
export const CYAN = '#58FFEE';
export const GLOW_PURPLE = '0 0 12px 3px rgba(102,45,248,.35), 0 0 42px 14px rgba(102,45,248,.45)';
export const GLOW_PURPLE_S = '0 0 24px 8px rgba(102,45,248,.6)';
export const GLOW_ORANGE = '0 0 40px rgba(243,95,69,.75), 0 0 100px 10px rgba(243,95,69,.25)';
export const GLOW_RED = '0 0 60px 20px rgba(236,8,31,.42), 0 0 20px 6px rgba(236,8,31,.45)';
export const BLOOM = 'drop-shadow(0 0 3px rgba(255,255,255,0.5))';
export const BLOOM_SOFT = 'drop-shadow(0 0 2px rgba(255,255,255,0.35))';
export const TEXT_GLOW = '0 0 12px rgba(255,255,255,.55), 0 0 4px rgba(255,255,255,.35)';
export const PILL_SHADOW = 'drop-shadow(0 0 2px rgba(200,180,255,.6))';

// ---- motion helpers (n = N − f0) ----
export const fadeIn = (n: number, len = 12) => clamp01(n / len);
export const fadeOut = (n: number, len = 15) => 1 - clamp01(n / len);
/** Remaining offset of a bottom-up slide (px): Δ·(1−n/22)^2.5. Usage: top = yEnd + slideUp(n) */
export const slideUp = (n: number, d = 300, N = 22) => d * powOutRemain(n, N, 2.5);
/** 21-frame scale-in, 0→1 */
export const scaleIn = (n: number, N = 21) => BEZ_SCALE_IN(clamp01(n / N));
/** Accelerating exit offset (px): c·n² (n frames). Pair with exitFade */
export const exitAccel = (n: number, c = 0.5) => (n <= 0 ? 0 : c * n * n);
/** Exit fade of 6.7% per frame */
export const exitFade = (n: number) => (n <= 0 ? 1 : Math.pow(0.933, n));
/** Staggering: element i is delayed by i·step frames */
export const stagger = (i: number, step = 2) => i * step;

export const abs = (x: number, y: number, w?: number, h?: number): React.CSSProperties => ({position: 'absolute', left: x, top: y, width: w, height: h});


/** Non-flicker entry (user decision: glitch only for key terms; all other text and labels use this): len-frame easeOut fade-in plus dy px rise. n<0 renders nothing. Its signature matches GlitchIn (N, f0, children, style), so it can replace it directly. */
// ---- entry / exit / color mixing (tools the protocol mentions must really exist in the shared layer. They come from G1's g1ui.tsx. Groups import them directly, so no group writes its own copy) ----
/** Fade-in that is already visible on the first frame: n<0 → 0; n=0 ≈ 25% (len 8) / 32% (len 6); easeOut 2.5. Use it for a shot's first-frame entry. Do not use fadeIn(0)=0 */
export const softOp = (n: number, len = 8) => (n < 0 ? 0 : 1 - Math.pow(1 - clamp01((n + 1) / (len + 1)), 2.5));
/** For elements on a shot's first frame: ≈57% on the first frame (lessons: softOp(n+1,6)), so the empty-frame criterion can measure it */
export const firstOp = (n: number, len = 6) => (n < 0 ? 0 : softOp(n + 1, len));
/** Fade to zero before a hard cut: 1−(n/len)^1.5 over the last len frames. It is 0 when N = to */
export const exitOp = (N: number, to: number, len = 8) => {
  const n = N - (to - len);
  return n <= 0 ? 1 : Math.max(0, 1 - Math.pow(n / len, 1.5));
};
/** Lit element turns its light off first: the glow strength goes 1→0 over the len frames before the fade-to-zero starts (it is 0 when N = to−exitLen) */
export const glowOffK = (N: number, to: number, len = 6, exitLen = 8) => 1 - clamp01((N - (to - exitLen - len)) / len);
export const mix = (a: number, b: number, t: number) => a + (b - a) * clamp01(t);
/** Mixes two #rrggbb colors by k, returns rgb() */
export const mixHex = (a: string, b: string, k: number) => {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  const t = clamp01(k);
  return `rgb(${pa.map((v, i) => Math.round(v + (pb[i] - v) * t)).join(',')})`;
};
/** Strength-scaled GLOW_PURPLE (k 0→1), used with glowOffK to turn light off first */
export const glowPurple = (k: number) => `0 0 12px 3px rgba(102,45,248,${(0.35 * clamp01(k)).toFixed(3)}), 0 0 42px 14px rgba(102,45,248,${(0.45 * clamp01(k)).toFixed(3)})`;
export const glowPurpleS = (k: number) => `0 0 24px 8px rgba(102,45,248,${(0.6 * clamp01(k)).toFixed(3)})`;

export const SoftIn: React.FC<{N: number; f0: number; children: React.ReactNode; len?: number; dy?: number; style?: React.CSSProperties}> = ({N, f0, children, len = 8, dy = 10, style}) => {
  const n = N - f0;
  if (n < 0) return null;
  const t = clamp01((n + 1) / (len + 1)); // already ≈25% visible on the first frame (final check v3: at n=0 it was 0, so an HUD term change and an entry each lost one frame)
  const e = 1 - Math.pow(1 - t, 2.5);
  const extra = typeof style?.opacity === 'number' ? style.opacity : 1;
  return (
    <div style={{position: 'absolute', inset: 0, ...style, opacity: e * extra, transform: `translateY(${((1 - e) * dy).toFixed(2)}px)${style?.transform ? ' ' + style.transform : ''}`}}>
      {children}
    </div>
  );
};

// ---- text ----
export type CTextProps = {
  cx: number; cy: number; size: number; weight?: number; family?: string; color?: string; letterSpacing?: number;
  dy?: number; scaleX?: number; italic?: boolean; opacity?: number; shadow?: string; style?: React.CSSProperties; children: React.ReactNode;
};
/** Single line of text, placed by its ink center (cx, cy). Noto CJK ink sits 3–7px below the center of the line box, so dy defaults to −2 */
export const CText: React.FC<CTextProps> = ({cx, cy, size, weight = 700, family = FONT_HEAVY, color = WHITE, letterSpacing = 0, dy = TEXT_DY, scaleX = 1, italic = false, opacity = 1, shadow, style, children}) => (
  <div style={{position: 'absolute', left: cx, top: cy + dy, transform: `translate(-50%,-50%) scaleX(${scaleX})`, whiteSpace: 'nowrap', fontFamily: family, fontWeight: weight, fontSize: size, fontStyle: italic ? 'italic' : 'normal', lineHeight: 1, color, letterSpacing, opacity, textShadow: shadow, ...style}}>
    {children}
  </div>
);
/** English technical term: Exo 2 purple italic, narrowed with scaleX */
export const TechText: React.FC<{cx: number; cy: number; text: string; fontSize?: number; color?: string; scaleX?: number; weight?: number; letterSpacing?: number; glow?: boolean; opacity?: number; style?: React.CSSProperties}> = ({cx, cy, text, fontSize = 32, color = PURPLE_TECH, scaleX = 0.81, weight = 600, letterSpacing = 1, glow = true, opacity = 1, style}) => (
  <CText cx={cx} cy={cy} size={fontSize} weight={weight} family={FONT_TECH} color={color} letterSpacing={letterSpacing} scaleX={scaleX} italic opacity={opacity} dy={0} shadow={glow ? '0 0 6px rgba(80,30,200,.7)' : undefined} style={style}>
    {text}
  </CText>
);
/** Monospaced numbers or code text */
export const MonoText: React.FC<{x: number; y: number; size?: number; color?: string; opacity?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({x, y, size = 22, color = WHITE, opacity = 1, children, style}) => (
  <div style={{position: 'absolute', left: x, top: y, fontFamily: FONT_MONO, fontSize: size, lineHeight: 1.3, color, opacity, whiteSpace: 'pre', ...style}}>{children}</div>
);

// ---- boxes / capsules ----
export type BoxProps = {x: number; y: number; w: number; h: number; r?: number; fill?: string; stroke?: string; sw?: number; dashed?: boolean; opacity?: number; glow?: string; style?: React.CSSProperties; children?: React.ReactNode};
/** Black rectangle with a white border (border-box; fill can be a gradient string; glow is passed as boxShadow) */
export const Box: React.FC<BoxProps> = ({x, y, w, h, r = 0, fill = '#000', stroke = WHITE, sw = 2, dashed = false, opacity = 1, glow, style, children}) => (
  <div style={{...abs(x, y, w, h), boxSizing: 'border-box', background: fill, border: sw > 0 ? `${sw}px ${dashed ? 'dashed' : 'solid'} ${stroke}` : undefined, borderRadius: r, opacity, boxShadow: glow, ...style}}>{children}</div>
);
export type PillProps = BoxProps & {text?: React.ReactNode; fontSize?: number; weight?: number; color?: string; family?: string; textDy?: number; letterSpacing?: number; scaleX?: number};
/** Fully rounded capsule with centered text ((x, y, w, h) includes the outline) */
export const Pill: React.FC<PillProps> = ({text, fontSize = 28, weight = 700, color = WHITE, family = FONT_HEAVY, textDy = TEXT_DY, letterSpacing = 0, scaleX = 1, r, h, ...box}) => (
  <Box {...box} h={h} r={r ?? h / 2}>
    <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `translateY(${textDy}px) scaleX(${scaleX})`, fontFamily: family, fontWeight: weight, fontSize, color, letterSpacing, lineHeight: 1, whiteSpace: 'nowrap'}}>{text}</div>
  </Box>
);
/** Large label block (a simplified version of the recall/rerank system): color block, extra-bold text at scaleX .73, and a same-colored outer glow */
export const TagBlock: React.FC<{x: number; y: number; w?: number; h?: number; color?: string; text: string; fontSize?: number; opacity?: number; glow?: boolean; skewPx?: number}> = ({x, y, w = 237, h = 62, color = PURPLE, text, fontSize = 44, opacity = 1, glow = true, skewPx = 0}) => (
  <div style={{...abs(x, y, w, h), opacity}}>
    <div style={{position: 'absolute', inset: 0, background: color, transform: skewPx ? `skewX(${(-Math.atan2(skewPx, h) * 180) / Math.PI}deg)` : undefined, boxShadow: glow ? `0 0 28px 10px ${color}99` : undefined}} />
    <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_HEAVY, fontWeight: 900, fontSize, color: WHITE, letterSpacing: -1, lineHeight: 1, transform: 'translateY(-2px) scaleX(0.8)', WebkitTextStroke: '1.5px #000', paintOrder: 'stroke fill'}}>{text}</div>
  </div>
);

// ---- SVG graphics ----
/** Full-frame 1280×720 SVG container (BLOOM by default) */
export const Svg: React.FC<{children: React.ReactNode; style?: React.CSSProperties; bloom?: boolean; opacity?: number}> = ({children, style, bloom = true, opacity = 1}) => (
  <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: bloom ? BLOOM : undefined, opacity, ...style}}>
    {children}
  </svg>
);
/** Straight arrow in any direction (SVG <g>): p = growth progress 0→1 (grows from the root: the shaft arrives first, then the head follows). The endpoint (x1,y1) is the tip */
export const LineArrow: React.FC<{x0: number; y0: number; x1: number; y1: number; p?: number; rodW?: number; headL?: number; headW?: number; color?: string; opacity?: number; dashed?: boolean}> = ({x0, y0, x1, y1, p = 1, rodW = 3, headL = 22, headW = 24, color = WHITE, opacity = 1, dashed = false}) => {
  if (p <= 0) return null;
  const dx = x1 - x0, dy = y1 - y0;
  const L = Math.hypot(dx, dy) || 1;
  const ux = dx / L, uy = dy / L;
  const len = L * clamp01(p);
  const hl = Math.min(headL, len);
  const tx = x0 + ux * len, ty = y0 + uy * len; // current tip
  const bx = tx - ux * hl, by = ty - uy * hl; // center of the head's base
  const px = -uy, py = ux;
  const hw = (headW / 2) * (hl / headL);
  return (
    <g opacity={opacity}>
      <line x1={x0} y1={y0} x2={bx + ux * 1} y2={by + uy * 1} stroke={color} strokeWidth={rodW} strokeLinecap="butt" strokeDasharray={dashed ? '8 7' : undefined} />
      <polygon points={`${tx},${ty} ${bx + px * hw},${by + py * hw} ${bx - px * hw},${by - py * hw}`} fill={color} />
    </g>
  );
};
/** Horizontal arrow as a div (anchored at the left end with scaleX, so it grows from the root). When dir is 'left', the right end is the root */
export const ArrowH: React.FC<{x: number; y: number; w?: number; h?: number; p?: number; color?: string; dir?: 'right' | 'left'; shaft?: number; opacity?: number}> = ({x, y, w = 70, h = 27, p = 1, color = WHITE, dir = 'right', shaft = 3, opacity = 1}) => (
  <div style={{...abs(x, y, w, h), opacity, transform: `scaleX(${clamp01(p) * (dir === 'left' ? -1 : 1)})`, transformOrigin: dir === 'left' ? '100% 50%' : '0 50%'}}>
    <div style={{position: 'absolute', left: 0, top: h / 2 - shaft / 2, width: w - 20, height: shaft, background: color}} />
    <div style={{position: 'absolute', left: w - 24, top: 0, width: 0, height: 0, borderTop: `${h / 2}px solid transparent`, borderBottom: `${h / 2}px solid transparent`, borderLeft: `24px solid ${color}`}} />
  </div>
);
/** Check / cross (used inside a full-frame SVG; p is the draw-on progress) */
export const Check: React.FC<{cx: number; cy: number; size?: number; color?: string; sw?: number; p?: number; opacity?: number}> = ({cx, cy, size = 60, color = GREEN, sw = 7, p = 1, opacity = 1}) => {
  const s = size / 60;
  const pts: Array<[number, number]> = [[cx - 26 * s, cy + 2 * s], [cx - 8 * s, cy + 20 * s], [cx + 28 * s, cy - 20 * s]];
  const total = Math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]) + Math.hypot(pts[2][0] - pts[1][0], pts[2][1] - pts[1][1]);
  return <polyline points={pts.map((q) => q.join(',')).join(' ')} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={total} strokeDashoffset={total * (1 - clamp01(p))} opacity={opacity} />;
};
export const Cross: React.FC<{cx: number; cy: number; size?: number; color?: string; sw?: number; p?: number; opacity?: number}> = ({cx, cy, size = 50, color = CORAL, sw = 7, p = 1, opacity = 1}) => {
  const r = size / 2;
  const d = size * Math.SQRT2;
  return (
    <g opacity={opacity} stroke={color} strokeWidth={sw} strokeLinecap="round">
      <line x1={cx - r} y1={cy - r} x2={cx + r} y2={cy + r} strokeDasharray={d} strokeDashoffset={d * (1 - clamp01(Math.min(1, p * 2)))} />
      <line x1={cx + r} y1={cy - r} x2={cx - r} y2={cy + r} strokeDasharray={d} strokeDashoffset={d * (1 - clamp01(Math.max(0, p * 2 - 1)))} />
    </g>
  );
};

// ---- semantic icons (RAG theme) ----
/** Document page: black fill with white border, a folded corner, and text lines (lines of them). The label sits below */
export const DocIcon: React.FC<{x: number; y: number; w?: number; h?: number; lines?: number; color?: string; fill?: string; sw?: number; label?: string; labelSize?: number; opacity?: number; accent?: string; glow?: string}> = ({x, y, w = 64, h = 80, lines = 4, color = WHITE, fill = '#000', sw = 2, label, labelSize = 22, opacity = 1, accent, glow}) => {
  const f = w * 0.3;
  return (
    <div style={{...abs(x, y, w, h + (label ? labelSize + 14 : 0)), opacity}}>
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: glow ? undefined : BLOOM_SOFT}}>
        <path d={`M${sw / 2},${sw / 2} H${w - f - sw / 2} L${w - sw / 2},${f + sw / 2} V${h - sw / 2} H${sw / 2} Z`} fill={fill} stroke={color} strokeWidth={sw} strokeLinejoin="round" />
        <path d={`M${w - f - sw / 2},${sw / 2} V${f + sw / 2} H${w - sw / 2}`} fill="none" stroke={color} strokeWidth={sw} strokeLinejoin="round" />
        {Array.from({length: lines}, (_, i) => {
          const ly = f + 12 + i * ((h - f - 22) / Math.max(1, lines - 1 + 0.6));
          const lw = (i === lines - 1 ? 0.55 : 0.72) * w;
          return <rect key={i} x={w * 0.14} y={ly} width={lw} height={3} fill={accent && i === 0 ? accent : color} opacity={accent && i === 0 ? 1 : 0.85} />;
        })}
      </svg>
      {label ? <CText cx={w / 2} cy={h + labelSize / 2 + 8} size={labelSize} weight={600} color={color} dy={-1}>{label}</CText> : null}
    </div>
  );
};
/** Database cylinder (vector database / index) */
export const DBIcon: React.FC<{cx: number; cy: number; w?: number; h?: number; color?: string; fill?: string; sw?: number; opacity?: number; label?: string; labelSize?: number; accent?: string}> = ({cx, cy, w = 120, h = 130, color = WHITE, fill = '#000', sw = 2.5, opacity = 1, label, labelSize = 24, accent}) => {
  const ry = w * 0.18;
  const x0 = cx - w / 2, y0 = cy - h / 2;
  return (
    <div style={{...abs(x0, y0, w, h + (label ? labelSize + 14 : 0)), opacity}}>
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: BLOOM_SOFT}}>
        <path d={`M${sw},${ry} V${h - ry} A${w / 2 - sw},${ry} 0 0 0 ${w - sw},${h - ry} V${ry}`} fill={fill} stroke={color} strokeWidth={sw} />
        <ellipse cx={w / 2} cy={ry} rx={w / 2 - sw} ry={ry - sw / 2} fill={accent ?? fill} stroke={color} strokeWidth={sw} />
        {[0.42, 0.66].map((t) => <path key={t} d={`M${sw},${h * t} A${w / 2 - sw},${ry} 0 0 0 ${w - sw},${h * t}`} fill="none" stroke={color} strokeWidth={sw * 0.7} opacity={0.8} />)}
      </svg>
      {label ? <CText cx={w / 2} cy={h + labelSize / 2 + 8} size={labelSize} weight={600} color={color} dy={-1}>{label}</CText> : null}
    </div>
  );
};
/** Text chunk card: black fill with a rounded white border and several grey-white text lines. active → purple border and soft glow */
export const ChunkCard: React.FC<{x: number; y: number; w?: number; h?: number; lines?: number; active?: boolean; opacity?: number; r?: number; title?: string; seed?: number; sw?: number}> = ({x, y, w = 150, h = 92, lines = 4, active = false, opacity = 1, r = 8, title, seed = 1, sw = 2}) => (
  <Box x={x} y={y} w={w} h={h} r={r} stroke={active ? PURPLE_LIGHT : WHITE} sw={sw} opacity={opacity} glow={active ? GLOW_PURPLE_S : undefined}>
    {title ? <div style={{position: 'absolute', left: 12, top: 8, fontFamily: FONT_HEAVY, fontSize: 15, fontWeight: 600, color: PURPLE_LIGHT, whiteSpace: 'nowrap', lineHeight: 1}}>{title}</div> : null}
    {Array.from({length: lines}, (_, i) => {
      const lw = (0.5 + 0.42 * (((seed * 7 + i * 13) % 10) / 10)) * (w - 24);
      const top = (title ? 30 : 14) + i * ((h - (title ? 40 : 26)) / Math.max(1, lines - 0.3));
      return <div key={i} style={{position: 'absolute', left: 12, top, width: i === lines - 1 ? lw * 0.6 : lw, height: 3, background: active ? WHITE : GREY_LIGHT, opacity: 0.9}} />;
    })}
  </Box>
);
/** Language-model icon: a rounded square with a three-layer dot grid of "neurons" inside. The label is optional */
export const LLMIcon: React.FC<{cx: number; cy: number; size?: number; color?: string; accent?: string; opacity?: number; label?: string; labelSize?: number; glow?: boolean}> = ({cx, cy, size = 140, color = WHITE, accent = PURPLE, opacity = 1, label, labelSize = 28, glow = true}) => {
  const s = size;
  const cols = [0.28, 0.5, 0.72];
  const rows = [[0.3, 0.5, 0.7], [0.22, 0.38, 0.62, 0.78], [0.3, 0.5, 0.7]];
  return (
    <div style={{...abs(cx - s / 2, cy - s / 2, s, s + (label ? labelSize + 16 : 0)), opacity}}>
      <div style={{position: 'absolute', left: 0, top: 0, width: s, height: s, boxSizing: 'border-box', background: '#000', border: `3px solid ${color}`, borderRadius: s * 0.16, boxShadow: glow ? GLOW_PURPLE : undefined}} />
      <svg width={s} height={s} viewBox={`0 0 ${s} ${s}`} style={{position: 'absolute', left: 0, top: 0}}>
        {cols.slice(0, -1).map((cxr, ci) => rows[ci].map((ry, i) => rows[ci + 1].map((ry2, j) => <line key={`${ci}-${i}-${j}`} x1={cxr * s} y1={ry * s} x2={cols[ci + 1] * s} y2={ry2 * s} stroke={GREY} strokeWidth={1.3} opacity={0.7} />)))}
        {cols.map((cxr, ci) => rows[ci].map((ry, i) => <circle key={`${ci}-${i}`} cx={cxr * s} cy={ry * s} r={s * 0.045} fill={ci === 1 ? accent : color} />))}
      </svg>
      {label ? <CText cx={s / 2} cy={s + labelSize / 2 + 10} size={labelSize} weight={700} color={color}>{label}</CText> : null}
    </div>
  );
};
/** Top HUD capsule (keeps the (533,28,216,51) position, width follows the text). GlitchIn entry. tech is the English subtitle below it (center y 92) */
export const TopCapsule: React.FC<{N: number; f0: number; text: string; w?: number; fill?: string; tech?: string; opacity?: number; textSize?: number; glitch?: boolean}> = ({N, f0, text, w = 216, fill = PURPLE, tech, opacity = 1, textSize = 33, glitch = false}) => (
  // User decision (2026-09-06): glitch only on key terms. HUD term changes default to a SoftIn fade-in, and glitch must be requested explicitly
  glitch ? (
  <GlitchIn N={N} f0={f0} style={{opacity}}>
    <Pill x={640 - w / 2} y={28} w={w} h={51} fill={fill} sw={2} text={text} fontSize={textSize} weight={700} letterSpacing={1} textDy={TEXT_DY} style={{filter: PILL_SHADOW}} />
    {tech ? <TechText cx={640} cy={94} text={tech} fontSize={30} scaleX={0.8} /> : null}
  </GlitchIn>
  ) : (
  <SoftIn N={N} f0={f0} style={{opacity}} dy={6}>
    <Pill x={640 - w / 2} y={28} w={w} h={51} fill={fill} sw={2} text={text} fontSize={textSize} weight={700} letterSpacing={1} textDy={TEXT_DY} style={{filter: PILL_SHADOW}} />
    {tech ? <TechText cx={640} cy={94} text={tech} fontSize={30} scaleX={0.8} /> : null}
  </SoftIn>
  )
);

// ---- funnel layers (layered filtering such as recall → rerank → generate) ----
/** Asymmetric horizontal gradient stops from grey to purple (measured on the original: the darkest plateau is at t≈0.5–0.6, and the right half rises more slowly). k=0 grey, k=1 purple. */
const TRAP_STOPS: Array<[number, number, number[]]> = [[0, 224, [230, 220, 255]], [0.18, 190, [170, 140, 250]], [0.45, 160, [110, 60, 248]], [0.6, 160, [102, 45, 248]], [0.8, 178, [125, 85, 248]], [1, 224, [230, 220, 255]]];
export const trapStops = (k: number): Array<[number, string]> => TRAP_STOPS.map(([t, g, p]) => [t, `rgb(${p.map((v) => Math.round(g + (v - g) * k)).join(',')})`] as [number, string]);
let trapSeq = 0;
/** Inverted-trapezoid funnel layer: top width wTop, bottom width wBot, height h. Horizontal gradient fill, 2px white border, centered text. k 0→1 turns grey to purple (used for an 11-frame color change). */
export const Trap: React.FC<{cx: number; y: number; wTop: number; wBot: number; h: number; k?: number; stops?: Array<[number, string]>; text?: React.ReactNode; fontSize?: number; textDy?: number; stroke?: number; textShadow?: string; opacity?: number}> = ({cx, y, wTop, wBot, h, k = 1, stops, text, fontSize = 34, textDy = TEXT_DY, stroke = 2, textShadow = '0 2px 12px rgba(0,0,0,.45)', opacity = 1}) => {
  const idRef = React.useRef<string | undefined>(undefined);
  if (!idRef.current) idRef.current = `trap-${trapSeq++}`;
  const id = idRef.current;
  const Wd = wTop + 8, x0 = cx - Wd / 2;
  const pts = `${4},${1} ${4 + wTop},${1} ${4 + (wTop + wBot) / 2},${1 + h} ${4 + (wTop - wBot) / 2},${1 + h}`;
  return (
    <div style={{...abs(x0, y, Wd, h + 4), opacity}}>
      <svg width={Wd} height={h + 4} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="1" y2="0">
            {(stops ?? trapStops(k)).map(([o, c], i) => <stop key={i} offset={o} stopColor={c} />)}
          </linearGradient>
        </defs>
        <polygon points={pts} fill={`url(#${id})`} stroke={WHITE} strokeWidth={stroke} strokeLinejoin="miter" />
      </svg>
      {text !== undefined ? <div style={{position: 'absolute', left: 0, top: 0, width: Wd, height: h, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_HEAVY, fontWeight: 700, fontSize, color: WHITE, lineHeight: 1, textShadow, transform: `translateY(${textDy}px)`}}>{text}</div> : null}
    </div>
  );
};

/** General numeric counter (tabular; Orbitron by default. A lone "0" is read as Ø, so pass family={FONT_HEAVY} in that case) */
export const Counter: React.FC<{cx: number; cy: number; value: string | number; size?: number; color?: string; opacity?: number; weight?: number; family?: string}> = ({cx, cy, value, size = 58, color = WHITE, opacity = 1, weight = 700, family = FONT_ORB}) => (
  <CText cx={cx} cy={cy} size={size} weight={weight} family={family} color={color} opacity={opacity} letterSpacing={-0.5} shadow={TEXT_GLOW} style={{fontVariantNumeric: 'tabular-nums'}}>
    {value}
  </CText>
);

// ---- semantic icons (AI systems / performance engineering theme, added in the fourth video; pick and trim per topic) ----
/** GPU chip: pins on all four sides, a black rounded body with a white border, and a square core grid inside (lit 0–1 is the fraction lit, row-major. Lit cores are purple, unlit ones have grey borders). glow adds a purple soft glow (turn it on when this is the protagonist). label sits below. size is the outer edge length including the pins. */
export const GPUChip: React.FC<{cx: number; cy: number; size?: number; color?: string; accent?: string; lit?: number; grid?: number; opacity?: number; label?: string; labelSize?: number; glow?: boolean; pins?: boolean; sw?: number; glowK?: number}> = ({cx, cy, size = 170, color = WHITE, accent = PURPLE, lit = 1, grid = 6, opacity = 1, label, labelSize = 26, glow = true, pins = true, sw = 3, glowK = 1}) => {
  const s = size;
  const pinL = s * 0.075;
  const inner = s - 2 * pinL;
  const x0 = pinL, y0 = pinL;
  const coreArea = inner * 0.62;
  const cell = coreArea / grid;
  const c0 = x0 + (inner - coreArea) / 2;
  const nLit = Math.round(clamp01(lit) * grid * grid);
  const pinsPerSide = 7;
  const pinW = inner / (pinsPerSide * 2.4);
  return (
    <div style={{...abs(cx - s / 2, cy - s / 2, s, s + (label ? labelSize + 16 : 0)), opacity}}>
      {glow && glowK > 0.005 ? <div style={{position: 'absolute', left: x0, top: y0, width: inner, height: inner, borderRadius: inner * 0.12, boxShadow: glowPurple(glowK)}} /> : null}
      <svg width={s} height={s} viewBox={`0 0 ${s} ${s}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: BLOOM_SOFT}}>
        {pins
          ? Array.from({length: pinsPerSide}, (_, i) => {
              const t = x0 + inner * ((i + 0.5) / pinsPerSide) - pinW / 2;
              return (
                <g key={i} fill={color} opacity={0.9}>
                  <rect x={t} y={0} width={pinW} height={pinL} />
                  <rect x={t} y={s - pinL} width={pinW} height={pinL} />
                  <rect x={0} y={t} width={pinL} height={pinW} />
                  <rect x={s - pinL} y={t} width={pinL} height={pinW} />
                </g>
              );
            })
          : null}
        <rect x={x0 + sw / 2} y={y0 + sw / 2} width={inner - sw} height={inner - sw} rx={inner * 0.12} fill="#000" stroke={color} strokeWidth={sw} />
        {Array.from({length: grid * grid}, (_, i) => {
          const r = Math.floor(i / grid), c = i % grid;
          const on = i < nLit;
          return <rect key={i} x={c0 + c * cell + cell * 0.12} y={c0 + r * cell + cell * 0.12} width={cell * 0.76} height={cell * 0.76} rx={cell * 0.12} fill={on ? accent : '#141414'} stroke={on ? 'none' : GREY_LINE} strokeWidth={1} />;
        })}
      </svg>
      {label ? <CText cx={s / 2} cy={s + labelSize / 2 + 10} size={labelSize} weight={700} color={color}>{label}</CText> : null}
    </div>
  );
};

/** Timeline bar (profiler track / GPU utilization): a row of segments. The f value of each segment is its share (sum ≈1). kind: busy = purple, idle = black with a grey dashed edge, comm = orange, cpu = grey, sync = light purple (communication segments in the profiler panel, so they do not clash with the orange glow of idle. QC v1 C2 #2). p is the draw-on ratio from the left. label is the track name on the left (grey, 22px).
 *  glowIdleK (0–1; glowIdle=true is 1) gives an orange glow to every idle segment ("this is the problem"). It is **drawn outside the clipping container** (otherwise overflow:hidden would clip it), and it can fade in and out. */
export type TlSeg = {f: number; kind: 'busy' | 'idle' | 'comm' | 'cpu' | 'sync'};
export const TimelineBar: React.FC<{x: number; y: number; w: number; h?: number; segs: TlSeg[]; p?: number; label?: string; labelW?: number; labelSize?: number; opacity?: number; sw?: number; glowIdle?: boolean; glowIdleK?: number}> = ({x, y, w, h = 44, segs, p = 1, label, labelW = 110, labelSize = 22, opacity = 1, sw = 2, glowIdle = false, glowIdleK}) => {
  const bw = w - (label ? labelW : 0);
  const gk = clamp01(glowIdleK ?? (glowIdle ? 1 : 0));
  const fill: Record<TlSeg['kind'], string> = {busy: PURPLE, idle: '#000', comm: ORANGE, cpu: GREY_MID, sync: PURPLE_LIGHT};
  let acc = 0;
  const segsX = segs.map((sg) => { const sx = acc * bw; acc += sg.f; return {...sg, sx, sw: sg.f * bw}; });
  const shown = bw * clamp01(p);
  return (
    <div style={{...abs(x, y, w, h), opacity}}>
      {label ? <CText cx={labelW / 2 - 6} cy={h / 2} size={labelSize} weight={600} color={GREY}>{label}</CText> : null}
      {gk > 0.005
        ? segsX.filter((sg) => sg.kind === 'idle' && sg.sx < shown).map((sg, i) => (
            <div key={`g${i}`} style={{position: 'absolute', left: (label ? labelW : 0) + sg.sx, top: 0, width: Math.min(sg.sw, shown - sg.sx), height: h, borderRadius: 4, boxShadow: `0 0 ${Math.round(40 * gk)}px rgba(243,95,69,${(0.75 * gk).toFixed(3)}), 0 0 ${Math.round(100 * gk)}px 10px rgba(243,95,69,${(0.25 * gk).toFixed(3)})`}} />
          ))
        : null}
      <div style={{position: 'absolute', left: label ? labelW : 0, top: 0, width: shown, height: h, overflow: 'hidden'}}>
        {segsX.map((sg, i) => {
          const idle = sg.kind === 'idle';
          return <div key={i} style={{position: 'absolute', left: sg.sx, top: 0, width: sg.sw, height: h, boxSizing: 'border-box', background: fill[sg.kind], border: `${sw}px ${idle ? 'dashed' : 'solid'} ${idle ? GREY : WHITE}`, borderRadius: 4}} />;
        })}
      </div>
    </div>
  );
};

/** Gauge (the throttle or utilization dial of "fed at full throttle"): a 240° arc (−210°→30°), v∈[0,1]. The part of the arc reached is purple with a soft glow, the rest is grey. White needle. value is an optional large number (Orbitron) in the lower part of the dial. label is grey text below the dial. The radius r should be at least 120 to be a protagonist (overall height ≈1.7r). */
export const Gauge: React.FC<{cx: number; cy: number; r?: number; v: number; color?: string; accent?: string; sw?: number; label?: string; labelSize?: number; value?: string; valueSize?: number; opacity?: number; glow?: boolean}> = ({cx, cy, r = 120, v, color = WHITE, accent = PURPLE, sw = 8, label, labelSize = 24, value, valueSize = 44, opacity = 1, glow = true}) => {
  const a0 = -210, a1 = 30;
  const vv = clamp01(v);
  const toXY = (deg: number, rr: number): [number, number] => [cx + rr * Math.cos((deg * Math.PI) / 180), cy + rr * Math.sin((deg * Math.PI) / 180)];
  const arc = (from: number, to: number, rr: number) => {
    const [ax, ay] = toXY(from, rr), [bx, by] = toXY(to, rr);
    return `M${ax},${ay} A${rr},${rr} 0 ${to - from > 180 ? 1 : 0} 1 ${bx},${by}`;
  };
  const av = a0 + (a1 - a0) * vv;
  const [nx, ny] = toXY(av, r - sw - 10);
  return (
    <div style={{position: 'absolute', inset: 0, opacity, pointerEvents: 'none'}}>
      <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: BLOOM_SOFT}}>
        <path d={arc(a0, a1, r)} fill="none" stroke={GREY_LINE} strokeWidth={sw} strokeLinecap="round" />
        {vv > 0.005 ? <path d={arc(a0, av, r)} fill="none" stroke={accent} strokeWidth={sw} strokeLinecap="round" style={glow ? {filter: 'drop-shadow(0 0 10px rgba(102,45,248,.85))'} : undefined} /> : null}
        {Array.from({length: 9}, (_, i) => {
          const d = a0 + ((a1 - a0) * i) / 8;
          const [tx0, ty0] = toXY(d, r - sw - 4), [tx1, ty1] = toXY(d, r - sw - 14);
          return <line key={i} x1={tx0} y1={ty0} x2={tx1} y2={ty1} stroke={color} strokeWidth={2} opacity={0.8} />;
        })}
        <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={color} strokeWidth={4} strokeLinecap="round" />
        <circle cx={cx} cy={cy} r={9} fill="#000" stroke={color} strokeWidth={3} />
      </svg>
      {value ? <CText cx={cx} cy={cy + r * 0.68} size={valueSize} weight={700} family={FONT_ORB} color={WHITE} shadow={TEXT_GLOW}>{value}</CText> : null}
      {label ? <CText cx={cx} cy={cy + r + labelSize + 6} size={labelSize} weight={600} color={GREY}>{label}</CText> : null}
    </div>
  );
};

/** Cluster grid (shows "many": 8 → 80,000 GPUs): cols×rows squares of at least 6px (SVG. The per-frame DOM budget is ≤600, so the grid is at most about 450 cells). The first lit squares are lit in accent, the rest are grey-bordered. scatter=true lights them in a deterministic shuffled order ("coming online gradually"). */
export const ClusterGrid: React.FC<{x: number; y: number; cols: number; rows: number; cell?: number; gap?: number; lit?: number; color?: string; accent?: string; opacity?: number; seed?: number; scatter?: boolean}> = ({x, y, cols, rows, cell = 14, gap = 6, lit, color = GREY_LINE, accent = PURPLE, opacity = 1, seed = 1, scatter = false}) => {
  const n = cols * rows;
  const nl = lit === undefined ? n : Math.max(0, Math.min(n, Math.round(lit)));
  const order = Array.from({length: n}, (_, i) => i);
  if (scatter) for (let i = n - 1; i > 0; i--) { const j = Math.floor(rnd(seed, i) * (i + 1)); const t = order[i]; order[i] = order[j]; order[j] = t; }
  const rank: number[] = new Array(n); order.forEach((idx, k) => { rank[idx] = k; });
  const W2 = cols * (cell + gap) - gap, H2 = rows * (cell + gap) - gap;
  return (
    <div style={{...abs(x, y, W2, H2), opacity}}>
      <svg width={W2} height={H2} viewBox={`0 0 ${W2} ${H2}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
        {Array.from({length: n}, (_, i) => {
          const r = Math.floor(i / cols), c = i % cols;
          const on = rank[i] < nl;
          return <rect key={i} x={c * (cell + gap) + 0.5} y={r * (cell + gap) + 0.5} width={cell - 1} height={cell - 1} rx={2} fill={on ? accent : '#000'} stroke={on ? accent : color} strokeWidth={1} opacity={on ? 1 : 0.8} />;
        })}
      </svg>
    </div>
  );
};

/** Server rack: a vertical frame plus `units` server rows (a status light on the left of each row: the first lit rows are purple, the rest grey). glow adds a purple soft glow. label below. h should be at least 170 to carry a protagonist. */
export const RackIcon: React.FC<{cx: number; cy: number; w?: number; h?: number; units?: number; lit?: number; color?: string; accent?: string; sw?: number; opacity?: number; label?: string; labelSize?: number; glow?: boolean}> = ({cx, cy, w = 110, h = 200, units = 6, lit, color = WHITE, accent = PURPLE, sw = 2.5, opacity = 1, label, labelSize = 22, glow = false}) => {
  const nl = lit ?? units;
  const uh = (h - 2 * sw - 8) / units;
  return (
    <div style={{...abs(cx - w / 2, cy - h / 2, w, h + (label ? labelSize + 14 : 0)), opacity}}>
      {glow ? <div style={{position: 'absolute', left: 0, top: 0, width: w, height: h, borderRadius: 8, boxShadow: GLOW_PURPLE}} /> : null}
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: BLOOM_SOFT}}>
        <rect x={sw / 2} y={sw / 2} width={w - sw} height={h - sw} rx={8} fill="#000" stroke={color} strokeWidth={sw} />
        {Array.from({length: units}, (_, i) => {
          const y = sw + 4 + i * uh;
          const on = i < nl;
          return (
            <g key={i}>
              <rect x={sw + 6} y={y + 3} width={w - 2 * sw - 12} height={uh - 6} rx={3} fill="#0a0a0a" stroke={GREY_MID} strokeWidth={1.5} />
              <circle cx={sw + 16} cy={y + uh / 2} r={3.5} fill={on ? accent : GREY_LINE} />
              <rect x={sw + 28} y={y + uh / 2 - 1.5} width={w - 2 * sw - 44} height={3} fill={on ? GREY_LIGHT : GREY_LINE} opacity={0.8} />
            </g>
          );
        })}
      </svg>
      {label ? <CText cx={w / 2} cy={h + labelSize / 2 + 6} size={labelSize} weight={600} color={color}>{label}</CText> : null}
    </div>
  );
};

/** Person (head and shoulders): a team role. accent fills the shoulders (current focus). glow adds a purple light. label below. size ≥96. */
export const PersonIcon: React.FC<{cx: number; cy: number; size?: number; color?: string; fill?: string; sw?: number; label?: string; labelSize?: number; accent?: string; opacity?: number; glow?: boolean}> = ({cx, cy, size = 96, color = WHITE, fill = '#000', sw = 2.5, label, labelSize = 22, accent, opacity = 1, glow = false}) => {
  const s = size;
  const hr = s * 0.2;
  return (
    <div style={{...abs(cx - s / 2, cy - s / 2, s, s + (label ? labelSize + 14 : 0)), opacity}}>
      <svg width={s} height={s} viewBox={`0 0 ${s} ${s}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: glow ? 'drop-shadow(0 0 10px rgba(102,45,248,.75))' : BLOOM_SOFT}}>
        <path d={`M${sw},${s - sw} V${s * 0.8} A${s / 2 - sw},${s * 0.3} 0 0 1 ${s - sw},${s * 0.8} V${s - sw} Z`} fill={accent ?? fill} stroke={color} strokeWidth={sw} strokeLinejoin="round" />
        <circle cx={s / 2} cy={hr + sw + s * 0.06} r={hr} fill={fill} stroke={color} strokeWidth={sw} />
      </svg>
      {label ? <CText cx={s / 2} cy={s + labelSize / 2 + 6} size={labelSize} weight={600} color={color}>{label}</CText> : null}
    </div>
  );
};

/** Code card: black fill, rounded white border, a language tag at the top left (22px, **drawn 17px above the card**. Watch the y position in chapters with a flow track), and monospaced code lines. Lines marked hot glow orange ("hot spot"). active → purple border and soft glow. */
export const CodeCard: React.FC<{x: number; y: number; w?: number; h?: number; tag?: string; tagColor?: string; lines?: number; hot?: number; active?: boolean; seed?: number; opacity?: number; r?: number; glowK?: number}> = ({x, y, w = 220, h = 150, tag, tagColor = PURPLE, lines = 5, hot = -1, active = false, seed = 1, opacity = 1, r = 10, glowK = 1}) => (
  <Box x={x} y={y} w={w} h={h} r={r} stroke={active ? PURPLE_LIGHT : WHITE} sw={2} opacity={opacity} glow={active && glowK > 0.005 ? glowPurpleS(glowK) : undefined}>
    {tag ? <Pill x={14} y={-17} w={Math.max(76, Math.round(tag.length * 13.5) + 30)} h={34} fill={tagColor} sw={2} text={tag} fontSize={22} weight={700} /> : null}
    {Array.from({length: lines}, (_, i) => {
      const indent = ((seed * 3 + i * 5) % 3) * 14;
      const lw = (0.35 + 0.5 * (((seed * 7 + i * 13) % 10) / 10)) * (w - 40 - indent);
      const top = 30 + i * ((h - 44) / lines);
      const isHot = i === hot;
      return <div key={i} style={{position: 'absolute', left: 18 + indent, top, width: lw, height: 4, borderRadius: 2, background: isHot ? ORANGE : GREY_LIGHT, opacity: isHot ? 1 : 0.85, boxShadow: isHot ? GLOW_ORANGE : undefined}} />;
    })}
  </Box>
);

/** Open-source repository card: black fill, rounded white border, a small fork icon on the left, the repo name (700), and one line of grey description. active → purple border with soft glow and a purple dot at the base of the fork. */
export const RepoCard: React.FC<{x: number; y: number; w?: number; h?: number; name: string; desc?: string; active?: boolean; opacity?: number; nameSize?: number; descSize?: number}> = ({x, y, w = 360, h = 84, name, desc, active = false, opacity = 1, nameSize = 28, descSize = 22}) => {
  const sc = active ? PURPLE_LIGHT : WHITE;
  return (
    <Box x={x} y={y} w={w} h={h} r={12} stroke={sc} sw={2} opacity={opacity} glow={active ? GLOW_PURPLE_S : undefined}>
      <svg width={44} height={44} viewBox="0 0 44 44" style={{position: 'absolute', left: 16, top: h / 2 - 22}}>
        <path d="M12,14 V20 Q12,26 18,26 H26 Q32,26 32,20 V14 M22,26 V31" fill="none" stroke={sc} strokeWidth={2.5} />
        <circle cx={12} cy={9} r={5} fill="#000" stroke={sc} strokeWidth={2.5} />
        <circle cx={32} cy={9} r={5} fill="#000" stroke={sc} strokeWidth={2.5} />
        <circle cx={22} cy={36} r={5} fill={active ? PURPLE : '#000'} stroke={sc} strokeWidth={2.5} />
      </svg>
      <div style={{position: 'absolute', left: 74, top: desc ? 14 : h / 2 - nameSize / 2 - 2, fontFamily: FONT_HEAVY, fontSize: nameSize, fontWeight: 700, color: WHITE, lineHeight: 1, whiteSpace: 'nowrap'}}>{name}</div>
      {desc ? <div style={{position: 'absolute', left: 74, top: 14 + nameSize + 8, fontFamily: FONT_HEAVY, fontSize: descSize, fontWeight: 500, color: GREY, lineHeight: 1, whiteSpace: 'nowrap'}}>{desc}</div> : null}
    </Box>
  );
};

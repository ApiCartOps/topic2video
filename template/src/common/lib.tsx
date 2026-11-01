import React from 'react';
import {AbsoluteFill, continueRender, delayRender, staticFile} from 'remotion';
import {VIDEO} from '../config';

// Canvas and frame-number conventions: 1280×720 at 30 fps. Frame number N starts at 1 (N = useCurrentFrame() + F0, where F0 = the shot's ShotDef.from).
export const W = 1280;
export const H = 720;
export const FPS = 30;

export const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
export const lerp = (t: number, t0: number, t1: number, v0: number, v1: number) => {
  if (t1 === t0) return v1;
  return v0 + (v1 - v0) * clamp((t - t0) / (t1 - t0), 0, 1);
};
/** Piecewise-linear keyframes [frame, value][]. ⚠ First-value trap: when t is before the first keyframe, it returns the first value (not 0). */
export const keyframes = (t: number, kf: Array<[number, number]>) => {
  if (t <= kf[0][0]) return kf[0][1];
  for (let i = 1; i < kf.length; i++) if (t <= kf[i][0]) return lerp(t, kf[i - 1][0], kf[i][0], kf[i - 1][1], kf[i][1]);
  return kf[kf.length - 1][1];
};
export const stepHold = (t: number, kf: Array<[number, number]>) => {
  if (t < kf[0][0]) return 0;
  for (let i = kf.length - 1; i >= 0; i--) if (t >= kf[i][0]) return kf[i][1];
  return 0;
};

// ---- directional blur (SVG feGaussianBlur. σ<0.8 does nothing in Chromium. feConvolveMatrix is banned) ----
let blurSeq = 0;
export const DirBlur: React.FC<{bx: number; by: number; style?: React.CSSProperties; children: React.ReactNode}> = ({bx, by, style, children}) => {
  const idRef = React.useRef<string | undefined>(undefined);
  if (!idRef.current) idRef.current = `dirblur-${blurSeq++}`;
  const id = idRef.current;
  const active = bx > 0.05 || by > 0.05;
  return (
    <AbsoluteFill style={style}>
      {active ? (
        <svg width={0} height={0} style={{position: 'absolute'}}>
          <defs>
            <filter id={id} x="-60%" y="-60%" width="220%" height="220%" colorInterpolationFilters="sRGB">
              <feGaussianBlur stdDeviation={`${Math.max(0, bx)} ${Math.max(0, by)}`} />
            </filter>
          </defs>
        </svg>
      ) : null}
      <AbsoluteFill style={{filter: active ? `url(#${id})` : undefined}}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---- fonts (all bundled with the template under the OFL license. Noto Sans SC includes the full Latin character set, so English videos use it for body text and subtitles too) ----
export const FONT_HEAVY = `'Noto Sans SC', 'PingFang SC', 'Hiragino Sans GB', sans-serif`; // all Chinese text: titles at 900 (often narrowed with scaleX .8–.85), labels 600–800, subtitles 700
export const FONT_TECH = `'Exo 2', 'Helvetica Neue', sans-serif`; // English technical terms: purple bold italic with scaleX .8
export const FONT_WIDE = `'Audiowide', 'Orbitron', sans-serif`; // wide display type (video title, uppercase abbreviations)
export const FONT_ORB = `'Orbitron', 'Audiowide', sans-serif`; // numbers, chapter numerals, HUD counters
export const FONT_MONO = `'SF Mono', Menlo, Consolas, monospace`; // code and vector numbers
export const FONT_SERIF = `'Times New Roman', Times, serif`; // formulas
export const FONT_EN = `'Helvetica Neue', Helvetica, Arial, sans-serif`;

// ---- language switch (VIDEO.lang in src/config.ts) ----
/** 'zh' Chinese video (default) or 'en' English video. Affects font narrowing, baseline compensation, and copy and subtitle budgets (see reference/narration-storyboard.md §5). */
export const LANG = VIDEO.lang ?? 'zh';
/** Chinese titles are conventionally narrowed with scaleX .8–.85. Narrowing Latin letters distorts them, so English videos always use 1. */
export const SQUEEZE = LANG === 'en' ? 1 : 0.85;
/** The CJK line box puts the ink 3–7px below the top, so centered text needs pre-compensation. Latin does not. */
export const TEXT_DY = LANG === 'en' ? 0 : -2;

/** Mounted once at the top of Main. Uses delayRender to wait until the fonts are ready. */
export const Fonts: React.FC = () => {
  const [handle] = React.useState(() => delayRender('fonts'));
  React.useEffect(() => {
    Promise.all([
      new FontFace('Noto Sans SC', `url(${staticFile('fonts/NotoSansSC.ttf')})`, {weight: '100 900'} as FontFaceDescriptors).load(),
      new FontFace('Exo 2', `url(${staticFile('fonts/Exo2-Italic.ttf')})`, {weight: '100 900', style: 'italic'} as FontFaceDescriptors).load(),
      new FontFace('Audiowide', `url(${staticFile('fonts/Audiowide-Regular.ttf')})`).load(),
      new FontFace('Orbitron', `url(${staticFile('fonts/Orbitron[wght].ttf')})`, {weight: '400 900'} as FontFaceDescriptors).load(),
    ])
      .then((fs) => {
        fs.forEach((f) => (document.fonts as unknown as {add: (f: FontFace) => void}).add(f));
        continueRender(handle);
      })
      .catch(() => continueRender(handle));
  }, [handle]);
  return null;
};

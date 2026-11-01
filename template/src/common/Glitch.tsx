import React from 'react';
import {rnd} from './easing';

/**
 * 12-frame glitch entry template. Per-frame lum matches seg_06/07/08/10/19/20/23/24 exactly, so it can be a global constant:
 * opacity = [0.5,1,0.5,0,0.5,0,0.5,1,0.75,0.5,0.75,1], and it stays at 1 from frame 13 on. Measured across several segments: **pure opacity**, with no displacement, RGB offset or slicing.
 * Exact levels are 0.53–0.55 and 0.77–0.78 (using 0.55/0.78 for all three segments also works, via GLITCH_SEQ_B).
 * Versions with afterimages or RGB offset (such as seg_00 "召回", frames f34–44, seg_20 "粗排" glitch text, and seg_28's six-frame full-frame slicing at the ending) use the rgbSplit / slices parameters.
 */
export const GLITCH_SEQ = [0.5, 1, 0.5, 0, 0.5, 0, 0.5, 1, 0.75, 0.5, 0.75, 1];
export const GLITCH_SEQ_B = [0.55, 1, 0.55, 0, 0.55, 0, 0.55, 1, 0.78, 0.55, 0.78, 1];
/** n = N − f0: n<0 → 0 (not yet entered); 0..11 → the sequence; ≥12 → 1. */
export const glitchOpacity = (n: number, seq: number[] = GLITCH_SEQ) => (n < 0 ? 0 : n >= seq.length ? 1 : seq[n]);

let glitchSeq = 0;
/** Tints any content to a single color (for the magenta and cyan copies): feColorMatrix takes luminance into the given channels and keeps alpha. */
const TintDefs: React.FC<{id: string}> = ({id}) => (
  <svg width={0} height={0} style={{position: 'absolute'}}>
    <defs>
      {/* magenta #D100D6 (209,0,214) */}
      <filter id={`${id}-m`} colorInterpolationFilters="sRGB">
        <feColorMatrix type="matrix" values="0.174 0.586 0.059 0 0  0 0 0 0 0  0.178 0.600 0.061 0 0  0 0 0 1 0" />
      </filter>
      {/* cyan #58FFEE (88,255,238) */}
      <filter id={`${id}-c`} colorInterpolationFilters="sRGB">
        <feColorMatrix type="matrix" values="0.073 0.247 0.025 0 0  0.213 0.715 0.072 0 0  0.199 0.667 0.067 0 0  0 0 0 1 0" />
      </filter>
    </defs>
  </svg>
);

export type GlitchInProps = {
  N: number; // current frame number in the original footage
  f0: number; // entry start frame (frame 0 of the sequence)
  children: React.ReactNode;
  seq?: number[];
  /** Maximum px offset of the RGB-shifted copies (0 = off). Random offset per frame during the flicker. With persistSplit, the fixed offset (−6,−3)/(+3,+5) is kept after entry (seg_28 title). */
  rgbSplit?: number;
  persistSplit?: boolean;
  /** Maximum px horizontal offset of slices (0 = off). During the flicker, each frame has 3–4 random bands offset independently (seg_00 afterimage ±8, seg_28 ending ±80). */
  slices?: number;
  sliceBands?: number;
  seed?: number;
  /** Whether slicing continues after the flicker ends (default no). */
  persistSlices?: boolean;
  style?: React.CSSProperties;
};

/** 12-frame glitch entry container. n<0 renders nothing. n≥12 renders as is (the RGB offset can be kept). Children use absolute positioning (the container is the full-frame AbsoluteFill). */
export const GlitchIn: React.FC<GlitchInProps> = ({N, f0, children, seq = GLITCH_SEQ, rgbSplit = 0, persistSplit = false, slices = 0, sliceBands = 4, seed = 1, persistSlices = false, style}) => {
  const idRef = React.useRef<string | undefined>(undefined);
  if (!idRef.current) idRef.current = `rsglitch-${glitchSeq++}`;
  const id = idRef.current;
  const n = N - f0;
  if (n < 0) return null;
  const active = n < seq.length;
  const op = glitchOpacity(n, seq);
  const box: React.CSSProperties = {position: 'absolute', inset: 0, overflow: 'hidden', ...style};
  if (op <= 0) return <div style={box} />;

  // slicing: cut the full frame into sliceBands random horizontal bands, each shifted horizontally on its own
  const sliced = (node: React.ReactNode, key: string) => {
    const doSlice = slices > 0 && (active || persistSlices);
    if (!doSlice) return <div key={key} style={{position: 'absolute', inset: 0}}>{node}</div>;
    const cuts: number[] = [0];
    for (let b = 1; b < sliceBands; b++) cuts.push(rnd(seed, N, b, 11) * 720);
    cuts.push(720);
    cuts.sort((a, b) => a - b);
    return (
      <React.Fragment key={key}>
        {cuts.slice(0, -1).map((y0, b) => {
          const y1 = cuts[b + 1];
          const dx = (rnd(seed, N, b, 12) * 2 - 1) * slices * (rnd(seed, N, b, 13) < 0.35 ? 0 : 1);
          return (
            <div key={b} style={{position: 'absolute', inset: 0, clipPath: `inset(${y0}px 0 ${720 - y1}px 0)`, transform: `translateX(${dx.toFixed(1)}px)`}}>
              {node}
            </div>
          );
        })}
      </React.Fragment>
    );
  };

  const doSplit = rgbSplit > 0 && (active || persistSplit);
  let mOff: [number, number] = [-6, -3];
  let cOff: [number, number] = [3, 5];
  if (doSplit && active) {
    const k = rgbSplit / 6;
    mOff = [-(3 + 6 * rnd(seed, N, 21)) * k, -(1 + 4 * rnd(seed, N, 22)) * k];
    cOff = [(1 + 4 * rnd(seed, N, 23)) * k, (2 + 6 * rnd(seed, N, 24)) * k];
  } else if (doSplit) {
    const k = rgbSplit / 6;
    mOff = [-6 * k, -3 * k];
    cOff = [3 * k, 5 * k];
  }
  return (
    <div style={{...box, opacity: op * (typeof style?.opacity === 'number' ? style.opacity : 1)}}> {/* Root cause of RF3: the sequence opacity must multiply the incoming style.opacity. Otherwise the outer fade multiplier is overwritten */}
      {doSplit ? <TintDefs id={id} /> : null}
      {doSplit ? (
        <div style={{position: 'absolute', inset: 0, filter: `url(#${id}-m)`, transform: `translate(${mOff[0].toFixed(1)}px, ${mOff[1].toFixed(1)}px)`}}>{sliced(children, 'm')}</div>
      ) : null}
      {doSplit ? (
        <div style={{position: 'absolute', inset: 0, filter: `url(#${id}-c)`, transform: `translate(${cOff[0].toFixed(1)}px, ${cOff[1].toFixed(1)}px)`}}>{sliced(children, 'c')}</div>
      ) : null}
      {sliced(children, 'main')}
    </div>
  );
};

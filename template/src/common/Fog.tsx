import React from 'react';
/**
 * Bottom fog gradient (backdrop layer, beneath the content). Measured column medians (f700/f3000/f9000/f12500/f13060 are identical, so it is present across the whole video. The "pure black" on seg_19 only meant the bottom was not measured):
 * y≤430 → 1; y460 6; y500 10; y540 15; y580 19; y620 24; y660 29; y680 31 ≈ linear 0→#1F1F1F (0.124 gray levels per px), full width, no fade-in.
 * It sits below the grid and content layers (values under the content layer at seg_22 f12380 and f12500 are unchanged). Subtitles and the progress bar sit above it.
 * Still calibration v1 (top 430→#1F1F1F) came out 2 gray levels darker than the original column medians → top 415 / #212121 (original: y440 3, y520 13, y600 22, y680 31).
 * Shot components must **not** draw an opaque black background again (it would cover the fog and stars). For a full-black section, turn it off with BgSpec.fog=false.
 */
export const FOG_DEFAULT_ON = true; // final call pending from the main session (seg_19 is recorded as "pure black", but measurement shows fog)
export const Fog: React.FC<{top?: number; bottom?: number; from?: string; to?: string; opacity?: number}> = ({top = 415, bottom = 687, from = '#000000', to = '#212121', opacity = 1}) => (
  // Main session (QC v1 RQ3): the fog's final color must extend all the way to the bottom edge at y720. The original progress bar sits on ≈#212121 (track 100 / fill (114,103,145)). v1 stopped at 687, so the bar sat over pure black (78 / (100,89,131))
  <div style={{position: 'absolute', left: 0, top, width: 1280, height: 720 - top, background: `linear-gradient(180deg, ${from} 0%, ${to} ${(((bottom - top) / (720 - top)) * 100).toFixed(2)}%, ${to} 100%)`, opacity, pointerEvents: 'none'}} />
);

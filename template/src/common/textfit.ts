/**
 * Text-width estimation and adaptive font size. Pure functions that do not measure the DOM, so rendering is deterministic (the same frame is identical on any machine).
 *
 * Em widths are averages measured on the fonts bundled with the template (fontTools, weights 700–900):
 *   Noto Sans SC: lowercase .566, uppercase .668, digits .590, space .227, half-width punctuation .325, CJK ideographs 1.000
 *   Accented Latin letters (é ü ñ ß…) .49–.69, so .58 is used
 *   Punctuation, arrows and math symbols from U+2000 on (— … “ ” → ∑ ≤ ×) are almost all 1em in Noto Sans SC
 *   (exceptions: en dash .53, em dash .88. Treating them as 1 overestimates, which is the safe direction and only shrinks the font sooner)
 *   Audiowide uppercase .788 / Orbitron uppercase .815 / Exo 2 uppercase .606 → converted with the EM_* factors
 * text_em() in scripts/tts_build.py is the Python version of the same table. Change one, and update the other.
 * Purpose: a Chinese subtitle chunk of up to 16 characters (≈704px) always fits, but an English chunk of 8 words can run to 1300px and off the frame,
 * so subtitles, progress-bar chapter names and chapter-card titles all pass through fitSize as a fallback. The real constraint is still on the script side (see narration-storyboard.md).
 */
export const EM_HEAVY = 1;      // Noto Sans SC (body text / subtitles / titles)
export const EM_WIDE = 1.18;    // Audiowide (video title, uppercase abbreviations)
export const EM_ORB = 1.2;      // Orbitron (numbers / chapter numerals)
export const EM_TECH = 0.92;    // Exo 2 (English technical terms, narrow italic)

/** Estimates the width of a string, in em (1em = fontSize px) */
export const textEm = (s: string, emScale = 1): number => {
  let em = 0;
  for (const ch of s) {
    const c = ch.codePointAt(0) ?? 32;
    if (c >= 0x2000) em += 1;                              // CJK, fullwidth punctuation, and punctuation, arrows and math symbols from U+2000 on
    else if (ch === ' ') em += 0.227;
    else if (ch >= 'A' && ch <= 'Z') em += 0.668;
    else if (ch >= '0' && ch <= '9') em += 0.59;
    else if (ch >= 'a' && ch <= 'z') em += 0.566;
    else if (c >= 0xc0 && c < 0x250) em += 0.58;           // accented Latin letters (Latin-1 / Extended-A / B)
    else em += 0.325;                                      // half-width punctuation
  }
  return em * emScale;
};

/** Character count (by code point, not by UTF-16 unit) */
const charCount = (s: string): number => [...s].length;

/**
 * Estimated width in px. letterSpacing is a CSS px value. Chromium adds it after every character, including the last,
 * and it does not scale with font size. So large text with letterSpacing, such as the opening or chapter cards, must include it in the calculation.
 */
export const textW = (s: string, size: number, emScale = 1, letterSpacing = 0): number => textEm(s, emScale) * size + letterSpacing * charCount(s);

/**
 * If the text is too wide, it scales the font proportionally, down to minSize (default 78%). The return value keeps one decimal place to avoid sub-pixel jitter.
 * The letterSpacing portion of the width does not change with font size, so it is subtracted from maxW before solving for the font size.
 * If it is still too wide at minSize, the copy violates the per-chunk length budget. Shorten the copy. Do not rely on this function.
 */
export const fitSize = (s: string, maxW: number, size: number, minSize = size * 0.78, emScale = 1, letterSpacing = 0): number => {
  const em = textEm(s, emScale);
  const extra = letterSpacing * charCount(s);
  if (em * size + extra <= maxW) return size;
  return Math.max(minSize, Math.round(((maxW - extra) / Math.max(1e-6, em)) * 10) / 10);
};

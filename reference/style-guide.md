# Style guide (visual system)

In one line: **a black backdrop (stars plus a fog gradient at the bottom, or a dot wave)** with white line-art motion graphics. Every shape is either "black fill with a 2–3px white outline" or "solid purple or orange fill with a white outline". Chinese titles use extra-bold Noto Sans SC 900, often squeezed with scaleX .8–.85. English technical terms use bold italic purple Exo 2. A purple HUD capsule sits at the top, 44px white subtitles with black outlines sit at the bottom, and a semi-transparent chapter progress bar runs along the bottom edge. Reference frames: `examples/rag/frames/ref_*.jpg` (look at them before drawing anything).

## 1. Canvas and safe area (1280×720 at 30 fps)
| Area | Pixels | Notes |
|---|---|---|
| Black base | full frame #000 | The only opaque black in Main. Shot components **must not** draw their own opaque black background. |
| Fog | y415→687 linear #000→#212121, 687→720 fixed #212121 | Always on across the video (`common/Fog.tsx`). |
| StarField | spawn zone 0–687, 80 stars of 2–4px, brightness 35–255 (dim), drift 0.4–3.2px/frame, lifetime 60–200 frames, ±30% flicker per frame | Deterministic pure function (`common/StarField.tsx`). `BG_Gn` can turn it off for a frame range with `{fog:false, stars:'none'}`. |
| DotFieldBg (optional, replaces fog and stars) | Scaled from a 960×540 design coordinate: dot spacing 48px, radius 2–2.7px, base color #0b0c11, dot color #cfe0ff, opacity (0.2 + 0.6k²) × radial edge falloff. A diagonal wavefront sweeps across in about 9.3 s. A static .06 noise layer prevents color banding. | Port of the dot-field-wave from video-talkcraft `motion-systems/backdrop.tsx` (`common/DotFieldBg.tsx`). Enable with `config.bg = 'dots'`. It is mutually exclusive with the star-and-fog backdrop. `stars:'none'` in `BG_Gn` also turns it off. It is a screen-space static texture that does not follow camera moves. `frame_metrics.py` removes the dots on the same grid before measuring. |
| Top HUD capsule | (533,28,216,51) r25.5, purple #6630F8 fill with a 2px white border, 33px 700 white text. English subtitle in Exo 2 30px purple at about y≈94. | Drawn by the overlay. Text changes fade in over 8 frames. |
| Flow track (optional) | Capsules top 118, height 44, width 150, centers at x 240/440/640/840/1040, with small arrows between | Current step purple. Completed steps #2A2A2A with white text. Upcoming steps black with grey border and grey text. |
| **Content area** | No track: y110–620. With track: y175–620. x60–1220. | Key information goes only here. |
| Subtitle band | CSS top 637, ink y644–684, 44px Noto 700 white with a 4px black outline (16+8+4 text-shadow ring), centered | **No content here.** Entry paths must not cross it. |
| Progress bar | y687–720, semi-transparent. Played: rgba(190,170,250,.52). Unplayed: rgba(243,243,243,.32). White dividers at n−1. Chapter names in Noto 900 24px, skewX(−10°) scaleY(.9). The current chapter is at α1, the others at .55. | Content crossing it is brightened. Only full-width backgrounds and large shapes may cross it. |
| Stacking | black base < backdrop (fog + stars, or DotFieldBg) < live footage < overlay < shots < ending blackout < progress bar < aboveBar shots < subtitles | |

## 2. Palette (constants in `src/ui.tsx`)
| Name | Value | Meaning |
|---|---|---|
| PURPLE | #6630F8 (102,48,248) | Current focus, active state, brand color. Used on capsules, boxes, the current step. |
| PURPLE_LIGHT | #A175F1 | Highlight end, purple after crossing the progress bar, active card border. |
| PURPLE_TECH | #6530F4 | English technical terms in Exo 2. |
| PURPLE_DEEP | #5A3AD5 | Curves and hard shadows on titles. |
| ORANGE / CORAL | #F05F41 / #F16043 | Metric numbers, warnings, "the other side", query points. |
| RED_DEEP | #EC081F with a double red glow | Deep red warning blocks (hallucination, unreliable). |
| GREEN | #8FF740 | Green check (correct). |
| GREY / GREY_MID / GREY_LINE / GREY_LIGHT | #A0A0A1 / #747474 / #4A4A4A / #D4D4D4 | Non-focus text / grey blocks / grid lines / text lines. |
| WHITE / black | #FFF / #000 | Text, outlines, arrows / fills. |
| MAGENTA / CYAN | #D100D6 / #58FFEE | Only in the RGB-shifted copies of glitch. |
| Glows | GLOW_PURPLE (12px and 42px double layer), GLOW_PURPLE_S (24px, 8px), GLOW_ORANGE, GLOW_RED, BLOOM (drop-shadow 3px white .5), TEXT_GLOW | |

**Color means meaning:** purple = focus or ours, grey = inactive or background, orange-red = metric or warning or the opposing side, white = structural text, green = correct. Keep at most one large purple area in a frame.

## 3. Fonts (`public/fonts`, all OFL; `Fonts` in `common/lib.tsx` loads once in Main)
| Role | Family | Size, weight, transform |
|---|---|---|
| Large titles (video title, chapter cards, key term in a shot) | Noto Sans SC | 56–96px, 900, scaleX .85. May add a 1px black outline with paintOrder stroke. |
| HUD capsule text | Noto Sans SC | 33px, 700, letter-spacing 1 |
| Capsules and labels | Noto Sans SC | 24–30px, 600–800, textDy −2 (CJK ink sits 3–7px low, so pre-compensate) |
| In-figure notes | Noto Sans SC | 22–26px, 500–600, grey or white. **Minimum 22px.** |
| Subtitles | Noto Sans SC | 44px, 700, no compression |
| English technical terms | Exo 2 Italic | 26–38px, 600–700, scaleX .8, purple. TechText component. |
| Wide display type (title abbreviations, capitalized words) | Audiowide | 96–150px, letter-spacing 6, white with a 6px purple hard shadow |
| Numbers, chapter numerals, counters | Orbitron | 24–110px, 700, tabular-nums |
| Formulas | Times New Roman Italic | 34–36px white with a 3px drop shadow |
| Code and vector numbers | Monospace FONT_MONO | 22–24px |

### 3.1 English video (`lang: 'en'` in config.ts)
Noto Sans SC already includes the full Latin character set (verified across weights 100–900), so **no extra font is needed**. Body text, labels and subtitles still use `FONT_HEAVY`. Large display type uses Audiowide or Orbitron. Three differences take effect automatically when `lang` is set, so do not hard-code values in shots:
- **No squeezing:** `SQUEEZE` (`common/lib.tsx`) is .85 for Chinese and 1 for English. Latin letters at scaleX .85 look visibly distorted. The opening and chapter cards already use it.
- **No baseline pre-compensation:** `CText` defaults `dy` to `TEXT_DY` (−2 for Chinese, 0 for English). CJK line boxes place ink low, while Latin does not.
- **Width fallback:** subtitles, progress-bar chapter names, chapter-card titles and the large opening text all pass through `fitSize()` (`common/textfit.ts`, which estimates from measured em widths and is a pure function, so rendering stays deterministic). It is only a fallback. If text goes over budget, the copy should be split. See `narration-storyboard.md` §5.
- In an English video, `TechText` (Exo 2 purple italic) is for **emphasizing a term only**. Do not set whole sentences in it, because a fully italic sentence reads like a quotation.
- English capitalized words are much wider than Chinese: Audiowide capitals average .79em, Orbitron .82em, Noto capitals .67em and lowercase .57em (measured with fontTools). Estimate width with `textW(s, size, EM_WIDE|EM_ORB|EM_TECH, letterSpacing)`. Large type with `letterSpacing` (the opening, chapter cards) must pass that value in, because it is a fixed px amount that does not scale with font size. `fitSize()` takes the same parameter.

## 4. Component catalog (`src/ui.tsx`, imported in shots as `import {…} from '../../ui'`)
| Component | Use | Key props |
|---|---|---|
| `CText` | Single line of text, positioned by ink center | cx cy size weight color scaleX dy italic shadow |
| `TechText` | English technical term in Exo 2 purple italic | cx cy text fontSize scaleX glow |
| `MonoText` | Monospace, multi-line | x y size |
| `Box` | Black box with white border (fill can be a gradient; dashed; glow) | x y w h r sw |
| `Pill` | Fully rounded capsule with centered text | Box props plus text fontSize weight textDy |
| `TagBlock` | Large colored label block (purple, orange, deep red) with 900 text at scaleX .8 and a same-colored outer glow | x y w h color text |
| `Svg` | Full-frame 1280×720 SVG container (default BLOOM) | children |
| `LineArrow` | Arrow in any direction; p grows it from the root | x0 y0 x1 y1 p rodW headL headW dashed |
| `ArrowH` | Horizontal arrow as a div (left end anchored for scaleX) | x y w p dir |
| `Check` / `Cross` | Green check and red cross, draw-on (no render when p≤0) | cx cy size p |
| `DocIcon` | Document with folded corner, text lines and label | x y w h lines label accent |
| `DBIcon` | Database cylinder | cx cy w h label accent |
| `ChunkCard` | Text-block card (active state has a purple border and glow) | x y w h lines active title |
| `LLMIcon` | Language model: rounded square with a three-layer neuron dot grid | cx cy size label glow |
| `Trap` | Inverted trapezoid funnel layer, grey to purple with k gradient | cx y wTop wBot h k text |
| `TopCapsule` | Top HUD capsule (for the overlay) | N f0 text w tech glitch |
| `Counter` | Tabular numerals | cx cy value size |
| `SoftIn` | **Default entry:** 8-frame fade-in plus 10px rise (same signature as GlitchIn) | N f0 children len dy |
| `GlitchIn` (common) | 12-frame opacity-flicker entry, with rgbSplit and slices variants | N f0 seq rgbSplit slices |
| Helpers | `fadeIn / fadeOut / slideUp / scaleIn / exitAccel / exitFade / stagger / abs` | |

When a topic needs new graphics, add them to `ui.tsx` (the sample added DocIcon, DBIcon, ChunkCard and LLMIcon). Anything specific to one group goes in that group's own `gNui.tsx`. Reference implementations: `examples/rag/shots_src/*/`.

Light, highlight-moment, depth and camera primitives are in `src/fx.tsx` (imported as `import {…} from '../../fx'`):
| Component | Use |
|---|---|
| `LightBar` / `LightSweep` | Purple light bars sweeping across (three rounds for the highlight-moment opening) |
| `StageLine` | Central stage line: widens, breathes, and disappears with a white flash on the beat frame |
| `GhostText` / `ghostOpacity` | White-outline silhouette of the protagonist's large text, shown at 10% before it appears |
| `HaloRing` | Purple halo under the subject, can be split into back and front to sandwich the subject |
| `HeroGlow` | Double-layer purple glow around a rectangular protagonist, with a 30-frame breathing cycle |
| `BigNumber` / `countTo` | Orbitron large number with a purple hard shadow and counting animation |
| `Sparkle` / `GradBall` | Four-point star / bright-top black ball |
| `TiltPlane` | Tilted plane (depth layer) |
| `CameraRig` / `camAt` | Fixed push-in / pull-back / pan / full-page scroll / carry-shift |
| `SET_PIECE` / `setPiece` | Standard relative frames for the entrance-type highlight moment |

## 5. Layout patterns
- **Title card:** centered at (640, 345–372). Noto 900 80px with scaleX .85, a 3px white short line 300 wide beneath, and an Exo 2 subtitle at about y≈470. The chapter number is Orbitron 54px purple at y268.
- **Flow diagram:** nodes are 150×44 Pills or 200×70 Boxes, spaced 200 apart. Arrows are 38–70 wide with a 3px shaft and 22–24 headL. The current node is purple, completed nodes are grey-filled, and upcoming nodes have grey borders.
- **Card array:** cards 150×92 with r8, column gap 24, staggered entry 2 frames apart. Shrink to 70 wide when there are 12 or more.
- **Side-by-side comparison:** left at x≈300–380 and right at x≈900–1000, each with a label Pill above at y≈250. Put ≈, vs or + symbols at 46–60px in the middle.
- **Chart card:** 440×300, white border, black fill, grid #4A4A4A 1px, axis labels 15–18px, curve purple 3px, highlight point in red.
- **Formula:** Times Italic 34px, each token positioned absolutely, one token every 3 frames. Grey small-print notes give parameters (k=60).
- **Label plus description:** purple or orange Pill on top, white Noto 24px description 12px below.
- **Information hierarchy:** one focus per frame. Description text is grey #A0A0A1. Numbers use orange Orbitron.
- **Three size tiers and light** (details in `composition-and-light.md`): protagonist ≥170px or large type ≥96px and always lit. Supporting elements 60–110. Labels 22–30. The card 150×92 and Pill 150×44 above are **supporting sizes** and must not be used as protagonists. Show "many" with a grid of squares. The background is only the backdrop (stars or dot wave).

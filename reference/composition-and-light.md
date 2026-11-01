# Composition and light (visual rules)

> This file covers how big things are, what glows, and how highlight moments are arranged. It was written after comparing frame by frame two videos made with this skill: the ad-auction video 《eCPM 与广告竞价》 and the sample 《RAG 与知识库》. Their motion counts, pacing and total glow area were nearly identical. The gap came down entirely to the four points below. Build agents read this after `style-guide.md`. QC uses the criteria in §6.

| Metric (per frame, content area) | Ad auction | RAG sample |
|---|---|---|
| Average frame-to-frame change / motion events per minute | 0.47 / 72 | 0.56 / 76 |
| Median size of the largest object | 172px | 219px |
| Share of time the largest object is under 110px for at least 1.5 s | 29% | 12% |
| Source keyword counts: halo / sweep / ghost | 0 / 0 / 0 | 14 / 12 / 5 |
| Source keyword counts: skew / perspective / rotate | 1 / 0 / 4 | 7 / 1 / 15 |

## 1. Visual hierarchy: one protagonist per shot
- **Every shot needs a protagonist:** one subject occupying at least a third of the content area's height. That means a graphic at least 170px tall, or large type or a big number at least 96px with a line width of at least 300px (Orbitron, Audiowide or Noto 900, three or more characters). A protagonist of two or three characters at 96px cannot carry a frame. Go up to 110–150px, or pair it with a graphic. The protagonist enters on beat 1 or 2, and the other elements arrange around it afterward.
- **Three size tiers:** protagonist ≥170, supporting 60–110, labels and notes 22–30. There are at most four supporting elements and six labels. No fourth size tier exists beyond these three.
- **Quick size reference:** phone mockup ≥300×520, with the first readable content visible on screen. Human figure ≥96. Machine, database or document card ≥160 tall. Book or exam paper ≥240 wide. Main formula term ≥48px, result item ≥72px. Year or large number 96–150px. Chart card ≥440×300.
- **Small subjects need a protagonist:** timelines, formulas, tables and flow diagrams are not big enough on their own. Build a protagonist for them: a large number ("0.1 seconds" at 96px, not 34px), a lit current item (current row enlarged 1.15 with purple light), or a magnified detail. A single line with several 34px capsules holding the screen for 100 frames is a defect.
- **Show "many" with a grid, not debris:** use a grid of at least 6px squares, arranged neatly, lighting and dimming on the beat. Do not scatter small icons in the background. **The background is only the backdrop** (stars or the dot wave). Any "atmosphere element" dilutes the protagonist.
- **Empty-frame criterion:** the largest object in the content area is under 110px for more than 45 frames → medium. Under 80px for more than 45 frames → high.

## 2. Light follows the protagonist
- **The protagonist always carries light:** graphic protagonists use `GLOW_PURPLE` (double-layer purple soft glow; wrap in `HeroGlow`), or a `HaloRing` under the feet. Large text uses `TEXT_GLOW` and a purple hard shadow `6px 6px 0 PURPLE` (the same for wide display type and titles). Orange metric numbers use `GLOW_ORANGE`. White line graphics with only `BLOOM_SOFT` are not enough.
- **Supporting elements do not glow:** capsules, flow tracks, labels, table rows and descriptive text have no glow by default. Only the "current focus" item may have `GLOW_PURPLE_S`, and at most one per frame. When focus moves, the previous glow turns off over 8 frames.
- **Three layers of light:** white bloom (constant on structural lines) < purple soft glow (protagonist's constant light, plus the current focus) < white flash (events, 3–6 frames). Only these three layers are used across the video, and light colors are limited to purple, orange and red.
- **Light moves:** the protagonist's light breathes ±15% on a 30-frame cycle. Focus activation runs α 0→1 over 8 frames. On exit, the light goes off first (6 frames), then the whole element fades. Do not cut hard while still fully lit.
- **Hard shadows are the standard for heavy text:** Audiowide and Orbitron large text always uses `6px 6px 0 PURPLE` (or PURPLE_DEEP) plus `0 0 28px rgba(102,45,248,.45)`. Noto 900 large text uses a 1–2.5px purple outline with `paintOrder: stroke fill` and a purple soft glow.

## 3. Highlight moments (set pieces)
Each chapter has one or two: the chapter's main claim, a protagonist introduction, and the closing payoff. In the storyboard's global constraints, the highlight moment list gives the shots, and build groups follow the arrangement below. Do not handle them with a "capsule + icon + one line of text".

**Standard arrangement (entrance type, at least 90 frames; relative frames are in `SET_PIECE` in `fx.tsx`)**
| Relative frame | Action | Component |
|---|---|---|
| T0 | Clear the scene: the previous shot has faded to zero, and only the backdrop remains | — |
| T0+4 / +22 / +40 | Three rounds of purple light bars sweeping across (each round three bars, 2-frame stagger, 16 frames, α .6/.55/.55 white core) | `LightBar` |
| T0+18 | Central stage line widens to 720, then breathes | `StageLine` |
| T0+37 | Protagonist's white-outline silhouette fades in at 10% (preview) | `GhostText` |
| T1 (beat frame) | Stage line flashes white for 3 frames and disappears. Protagonist `GlitchIn` (rgbSplit 8 and slices 20 are allowed). | `GlitchIn` |
| T1+12 | `emphasisPulse` to 1.11 | — |
| T1+16 | Chinese subtitle slides up from below, Δ80 over 22 frames | `slideUp` |
| T1+24 | Word-by-word label or Pill SoftIn, staggered by 2 frames | `SoftIn` |

**Variants**
- Large-number type: `BigNumber` counts up over 20 frames to its final value, with a small unit label, a comparison object (an icon or another number), and an orange question mark or conclusion with `GlitchIn`. Sample: SC39, "1,000,000 tokens".
- Symbol type: the subject slides up Δ≤170, with a `HaloRing` draw-on under its feet over 20 frames (outer and inner white outlines, purple gradient fill, three dashed ripple rings with a 2-frame phase offset), plus a large conclusion in Noto 900 at 60px with a purple outline and `GlitchIn`. Sample: SC44, "knowledge base = moat".
- Year or source type: a year as a `BigNumber` at 96px rolls to its final value, with an institution Pill, and a paper or results card at least 240 wide beside it. The year must not stand alone on an empty screen for more than 30 frames.

## 4. Depth and carry-over
- Shots about space, hierarchy or indexes use tilted planes: `skewX(-20deg) scaleY(.5)` stacked two or three layers, with 90px between layers, and paths draw on between layers. Shots about filtering use a `Trap` funnel. Rotation is only for gears, dials and turntables. Flat layouts throughout the video are a defect.
- Carry-over: the previous shot's protagonist shrinks and shifts aside to make room for the new protagonist (`kf` over 16 frames with `easeInOutPow(2.5)`, scaling to 0.6 at the same time). It does not disappear and then redraw a smaller version. Two shots that carry over share the same component and the same parameters.
- Camera: at least 3 moves per chapter and at most 1 per shot, using `CameraRig`. A fixed push-in from 1 to 1.33 over 33 frames orbits the protagonist. A carry-over takes 16 frames. Group pans and parallax show "many". HUD and subtitles do not move during a camera move, and moves must not overlap a glitch or a staggered entry. Budget and frame counts are in `motion-vocabulary.md`, camera-moves section.

## 5. Build group self-check (one row per shot in BUILD_NOTES)
| Shot | Protagonist | Protagonist height px | Protagonist light | Highlight moment | Supporting / label count |
Any row where the protagonist is under 170px or unlit must give a reason. The empty-frame criterion must never trigger.

## 6. QC criteria (with `scripts/frame_metrics.py`)
The script's "subject size" is the height of the largest connected object. Wide but thin objects (a line of large text, a wide card) are scaled by min(width, 4×height)/2.5. Characters in one line of text (gaps of 40px or less) merge into one object. Stars are not counted. When the backdrop is the dot wave (`config.bg='dots'`), the script removes dots on the same grid coordinates, and it raises the soft-light brightness floor from 10 to 22. The dot base color #0b0c11 has a slight blue cast, so without raising the floor, the whole screen would count as soft light. Light-sweep, stage-line and halo phases (content-area soft light of at least 10000px²) are not counted as empty, and the median subject size excludes those frames.
- Shot median subject size under 170 → low. Under 110 with no large light activity for more than 45 frames → medium. Under 80 for more than 45 frames → high.
- Highlight-moment shots with under 3000px² of soft light in the protagonist area → medium. Ordinary shots with under 800px² of soft light in the protagonist area → low (unlit protagonist).
- Eight or more separate purple patches in one frame (purple fragment index) → low, suggesting purple is spread across supporting elements.
- Ten or more background shapes under 60px (not stars and not backdrop dots) → medium (debris). **A tidy dot cloud or grid of squares (vector spaces, exposure walls) also trips this rule. That is an allowed design.** QC checks the frame: a regular arrangement lit on the beat is a matrix. Randomly scattered small icons are debris.

## 7. Verb-driven continuous motion (fourth video, user decision 2026-09-10: "still after entering" is a defect)
- Symptom: elements enter on the subtitle beat and then sit still waiting for the next beat, with only a soft glow breathing. The user's first reaction, watching the 30-second sample, was to this. Measured: 4 of 6 shots had still-frame shares of 42–72%, and the longest still stretch was 2.8 s. The sample RAG video has the same problem, so "match the sample" does not catch it.
- Rule: **each subtitle block's verb needs an on-screen action that continues until the next beat** (data flowing, a light pulse running along an arrow, typing line by line, lighting cells one by one, growing, rotating, a gate opening or closing, a queue compressing). After entering, an element **must not stay completely still for more than 30 frames** (breathing glow does not count). A shot without any other camera move gets a slow 1.0→1.05 push-in across its whole duration (this counts as that shot's one camera move). After the slow push-in, content must stay within x 89–1191 and y 122–607. The boundaries do not change: one protagonist, one glitch, backdrop only, no debris, and the motion must serve the verb.
- Measurement (`scripts/motion_check.py`): sample the content area (excluding HUD, subtitles and progress bar) at 320×180 and compute average grayscale change frame by frame. Change under 0.35 counts as a still frame. Per shot, still share must be ≤40%, and the longest still run ≤1.0 s (build groups aim for ≤0.7 s for margin). **The final-cut check (`fin_frames`) is the criterion.** Group-level low-resolution renders read too loose: in the fourth video, group checks passed 48/48, but the final cut had 11 shots over the limit. The `--frames` mode adds a column for "changed full-resolution pixels within the longest still run". Under 800 is a true still (→ medium, add motion). 800–2500 is small-area motion (→ low, **increase the amplitude**: make moving elements brighter, larger and denser, with a ±2% breathing cycle over 30 frames on the protagonist itself. Do not add elements).
- Storyboard format: the motion column of each shot ends with a "Continues:" line. The global constraints get a §9. Each build group's BUILD_NOTES shot table gets two columns: "motion_check still share" and "longest still".

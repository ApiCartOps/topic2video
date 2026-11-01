# Motion vocabulary (n = N − f0, where N is the final-cut frame number. All formulas are pure functions. Randomness only through rnd.)

## Entry
| Name | Formula or component | Frames | Use |
|---|---|---|---|
| **SoftIn (default)** | `<SoftIn N f0>`: opacity easeOut(2.5), first frame ≈25% rising to 1, rising 10px to 0 | 8 | All text, labels, HUD term changes, small icons |
| GlitchIn (key term) | `<GlitchIn N f0>`: 12-frame opacity template [.5,1,.5,0,.5,0,.5,1,.75,.5,.75,1] | 12 | **At most one per shot**, only for the core term. The heavy rgbSplit and slices variants are only for the opening, chapter cards, protagonist introductions and closing. |
| Slide up from below | `top = yEnd + slideUp(n, Δ)`, with Δ·(1−n/22)^2.5 | 22 | Cards and graphics. **Δ≤120** (Δ300 would cross the subtitle band). Pair with a 6-frame fadeIn at the start. |
| Sideways slide | `left = xEnd − Δ·powOutRemain(n,18,2.5)`, Δ 260–320 | 18 | An alternative when entering from outside the safe area |
| Scale-in | `scale = scaleIn(n)` (cubic-bezier(.1,.1,.35,1)) | 21 | Icons, balls, cards |
| Staggered | Element i starts at f0 + stagger(i, 2) | 2 per item | Lists and card arrays. **Do not use GlitchIn for staggering**, because it looks like dropped frames. |
| Draw-on line or arrow | `<LineArrow p={clamp01(n/20)}>`: the arrow grows from its root, the head follows the shaft | 16–28 | Connections and pointing |
| Draw-on box | SVG stroke-dasharray plus dashoffset, or a clipPath rect wipe | 20–30 | Dashed boxes, checks, paths |
| Typewriter | `text.slice(0, floor(n/2))`, one character every 2 frames | by character count | Questions, answers, prompt rules |
| Counter | Counter, value = kf(n,[[0,a],[20,b]]) rounded | 14–26 | Years, percentages, token counts |
| Line-by-line wipe | Each line's clip width goes 0→100% over 2 frames | 2 per line | Text lines on document cards |

## Emphasis
| Name | Formula | Frames |
|---|---|---|
| Pulse | `scale = emphasisPulse(n, {peak: 1.11, up: 13, hold: 4, down: 13})` | 30 |
| Grey to purple | `mix(GREY, PURPLE, clamp01(n/11))` (border and fill change together) | 11 |
| Soft glow on | boxShadow GLOW_PURPLE_S, α 0→1 | 8 |
| White flash | element filter brightness 1→1.6→1 | 6–10 |
| Highlight bar wipe | Semi-transparent purple bar scaling from the left, scaleX 0→1 | 12 |

## Light effects (who glows and how; rules in `composition-and-light.md`; components in `src/fx.tsx`)
| Name | Formula or component | Frames | Use |
|---|---|---|---|
| Protagonist constant light | `<HeroGlow x y w h N>`: double purple soft glow, breathing ±15% over 30 frames; or `LLMIcon glow` | Always on | **Every shot's protagonist must glow.** Supporting elements do not. |
| Purple light-bar sweep | `<LightSweep N rounds={[T0+4,T0+22,T0+40]}>`: three bars per round, 2-frame stagger, 16 frames, α .6/.55/.55 white core | 3×16 | The "stage spotlight" at the start of a highlight moment |
| Stage line | `<StageLine N f0 flashAt>`: 14 frames widening to 720, then breathing, then a 3-frame white flash on the beat frame and it disappears | 14+ | Previews where the protagonist lands |
| Ghost outline | `<GhostText opacity={ghostOpacity(N,f0,until)}>`: white outline at 10%, fading in | 12 fade-in | About 40 frames before a protagonist's large text appears |
| Halo | `<HaloRing p fillOp phase half>`: white outline draw-on over 20 frames, purple gradient over 12 frames, three dashed ripple rings with a 2-frame phase offset | 20 | Under a symbol (three layers: back, subject, front) |
| Purple hard shadow | Large text textShadow `6px 6px 0 PURPLE, 0 0 28px rgba(102,45,248,.45)` (default for `BigNumber`) | Always on | Audiowide and Orbitron large text, the video title |
| Purple outline | Noto 900 large text with `WebkitTextStroke 2.5px PURPLE`, `paintOrder: stroke fill`, plus a purple soft glow | Always on | Conclusion text |
| Orange glow | `GLOW_ORANGE`, or an orange textShadow | Always on | Metric numbers and result items (−49%, ¥3.20) |
| Soft glow on | boxShadow `GLOW_PURPLE_S`, α 0→1 | 8 | Shifting focus to one item |
| Light off first | Six frames before exit the glow goes α→0, then the whole element fades | 6+8 | Exit of any element that glows |
| White flash | filter brightness 1→1.6→1, or the flash on `StageLine` | 3–6 | Events: a click, a hit, a gavel strike |

At any moment: one protagonist light, plus at most one focus light. Light is only purple, orange or red. White bloom is only for structural lines. For the full sequence of three sweep rounds, stage line, outline and white flash with glitch, see `composition-and-light.md` §3 and `SET_PIECE` in `fx.tsx`.

## Exit (**must reach zero before a hard cut**)
| Name | Formula | Frames |
|---|---|---|
| Fade to zero | `opacity = 1 − (n/N)^1.5` (N = 6–12), zero on the last frame | 6–12 |
| Accelerating drop | `translateY(exitAccel(n, c))`, c 0.2–1.2, with fade to zero. Limit to ≤10px if a subtitle band is nearby. | 6–12 |
| Accelerating exit upward (overlay) | `dy = −(n/11)^2·440`, `opacity = 1 − (n/11)^1.6` | 12 |
| Left-slide exit | `translateX(−c·n²)` with fade to zero | 12–15 |
| Grey sink | Turns grey over 11 frames, then sinks 12px over 12 frames (the "memory" recedes to secondary) | 12 |

Forbidden: using exitFade's 6.7% per frame alone before a hard cut (its last frame still has 40–60% opacity, so it "pops"). When visibility is still above 20%, the Sequence must not end.

## Camera moves (components `CameraRig` and `camAt` in `fx.tsx`)
> Background measured 2026-09-08: the recommendation-app original, which is the style source, has 6.6 overall camera moves per minute, averaging 16 frames each, including push-ins, pull-backs, parallax, and a scroll of up to 150 frames. The sample RAG video and the ad-auction video each had only 2.2–2.5 moves per minute, averaging 5–8 frames, and **no push-ins at all**. The old version of this guide said "mostly static shots", and that is why. The following sets the budget and the vocabulary.

**Budget:** at least 3 camera moves per chapter, at most 1 per shot. Each move takes 30–45 frames of easeInOut. No GlitchIn and no staggered entries during a move (let an element sit still for at least 10 frames before moving). Text readability comes first: scale ≤1.33 (outlines thicken with the group, and above 1.4 they look heavy). HUD, flow track and subtitles do not move in screen space, so the move only affects the content layer.

| Name | Formula or component | Frames | When to use |
|---|---|---|---|
| Fixed push-in | `<CameraRig N keys={[{f:a,x:640,y:360,s:1},{f:a+33,x:px,y:py,s:1.33}]}>` (original 1→1.329 over 33 frames with bezier(.6,.05,.4,.95); 1→1.358 over 35 frames with a power 2.5 curve) | 30–40 | Push in toward the protagonist when it's still on screen for the second beat for at least 60 frames. Vignette at the top and bottom fades in over 18 frames during the push-in. |
| Pull-back | Same as above in reverse (original 37–42 frames with bezier(.55,.05,.4,1)) | 37–45 | Moving from detail back to the full view, closing out a chapter, or revealing a second subject cropped out earlier |
| Carry-shift | The previous shot's protagonist goes from `kf` over 16 frames with easeInOutPow(2.5), shrinks to 0.6 and moves to a corner, making room for the new protagonist. The two shots share the same component and parameters. | 16 | Every "no exit" handover needs this. Do not disappear and redraw a smaller version. |
| Group pan (stage pan) | The whole group moves as a rigid body one screen to the left, or 110px up (original: the end of a flow-chart section, a conveyor belt rising) | 20–30 | One screen is complete and the next is beside it. Lists longer than one screen. |
| Full-page scroll | Y offset with easeInOutPow(2.5), can include a scroll bar | 43 | Long lists or long document cards |
| Parallax | 2–3 layers at different speeds (original 6.4 / 9.6 / 12.8 px/frame, background layer dimmed ×0.43), or the content layer moves 1.33× the foreground | 26+ | Showing "many" or "a very large world": screenshot walls, document walls, log streams |
| Accelerating exit | The whole scene moves down or left with an accelerating offset table, and all of it leaves the frame on the last frame | 12–25 | Clearing the scene at the end of a chapter, or after an analogy ends |
| Whip | A hollow copy offset sideways by −63 or +38px for 1–3 frames, then snaps back. Or the whole group moves 3 frames with directional blur. | 1–3 | The instant of a conflict or comparison cut. At most two per chapter. |
| Screen-space vignette | Top and bottom linear gradients, black at α .38–.42, fading in over 18 frames | 18 | Synchronized with a push-in, to draw attention to the center |

A camera move also counts as "one noticeable change per sentence". When a sentence adds no new element, use one 30-frame push-in instead of forcing an element in.

## Beats
- An element's appearance frame equals the start frame of its subtitle block (each ｜ block in `script/timeline.md`). Tolerance −6…+3.
- Every narration sentence has at least one noticeable change on screen. A still period over 45 frames needs breathing (a 20-frame light cycle, a 30-frame glow cycle, or star drift).
- The 10-frame gap between sentences: the previous shot uses its last 2 frames to finish, and the next shot uses its first 8 to enter (shot range [sentence from−8, last sentence to+2]).
- A 45-frame gap before a chapter makes room for the chapter card: the previous chapter's last shot exits to zero, the card glitches in after 3 frames, the last 12 frames of the card accelerate out, and the new chapter's HUD fades in on the frame after the card ends.

## Continuity (the storyboard must describe both sides of each cut)
- Write it as: "Shot A fades to zero over its last 8 frames with a slight drop; Shot B's first elements enter with SoftIn from its first frame." Do not write only "hard cut", because each side will read it as "I stay still, and you enter on the beat frame", which produces 6–8 empty frames.
- Group boundary frames (where two build groups meet): each group matches the storyboard on its own side, and QC checks boundary frames as a separate list. Adjacent Sequences may overlap by 0–4 frames.
- When one element carries across shots (for example a document card moving from one shot into the next), both shots use the same component and the same parameters, so the boundary frame is pixel-identical.

## Glitch allow-list (user decision)
- At most one GlitchIn per shot, only on the term the shot is talking about. In the storyboard, the word glitch appears only in that cell. Everything else is written as "fade in".
- HUD term changes, flow track, numbers, badges, small labels, numbers and icons: always SoftIn, fade in, or scale.
- The final check scans the whole video with the 12-frame template. The number of hits must equal the number of allow-list entries.

import type {ShotDef, BgSpec} from '../common';
import {TOTAL_FRAMES} from '../common';
import {Title, TITLE_RANGE, ChapterCard, CHAPTER_CARDS, Hud, HUD_RANGE, Rail, RAILS, Ending, ENDING_RANGE, EndingTop, ENDING_TOP_RANGE, EndCredit, END_CREDIT_RANGE} from './Overlay';
// Overlay (maintained by the main session; build groups do not draw these): opening / chapter cards / top HUD capsule / flow track / closing blackout. Lowest in the stack (Main puts it first).
export const SHOTS_OVERLAY: ShotDef[] = [
  {id: 'OV-Title', from: TITLE_RANGE[0], to: TITLE_RANGE[1], Comp: Title},
  ...CHAPTER_CARDS.map((c) => ({id: `OV-Chapter${c.n}`, from: c.from, to: c.to, Comp: (() => ChapterCard({card: c})) as unknown as React.FC})),
  ...(HUD_RANGE[1] > HUD_RANGE[0] ? [{id: 'OV-Hud', from: HUD_RANGE[0], to: HUD_RANGE[1], Comp: Hud}] : []),
  ...RAILS.map((r, i) => ({id: `OV-Rail${i + 1}`, from: r.from, to: r.to, Comp: (() => Rail({spec: r})) as unknown as React.FC})),
];
// Over all content: the closing blackout (below the progress bar) + the progress bar blacking out in sync with endingFade (aboveBar) + the credit card (aboveBar, above the blackout)
export const SHOTS_OVERLAY_TOP: ShotDef[] = [
  {id: 'OV-Ending', from: ENDING_RANGE[0], to: ENDING_RANGE[1], Comp: Ending},
  {id: 'OV-EndingTop', from: ENDING_TOP_RANGE[0], to: ENDING_TOP_RANGE[1], Comp: EndingTop, layer: 'aboveBar'},
  {id: 'OV-EndCredit', from: END_CREDIT_RANGE[0], to: END_CREDIT_RANGE[1], Comp: EndCredit, layer: 'aboveBar'},
];
export const BG_OVERLAY: BgSpec[] = [
  {from: 1, to: 10, fog: false, stars: 'none'},
  {from: TOTAL_FRAMES - 40, to: TOTAL_FRAMES, fog: false, stars: 'none'},
];

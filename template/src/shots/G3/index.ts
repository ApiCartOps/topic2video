import type {ShotDef, BgSpec, FootageSpec} from '../../common';
// Group G3: shot table / backdrop overrides / live-footage layer. Array order is the stacking order (later entries sit on top). Frame ranges are in 分镜表.md and script/timeline.md.
// Shot components: const N = useCurrentFrame() + F0 (F0 = this shot's from). Graphics come from '../../ui', easing and shared helpers from '../../common'.
export const SHOTS_G3: ShotDef[] = [];
export const BG_G3: BgSpec[] = [];
export const FOOTAGE_G3: FootageSpec[] = [];

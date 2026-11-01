import React from 'react';
import type {StarVariant, StarFieldProps} from './StarField';
/** Shot definition: from/to are original-footage frame numbers (starting at 1, inclusive). Main mounts it with <Sequence from={from-1} durationInFrames={to-from+1}>. */
/** layer:'aboveBar' → Main mounts the shot above the progress bar and below the subtitles. Some shots in the original have content layered over the semi-transparent progress bar, such as the element that rises from y720 in SC019.p1-b. By default, shots sit below the bar, which brightens it. */
export type ShotDef = {id: string; from: number; to: number; Comp: React.FC; layer?: 'aboveBar'};
/** Backdrop override (by original-footage frame range): stars selects a star variant or fine-tuning parameters ('none' turns them off), and fog turns the fog off or on. Ranges without an override use the global default (drift, fog on). */
export type BgSpec = {from: number; to: number; stars?: StarVariant | Partial<StarFieldProps>; fog?: boolean};

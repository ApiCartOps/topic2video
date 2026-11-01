#!/usr/bin/env python3
"""
Per-shot composition, light and motion measurements (see reference/composition-and-light.md §6 and agent-qc-rules.md).
Usage:
  python3 scripts/frame_metrics.py [--frames fin_frames] [--storyboard 分镜表.md] [--shots SC11:1627-1806,SC12:1852-1965] [--step 4] [--out qc/frame_metrics_vN.md]
By default, shot ranges are parsed from the `| SCxx … | a–b |` rows of 分镜表.md (the storyboard table). Frames default to fin_frames/f_%04d.jpg.
Per-shot output: subject size (height of the largest object; wide objects are scaled as min(w,4h)/2.5, and a line of large text counts as one object) median and minimum, longest run of empty frames (no subject ≥110 and no large light activity), median soft-light area (protagonist area / whole content area), median count of purple fragments, longest still run, and flags.
Dependencies: numpy, pillow, scipy. Brightness is computed in int32.
"""
import argparse, os, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ap = argparse.ArgumentParser()
ap.add_argument('--frames', default='fin_frames')
ap.add_argument('--storyboard', default='分镜表.md')
ap.add_argument('--shots', default='')
ap.add_argument('--step', type=int, default=4)
ap.add_argument('--out', default='')
ap.add_argument('--rail-top', type=int, default=100, help='upper bound of the content area (shots with a flow track can pass 175)')
ap.add_argument('--bg', default='auto', help="backdrop mode: stars | dots | auto (auto reads bg from src/config.ts). In dots mode, the dots of DotFieldBg are masked out on their grid before measuring, otherwise the wavefront's bright dots would be counted as background debris")
a = ap.parse_args()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cfg_bg():
    try:
        m = re.search(r"bg:\s*'(stars|dots)'", open(f'{ROOT}/src/config.ts', encoding='utf-8').read())
        return m.group(1) if m else 'stars'
    except OSError:
        return 'stars'
BG = cfg_bg() if a.bg == 'auto' else a.bg

def dot_mask(W=1280, H=720, r=5):
    """Screen-space mask for the dot-wave backdrop (same constants as src/common/DotFieldBg.tsx: design grid 960×540, step 36, origin (24,18), scaled uniformly).
    Dot radius is actually 2–2.7px, and JPEG blurs by another 1px, so a 5px mask is enough. Dot spacing is 48px, and the masked area is under 4%, so the effect on real subjects is negligible."""
    m = np.zeros((H, W), bool)
    if BG != 'dots':
        return m
    sc = max(W / 960, H / 540); ox = (W - 960 * sc) / 2; oy = (H - 540 * sc) / 2
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]; disc = (xx * xx + yy * yy) <= r * r
    for y in range(18, 540, 36):
        for x in range(24, 960, 36):
            cx = int(round(ox + x * sc)); cy = int(round(oy + y * sc))
            y0, y1 = max(0, cy - r), min(H, cy + r + 1); x0, x1 = max(0, cx - r), min(W, cx + r + 1)
            if y1 <= y0 or x1 <= x0: continue
            m[y0:y1, x0:x1] |= disc[(y0 - cy + r):(y1 - cy + r), (x0 - cx + r):(x1 - cx + r)]
    return m
DOT_MASK = dot_mask()
# The dot-field base color #0b0c11 has a slight blue cast (sat≈.35, lum≈12). It would fall into the soft-light criterion across the whole screen (sat>.25 and 10<lum<110),
# which would hide empty-frame detection and inflate protagonist soft light. In dots mode, the soft-light brightness floor is raised to 22
# (measured: base color plus noise stays at or below 18. Purple soft light in the content area is mostly 25–110, so it is barely affected).
SOFT_LO = 22 if BG == 'dots' else 10

def parse_shots():
    if a.shots:
        out = []
        for tok in a.shots.split(','):
            sid, rng = tok.split(':'); lo, hi = re.split(r'[–-]', rng)
            out.append((sid, int(lo), int(hi)))
        return out
    out = []
    for line in open(a.storyboard, encoding='utf-8'):
        m = re.match(r'^\|\s*(SC\d+)[^|]*\|\s*(\d+)\s*[–-]\s*(\d+)\s*\|', line)
        if m:
            out.append((m.group(1), int(m.group(2)), int(m.group(3))))
    # de-duplicate: the allow-list and continuity tables after the storyboard also start with SC but have no frame-range column, which the regex already excludes
    seen = {}
    for s in out:
        seen.setdefault(s[0], s)
    return list(seen.values())

def frame_path(i):
    p = os.path.join(a.frames, f'f_{i:04d}.jpg')
    return p if os.path.exists(p) else os.path.join(a.frames, f'frame_{i:04d}.jpg')

Z = slice(a.rail_top, 621)

def analyze(i):
    im = Image.open(frame_path(i)).convert('RGB'); arr = np.asarray(im).astype(np.int32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    lum = (r * 299 + g * 587 + b * 114) // 1000
    mx = arr.max(2); mn = arr.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    bright = (lum[Z] > 120) & ~DOT_MASK[Z]   # in dots mode, strip the backdrop dots first, otherwise 40–60 wavefront dots would be counted as debris
    # 41×13 structuring element: merges the characters of a line of large text (including thousands separators and letter gaps ≤40px) into one object, but does not merge capsule rows with gaps of 50 or more
    obj = ndi.binary_dilation(bright, structure=np.ones((13, 41), bool))
    lab, n = ndi.label(obj)
    hero_h = 0; hero_box = None; small = 0
    if n:
        ink = ndi.sum(bright, lab, index=np.arange(1, n + 1))  # actual bright pixels per object (stars have only 2–16px and are excluded)
        for k, s in enumerate(ndi.find_objects(lab)):
            if s is None or ink[k] < 30: continue
            h = s[0].stop - s[0].start; w = s[1].stop - s[1].start
            if h < 60 and w < 60: small += 1
            # subject size: height, or the "width-scaled" value. Wide but not tall objects (a line of large text, a wide card) count as min(w, 4h)/2.5. Thin lines (very small h) add almost nothing.
            size = max(h, min(w, 4 * h) / 2.5)
            if size > hero_h: hero_h = size; hero_box = s
    soft = (sat[Z] > 0.25) & (lum[Z] > SOFT_LO) & (lum[Z] < 110) & ~DOT_MASK[Z]
    glow_total = int(soft.sum())  # soft-light area across the whole content area. Sweep, stage-line and halo phases are very large, so those frames are not counted as empty
    glow_hero = 0
    if hero_box is not None:
        y0 = max(0, hero_box[0].start - 30); y1 = hero_box[0].stop + 30
        x0 = max(0, hero_box[1].start - 30); x1 = hero_box[1].stop + 30
        sub = soft[y0:y1, x0:x1]
        if sub.any():
            lab2, n2 = ndi.label(sub)
            glow_hero = int(np.bincount(lab2.ravel())[1:].max()) if n2 else 0
    # purple fragments: solid purple only (excludes the soft haze and dashed ripples). Not dilated, and only blobs of 80px or more count.
    purple = (b[Z] > r[Z]) & (r[Z] > g[Z]) & (sat[Z] > 0.45) & (lum[Z] > 45)
    lab3, n3 = ndi.label(ndi.binary_dilation(purple, structure=np.ones((7, 25), bool)))  # merge the per-character hard shadows of a line of text into one blob
    npurple = int((np.bincount(lab3.ravel())[1:] >= 80).sum()) if n3 else 0
    return hero_h, glow_hero, npurple, small, int(bright.sum()), glow_total

def diff_series(lo, hi):
    prev = None; out = []
    for i in range(lo, hi + 1):
        im = Image.open(frame_path(i)); im.draft('L', (320, 180)); l = np.asarray(im.convert('L').resize((320, 180))).astype(np.int32)
        out.append(0 if prev is None else float(np.abs(l - prev).mean())); prev = l
    return out

shots = parse_shots()
if not shots:
    sys.exit('No shot ranges parsed. Check --storyboard, or pass --shots')
lines = ['| Shot | Frames | Subject size median/min px | Longest empty run (frames) | Soft light protagonist/total median px² | Purple fragments median | Longest still (frames) | Flags |', '|---|---|---|---|---|---|---|---|']
flags_total = {'high': 0, 'medium': 0, 'low': 0}
for sid, lo, hi in shots:
    hh = []; gl = []; pp = []; sm = []; gt = []
    for i in range(lo, hi + 1, a.step):
        h, g, p, s, br, g_all = analyze(i)
        if br < 200: h = 0
        hh.append(h); gl.append(g); pp.append(p); sm.append(s); gt.append(g_all)
    hh = np.array(hh); gt = np.array(gt); run = 0; best = 0
    for h, g_all in zip(hh, gt):
        # empty frame = no subject ≥110 **and** no large light activity (soft light ≥10000px² from sweeps, stage lines or halos does not count as empty. A single glowing cursor is only a few thousand px²)
        run = run + 1 if (h < 110 and g_all < 10000) else 0; best = max(best, run)
    low_run = best * a.step
    d = diff_series(lo, hi); srun = 0; sbest = 0
    for v in d[1:]:
        srun = srun + 1 if v < 0.15 else 0; sbest = max(sbest, srun)
    flags = []
    # the median subject size counts only frames that have content and are not light effects. Sweep and stage-line phases of a highlight moment do not count as the protagonist being absent.
    solid = hh[(hh > 0) & ~((hh < 110) & (gt >= 10000))]
    med_h = float(np.median(solid)) if len(solid) else 0.0; min_h = int(hh.min())
    if low_run > 45:
        low_vals = hh[(hh < 110) & (hh > 0)]
        flags.append('high: empty frames (subject <80px for >45 frames)' if len(low_vals) and np.median(low_vals) < 80 else 'medium: empty frames (subject <110px for >45 frames)')
    elif med_h < 170:
        flags.append('low: subject <170px')
    if float(np.median(gl)) < 800: flags.append('low: protagonist unlit')
    if float(np.median(pp)) >= 8: flags.append('low: purple fragments ≥8')
    if float(np.median(sm)) >= 10: flags.append('medium: background debris ≥10')
    if sbest > 45: flags.append(f'low: still for {sbest} frames')
    for f in flags:
        flags_total[f.split(':')[0]] += 1
    lines.append(f'| {sid} | {lo}–{hi} | {med_h:.0f} / {min_h} | {low_run} | {np.median(gl):.0f} / {np.median(gt):.0f} | {np.median(pp):.0f} | {sbest} | {"; ".join(flags) or "OK"} |')
head = f'# Composition / light / motion measurements ({a.frames}, step {a.step}, backdrop {BG})\n\nFlag totals: high {flags_total["high"]} / medium {flags_total["medium"]} / low {flags_total["low"]}. Criteria: reference/composition-and-light.md §6.\n\n'
txt = head + '\n'.join(lines) + '\n'
if a.out:
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True); open(a.out, 'w', encoding='utf-8').write(txt); print(a.out)
print(txt)

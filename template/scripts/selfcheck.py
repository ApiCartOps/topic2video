#!/usr/bin/env python3
"""Static self-check for the main session (no rendering; finishes in seconds. Complements QC, which checks from pixels):
  1) Frame coverage: reconciles each group's {id, from, to} in index.ts against the shot ranges in 分镜表.md. Reports gaps, overlaps and missing shots.
  2) Glitch allow-list: counts GlitchIn occurrences in each SCxx.tsx against the allow-list in the storyboard's global constraints §3.
  3) On-screen literals: extracts strings that appear on screen from each SC file, filters out CSS and identifier noise, and lists words that are not in the fact list for a person to check.
Usage: python3 scripts/selfcheck.py [G1 G2 …] (with no arguments, checks every group that has been built)"""
import re, os, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sb = open(f'{ROOT}/分镜表.md', encoding='utf-8').read()

# ---- shot ranges from the storyboard ----
sb_shots = {}
for m in re.finditer(r'^\| (SC\d\d)[^|]*\| (\d+)–(\d+) \|', sb, re.M):
    sb_shots[m.group(1)] = (int(m.group(2)), int(m.group(3)))

# ---- allow-list ----
wl_text = re.search(r'\*\*闪烁白名单.*?\*\*：(.*?)。\*\*不在表内', sb, re.S)
whitelist = {}
if wl_text:
    for part in wl_text.group(1).split('·'):
        mm = re.match(r'\s*(SC\d\d)\s+(.*)', part.strip())
        if mm: whitelist[mm.group(1)] = mm.group(2).strip()

groups = sys.argv[1:] or sorted(os.path.basename(p) for p in glob.glob(f'{ROOT}/src/shots/G*'))
problems = 0

# ---- 1) frame coverage ----
built = {}
for g in groups:
    idx = f'{ROOT}/src/shots/{g}/index.ts'
    if not os.path.exists(idx): continue
    src = open(idx, encoding='utf-8').read()
    for m in re.finditer(r"id:\s*'([^']+)'\s*,\s*from:\s*(\d+)\s*,\s*to:\s*(\d+)", src):
        built[m.group(1)] = (int(m.group(2)), int(m.group(3)), g)
    if not re.search(r"id:\s*'", src):
        print(f'[coverage] {g}: index.ts has no literal from/to (it may use constants). Check by hand.')
print(f'[coverage] storyboard has {len(sb_shots)} shots; {len(built)} built')
for sid, (a, b) in sorted(sb_shots.items()):
    if sid in built:
        ba, bb, g = built[sid]
        if (ba, bb) != (a, b):
            print(f'  ✗ {sid} ({g}) range {ba}–{bb} ≠ storyboard {a}–{b}'); problems += 1
import json
_tl = json.load(open(f'{ROOT}/script/timeline.json'))
_chapter_starts = {c['from'] for c in _tl['chapters']}
ids = sorted(built, key=lambda k: built[k][0])
for p, q in zip(ids, ids[1:]):
    gap = built[q][0] - built[p][1]
    # chapter-card gap (last sentence of the previous chapter to+3 → first sentence of this chapter from−9) is designed in, so skip it
    if gap > 1 and any(built[q][0] == cs - 8 for cs in _chapter_starts):  # next shot's first frame = this chapter's first sentence from−8
        print(f'  · chapter-card gap {p}→{q}: {built[p][1]}→{built[q][0]} (the overlay takes over)'); continue
    if gap > 1: print(f'  ✗ gap {p}→{q}: {built[p][1]}→{built[q][0]} ({gap-1} frames with no shot)'); problems += 1
    if gap < -4: print(f'  ✗ overlap {p}→{q}: {-gap+1} frames'); problems += 1

# ---- 2) glitch ----
print(f'[glitch] allow-list has {len(whitelist)} entries')
for g in groups:
    for f in sorted(glob.glob(f'{ROOT}/src/shots/{g}/SC*.tsx')):
        sid = os.path.basename(f)[:4]
        src = open(f, encoding='utf-8').read()
        n = len(re.findall(r'<GlitchIn\b', src)) + len(re.findall(r'glitchOpacity\(', src))
        want = 1 if sid in whitelist else 0
        flag = '' if n == want else '  ✗'
        if n != want: problems += 1
        print(f'  {sid} GlitchIn×{n} (allow-list {whitelist.get(sid, "—")}){flag}')

# ---- 3) literals ----
fact = re.search(r'1\. \*\*事实清单.*?\n', sb, re.S)
fact_txt = (fact.group(0) if fact else '') + sb  # the whole storyboard counts as checked (on-screen text is written in the storyboard)
noise = re.compile(r'^(#|rgb|[0-9.\s%pxem-]+$|[a-z][A-Za-z0-9]*$|\.\./|src/|[A-Z_]+$|none|auto|absolute|relative|center|left|right|top|bottom|solid|dashed|round|butt|square|nowrap|hidden|visible|inherit|bold|italic|normal)')
print('[literals] on-screen strings not in the storyboard or fact list (check by hand):')
seen = set()
for g in groups:
    for f in sorted(glob.glob(f'{ROOT}/src/shots/{g}/*.tsx')):
        src = open(f, encoding='utf-8').read()
        for s in re.findall(r"(?:'|\"|`)([^'\"`\n]{3,80})(?:'|\"|`)", src):
            s2 = s.strip()
            if not s2 or noise.match(s2) or s2 in seen: continue
            if '${' in s2 or 'px' in s2 or 'rgba' in s2 or 'gradient' in s2 or re.fullmatch(r'[\d.,\s]+', s2) or s2.startswith('./') or re.match(r'^[a-zA-Z-]+\(', s2) or s2 in ('border-box','content-box'): continue  # CSS / template-string / path noise
            if re.fullmatch(r'[\d.,×x%+\-–\s]+', s2): pass  # list all numeric strings
            elif not re.search(r'[A-Za-z]{3}', s2): continue
            if s2 in fact_txt or s2 in sb: continue
            seen.add(s2); print(f'  {os.path.basename(f)}: {s2}')
print(f'\nproblems: {problems}')

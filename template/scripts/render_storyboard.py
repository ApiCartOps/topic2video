#!/usr/bin/env python3
"""Replaces the time tokens in script/storyboard_src.md with frame numbers from script/timeline.json, and writes the result to <project-root>/分镜表.md (the storyboard table).
Tokens: {S12.from} {S12.to} {S12.c3} (start frame of the third subtitle chunk) {C2} (start frame of chapter 2) {TOTAL}. Each can take an integer offset, such as {S12.from-8}."""
import json, re, sys, os
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
tl = json.load(open(f'{here}/script/timeline.json'))
S = {s['id']: s for s in tl['sentences']}
C = {c['n']: c['from'] for c in tl['chapters']}
def sub(m):
    key, field, off = m.group(1), m.group(2), int(m.group(3) or 0)
    if key == 'TOTAL': v = tl['total_frames']
    elif key.startswith('C'): v = C[int(key[1:])]
    else:
        s = S[key]
        if field == 'from': v = s['from']
        elif field == 'to': v = s['to']
        elif field and field.startswith('c'): v = s['subs'][int(field[1:]) - 1]['from']
        else: raise SystemExit(f'bad token {m.group(0)}')
    return str(v + off)
src = open(f'{here}/script/storyboard_src.md', encoding='utf-8').read()
out = re.sub(r'\{(S\d\d|C\d|TOTAL)(?:\.(from|to|c\d+))?([+-]\d+)?\}', sub, src)
open(f'{here}/分镜表.md', 'w', encoding='utf-8').write(out)
left = re.findall(r'\{S\d\d[^}]*\}', out)
print('written 分镜表.md; unresolved:', left[:5])

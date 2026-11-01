#!/usr/bin/env python3
"""LinkedIn demo of Topic2video, built with the Python-only build in template/py.

Reuses template/py for the voiceover + timeline (tts.py) and the checks (qc.py). The renderer here is demo-specific: instead of a
star field and subtitles only, every narration beat gets a scene drawn in code (calendar, input box, sentence cards, waveform,
code next to its frame, build comparison, terminal, two-language subtitles). The picture is 1920x1080, the layout is designed on a
1280x720 grid (K = 1.5), text is large and bold, and the MP4 is H.264 at about 6 Mbps with AAC audio.

  python demo/build.py build [--ver v1] [--engine edge|dummy]   # tts -> render -> qc
  python demo/build.py tts | render | qc

Needs the packages in template/py/requirements.txt. Monospace text uses Consolas, falling back to Cascadia or Courier New.
"""
import argparse, bisect, math, multiprocessing as mp, os, re, subprocess, sys, wave

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), 'template')
for k, v in {'VOICE': 'en-US-AndrewNeural', 'RATE': '+0%', 'LEAD': '60', 'CHAPTER_GAP': '18', 'TAIL': '75'}.items():
    os.environ.setdefault(k, v)
sys.path.insert(0, os.path.join(TEMPLATE, 'py'))
import common  # noqa: E402

# Point the template build at this demo project (script/, py/video.json, renders/ live in demo/) and at 1080p.
common.ROOT = HERE
common.FONTS = os.path.join(TEMPLATE, 'public', 'fonts')
common.W, common.H = 1920, 1080

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from common import FPS, W, H, FONTS  # noqa: E402

K = 1.5                       # design units (1280x720) -> pixels
BITRATE = os.environ.get('BITRATE', '5M')   # CBR: flat UI content is cheap (CRF 9 gave ~1 Mbps), so the rate is pinned to stay above 4 Mbps

BG = (10, 12, 24)
CARD = (22, 27, 48)
CARD2 = (32, 38, 66)
LINE = (86, 96, 150)
WHITE = (255, 255, 255)
SOFT = (208, 214, 236)
DIM = (150, 158, 190)
VIOLET = (167, 139, 250)
VIOLET_D = (98, 70, 200)
AMBER = (251, 191, 36)
GREEN = (74, 222, 128)
RED = (248, 113, 113)
CYAN = (103, 232, 249)
INK = (16, 18, 30)


# ---------------------------------------------------------------- drawing helpers
_fonts = {}


def get_font(kind, size, weight=700):
    key = (kind, size, weight)
    if key in _fonts:
        return _fonts[key]
    if kind == 'mono':
        for name in ('consolab.ttf', 'consola.ttf', 'CascadiaMono.ttf', 'courbd.ttf'):
            p = os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts', name)
            if os.path.exists(p):
                f = ImageFont.truetype(p, size)
                break
        else:
            f = ImageFont.truetype(os.path.join(FONTS, 'NotoSansSC.ttf'), size)
    elif kind == 'display':
        f = ImageFont.truetype(os.path.join(FONTS, 'Audiowide-Regular.ttf'), size)
    else:
        f = ImageFont.truetype(os.path.join(FONTS, 'NotoSansSC.ttf'), size)
        f.set_variation_by_axes([weight])
    _fonts[key] = f
    return f


def px(v):
    return int(round(v * K))


def clamp01(x):
    return max(0.0, min(1.0, x))


def seg(n, a, b):
    """0..1 progress of n between frames a and b."""
    return clamp01((n - a) / max(1e-9, b - a))


def ss(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


class Canvas:
    """Draws in design units on an RGB image."""

    def __init__(self, img):
        self.im = img
        self.d = ImageDraw.Draw(img)

    def rect(self, x, y, w, h, fill=None, outline=None, r=0, width=2):
        if w < 1 or h < 1:
            return
        box = (px(x), px(y), px(x + w) - 1, px(y + h) - 1)
        if r:
            self.d.rounded_rectangle(box, radius=px(r), fill=fill, outline=outline, width=px(width))
        else:
            self.d.rectangle(box, fill=fill, outline=outline, width=px(width) if outline else 0)

    def ellipse(self, cx, cy, rx, ry=None, fill=None, outline=None, width=2):
        ry = rx if ry is None else ry
        self.d.ellipse((px(cx - rx), px(cy - ry), px(cx + rx), px(cy + ry)), fill=fill, outline=outline, width=px(width))

    def line(self, pts, color, width=2):
        self.d.line([(px(x), px(y)) for x, y in pts], fill=color, width=max(1, px(width)), joint='curve')

    def poly(self, pts, fill):
        self.d.polygon([(px(x), px(y)) for x, y in pts], fill=fill)

    def text(self, x, y, s, size, color=WHITE, weight=700, anchor='lm', kind='text'):
        self.d.text((px(x), px(y)), s, font=get_font(kind, px(size), weight), fill=color, anchor=anchor)

    def tw(self, s, size, weight=700, kind='text'):
        return get_font(kind, px(size), weight).getlength(s) / K

    def card(self, x, y, w, h, fill=CARD, outline=LINE, r=18, width=2):
        self.rect(x, y, w, h, fill=fill, outline=outline, r=r, width=width)

    def arrow(self, x0, y, x1, color=SOFT, width=5, head=16):
        self.line([(x0, y), (x1 - head * 0.6, y)], color, width)
        self.poly([(x1, y), (x1 - head, y - head * 0.6), (x1 - head, y + head * 0.6)], color)

    def check(self, cx, cy, s, color=GREEN, width=6):
        self.line([(cx - s * 0.5, cy), (cx - s * 0.1, cy + s * 0.4), (cx + s * 0.55, cy - s * 0.4)], color, width)

    def cross(self, cx, cy, s, color=RED, width=6):
        self.line([(cx - s / 2, cy - s / 2), (cx + s / 2, cy + s / 2)], color, width)
        self.line([(cx - s / 2, cy + s / 2), (cx + s / 2, cy - s / 2)], color, width)


def wrap(c, text, size, width, weight=700):
    """Greedy wrap that breaks between words and between CJK characters."""
    tokens = re.findall(r"[A-Za-z0-9_\-.']+\s*|\s+|.", text)
    lines, cur = [], ''
    for t in tokens:
        if cur and c.tw((cur + t).rstrip(), size, weight) > width:
            lines.append(cur.rstrip())
            cur = t.lstrip()
        else:
            cur += t
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def ellipsize(c, text, size, width, weight=700):
    if c.tw(text, size, weight) <= width:
        return text
    while len(text) > 1 and c.tw(text + '…', size, weight) > width:
        text = text[:-1]
    return text.rstrip() + '…'


def heading(c, label):
    c.text(64, 52, label, 27, VIOLET, kind='display')
    c.rect(64, 76, 64, 4, fill=VIOLET)


# ---------------------------------------------------------------- timeline access
class TL:
    def __init__(self, tl):
        self.tl = tl
        self.s = {s['id']: s for s in tl['sentences']}
        self.subs = [sb for s in tl['sentences'] for sb in s['subs']]
        self.starts = [sb['from'] for sb in self.subs]
        self.chapters = tl['chapters']
        self.total = tl['total_frames']

    def span(self, sid):
        return self.s[sid]['from'], self.s[sid]['to']

    def chunk(self, sid, k):
        sb = self.s[sid]['subs'][k]
        return sb['from'], sb['to'] + 1


# ---------------------------------------------------------------- scenes
def scene_intro(c, n, T, ctx):
    p = ss(seg(n, 1, 20))
    col = mix(BG, WHITE, p)
    c.text(640 + 5, 290 + 5, 'Topic2video', 118, mix(BG, VIOLET, p), anchor='mm', kind='display')
    c.text(640, 290, 'Topic2video', 118, col, anchor='mm', kind='display')
    q = ss(seg(n, 18, 38))
    c.text(640, 400, 'Any topic in. A narrated video out.', 44, mix(BG, SOFT, q), anchor='mm')
    c.text(640, 465, 'Python build', 34, mix(BG, AMBER, q), anchor='mm')


def clock(c, cx, cy, r, n):
    c.ellipse(cx, cy, r, fill=WHITE, outline=INK, width=4)
    for i in range(12):
        a = i * math.pi / 6
        c.line([(cx + math.sin(a) * r * 0.82, cy - math.cos(a) * r * 0.82), (cx + math.sin(a) * r * 0.95, cy - math.cos(a) * r * 0.95)], INK, 2)
    am = n * 0.22
    ah = am / 12
    c.line([(cx, cy), (cx + math.sin(am) * r * 0.78, cy - math.cos(am) * r * 0.78)], INK, 4)
    c.line([(cx, cy), (cx + math.sin(ah) * r * 0.5, cy - math.cos(ah) * r * 0.5)], INK, 5)
    c.ellipse(cx, cy, 4, fill=INK)


def scene_problem(c, n, T, ctx):
    heading(c, 'THE PROBLEM')
    s0, s1 = T.span('S01')
    b0, b1 = T.chunk('S01', 1)
    c.card(64, 104, 560, 440)
    c.rect(64, 104, 560, 92, fill=VIOLET_D, r=18)
    c.rect(64, 160, 560, 36, fill=VIOLET_D)
    c.text(96, 150, 'DAYS', 54, WHITE, kind='display')
    clock(c, 556, 150, 36, n)
    filled = int(seg(n, s0, s1 + 50) * 21)
    for i in range(21):
        r_, col_ = divmod(i, 7)
        x, y = 92 + col_ * 74, 214 + r_ * 104
        on = i < filled
        c.rect(x, y, 66, 88, fill=AMBER if on else CARD2, r=10)
        c.text(x + 33, y + 44, str(i + 1), 34, INK if on else SOFT, anchor='mm')
    p = ss(seg(n, b0 - 6, b0 + 14))
    for i, (title, y) in enumerate((('Drawing', 104), ('Timing', 334))):
        dx = (1 - p) * 120
        if p <= 0:
            continue
        x = 680 + dx
        fade = p
        c.card(x, y, 536, 210, fill=mix(BG, CARD, fade), outline=mix(BG, AMBER, fade), width=3)
        if i == 0:
            c.rect(x + 28, y + 40, 56, 56, fill=mix(BG, CYAN, fade), r=6)
            c.ellipse(x + 130, y + 68, 28, fill=mix(BG, VIOLET, fade))
            c.poly([(x + 188, y + 96), (x + 216, y + 40), (x + 244, y + 96)], mix(BG, GREEN, fade))
        else:
            c.rect(x + 28, y + 62, 220, 12, fill=mix(BG, SOFT, fade), r=4)
            for t in range(11):
                hh = 30 if t % 5 == 0 else 18
                c.rect(x + 28 + t * 21, y + 74, 4, hh, fill=mix(BG, SOFT, fade))
            c.rect(x + 28 + 130, y + 36, 6, 78, fill=mix(BG, RED, fade))
        c.text(x + 290, y + 66, title, 50, mix(BG, WHITE, fade))
        c.rect(x + 28, y + 150, 480, 24, fill=mix(BG, CARD2, fade), r=12)
        bar = ss(seg(n, b0 + 6 + i * 10, b1 + 40)) * 0.93
        if bar > 0:
            c.rect(x + 28, y + 150, 480 * bar, 24, fill=mix(BG, AMBER, fade), r=12)


def mini_frame(c, x, y, w, h, k, total=6):
    """A small video frame with a ball at position k/total: used as 'frames' in the hero scene."""
    c.rect(x, y, w, h, fill=(8, 10, 20), outline=LINE, r=8, width=2)
    t = k / (total - 1)
    c.rect(x + 10, y + h - 24, w - 20, 8, fill=CARD2, r=3)
    c.ellipse(x + 26 + (w - 52) * t, y + h * 0.42 + math.sin(t * math.pi) * -22, 15, fill=VIOLET)
    c.text(x + w - 10, y + 18, f'{k + 1}', 20, SOFT, anchor='rm')


def scene_hero(c, n, T, ctx):
    heading(c, 'WHAT IT DOES')
    a0, a1 = T.chunk('S02', 0)
    b0, b1 = T.chunk('S02', 1)
    steps = [(a0, 64, 'Any topic'), (a0 + (a1 - a0) * 0.34, 475, 'Topic2video'), (a0 + (a1 - a0) * 0.68, 886, 'Narrated video')]
    for i, (st, x, label) in enumerate(steps):
        p = ss(seg(n, st - 4, st + 10))
        if p <= 0:
            continue
        fill = VIOLET_D if i == 1 else CARD
        out = VIOLET if i == 1 else LINE
        c.card(x, 110, 330, 200, fill=mix(BG, fill, p), outline=mix(BG, out, p), width=3)
        if i == 0:
            c.rect(x + 36, 150, 258, 46, fill=mix(BG, WHITE, p), r=10)
            c.text(x + 52, 173, 'How vaccines work', 23, mix(BG, INK, p))
        elif i == 1:
            c.text(x + 165, 173, '</>', 56, mix(BG, WHITE, p), anchor='mm', kind='mono')
        else:
            c.rect(x + 36, 144, 258, 58, fill=mix(BG, (8, 10, 20), p), r=8)
            c.poly([(x + 152, 158), (x + 152, 188), (x + 178, 173)], mix(BG, WHITE, p))
        c.text(x + 165, 262, label, 40 if i != 1 else 36, mix(BG, WHITE, p), anchor='mm', kind='text' if i != 1 else 'display')
    for i, ax in enumerate((402, 813)):
        p = ss(seg(n, steps[i + 1][0] - 10, steps[i + 1][0] + 4))
        if p > 0:
            c.arrow(ax, 210, ax + 66, mix(BG, SOFT, p), width=6, head=20)
    # chunk b: frames drawn in code
    p = ss(seg(n, b0 - 4, b0 + 10))
    if p > 0:
        c.card(64, 350, 1152, 200, fill=mix(BG, CARD, p), outline=mix(BG, LINE, p))
        c.text(96, 386, '</>', 40, mix(BG, AMBER, p), kind='mono')
        c.text(190, 386, 'Every frame is drawn in code', 36, mix(BG, WHITE, p))
        for k in range(6):
            q = ss(seg(n, b0 + 6 + k * (b1 - b0) * 0.11, b0 + 18 + k * (b1 - b0) * 0.11))
            if q > 0:
                mini_frame(c, 96 + k * 178, 418, 164, 108, k)


def scene_input(c, n, T, ctx):
    heading(c, 'TOPIC OR ARTICLE IN')
    a0, a1 = T.chunk('S03', 0)
    b0, b1 = T.chunk('S03', 1)
    article = n >= a0 + (a1 - a0) * 0.56
    for i, (label, x) in enumerate((('Topic', 64), ('Article', 262))):
        on = (i == 1) == article
        c.rect(x, 108, 186, 56, fill=VIOLET_D if on else CARD, outline=VIOLET if on else LINE, r=14, width=3)
        c.text(x + 93, 137, label, 32, WHITE if on else SOFT, anchor='mm')
    c.card(64, 176, 540, 300, fill=(240, 242, 252), outline=VIOLET, width=4)
    if not article:
        s = 'How vaccines work'
        shown = s[:int(len(s) * ss(seg(n, a0, a0 + (a1 - a0) * 0.5)))]
        c.text(92, 222, shown, 44, INK)
        if (n // 8) % 2 == 0:
            cx = 92 + c.tw(shown, 44)
            c.rect(cx + 3, 200, 4, 46, fill=INK)
    else:
        q = seg(n, a0 + (a1 - a0) * 0.56, a1)
        c.text(92, 214, 'article.txt', 30, VIOLET_D)
        for i, wd in enumerate((440, 400, 450, 360, 430, 300)):
            w_ = wd * ss(seg(q, i * 0.1, i * 0.1 + 0.3))
            c.rect(92, 252 + i * 34, w_, 14, fill=(150, 156, 190), r=6)
    sentences = ['Vaccines train your body.', 'It learns to spot a germ.', 'Next time, it reacts fast.', 'That keeps you protected.']
    p0 = ss(seg(n, b0 - 6, b0 + 8))
    if p0 > 0:
        c.arrow(620, 326, 676, mix(BG, SOFT, p0), width=6, head=20)
    for i, sentence in enumerate(sentences):
        st = b0 + i * (b1 - b0) * 0.2
        p = ss(seg(n, st, st + 10))
        if p <= 0:
            continue
        x, y = 690 + (1 - p) * 80, 104 + i * 114
        c.card(x, y, 526, 98, fill=mix(BG, CARD, p), outline=mix(BG, LINE, p), width=3)
        c.ellipse(x + 44, y + 49, 26, fill=mix(BG, VIOLET_D, p))
        c.text(x + 44, y + 49, str(i + 1), 30, mix(BG, WHITE, p), anchor='mm')
        c.text(x + 88, y + 49, sentence, 29, mix(BG, WHITE, p))
    c.text(334, 520, 'Input', 30, SOFT, anchor='mm')


def scene_audio(c, n, T, ctx):
    heading(c, 'VOICEOVER + TIMED SUBTITLES')
    a0, a1 = T.chunk('S04', 0)
    b0, b1 = T.chunk('S04', 1)
    t0 = ctx['win_t0']
    span = ctx['win_span']
    env = ctx['env']
    x0, x1 = 64, 1216
    pps = (x1 - x0) / span
    c.text(64, 108, 'Voiceover', 32, CYAN)
    c.card(64, 132, 1152, 230, fill=(14, 17, 34), outline=LINE)
    reveal = ss(seg(n, a0, a1 - 6))
    ncol = len(env)
    cols = int(ncol * reveal)
    for i in range(cols):
        h = max(2, env[i] * 100)
        x = x0 + 12 + (x1 - x0 - 24) * i / ncol
        c.rect(x, 247 - h, (x1 - x0 - 24) / ncol * 0.62, 2 * h, fill=CYAN)
    # subtitle blocks
    q = ss(seg(n, b0 - 2, b0 + 8))
    if q > 0:
        c.text(64, 390, 'Subtitles', 32, AMBER)
    for k, sb in enumerate(ctx['blocks']):
        st = b0 + k * (b1 - b0) * 0.12
        p = ss(seg(n, st, st + 10))
        if p <= 0:
            continue
        bx = x0 + 12 + (sb['t0'] - t0) / span * (x1 - x0 - 24)
        bw = (sb['t1'] - sb['t0']) / span * (x1 - x0 - 24) - 8
        c.line([(bx, 362), (bx, 424)], mix(BG, AMBER, p), 3)
        by = 424 + (1 - p) * 20
        c.rect(bx, by, bw, 118, fill=mix(BG, AMBER, p), r=12)
        lines = wrap(c, sb['text'], 26, bw - 20)[:3]
        if len(lines) == 3 and len(wrap(c, sb['text'], 26, bw - 20)) > 3:
            lines[2] = ellipsize(c, lines[2] + ' …', 26, bw - 20)
        for j, ln in enumerate(lines):
            c.text(bx + 12, by + 26 + j * 33, ln, 26, mix(BG, INK, p))
    ph = seg(n, b0, b1 + 20)
    if 0 < ph < 1:
        x = x0 + 12 + ph * (x1 - x0 - 24)
        c.rect(x - 2, 134, 4, 226, fill=WHITE)


def scene_code(c, n, T, ctx):
    heading(c, 'EVERY FRAME IS CODE')
    a0, a1 = T.chunk('S05', 0)
    b0, b1 = T.chunk('S05', 1)
    swap = n >= b0 + (b1 - b0) * 0.35
    col_name = 'GREEN' if swap else 'VIOLET'
    lines = [
        [('d.rounded_rectangle(card, ', WHITE), ('fill=' + col_name, AMBER if not swap else GREEN), (')', WHITE)],
        [('d.ellipse(star, ', WHITE), ('fill=WHITE', AMBER), (')', WHITE)],
        [('d.text(pos, ', WHITE), ('"Topic2video"', CYAN), (', font=f)', WHITE)],
        [('img.save(', WHITE), ('"frame_0001.png"', CYAN), (')', WHITE)],
    ]
    c.card(64, 104, 630, 440, fill=(12, 15, 30), outline=LINE)
    c.rect(64, 104, 630, 48, fill=CARD2, r=18)
    c.rect(64, 130, 630, 22, fill=CARD2)
    for i, col_ in enumerate((RED, AMBER, GREEN)):
        c.ellipse(94 + i * 28, 128, 8, fill=col_)
    c.text(664, 128, 'draw_frame.py', 24, SOFT, anchor='rm')
    # typing progress over chunk a: line i starts at i/4
    done_stage = 0
    for i, segs in enumerate(lines):
        total_chars = sum(len(t) for t, _ in segs)
        p = seg(n, a0 + (a1 - a0) * i / 4, a0 + (a1 - a0) * (i + 0.85) / 4)
        if i == 0 and swap:
            p = 1
        shown = int(round(total_chars * p))
        if shown >= total_chars:
            done_stage = max(done_stage, i + 1)
        if shown <= 0:
            continue
        x = 92
        y = 196 + i * 86
        for t, col_ in segs:
            if shown <= 0:
                break
            part = t[:shown]
            c.text(x, y, part, 26, col_, kind='mono')
            x += c.tw(part, 26, kind='mono')
            shown -= len(t)
    if swap:
        c.rect(84, 172, 598, 48, outline=GREEN, r=8, width=3)
    # frame preview, drawn by the same four calls
    c.card(722, 104, 494, 290 + 14, fill=(12, 15, 30), outline=LINE)
    ctx_frame = ctx['mini'](done_stage, (34, 197, 94) if swap else (124, 92, 230))
    c.im.paste(ctx_frame, (px(731), px(112)))
    if done_stage >= 4:
        c.text(969, 436, 'frame_0001.png', 30, SOFT, anchor='mm', kind='mono')
    if swap:
        q = ss(seg(n, b0 + (b1 - b0) * 0.4, b0 + (b1 - b0) * 0.7))
        c.card(722, 470, 494, 74, fill=mix(BG, CARD, q), outline=mix(BG, GREEN, q), width=3)
        c.text(969, 507, 'Edit the code, re-render', 34, mix(BG, WHITE, q), anchor='mm')
    elif n >= b0:
        c.card(722, 470, 494, 74, fill=CARD, outline=VIOLET, width=3)
        c.text(969, 507, 'Same code, same frame', 34, WHITE, anchor='mm')


def make_mini(stage, color):
    """The preview frame, produced by running the very calls the code panel shows (same order)."""
    w, h = px(476), px(282)
    img = Image.new('RGB', (w, h), (8, 10, 20))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(os.path.join(FONTS, 'Audiowide-Regular.ttf'), px(44))
    card = (px(30), px(30), px(446), px(252))
    star = (px(366), px(48), px(416), px(98))
    pos = (px(58), px(150))
    if stage >= 1:
        d.rounded_rectangle(card, radius=px(24), fill=color)
    if stage >= 2:
        d.ellipse(star, fill=(255, 255, 255))
    if stage >= 3:
        d.text(pos, 'Topic2video', font=f, fill=(255, 255, 255))
    return img


def scene_python(c, n, T, ctx):
    heading(c, 'PYTHON BUILD')
    a0, a1 = T.chunk('S06', 0)
    b0, b1 = T.chunk('S06', 1)
    p = ss(seg(n, a0 - 4, a0 + 12))
    if p > 0:
        c.card(64, 110, 560, 420, fill=mix(BG, CARD, p), outline=mix(BG, GREEN, p), width=5)
        c.ellipse(120, 176, 30, fill=mix(BG, GREEN, p))
        c.check(120, 176, 30, mix(BG, INK, p), 7)
        c.text(172, 176, 'Python build', 50, mix(BG, WHITE, p))
        steps = ['Narration', 'Frames', 'MP4']
        for i, s in enumerate(steps):
            q = ss(seg(n, a0 + 6 + i * (a1 - a0) * 0.2, a0 + 20 + i * (a1 - a0) * 0.2))
            if q <= 0:
                continue
            x = 90 + i * 168
            c.rect(x, 262, 140, 66, fill=mix(BG, VIOLET_D, q), r=12)
            c.text(x + 70, 295, s, 27, mix(BG, WHITE, q), anchor='mm')
            if i < 2:
                c.arrow(x + 144, 295, x + 164, mix(BG, SOFT, q), width=4, head=12)
        c.text(344, 420, 'renders the whole video', 36, mix(BG, SOFT, p), anchor='mm')
    q0 = ss(seg(n, b0 - 4, b0 + 10))
    if q0 > 0:
        c.text(948, 130, 'Not needed', 32, mix(BG, RED, q0), anchor='mm')
        for i, name in enumerate(('Node.js', 'Remotion')):
            st = b0 + i * (b1 - b0) * 0.25
            q = ss(seg(n, st, st + 10))
            if q <= 0:
                continue
            y = 164 + i * 190
            c.card(680, y, 536, 160, fill=mix(BG, CARD, q), outline=mix(BG, RED, q), width=4)
            c.text(948, y + 80, name, 62, mix(BG, SOFT, q), anchor='mm')
            s = ss(seg(n, st + 8, st + 22))
            if s > 0:
                wn = c.tw(name, 62)
                c.line([(948 - wn / 2 - 20, y + 80), (948 - wn / 2 - 20 + (wn + 40) * s, y + 80)], RED, 8)


def scene_terminal(c, n, T, ctx):
    heading(c, 'TRY IT')
    s7a, s7b = T.span('S07')
    s8a, s8b = T.span('S08')
    c.card(64, 104, 1152, 440, fill=(8, 10, 20), outline=LINE, width=3)
    c.rect(64, 104, 1152, 52, fill=CARD2, r=18)
    c.rect(64, 134, 1152, 22, fill=CARD2)
    for i, col_ in enumerate((RED, AMBER, GREEN)):
        c.ellipse(98 + i * 30, 130, 9, fill=col_)
    c.text(640, 130, 'terminal', 26, SOFT, anchor='mm')
    cmds = [('pip install -r py/requirements.txt', 0.0, 0.42, 1), ('python py/explain.py build', 0.52, 0.95, 2)]
    for cmd, f0, f1, num in cmds:
        y = 196 + (num - 1) * 66
        a = s7a - 4 + (s7b - s7a) * f0
        if n < a:
            continue
        p = seg(n, a, s7a + (s7b - s7a) * f1)
        shown = cmd[:int(math.ceil(len(cmd) * p))]
        c.ellipse(104, y, 20, fill=VIOLET_D)
        c.text(104, y, str(num), 26, WHITE, anchor='mm')
        c.text(146, y, '$', 34, GREEN, kind='mono')
        c.text(184, y, shown, 34, WHITE, kind='mono')
        if p < 1 and (n // 6) % 2 == 0:
            c.rect(184 + c.tw(shown, 34, kind='mono') + 2, y - 20, 16, 40, fill=WHITE)
    if n >= s7a and n < s8a - 4:
        if (n // 8) % 2 == 0 and n > s7a + (s7b - s7a) * 0.95:
            c.rect(184 + c.tw(cmds[1][0], 34, kind='mono') + 2, 196 + 66 - 20, 16, 40, fill=WHITE)
    outs = [('renders/topic2video-demo_v1.mp4', 'MP4', GREEN), ('renders/sheet_v1.png', 'Contact sheet', CYAN),
            ('script/timeline.json', 'Timeline', AMBER)]
    for i, (path, label, col_) in enumerate(outs):
        st = s8a + (s8b - s8a) * (0.0, 0.34, 0.66)[i]
        p = ss(seg(n, st, st + 8))
        if p <= 0:
            continue
        y = 338 + i * 66
        c.check(104, y, 28, mix(BG, col_, p), 7)
        c.text(146, y, path, 31, mix(BG, WHITE, p), kind='mono')
        wl = c.tw(label, 32) + 44
        c.rect(1176 - wl, y - 26, wl, 52, fill=mix(BG, col_, p), r=26)
        c.text(1176 - wl / 2, y, label, 32, mix(BG, INK, p), anchor='mm')


def scene_lang(c, n, T, ctx):
    heading(c, 'CHINESE + ENGLISH')
    a0, a1 = T.span('S09')
    panels = [(64, 'English', 'Topic2video turns any topic into a narrated video.', CYAN),
              (646, '中文', 'Topic2video 将任意主题变成解说视频。', AMBER)]
    for i, (x, label, text, col_) in enumerate(panels):
        p = ss(seg(n, a0 - 4 + i * (a1 - a0) * 0.22, a0 + 12 + i * (a1 - a0) * 0.22))
        if p <= 0:
            continue
        c.card(x, 108, 570, 340, fill=mix(BG, CARD, p), outline=mix(BG, col_, p), width=4)
        c.rect(x + 28, 134, 150 if i == 0 else 110, 52, fill=mix(BG, col_, p), r=26)
        c.text(x + 28 + (75 if i == 0 else 55), 160, label, 32, mix(BG, INK, p), anchor='mm')
        c.rect(x + 28, 214, 514, 200, fill=mix(BG, (0, 0, 0), p), r=14)
        for j, ln in enumerate(wrap(c, text, 36, 490)[:4]):
            c.text(x + 40, 252 + j * 52, ln, 36, mix(BG, WHITE, p))
    q = ss(seg(n, a0 + (a1 - a0) * 0.62, a0 + (a1 - a0) * 0.62 + 10))
    if q > 0:
        c.ellipse(480, 506, 28, fill=mix(BG, GREEN, q))
        c.check(480, 506, 28, mix(BG, INK, q), 7)
        c.text(528, 506, 'Both narrations work', 42, mix(BG, WHITE, q))


SCENES = [('intro', scene_intro, []), ('problem', scene_problem, ['S01']), ('hero', scene_hero, ['S02']),
          ('input', scene_input, ['S03']), ('audio', scene_audio, ['S04']), ('code', scene_code, ['S05']),
          ('python', scene_python, ['S06']), ('terminal', scene_terminal, ['S07', 'S08']), ('lang', scene_lang, ['S09'])]
XFADE = 8

_G = {}


def init_worker(tl_path, ver):
    import json
    with open(tl_path, encoding='utf-8') as f:
        tl = json.load(f)
    T = TL(tl)
    cfg = common.load_config()
    _G['T'] = T
    bounds = [0]
    for _, _, ids in SCENES[1:]:
        bounds.append(T.s[ids[0]]['from'] - 8)
    _G['bounds'] = bounds
    _G['ctx'] = make_ctx(T, cfg)
    _G['bg'] = make_bg()
    _G['ctx']['mini'] = make_mini


def make_bg():
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W * 0.5) / (W * 0.7)) ** 2 + ((yy - H * 0.0) / (H * 0.9)) ** 2)
    g = np.clip(1 - d, 0, 1) ** 2
    arr = np.zeros((H, W, 3), np.float32)
    arr[..., 0] = BG[0] + 22 * g
    arr[..., 1] = BG[1] + 14 * g
    arr[..., 2] = BG[2] + 46 * g
    return Image.fromarray(arr.astype(np.uint8), 'RGB')


def make_ctx(T, cfg):
    """Real voiceover envelope + subtitle blocks for the waveform scene."""
    with wave.open(common.audio_path(cfg), 'rb') as w:
        sr = w.getframerate()
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, w.getnchannels())
    mono = np.abs(raw.astype(np.float32).mean(axis=1)) / 32768.0
    t0 = max(0.0, (T.s['S01']['from'] - 1) / FPS - 1.9)
    span = 12.0
    ncol = 180
    edges = np.linspace(t0, t0 + span, ncol + 1)
    env = np.array([mono[int(a * sr):max(int(a * sr) + 1, int(b * sr))].max() if int(a * sr) < len(mono) else 0
                    for a, b in zip(edges[:-1], edges[1:])])
    env = np.clip(env / (env.max() or 1.0), 0, 1) ** 0.8
    blocks = []
    for sb in T.subs:
        a, b = (sb['from'] - 1) / FPS, sb['to'] / FPS
        if a >= t0 and b <= t0 + span + 0.01:
            blocks.append({'t0': a, 't1': b, 'text': sb['text']})
    return {'win_t0': t0, 'win_span': span, 'env': env, 'blocks': blocks}


def scene_index(n):
    b = _G['bounds']
    i = bisect.bisect_right(b, n) - 1
    return max(0, i)


def render_scene(i, n, base):
    img = base.copy()
    SCENES[i][1](Canvas(img), n, _G['T'], _G['ctx'])
    return img


def draw_overlay(img, n):
    """Subtitle (large, high contrast) and the chapter bar."""
    T = _G['T']
    c = Canvas(img)
    ov = ImageDraw.Draw(img, 'RGBA')
    k = bisect.bisect_right(T.starts, n) - 1
    if k >= 0 and n <= T.subs[k]['to']:
        sb = T.subs[k]
        size = 42
        while size > 28 and c.tw(sb['text'], size) > 1160:
            size -= 2
        tw_ = c.tw(sb['text'], size)
        bx0, bx1 = 640 - tw_ / 2 - 28, 640 + tw_ / 2 + 28
        ov.rounded_rectangle((px(bx0), px(582), px(bx1), px(662)), radius=px(16), fill=(0, 0, 0, 215))
        c.text(640, 622, sb['text'], size, WHITE, 800, anchor='mm')
    total = T.total
    chapters = T.chapters
    ov.rectangle((0, px(672), W, H), fill=(0, 0, 0, 255))
    c.rect(0, 672, 1280, 8, fill=(60, 64, 96))
    c.rect(0, 672, 1280 * n / total, 8, fill=VIOLET)
    cur = max((i for i, ch in enumerate(chapters) if ch['from'] <= n), default=-1)
    for i, ch in enumerate(chapters):
        x0 = 1280 * (ch['from'] - 1) / total
        x1 = 1280 * ((chapters[i + 1]['from'] - 1) if i + 1 < len(chapters) else total) / total
        label = f"{ch['n']}  {ch['title']}"
        c.text(x0 + 10, 701, ellipsize(c, label, 25, x1 - x0 - 20), 25, VIOLET if i == cur else DIM, 800)
        if i:
            c.rect(x0, 684, 2, 32, fill=(90, 96, 140))


def render_frame(n):
    bounds, base = _G['bounds'], _G['bg']
    i = scene_index(n)
    cur = render_scene(i, n, base)
    if i > 0 and n < bounds[i] + XFADE:
        cur = Image.blend(render_scene(i - 1, n, base), cur, ss(seg(n, bounds[i], bounds[i] + XFADE)))
    draw_overlay(cur, n)
    return n, cur.tobytes()


def do_render(cfg, ver):
    import json
    tl_path = common.timeline_path()
    if not os.path.exists(tl_path):
        raise SystemExit('script/timeline.json not found: run `python demo/build.py tts` first')
    with open(tl_path, encoding='utf-8') as f:
        total = json.load(f)['total_frames']
    out = common.video_path(cfg, ver)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = [common.ffmpeg_exe(), '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-i', common.audio_path(cfg), '-map', '0:v', '-map', '1:a',
           '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
           '-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high', '-b:v', BITRATE, '-minrate', BITRATE, '-maxrate', BITRATE, '-bufsize', '10M', '-x264-params', 'nal-hrd=cbr',
           '-g', '60', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart',
           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    sheet_every = 90
    thumbs = []
    ctx_mp = mp.get_context('spawn')
    try:
        with ctx_mp.Pool(max(2, (os.cpu_count() or 4) - 2), initializer=init_worker, initargs=(tl_path, ver)) as pool:
            batch = 48
            for a in range(1, total + 1, batch):
                for n, data in pool.map(render_frame, range(a, min(total, a + batch - 1) + 1)):
                    proc.stdin.write(data)
                    if (n - 1) % sheet_every == 0 or n == total:
                        thumbs.append((n, Image.frombytes('RGB', (W, H), data).resize((480, 270), Image.LANCZOS)))
                print(f'  frame {min(total, a + batch - 1)}/{total}', flush=True)
    finally:
        proc.stdin.close()
    if proc.wait() != 0 or not os.path.exists(out) or os.path.getsize(out) == 0:
        raise SystemExit(f'ffmpeg failed while writing {out}')
    write_sheet(thumbs, ver)
    print(f'rendered {out} ({total} frames, {total / FPS:.1f}s)')


def write_sheet(thumbs, ver):
    cols = 4
    rows = math.ceil(len(thumbs) / cols)
    tw_, th_ = 480, 270
    sheet = Image.new('RGB', (cols * (tw_ + 8) + 8, rows * (th_ + 40) + 8), (17, 17, 17))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(os.path.join(FONTS, 'NotoSansSC.ttf'), 22)
    f.set_variation_by_axes([600])
    for i, (n, img) in enumerate(thumbs):
        x, y = 8 + (i % cols) * (tw_ + 8), 8 + (i // cols) * (th_ + 40)
        sheet.paste(img, (x, y))
        d.text((x, y + th_ + 4), f'f{n}  {(n - 1) / FPS:.1f}s', font=f, fill=(210, 210, 210))
    path = os.path.join(common.ROOT, 'renders', f'sheet_{ver}.png')
    sheet.save(path)
    print(f'contact sheet: {path}')


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    p = argparse.ArgumentParser(description='Build the Topic2video LinkedIn demo (template/py + demo scenes).')
    sub = p.add_subparsers(dest='cmd', required=True)
    for name in ('build', 'tts', 'render', 'qc'):
        sp = sub.add_parser(name)
        sp.add_argument('--ver', default=os.environ.get('VER', 'v1'))
        if name in ('build', 'tts'):
            sp.add_argument('--engine', choices=['edge', 'dummy'], default=os.environ.get('TTS_ENGINE', 'edge'))
    args = p.parse_args()
    cfg = common.load_config()
    if args.cmd in ('build', 'tts'):
        import tts
        tts.run(cfg, args.engine)
    if args.cmd in ('build', 'render'):
        do_render(cfg, args.ver)
    if args.cmd in ('build', 'qc'):
        import qc
        if qc.run(cfg, args.ver):
            sys.exit(1)


if __name__ == '__main__':
    main()

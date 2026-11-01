"""Stage 2 (render): timeline + audio → renders/<slug>_<ver>.mp4 and a contact sheet, drawn with Pillow.

Visual language, a simplified port of the Remotion template: black canvas with a star field (or dot wave), an opening title,
chapter cards during the silent gaps, one subtitle chunk at a time, a progress bar with chapter labels, optional keyword cards
(script/cards.json) and an optional closing credit. Frames are piped as raw RGB into ffmpeg, which encodes H.264 and muxes the audio.

Frame numbers are 1-based, as in the Remotion template: frame n is shown at time (n - 1) / FPS.
"""
import bisect, json, math, os, random, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from common import ROOT, FPS, W, H, FONTS, ffmpeg_exe, timeline_path, audio_path, video_path

ACCENT = (167, 139, 250)
WHITE = (245, 245, 245)
GREY = (156, 163, 175)
SUB_SIZE = 44
SUB_MAX_W = 1160          # same safe width as the Remotion subtitles
SHEET_STEP = 60           # contact sheet: one thumbnail every SHEET_STEP frames
CHAPTER_GAP = int(os.environ.get('CHAPTER_GAP', 45))
FONT_FILES = {'display': 'Audiowide-Regular.ttf', 'text': 'NotoSansSC.ttf'}


@lru_cache(maxsize=None)
def font(kind, size, weight=600):
    f = ImageFont.truetype(os.path.join(FONTS, FONT_FILES[kind]), size)
    if kind == 'text':
        f.set_variation_by_axes([weight])   # NotoSansSC is a variable font whose default weight is Thin (100)
    return f


def text_kind(text):
    """Latin-only text uses the display face, as in the template's titles; anything with CJK uses the text face."""
    return 'display' if text.isascii() else 'text'


@lru_cache(maxsize=2048)
def text_img(text, kind, size, color, weight=600):
    """Pre-rendered RGBA text with a small margin (cached: a subtitle or title is drawn many times)."""
    f = font(kind, size, weight)
    l, t, r, b = f.getbbox(text)
    img = Image.new('RGBA', (r - l + 4, b - t + 4), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((2 - l, 2 - t), text, font=f, fill=color + (255,))
    return img


def scale_alpha(img, a):
    arr = np.array(img)
    arr[..., 3] = (arr[..., 3] * a).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


def paste(canvas, img, cx, top, alpha=1.0):
    """Draw img centred on x=cx with its top edge at y=top, at the given opacity."""
    if alpha <= 0:
        return
    if alpha < 1:
        img = scale_alpha(img, alpha)
    x = int(round(cx - img.width / 2))
    canvas.alpha_composite(img, (max(0, x), max(0, int(top))))


def ramp(n, a, b, fade=10):
    """Opacity envelope for frames a..b: fades in over `fade` frames, fades out over the last `fade` frames."""
    if n < a or n > b:
        return 0.0
    x = min(1.0, (n - a + 1) / fade, (b - n + 1) / fade)
    return x * x * (3 - 2 * x)


def fit_size(text, kind, size, max_w, min_size=24, weight=600):
    """Shrink the font until the text fits max_w (the template shrinks over-wide subtitles the same way)."""
    while size > min_size and font(kind, size, weight).getlength(text) > max_w:
        size -= 2
    return size


def make_stars(seed=7, count=420):
    """Static star layer twice the screen width, so it can drift sideways without an edge."""
    rng = random.Random(seed)
    layer = Image.new('RGBA', (2 * W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(count):
        x, y = rng.uniform(0, 2 * W), rng.uniform(0, H)
        r = rng.choice([0.7, 0.9, 1.1, 1.5, 2.0])
        v = rng.randint(90, 255)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(v, v, min(255, v + 20), 255))
    return layer


def make_fog():
    """Violet glow rising from the bottom edge (the template's fog gradient, simplified)."""
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((xx - W / 2) / (W * 0.6)) ** 2 + ((yy - H * 1.1) / (H * 0.9)) ** 2)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = 60, 40, 130
    arr[..., 3] = (np.clip(1 - dist, 0, 1) * 0.30 * 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


DOT_STEP = 30
DOTS = [(x, y) for y in range(DOT_STEP // 2, H, DOT_STEP) for x in range(DOT_STEP // 2, W, DOT_STEP)]


def dot_wave(canvas, n):
    """Dot-field backdrop: a diagonal sine wave of dots (config bg 'dots')."""
    d = ImageDraw.Draw(canvas)
    t = n / FPS
    for x, y in DOTS:
        b = 0.5 + 0.5 * math.sin(x * 0.012 + y * 0.018 - t * 1.6)
        c = (int(70 + 110 * b), int(70 + 110 * b), int(110 + 120 * b), 255)
        d.ellipse((x - 1.6, y - 1.6, x + 1.6, y + 1.6), fill=c)


def backdrop(n, bg, stars, fog):
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    if bg == 'dots':
        dot_wave(canvas, n)
    else:
        x0 = int(n * 0.2) % W
        canvas.alpha_composite(stars.crop((x0, 0, x0 + W, H)))
        canvas.alpha_composite(fog)
    return canvas


def draw_title(canvas, n, cfg, end):
    """Opening card: frames 1..end (up to the first chapter)."""
    t = cfg['title']
    a = ramp(n, 1, end - 1, fade=20)
    if a <= 0:
        return
    big = text_img(t['big'], 'display', 150, WHITE)
    shadow = text_img(t['big'], 'display', 150, ACCENT)
    rest = text_img(t['rest'], 'text', 120, WHITE, 900) if t.get('rest') else None
    total_w = big.width + (rest.width + 24 if rest else 0)
    x = W / 2 - total_w / 2
    paste(canvas, scale_alpha(shadow, 1), x + big.width / 2 + 5, 225 + 5, a)
    paste(canvas, big, x + big.width / 2, 225, a)
    if rest:
        paste(canvas, rest, x + big.width + 24 + rest.width / 2, 225 + 10, a)
    if t.get('en'):
        en = t['en']
        paste(canvas, text_img(en, 'display', 40, GREY), W / 2, 420, a)
    if t.get('tagline'):
        paste(canvas, text_img(t['tagline'], 'text', 48, ACCENT), W / 2, 490, a)


def draw_chapter(canvas, n, ch, tech, window):
    """Chapter card, shown in the silent gap before the chapter starts."""
    a = ramp(n, window[0], window[1], fade=12)
    if a <= 0:
        return
    paste(canvas, text_img(f"CHAPTER {ch['n']:02d}", 'display', 30, ACCENT), W / 2, 230, a)
    size = fit_size(ch['title'], 'text', 84, W - 160, weight=900)
    paste(canvas, text_img(ch['title'], 'text', size, WHITE, 900), W / 2, 290, a)
    if tech:
        paste(canvas, text_img(tech, text_kind(tech), 34, GREY), W / 2, 410, a)


def draw_card(canvas, n, card, window):
    """Keyword card shown over its sentence: one large term, with an optional English line."""
    a = ramp(n, window[0], window[1], fade=10)
    if a <= 0:
        return
    kind = text_kind(card['text'])
    size = fit_size(card['text'], kind, 120, W - 160, weight=900)
    paste(canvas, text_img(card['text'], kind, size, WHITE, 900), W / 2, 200, a)
    if card.get('sub'):
        paste(canvas, text_img(card['sub'], 'display', 34, ACCENT), W / 2, 388, a)


def draw_subtitle(canvas, n, subs, starts):
    i = bisect.bisect_right(starts, n) - 1
    if i < 0 or n > subs[i]['to']:
        return
    sb = subs[i]
    a = min(1.0, (n - sb['from'] + 1) / 4, (sb['to'] - n + 1) / 4)
    size = fit_size(sb['text'], 'text', SUB_SIZE, SUB_MAX_W)
    line = text_img(sb['text'], 'text', size, WHITE)
    pad_x, pad_y = 22, 10
    box = Image.new('RGBA', (line.width + 2 * pad_x, line.height + 2 * pad_y), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle((0, 0, box.width - 1, box.height - 1), radius=14, fill=(0, 0, 0, 150))
    box.alpha_composite(line, (pad_x, pad_y))
    paste(canvas, box, W / 2, H - 112, a)


def draw_progress(canvas, n, total, chapters):
    d = ImageDraw.Draw(canvas)
    frac = n / total
    d.rectangle((0, H - 8, W, H), fill=(255, 255, 255, 40))
    d.rectangle((0, H - 8, W * frac, H), fill=ACCENT + (255,))
    current = max((i for i, c in enumerate(chapters) if c['from'] <= n), default=-1)
    for i, c in enumerate(chapters):
        x0 = W * (c['from'] - 1) / total
        x1 = W * ((chapters[i + 1]['from'] - 1) if i + 1 < len(chapters) else total) / total
        label = c['title']
        size = 22
        while size > 14 and font('text', size).getlength(label) > x1 - x0 - 16:
            size -= 1
        while len(label) > 1 and font('text', size).getlength(label) > x1 - x0 - 16:
            label = label[:-1]
        color = ACCENT if i == current else GREY
        paste(canvas, text_img(label, 'text', size, color), x0 + 8 + font('text', size).getlength(label) / 2, H - 36)


def draw_credit(canvas, n, credit, start):
    a = ramp(n, start, 10 ** 9, fade=20)
    if a <= 0:
        return
    size = fit_size(credit['title'], text_kind(credit['title']), 52, W - 160, weight=900)
    paste(canvas, text_img(credit['kicker'], 'display', 28, ACCENT), W / 2, 250, a)
    paste(canvas, text_img(credit['title'], text_kind(credit['title']), size, WHITE, 900), W / 2, 300, a)
    paste(canvas, text_img(credit['byline'], text_kind(credit['byline']), 30, GREY), W / 2, 380, a)
    paste(canvas, text_img(credit['note'], text_kind(credit['note']), 24, GREY), W / 2, 430, a)


def sentence_by_id(tl):
    return {s['id']: s for s in tl['sentences']}


def render(cfg, ver):
    tl_file = timeline_path()
    if not os.path.exists(tl_file):
        raise SystemExit('script/timeline.json not found: run `python py/explain.py tts` first')
    with open(tl_file, encoding='utf-8') as f:
        tl = json.load(f)
    audio = audio_path(cfg)
    if not os.path.exists(audio):
        raise SystemExit(f'{audio} not found: run `python py/explain.py tts` first')

    total = tl['total_frames']
    chapters = tl['chapters']
    sents = sentence_by_id(tl)
    subs = [sb for s in tl['sentences'] for sb in s['subs']]
    starts = [sb['from'] for sb in subs]
    tech = cfg.get('chapter_tech', [])
    cards = []
    cards_file = os.path.join(ROOT, 'script', 'cards.json')
    if os.path.exists(cards_file):
        with open(cards_file, encoding='utf-8') as f:
            for c in json.load(f):
                s = sents.get(c['sentence'])
                if s is None:
                    raise SystemExit(f"cards.json: unknown sentence {c['sentence']}")
                cards.append((s['from'], s['to'], c))
    first_chapter = chapters[0]['from'] if chapters else total

    # Chapter card windows: from the end of the previous sentence to just after the chapter starts (the silent gap plus a few frames).
    chapter_windows = []
    for i, ch in enumerate(chapters):
        prev_end = max((s['to'] for s in tl['sentences'] if s['from'] < ch['from']), default=0)
        chapter_windows.append((prev_end + 4, ch['from'] + 4))

    stars = make_stars()
    fog = make_fog()
    out = video_path(cfg, ver)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = [ffmpeg_exe(), '-y', '-v', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-i', audio, '-map', '0:v', '-map', '1:a',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', str(os.environ.get('CRF', 16)), '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    thumbs = []
    credit = cfg.get('credit')
    last_sub_end = subs[-1]['to'] if subs else total
    credit_start = last_sub_end + 45
    try:
        for n in range(1, total + 1):
            canvas = backdrop(n, cfg.get('bg', 'stars'), stars, fog)
            if n < first_chapter:
                draw_title(canvas, n, cfg, first_chapter)
            for i, ch in enumerate(chapters):
                if i == 0:
                    continue
                draw_chapter(canvas, n, ch, tech[i] if i < len(tech) else '', chapter_windows[i])
            for a, b, c in cards:
                draw_card(canvas, n, c, (a, b))
            draw_subtitle(canvas, n, subs, starts)
            draw_progress(canvas, n, total, chapters)
            if credit:
                draw_credit(canvas, n, credit, credit_start)
            elif n > total - 30:
                # Without a credit card, fade the whole picture to black over the last second (endingFade).
                canvas = Image.blend(canvas.convert('RGB'), Image.new('RGB', (W, H)), 1 - (total - n) / 30).convert('RGBA')
            if (n - 1) % SHEET_STEP == 0:
                thumbs.append((n, canvas.convert('RGB').resize((256, 144))))
            proc.stdin.write(canvas.convert('RGB').tobytes())
            if n % (FPS * 10) == 0:
                print(f'  frame {n}/{total} ({n / total:.0%})', flush=True)
    finally:
        proc.stdin.close()
    if proc.wait() != 0 or not os.path.exists(out) or os.path.getsize(out) == 0:
        raise SystemExit(f'ffmpeg failed while writing {out}')
    write_sheet(thumbs, sents, ver)
    print(f'rendered {out} ({total} frames, {total / FPS:.1f}s)')
    return out


def write_sheet(thumbs, sents, ver):
    """renders/sheet_<ver>.png: a contact sheet of one thumbnail every SHEET_STEP frames, labelled with time and the sentence on screen."""
    cols = 6
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new('RGB', (cols * 262, rows * 186 + 40), (17, 17, 17))
    d = ImageDraw.Draw(sheet)
    for i, (n, img) in enumerate(thumbs):
        x, y = (i % cols) * 262 + 3, (i // cols) * 186 + 3
        sheet.paste(img, (x, y))
        d.text((x, y + 146), f'f{n} ({(n - 1) / FPS:.1f}s)', font=font('text', 14), fill=(200, 200, 200))
    path = os.path.join(ROOT, 'renders', f'sheet_{ver}.png')
    sheet.save(path)
    print(f'contact sheet: {path}')

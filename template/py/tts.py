"""Stage 1 (tts): narration → voiceover audio and script/timeline.json.

Same narration format and timeline schema as scripts/tts_build.py, so sheet.py and selfcheck.py keep working. This stage writes
only the Python outputs; it does not write the Remotion files src/common/subs.ts and timeline.ts.

Engines (--engine or TTS_ENGINE):
  edge   edge-tts, Microsoft's cloud voices. Sends the narration text to that service. Word boundaries give exact subtitle timing.
  dummy  Silence with an estimated length per sentence and no network. For dry-running layout and timing only, not a final video.

Environment overrides: VOICE, RATE, EDGE_TRIES, GAP, CHAPTER_GAP, LEAD, TAIL (frames, as in tts_build.py).
"""
import asyncio, hashlib, json, os, re, subprocess
import numpy as np
from common import ROOT, FPS, SR, detect_lang, ffmpeg_exe, parse_narration, timeline_path, audio_path, write_wav

VOICE = os.environ.get('VOICE', 'zh-CN-YunxiNeural')
RATE = os.environ.get('RATE', '+8%')
EDGE_TRIES = int(os.environ.get('EDGE_TRIES', 4))
GAP = int(os.environ.get('GAP', 10))                  # blank frames between sentences
CHAPTER_GAP = int(os.environ.get('CHAPTER_GAP', 45))  # blank frames before a chapter
LEAD = int(os.environ.get('LEAD', 40))                # silent frames at the start
TAIL = int(os.environ.get('TAIL', 90))                # silent frames at the end
CACHE = os.path.join(ROOT, 'audio', 'cache')
PUNCT = r'[\s，。、！？：；“”（）,.!?:;()\-—…]'


def cache_file(engine, text, ext):
    """Cache key covers engine, voice, rate and text, so editing one sentence only re-synthesizes that sentence."""
    sig = f'{engine}|{VOICE}|{RATE}|{text}'
    os.makedirs(CACHE, exist_ok=True)
    return os.path.join(CACHE, hashlib.sha1(sig.encode('utf-8')).hexdigest()[:16] + ext)


def decode(path, ffmpeg):
    """Any audio file → mono float32 at SR."""
    out = subprocess.run([ffmpeg, '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def trim_edges(x, thr=0.004):
    """Cut silence from both ends. Returns the trimmed audio and the seconds that were cut from the front."""
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x, 0.0
    a = max(0, idx[0] - int(0.03 * SR))
    b = min(len(x), idx[-1] + int(0.12 * SR))
    return x[a:b], a / SR


async def edge_fetch(text):
    """Fetch one sentence from edge-tts with word boundaries. The endpoint sometimes returns empty audio, so retry up to EDGE_TRIES times."""
    try:
        import edge_tts
    except ImportError:
        raise SystemExit('edge-tts is not installed: pip install -r py/requirements.txt')
    why = ''
    for attempt in range(1, EDGE_TRIES + 1):
        audio, words = bytearray(), []
        try:
            comm = edge_tts.Communicate(text, VOICE, rate=RATE, boundary='WordBoundary')
            async for ch in comm.stream():
                if ch['type'] == 'audio':
                    audio += ch['data']
                elif ch['type'] == 'WordBoundary':
                    words.append({'t': ch['offset'] / 1e7, 'd': ch['duration'] / 1e7, 'text': ch['text']})
            if audio:
                return bytes(audio), words
            why = 'endpoint returned empty audio'
        except TypeError:
            raise SystemExit('edge-tts is too old for word boundaries: pip install -r py/requirements.txt')
        except Exception as e:
            why = f'{type(e).__name__}: {e}'
        if attempt < EDGE_TRIES:
            print(f'  ⚠ edge-tts attempt {attempt} failed ({why}), retrying: {text[:16]}…')
            await asyncio.sleep(1.5 * attempt)
    raise SystemExit(f'edge-tts returned no audio after {EDGE_TRIES} tries ({why}): {text[:30]}…')


def chunk_starts(text, chunks, words, lead_cut, dur, sep):
    """Start second of each subtitle chunk within one sentence.
    With word boundaries, each chunk starts at its first word. Without them (dummy engine), chunks are placed in proportion to their length."""
    if not words:
        total = max(1, len(text))
        starts, pos = [], 0
        for c in chunks:
            starts.append(dur * pos / total)
            pos += len(c) + len(sep)
        return starts
    char_t = [None] * len(text)
    cur = 0
    for w in words:
        wt = re.sub(PUNCT, '', w['text'])
        if not wt:
            continue
        p = text.find(wt, cur)
        if p < 0:
            p = text.find(wt[0], cur)
            if p < 0:
                continue
        for i in range(p, min(len(text), p + len(wt))):
            char_t[i] = w['t'] - lead_cut
        cur = p + len(wt)
    starts, pos = [], 0
    for c in chunks:
        st = next((char_t[i] for i in range(pos, pos + len(c)) if char_t[i] is not None), None)
        starts.append(st)
        pos += len(c) + len(sep)
    for i, st in enumerate(starts):
        if st is None:
            starts[i] = starts[i - 1] if i else 0.0
    starts[0] = 0.0
    return [min(max(0.0, s), dur) for s in starts]


async def synth_sentence(chunks, sep, engine, lang, ffmpeg):
    """One sentence → (mono float32 audio at SR, subtitle chunk start seconds, duration in seconds)."""
    text = sep.join(chunks)
    if engine == 'dummy':
        dur = max(0.6, len(text) * 0.16) if lang == 'zh' else max(0.6, len(text.split()) * 0.4)
        x = np.zeros(int(dur * SR), dtype=np.float32)
        return x, chunk_starts(text, chunks, None, 0.0, dur, sep), dur
    mp3, js = cache_file('edge', text, '.mp3'), cache_file('edge', text, '.json')
    if not (os.path.exists(mp3) and os.path.exists(js)):
        audio, words = await edge_fetch(text)
        with open(mp3, 'wb') as f:
            f.write(audio)
        with open(js, 'w', encoding='utf-8') as f:
            json.dump(words, f, ensure_ascii=False)
    with open(js, encoding='utf-8') as f:
        words = json.load(f)
    x, lead_cut = trim_edges(decode(mp3, ffmpeg))
    dur = len(x) / SR
    return x, chunk_starts(text, chunks, words, lead_cut, dur, sep), dur


async def build(items, engine, cfg):
    """Build the timeline and audio. Mirrors tts_build.py's main(): the same frame arithmetic, so frame numbers match the Remotion template."""
    ffmpeg = ffmpeg_exe()
    lang = detect_lang(items)
    if lang != cfg['lang']:
        print(f"⚠ lang: '{cfg['lang']}' in py/video.json does not match the narration language '{lang}'. Fix it; titles and line lengths depend on it.")
    sep = ' ' if lang == 'en' else ''
    t = LEAD / FPS
    audio_parts, sentences, chapters = [], [], []
    sid = 0
    total_chars = total_words = 0
    speech_sec = 0.0
    for it in items:
        if it['type'] == 'chapter':
            t += CHAPTER_GAP / FPS
            chapters.append({'n': it['chapter'], 'title': it['title'], 'from': int(round(t * FPS)) + 1})
            continue
        t += it['gap_before'] / FPS
        chunks = [c.strip() for c in it['raw'].split('|') if c.strip()]
        if not chunks:
            continue
        tts_text = sep.join(chunks)
        x, starts, dur = await synth_sentence(chunks, sep, engine, lang, ffmpeg)
        sid += 1
        ends = starts[1:] + [dur]
        f0 = int(round(t * FPS)) + 1
        f1 = int(round((t + dur) * FPS))
        sentences.append({
            'id': f'S{sid:02d}', 'chapter': it['chapter'], 'from': f0, 'to': f1, 'text': tts_text,
            'subs': [{'from': int(round((t + a) * FPS)) + 1, 'to': int(round((t + b) * FPS)), 'text': c}
                     for c, a, b in zip(chunks, starts, ends)],
        })
        audio_parts.append((t, x))
        total_chars += len(re.sub(PUNCT, '', tts_text))
        total_words += len(tts_text.split())
        speech_sec += dur
        t += dur + GAP / FPS
    t += TAIL / FPS
    total = int(np.ceil(t * FPS))

    # Mix the voiceover track and normalize the peak to 0.89.
    y = np.zeros(int(total / FPS * SR) + SR, dtype=np.float32)
    for st, x in audio_parts:
        a = int(st * SR)
        y[a:a + len(x)] += x
    y = y[: int(total / FPS * SR)]
    y = y / (float(np.max(np.abs(y))) or 1.0) * 0.89
    os.makedirs(os.path.dirname(audio_path(cfg)), exist_ok=True)
    write_wav(audio_path(cfg), np.stack([y, y], 1))

    # Subtitle chunks must not overlap their neighbours (fixed in place, so the JSON and the video agree).
    all_subs = [sb for s in sentences for sb in s['subs']]
    for sb in all_subs:
        sb['to'] = max(sb['to'], sb['from'])
    for a, b in zip(all_subs, all_subs[1:]):
        if a['to'] >= b['from']:
            a['to'] = b['from'] - 1

    unit, cnt = ('chars', total_chars) if lang == 'zh' else ('words', total_words)
    tl = {'fps': FPS, 'total_frames': total, 'engine': engine,
          'voice': VOICE if engine == 'edge' else 'dummy',
          'rate': RATE if engine == 'edge' else 'n/a',
          'gap': GAP, 'chapter_gap': CHAPTER_GAP, 'lead': LEAD, 'tail': TAIL,
          'lang': lang, 'chapters': chapters, 'sentences': sentences,
          'chars': total_chars, 'words': total_words, 'speech_sec': round(speech_sec, 2)}
    os.makedirs(os.path.dirname(timeline_path()), exist_ok=True)
    with open(timeline_path(), 'w', encoding='utf-8') as f:
        json.dump(tl, f, ensure_ascii=False, indent=1)
    write_timeline_md(tl, unit, cnt)
    print(f'lang={lang} engine={engine} voice={tl["voice"]} total_frames={total} ({total / FPS:.1f}s) '
          f'sentences={len(sentences)} {unit}={cnt} speech={speech_sec:.1f}s')
    return tl


def write_timeline_md(tl, unit, cnt):
    """script/timeline.md: the human-readable table, the same layout as tts_build.py."""
    path = os.path.join(ROOT, 'script', 'timeline.md')
    total, speech_sec = tl['total_frames'], tl['speech_sec']
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# Timeline ({tl['engine']} · {tl['voice']} {tl['rate']}, {total} frames = {total / FPS:.1f}s, "
                f"{cnt} {unit}, speaking rate {cnt / max(1e-6, speech_sec):.2f} {unit}/s)\n\n")
        f.write('| Sentence | Chapter | Frames from–to | Length | Text (｜ marks subtitle splits) |\n|---|---|---|---|---|\n')
        for s in tl['sentences']:
            f.write(f"| {s['id']} | {s['chapter']} | {s['from']}–{s['to']} | {(s['to'] - s['from'] + 1) / FPS:.1f}s "
                    f"| {'｜'.join(sb['text'] for sb in s['subs'])} |\n")
        f.write('\n## Chapter start frames\n')
        for c in tl['chapters']:
            f.write(f"- Chapter {c['n']} {c['title']}: f{c['from']}\n")


def run(cfg, engine):
    narration = os.path.join(ROOT, 'script', 'narration.txt')
    if not os.path.exists(narration):
        raise SystemExit(f'missing {narration}')
    items = parse_narration(narration)
    return asyncio.run(build(items, engine, cfg))

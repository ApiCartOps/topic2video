#!/usr/bin/env python3
"""Voiceover and timeline generation. Project root = the parent of this script's scripts/ directory.
Input narration.txt:
  # CHAPTER <n> <title>      chapter marker (adds chapter_gap blank frames before the chapter)
  ## gap <frames>            inserts extra blank frames before the next sentence
  A sentence|split by vertical bars into subtitle chunks   → the bars only split subtitles, not the speech
                                       Budget per chunk: Chinese ≤16 characters / English ≤48 characters (over budget prints ⚠ and shrinks the font)
                                       Leading and trailing spaces in each chunk are removed. English joins the chunks back with spaces for TTS ("a|b" and "a | b" are equivalent). Chinese joins them directly.
Outputs:
  public/assets/<slug>/audio.wav (48 kHz stereo 16-bit; slug is read from src/config.ts)
  script/timeline.json / timeline.md
  src/common/subs.ts (subtitle table), src/common/timeline.ts (TOTAL_FRAMES / CHAPTER_STARTS / SENTENCES)
Each sentence (or each subtitle chunk) is cached in audio/cache/, so editing one sentence only re-synthesizes that sentence.

TTS engine (`TTS_ENGINE`; default `auto` picks based on the narration language. **Before running, ask the user whether they have a preferred TTS.** See SKILL.md confirmation point 3):
  edge     Chinese default. Cloud synthesis with edge-tts, with word-level boundaries, so subtitle beats are the most accurate. VOICE=zh-CN-YunxiNeural RATE=+8%
           Word boundaries must be requested explicitly (boundary='WordBoundary'; the default from edge-tts 7.2.0 onward does not give them). Otherwise subtitle starts silently fall back to interpolation.
  kokoro   English default. Local inference with kokoro-82m (`pip install kokoro soundfile` plus `brew install espeak-ng`).
           KOKORO_VOICE=am_liam (Liam, a male voice, positioned like the Chinese Yunxi) KOKORO_LANG=a KOKORO_SPEED=1.0
  kokoro has no word boundaries, so each subtitle chunk is synthesized separately and then concatenated. Chunk start frames are still exact (CHUNK_PAD sets the silence between chunks).
  If the user prefers a different TTS, do not use this script. Have them supply a finished voiceover wav, and fill in timeline.ts and subs.ts by hand from the sentence and chunk timings.
Other environment variables: GAP / CHAPTER_GAP / LEAD / TAIL (frames), and EDGE_TRIES (how many times edge retries each sentence, because the endpoint sometimes returns empty audio).
"""
import asyncio, hashlib, json, os, re, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REM = ROOT
_cfg = open(f'{ROOT}/src/config.ts', encoding='utf-8').read()
SLUG = re.search(r"slug:\s*'([^']+)'", _cfg).group(1)
_m = re.search(r"lang:\s*'(zh|en)'", _cfg)
CFG_LANG = _m.group(1) if _m else 'zh'
FPS = 30
SR = 48000
ENGINE = os.environ.get('TTS_ENGINE', 'auto')
VOICE = os.environ.get('VOICE', 'zh-CN-YunxiNeural')
RATE = os.environ.get('RATE', '+8%')
KOKORO_VOICE = os.environ.get('KOKORO_VOICE', 'am_liam')
KOKORO_LANG = os.environ.get('KOKORO_LANG', 'a')       # a=American English, b=British
KOKORO_SPEED = float(os.environ.get('KOKORO_SPEED', 1.0))
KOKORO_SR = 24000
CHUNK_PAD = float(os.environ.get('CHUNK_PAD', 0.06))  # engines without word boundaries: silence between chunks, in seconds
EDGE_TRIES = int(os.environ.get('EDGE_TRIES', 4))     # max edge-tts attempts per sentence (the endpoint sometimes returns empty audio)
GAP = int(os.environ.get('GAP', 10))          # blank frames between sentences
CHAPTER_GAP = int(os.environ.get('CHAPTER_GAP', 45))  # blank frames before a chapter
LEAD = int(os.environ.get('LEAD', 40))        # silent frames at the start of the video
TAIL = int(os.environ.get('TAIL', 90))        # silent frames at the end of the video
CACHE = f'{ROOT}/audio/cache'
os.makedirs(CACHE, exist_ok=True)
if ENGINE not in ('auto', 'edge', 'kokoro'):
    raise SystemExit(f'Unknown TTS_ENGINE={ENGINE} (choose auto / edge / kokoro)')


def parse(path):
    items = []
    chap = 0
    chap_title = ''
    pending_gap = 0
    for raw in open(path, encoding='utf-8'):
        line = raw.strip()
        if not line:
            continue
        m = re.match(r'^#\s*CHAPTER\s+(\d+)\s+(.*)$', line)
        if m:
            chap = int(m.group(1)); chap_title = m.group(2).strip()
            items.append({'type': 'chapter', 'chapter': chap, 'title': chap_title})
            continue
        m = re.match(r'^##\s*gap\s+(\d+)', line)
        if m:
            pending_gap += int(m.group(1)); continue
        if line.startswith('#'):
            continue
        items.append({'type': 'sent', 'chapter': chap, 'raw': line, 'gap_before': pending_gap})
        pending_gap = 0
    return items


def cache_path(text, ext):
    sig = f'{ENGINE}|{VOICE}|{RATE}|{KOKORO_VOICE}|{KOKORO_LANG}|{KOKORO_SPEED}|{text}'
    return f'{CACHE}/{hashlib.sha1(sig.encode()).hexdigest()[:16]}{ext}'


def detect_lang(items):
    """If CJK characters make up at least 20% of the narration, return 'zh'. Otherwise return 'en'."""
    txt = ''.join(it['raw'] for it in items if it['type'] == 'sent')
    cjk = sum(1 for c in txt if '一' <= c <= '鿿')
    return 'zh' if cjk >= 0.2 * max(1, len(txt)) else 'en'


# Subtitle width precheck: uses the same em-width table as src/common/textfit.ts (measured with fontTools).
# It computes directly whether a chunk at 44px would exceed the 1160px safe area. That is more accurate than counting characters,
# because mixed Chinese and English (such as 「几百个 token 一块」) would otherwise trigger false alarms.
# The writing guideline is still ≤16 Chinese characters or ≤48 English characters per chunk (see narration-storyboard.md).
SUB_MAX_W = 1160
SUB_SIZE = 44
SUB_BUDGET = {'zh': '16 characters', 'en': '48 characters'}


def text_em(s):
    """Same table as textEm() in src/common/textfit.ts. Change one and sync the other."""
    t = 0.0
    for ch in s:
        c = ord(ch)
        if c >= 0x2000:
            t += 1.0                     # CJK / fullwidth, and punctuation, arrows and math symbols from U+2000 on (— … “ ” → ∑ are all 1em in Noto)
        elif ch == ' ':
            t += 0.227
        elif 'A' <= ch <= 'Z':
            t += 0.668
        elif '0' <= ch <= '9':
            t += 0.59
        elif 'a' <= ch <= 'z':
            t += 0.566
        elif 0xc0 <= c < 0x250:
            t += 0.58                    # accented Latin letters
        else:
            t += 0.325                   # half-width punctuation
    return t


def write_wav(path, x, sr):
    """x: float32 mono (n,) or stereo (n,2) → 16-bit PCM wav."""
    import wave
    a = np.asarray(x, dtype=np.float32)
    pcm = (np.clip(a, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1 if a.ndim == 1 else a.shape[1]); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(pcm.tobytes())


async def synth_edge(text):
    """edge-tts: synthesizes the whole sentence and returns word-level boundaries (this sends text to Microsoft's cloud endpoint).
    boundary='WordBoundary' must be passed explicitly. From edge-tts 7.2.0 the default is 'SentenceBoundary', so without it no WordBoundary
    events arrive, and chunk_starts() silently falls back to interpolating by character count (subtitles can drift by half a second).
    The endpoint sometimes returns empty audio (NoAudioReceived). In a 50-sentence video, one or two sentences hit this at random, and a retry usually succeeds,
    so we try up to EDGE_TRIES times. If it still fails, exit with an error rather than passing an empty mp3 downstream."""
    import edge_tts
    mp3 = cache_path(text, '.mp3'); js = cache_path(text, '.json')
    if os.path.exists(mp3) and os.path.exists(js):
        return mp3, json.load(open(js))
    for attempt in range(1, EDGE_TRIES + 1):
        audio = bytearray(); words = []
        try:
            comm = edge_tts.Communicate(text, VOICE, rate=RATE, boundary='WordBoundary')
            async for ch in comm.stream():
                if ch['type'] == 'audio':
                    audio += ch['data']
                elif ch['type'] == 'WordBoundary':
                    words.append({'t': ch['offset'] / 1e7, 'd': ch['duration'] / 1e7, 'text': ch['text']})
            if audio:
                break
            why = 'endpoint returned empty audio'
        except TypeError:                # the boundary parameter only exists from edge-tts 7.2.0 on
            raise SystemExit("edge-tts is too old: pip install 'edge-tts==7.2.8'")
        except Exception as e:
            why = f'{type(e).__name__}: {e}'
        if attempt == EDGE_TRIES:
            raise SystemExit(f'edge-tts still returned no audio after {EDGE_TRIES} tries ({why}): {text[:30]}…')
        print(f'  ⚠ edge-tts attempt {attempt} failed ({why}), retrying in {1.5 * attempt:.1f}s: {text[:16]}…')
        await asyncio.sleep(1.5 * attempt)
    open(mp3, 'wb').write(audio)
    json.dump(words, open(js, 'w'), ensure_ascii=False)
    return mp3, words


_kokoro = None

# Pronunciation overrides for kokoro (these only change the text sent to TTS. Subtitles still show the original words). The syntax is kokoro/misaki's [word](/phonemes/).
# Measured: kokoro reads CUDA, NIXL, MIG and DeepGEMM letter by letter, and reads v5.0 as "v five zero", so they are overridden here. Add or remove entries per video.
PRONOUNCE = {
    'CUDA': '[CUDA](/kˈudə/)',
    'NIXL': '[NIXL](/nˈɪksəl/)',
    'MIG': '[MIG](/mˈɪɡ/)',
    'DeepGEMM': '[DeepGEMM](/dˌipʤˈɛm/)',
    'v5.0': '[v5.0](/vˈi fˈIv pYnt ˈO/)',
}


def apply_pronounce(text):
    for k, v in PRONOUNCE.items():
        text = re.sub(r'(?<![A-Za-z0-9])' + re.escape(k) + r'(?![A-Za-z0-9])', v, text)
    return text


def synth_kokoro(text):
    """kokoro-82m: local inference, 24 kHz, no word boundaries."""
    global _kokoro
    text = apply_pronounce(text)
    au = cache_path(text, '.wav')
    if os.path.exists(au):
        return au
    if _kokoro is None:
        try:
            from kokoro import KPipeline
        except ImportError:
            raise SystemExit('TTS_ENGINE=kokoro needs kokoro: pip install kokoro soundfile. English G2P also needs espeak-ng (brew install espeak-ng)')
        _kokoro = KPipeline(lang_code=KOKORO_LANG)
    parts = []
    for r in _kokoro(text, voice=KOKORO_VOICE, speed=KOKORO_SPEED):
        a = getattr(r, 'audio', None)
        if a is None:
            a = r[2]                                    # older versions yield (graphemes, phonemes, audio)
        if hasattr(a, 'detach'):
            a = a.detach().cpu().numpy()                # torch tensor
        parts.append(np.asarray(a, dtype=np.float32).reshape(-1))
    if not parts:
        raise SystemExit(f'kokoro produced no audio: {text[:24]}…')
    write_wav(au, np.concatenate(parts), KOKORO_SR)
    return au


def decode(mp3):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', mp3, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def trim_edges(x, thr=0.004):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x, 0.0
    a = max(0, idx[0] - int(0.03 * SR)); b = min(len(x), idx[-1] + int(0.12 * SR))
    return x[a:b], a / SR


def chunk_starts(tts_text, chunks, words, lead_cut, dur, sep=''):
    """Subtitle chunks split by | → start second of each chunk within the sentence. Word boundaries are matched back to the original sentence with a character cursor.
    tts_text == sep.join(chunks). For English, sep=' ', and the cursor must skip the space between chunks."""
    # start time of each character (filled from word boundaries)
    char_t = [None] * len(tts_text)
    cur = 0
    for w in words:
        wt = re.sub(r'[\s，。、！？：；“”（）,.!?:;()\-—…]', '', w['text'])
        if not wt:
            continue
        p = tts_text.find(wt, cur)
        if p < 0:
            p = tts_text.find(wt[0], cur)
            if p < 0:
                continue
        for i in range(p, min(len(tts_text), p + len(wt))):
            char_t[i] = (w['t'] - lead_cut, w['d'])
        cur = p + len(wt)
    # start time of each chunk's first character
    starts = []
    pos = 0
    for c in chunks:
        seg = tts_text[pos:pos + len(c)]
        st = None
        for i in range(pos, pos + len(c)):
            if char_t[i] is not None:
                st = char_t[i][0]; break
        starts.append(st)
        pos += len(c) + len(sep)
    # fallback: chunks without boundaries are interpolated by character count
    for i, st in enumerate(starts):
        if st is None:
            prev = starts[i - 1] if i > 0 and starts[i - 1] is not None else 0.0
            starts[i] = prev + dur * len(chunks[i - 1]) / max(1, len(tts_text)) if i > 0 else 0.0
    starts[0] = 0.0
    return [max(0.0, s) for s in starts]


async def synth_sentence(chunks, sep=''):
    """One sentence → (mono float32 audio, start second of each subtitle chunk within the sentence, sentence length in seconds). sep is the joiner between chunks (' ' for English, '' for Chinese).
    edge: synthesizes the whole sentence once, and chunk starts are aligned to word boundaries (most accurate).
    kokoro: no word boundaries, so each subtitle chunk is synthesized separately and then concatenated. Chunk starts are therefore exact, at the cost of slightly abrupt breaks between chunks."""
    text = sep.join(chunks)
    if ENGINE == 'edge':
        au, words = await synth_edge(text)
        x, lead_cut = trim_edges(decode(au))
        dur = len(x) / SR
        return x, chunk_starts(text, chunks, words, lead_cut, dur, sep), dur
    pad = np.zeros(int(CHUNK_PAD * SR), dtype=np.float32)
    parts = []; starts = []; pos = 0.0
    for i, c in enumerate(chunks):
        xi, _ = trim_edges(decode(synth_kokoro(c)))
        if i:
            parts.append(pad); pos += len(pad) / SR
        starts.append(pos)
        parts.append(xi); pos += len(xi) / SR
    x = np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)
    return x, starts, len(x) / SR


async def main(narr):
    global ENGINE
    items = parse(narr)
    lang = detect_lang(items)
    if ENGINE == 'auto':
        ENGINE = 'edge' if lang == 'zh' else 'kokoro'
        print(f'Narration language {lang} → TTS_ENGINE={ENGINE} (to override, set TTS_ENGINE=… explicitly)')
    if lang != CFG_LANG:
        print(f"⚠ lang: '{CFG_LANG}' in src/config.ts does not match the narration language {lang}. Fix it, "
              f"or title narrowing and centered baselines will be calculated for the wrong language")
    # Joiner used when the subtitle chunks are rejoined into a whole sentence for TTS. English words need spaces between them (otherwise "powerful|but" is read as "powerfulbut"). Chinese joins directly.
    sep = ' ' if lang == 'en' else ''
    t = LEAD / FPS
    audio_parts = []  # (start_sec, np.array)
    sentences = []; chapters = []
    sid = 0
    total_chars = 0; total_words = 0; speech_sec = 0.0
    for it in items:
        if it['type'] == 'chapter':
            t += CHAPTER_GAP / FPS
            chapters.append({'n': it['chapter'], 'title': it['title'], 'from': int(round(t * FPS)) + 1})
            continue
        t += it['gap_before'] / FPS
        raw = it['raw']
        chunks = [c.strip() for c in raw.split('|') if c.strip()]
        if not chunks:
            continue
        tts_text = sep.join(chunks)
        x, starts, dur = await synth_sentence(chunks, sep)
        sid += 1
        subs = [(t + starts[i], t + (starts[i + 1] if i + 1 < len(starts) else dur)) for i in range(len(chunks))]
        f0 = int(round(t * FPS)) + 1; f1 = int(round((t + dur) * FPS))
        sentences.append({'id': f'S{sid:02d}', 'chapter': it['chapter'], 'from': f0, 'to': f1, 'text': tts_text,
                          'subs': [{'from': int(round(a * FPS)) + 1, 'to': int(round(b * FPS)), 'text': c} for c, (a, b) in zip(chunks, subs)]})
        audio_parts.append((t, x))
        total_chars += len(re.sub(r'[，。、！？：；“”（）,.!?:;()\-—…\s]', '', tts_text))
        total_words += len(tts_text.split()); speech_sec += dur
        t += dur + GAP / FPS
    t += TAIL / FPS
    total = int(np.ceil(t * FPS))
    # mix the audio track
    y = np.zeros(int(total / FPS * SR) + SR, dtype=np.float32)
    for st, x in audio_parts:
        a = int(st * SR); y[a:a + len(x)] += x
    y = y[: int(total / FPS * SR)]
    peak = float(np.max(np.abs(y))) or 1.0
    y = y / peak * 0.89
    os.makedirs(f'{REM}/public/assets/{SLUG}', exist_ok=True)
    wav = f'{REM}/public/assets/{SLUG}/audio.wav'
    write_wav(wav, np.stack([y, y], 1), SR)
    # fix subtitles: subtitles of adjacent sentences must not overlap, and chunks within a sentence stay continuous
    all_subs = []
    for s in sentences:
        for k, sb in enumerate(s['subs']):
            if sb['to'] < sb['from']:
                sb['to'] = sb['from']
            all_subs.append(dict(sb))
    for i in range(len(all_subs) - 1):
        if all_subs[i]['to'] >= all_subs[i + 1]['from']:
            all_subs[i]['to'] = all_subs[i + 1]['from'] - 1
    # subtitle width check: chunks wider than the safe area get shrunk by Subtitle.tsx (over 1.3× they also wrap onto two lines and push into the content area). The correct fix is to split the script.
    over = [(sb, text_em(sb['text']) * SUB_SIZE) for sb in all_subs]
    over = [(sb, w) for sb, w in over if w > SUB_MAX_W]
    if over:
        print(f'⚠ {len(over)}/{len(all_subs)} subtitle chunks exceed the {SUB_MAX_W}px safe area at {SUB_SIZE}px'
              f' (they will shrink automatically; better to keep each chunk to {SUB_BUDGET[lang]} and add another | to split):')
        for sb, w in over[:5]:
            print(f"    f{sb['from']} (≈{w:.0f}px{', will wrap onto two lines' if w > SUB_MAX_W * 1.3 else ''}) {sb['text']}")
    # output
    tl = {'fps': FPS, 'total_frames': total, 'engine': ENGINE,
          'voice': VOICE if ENGINE == 'edge' else KOKORO_VOICE,
          'rate': RATE if ENGINE == 'edge' else KOKORO_SPEED,
          'gap': GAP, 'chapter_gap': CHAPTER_GAP, 'lead': LEAD, 'tail': TAIL,
          'lang': lang, 'chapters': chapters, 'sentences': sentences, 'chars': total_chars, 'words': total_words,
          'speech_sec': round(speech_sec, 2)}
    unit, cnt = ('chars', total_chars) if lang == 'zh' else ('words', total_words)
    os.makedirs(f'{ROOT}/script', exist_ok=True)
    json.dump(tl, open(f'{ROOT}/script/timeline.json', 'w'), ensure_ascii=False, indent=1)
    with open(f'{ROOT}/script/timeline.md', 'w') as f:
        f.write(f"# Timeline ({ENGINE} · {tl['voice']} {tl['rate']}, {total} frames = {total/FPS:.1f}s, {cnt} {unit}, speaking rate {cnt/max(1e-6,speech_sec):.2f} {unit}/s)\n\n")
        f.write('| Sentence | Chapter | Frames from–to | Length | Text (| marks subtitle splits) |\n|---|---|---|---|---|\n')
        ci = {c['from']: c for c in chapters}
        for s in sentences:
            for c in chapters:
                if s['from'] >= c['from'] and (not any(s['from'] >= c2['from'] > c['from'] for c2 in chapters)):
                    pass
            f.write(f"| {s['id']} | {s['chapter']} | {s['from']}–{s['to']} | {(s['to']-s['from']+1)/FPS:.1f}s | {'｜'.join(sb['text'] for sb in s['subs'])} |\n")
        f.write('\n## Chapter start frames\n')
        for c in chapters:
            f.write(f"- Chapter {c['n']} {c['title']}: f{c['from']}\n")
    # all text goes through json.dumps: a JSON string is a valid TS literal, and it escapes " \ and control characters.
    # (Hand-built quotes break on \ ' ` ${} in the narration, and can even turn the text into code.)
    def lit(s):
        return json.dumps(s, ensure_ascii=False)
    with open(f'{REM}/src/common/subs.ts', 'w') as f:
        f.write('// Auto-generated by scripts/tts_build.py (word boundaries / per-chunk synthesis → subtitle chunks). To change it, edit script/narration.txt and rerun.\n')
        f.write("export type SubEntry = {from: number; to: number; text: string};\nexport const SUBS: SubEntry[] = [\n")
        for sb in all_subs:
            f.write(f"  {{from: {sb['from']}, to: {sb['to']}, text: {lit(sb['text'])}}},\n")
        f.write('];\n')
    with open(f'{REM}/src/common/timeline.ts', 'w') as f:
        f.write('// Auto-generated by scripts/tts_build.py. Frame numbers start at 1 and are inclusive.\n')
        f.write(f'export const TOTAL_FRAMES = {total};\n')
        f.write('export const CHAPTER_STARTS: Array<{n: number; title: string; from: number}> = [\n')
        for c in chapters:
            f.write(f"  {{n: {c['n']}, title: {lit(c['title'])}, from: {c['from']}}},\n")
        f.write('];\n')
        f.write('export type Sentence = {id: string; chapter: number; from: number; to: number; text: string};\n')
        f.write('export const SENTENCES: Sentence[] = [\n')
        for s in sentences:
            f.write(f"  {{id: {lit(s['id'])}, chapter: {s['chapter']}, from: {s['from']}, to: {s['to']}, text: {lit(s['text'])}}},\n")
        f.write('];\n')
    print(f'lang={lang} engine={ENGINE} voice={tl["voice"]} total_frames={total} ({total/FPS:.1f}s) '
          f'sentences={len(sentences)} {"chars" if lang == "zh" else "words"}={cnt} speech={speech_sec:.1f}s '
          f'rate={cnt/max(1e-6,speech_sec):.2f} {unit}/s')
    for c in chapters:
        print(f"  chapter {c['n']} {c['title']} from f{c['from']}")

if __name__ == '__main__':
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else f'{ROOT}/script/narration.txt'))

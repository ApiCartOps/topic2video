"""Shared settings for the Python build: paths, video config, narration parsing and audio helpers.

Project layout assumed here (same as the Remotion template): script/narration.txt is the input, public/fonts holds the
typefaces, and outputs go to script/timeline.json, public/assets/<slug>/audio.wav and renders/.
"""
import json, os, re, shutil, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # project root (the folder holding script/ and public/)
FPS = 30
SR = 48000
W, H = 1280, 720
FONTS = os.path.join(ROOT, 'public', 'fonts')


def load_config():
    """py/video.json: per-video settings (slug, language, titles, chapter subtitles, optional closing credit)."""
    with open(os.path.join(ROOT, 'py', 'video.json'), encoding='utf-8') as f:
        return json.load(f)


def ffmpeg_exe():
    """ffmpeg from $FFMPEG, then PATH, then the binary that ships with imageio-ffmpeg (pip install imageio-ffmpeg)."""
    exe = os.environ.get('FFMPEG') or shutil.which('ffmpeg')
    if exe:
        return exe
    try:
        import imageio_ffmpeg
    except ImportError:
        raise SystemExit('ffmpeg not found. Install ffmpeg on PATH, or run: pip install imageio-ffmpeg')
    return imageio_ffmpeg.get_ffmpeg_exe()


def parse_narration(path):
    """Same format as scripts/tts_build.py: `# CHAPTER n Title`, `## gap N`, one sentence per line, `|` splits subtitle chunks."""
    items, chap, chap_title, pending_gap = [], 0, '', 0
    with open(path, encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            m = re.match(r'^#\s*CHAPTER\s+(\d+)\s+(.*)$', line)
            if m:
                chap, chap_title = int(m.group(1)), m.group(2).strip()
                items.append({'type': 'chapter', 'chapter': chap, 'title': chap_title})
                continue
            m = re.match(r'^##\s*gap\s+(\d+)', line)
            if m:
                pending_gap += int(m.group(1))
                continue
            if line.startswith('#'):
                continue
            items.append({'type': 'sent', 'chapter': chap, 'raw': line, 'gap_before': pending_gap})
            pending_gap = 0
    return items


def detect_lang(items):
    """'zh' if CJK characters are at least 20% of the narration, otherwise 'en'."""
    txt = ''.join(it['raw'] for it in items if it['type'] == 'sent')
    cjk = sum(1 for c in txt if '一' <= c <= '鿿')
    return 'zh' if cjk >= 0.2 * max(1, len(txt)) else 'en'


def write_wav(path, x, sr=SR):
    """x: float32 mono (n,) or stereo (n, 2) → 16-bit PCM wav."""
    a = np.asarray(x, dtype=np.float32)
    pcm = (np.clip(a, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1 if a.ndim == 1 else a.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def timeline_path():
    return os.path.join(ROOT, 'script', 'timeline.json')


def audio_path(cfg):
    return os.path.join(ROOT, 'public', 'assets', cfg['slug'], 'audio.wav')


def video_path(cfg, ver):
    return os.path.join(ROOT, 'renders', f"{cfg['slug']}_{ver}.mp4")

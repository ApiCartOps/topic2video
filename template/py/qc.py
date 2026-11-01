"""Stage 3 (qc): checks on the timeline, the audio and (when present) the rendered MP4. Exits 1 on any ✗.

Static checks (no rendering): sentence and subtitle timing, subtitle width at the real font size, card targets, audio length.
Video checks (need renders/<slug>_<ver>.mp4): duration and frame rate, an audio stream, and one sampled frame per second
during speech, flagging frames that are black while a subtitle is on screen.
"""
import json, os, re, subprocess
import numpy as np
from PIL import ImageFont
from common import ROOT, FPS, W, H, FONTS, ffmpeg_exe, timeline_path, audio_path, video_path, load_config
from render import SUB_SIZE, SUB_MAX_W


def probe(ffmpeg, path):
    """Parse ffmpeg's -i banner: duration, video fps and size, and whether an audio stream exists."""
    banner = subprocess.run([ffmpeg, '-hide_banner', '-i', path], capture_output=True, text=True, encoding='utf-8', errors='replace').stderr
    dur = re.search(r'Duration: (\d+):(\d+):([\d.]+)', banner)
    seconds = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3)) if dur else 0.0
    video = re.search(r'Video: .*?, (\d{3,5})x(\d{3,5}).*?, ([\d.]+) fps', banner)
    return {
        'seconds': seconds,
        'size': (int(video.group(1)), int(video.group(2))) if video else None,
        'fps': float(video.group(3)) if video else None,
        'has_audio': bool(re.search(r'Stream #\d+:\d+.*: Audio:', banner)),
    }


def sampled_luma(ffmpeg, path):
    """One grey thumbnail per second (160×90), as an array of mean brightness per second."""
    out = subprocess.run([ffmpeg, '-v', 'error', '-i', path, '-vf', 'fps=1,scale=160:90', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                         capture_output=True, check=True).stdout
    frames = np.frombuffer(out, dtype=np.uint8).reshape(-1, 90, 160)
    return frames.reshape(len(frames), -1).mean(axis=1)


def run(cfg, ver):
    problems = 0
    warnings = 0
    with open(timeline_path(), encoding='utf-8') as f:
        tl = json.load(f)
    total = tl['total_frames']
    sents = tl['sentences']
    print(f"[timeline] {len(sents)} sentences, {len(tl['chapters'])} chapters, {total} frames ({total / FPS:.1f}s)")

    for a, b in zip(sents, sents[1:]):
        if b['from'] <= a['to']:
            print(f"  ✗ sentence overlap {a['id']}→{b['id']}"); problems += 1
    for s in sents:
        if s['to'] < s['from']:
            print(f"  ✗ {s['id']} ends before it starts"); problems += 1
        for sb in s['subs']:
            if sb['from'] < s['from'] or sb['to'] > s['to'] + 1:
                print(f"  ✗ {s['id']} subtitle {sb['from']}–{sb['to']} outside the sentence {s['from']}–{s['to']}"); problems += 1

    subs = [sb for s in sents for sb in s['subs']]
    fnt = ImageFont.truetype(os.path.join(FONTS, 'NotoSansSC.ttf'), SUB_SIZE)
    for sb in subs:
        w = fnt.getlength(sb['text'])
        if w > SUB_MAX_W:
            print(f"  ⚠ subtitle {sb['from']} is {w:.0f}px at {SUB_SIZE}px (safe area {SUB_MAX_W}px), so it will be shrunk: {sb['text']}")
            warnings += 1

    ids = {s['id'] for s in sents}
    cards_file = os.path.join(ROOT, 'script', 'cards.json')
    if os.path.exists(cards_file):
        with open(cards_file, encoding='utf-8') as f:
            for c in json.load(f):
                if c['sentence'] not in ids:
                    print(f"  ✗ card for unknown sentence {c['sentence']}"); problems += 1

    audio = audio_path(cfg)
    if not os.path.exists(audio):
        print(f'  ✗ missing audio {audio}'); problems += 1
    else:
        import wave
        with wave.open(audio, 'rb') as w:
            secs = w.getnframes() / w.getframerate()
        if abs(secs - total / FPS) > 0.1:
            print(f'  ✗ audio is {secs:.2f}s but the timeline is {total / FPS:.2f}s'); problems += 1
        else:
            print(f'[audio] {secs:.2f}s, matches the timeline')

    mp4 = video_path(cfg, ver)
    if not os.path.exists(mp4):
        print(f'[video] {os.path.basename(mp4)} not rendered yet; run `python py/explain.py render` to check it')
    else:
        ffmpeg = ffmpeg_exe()
        info = probe(ffmpeg, mp4)
        print(f"[video] {os.path.basename(mp4)}: {info['seconds']:.2f}s, {info['size']}, {info['fps']} fps, audio={'yes' if info['has_audio'] else 'NO'}")
        if abs(info['seconds'] - total / FPS) > 0.1:
            print(f"  ✗ video is {info['seconds']:.2f}s but the timeline is {total / FPS:.2f}s"); problems += 1
        if info['size'] != (W, H):
            print(f"  ✗ video size {info['size']} is not {W}x{H}"); problems += 1
        if not info['has_audio']:
            print('  ✗ no audio stream'); problems += 1
        luma = sampled_luma(ffmpeg, mp4)
        black = []
        for sec in range(len(luma)):
            n = int((sec + 0.5) * FPS) + 1
            if any(sb['from'] <= n <= sb['to'] for sb in subs) and luma[sec] < 3:
                black.append(sec)
        if black:
            print(f'  ✗ near-black frame while a subtitle is shown, at seconds {black[:10]}'); problems += 1
        else:
            print('[video] no near-black frames while a subtitle is on screen')

    print(f'\nproblems: {problems}, warnings: {warnings}')
    return problems


if __name__ == '__main__':
    import sys
    sys.exit(1 if run(load_config(), os.environ.get('VER', 'v1')) else 0)

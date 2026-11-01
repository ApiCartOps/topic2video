#!/usr/bin/env python3
"""Python build for the explainer video: narration → voiceover and timeline → frames and MP4 → QC.
No Node.js or Remotion needed. Run from anywhere; paths resolve from the project root (the folder that holds script/ and public/).

  python py/explain.py build [--ver v1] [--engine edge|dummy]   # all three stages
  python py/explain.py tts    [--engine edge|dummy]               # narration → audio + script/timeline.json
  python py/explain.py render [--ver v1]                          # timeline + audio → renders/<slug>_<ver>.mp4 + contact sheet
  python py/explain.py qc     [--ver v1]                          # timing, audio and (if rendered) video checks

Environment: FFMPEG (path to ffmpeg), CRF (x264 quality, default 16), VER (default for --ver), plus the tts_build.py variables.
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    p = argparse.ArgumentParser(description='Build the explainer video with Python only (no Node/Remotion).')
    sub = p.add_subparsers(dest='cmd', required=True)
    for name in ('build', 'tts', 'render', 'qc'):
        sp = sub.add_parser(name)
        sp.add_argument('--ver', default=os.environ.get('VER', 'v1'), help='output version tag, e.g. v1 → renders/<slug>_v1.mp4')
        if name in ('build', 'tts'):
            sp.add_argument('--engine', choices=['edge', 'dummy'], default=os.environ.get('TTS_ENGINE', 'edge'),
                            help='edge = cloud voice with exact subtitle timing; dummy = silence, no network (layout dry run)')
    args = p.parse_args()

    cfg = common.load_config()
    if args.cmd in ('build', 'tts'):
        import tts
        tts.run(cfg, args.engine)
    if args.cmd in ('build', 'render'):
        import render
        render.render(cfg, args.ver)
    if args.cmd in ('build', 'qc'):
        import qc
        if qc.run(cfg, args.ver):
            sys.exit(1)


if __name__ == '__main__':
    main()

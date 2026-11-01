**English** · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [العربية](README.ar.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Italiano](README.it.md) · [Português](README.pt.md) · [Nederlands](README.nl.md) · [Русский](README.ru.md) · [Polski](README.pl.md)

<p align="center">
  <img src="assets/banner.svg" alt="topic2video: any topic, turned into a narrated motion-graphics explainer drawn in code" width="100%">
</p>

# topic2video

Turn any technical or science topic into a narrated motion-graphics explainer video, drawn entirely in code.

Give it a topic (or an article) and it produces an original explainer video in **Chinese or English**: black canvas, star-field or dot-field backdrop, white line graphics with purple emphasis, TTS voiceover, subtitles, and a chapter progress bar. Every frame is drawn with [Remotion](https://www.remotion.dev/) (React), so the video is reproducible and editable as source.

This repository is a **Claude Code skill** (`SKILL.md`) plus the reference docs, agent protocols, and a compilable Remotion project template it uses.

## What is in the repo

| Path | Contents |
|---|---|
| `SKILL.md` | Entry point for the skill: hard rules, four user confirmation points, eight-stage workflow, file index |
| `template/` | Compilable Remotion 4 project: common motion library, UI primitives, chapter/HUD/overlay components, fonts (OFL), and scripts for TTS, storyboard rendering, stills, previews, renders and checks |
| `reference/` | Style guide, motion vocabulary, composition and lighting rules, narration/storyboard format, research brief, agent prompts and build/QC protocols, lessons learned |
| `examples/rag/` | A complete sample video, *RAG and Knowledge Bases* (4′35″, Chinese narration): research, narration, storyboard, per-shot source code, QC reports and frames. Use it as the quality benchmark |
| `examples/contrast/` | Before/after frame pairs showing composition and lighting rules in practice |

## Requirements

- Claude Code (to run the skill workflow)
- Node.js and npm (Remotion project)
- Python 3 (TTS, storyboard, and metrics scripts)
- Roughly 2 GB of disk space per video project

See the header comment of `template/scripts/tts_build.py` for TTS engine setup.

## Quick start

1. Put this folder where Claude Code loads skills (for example `~/.claude/skills/anything2explainer`).
2. Ask Claude Code for an explainer, e.g. *"Make a 4-minute explainer video about vector databases, in Chinese."*
3. Claude follows `SKILL.md`: it asks for the duration and language, then pauses at the confirmation points (narration, voice, and a 30-second preview) before building the full video.

To build a project by hand from the template:

```bash
template/scripts/new_project.sh <work-dir> <slug>
cd <work-dir>
npm run studio            # open the Remotion studio for preview
```

## Credits and third-party components

- **Visual inspiration**: the look is inspired by the Douyin account "图灵宇宙" (Turing Universe). All frames are drawn in code; no footage or frames from other videos are used.
- **Fonts**: Noto Sans SC, Orbitron, Exo 2 and Audiowide, all under the SIL Open Font License 1.1. See [`template/public/fonts/LICENSE.md`](template/public/fonts/LICENSE.md).
- **Rendering**: [Remotion](https://www.remotion.dev/). Remotion is under its own license, not an OSI-approved one. Its terms require a company license for some commercial use, so check them before using it in a business.
- **Voices**: the default Chinese voice uses `edge-tts`, which calls Microsoft's online speech service and is subject to its terms. The default English voice uses `kokoro-82m`, which is Apache-2.0. You can also supply your own audio file.

## License

Code and documentation are released under the [MIT License](LICENSE). Fonts keep their own OFL license, and the third-party tools above keep their own terms.

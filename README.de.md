[English](README.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [العربية](README.ar.md) · [Français](README.fr.md) · **Deutsch** · [Español](README.es.md) · [Italiano](README.it.md) · [Português](README.pt.md) · [Nederlands](README.nl.md) · [Русский](README.ru.md) · [Polski](README.pl.md)

<p align="center">
  <img src="assets/banner.svg" alt="topic2video: Verwandeln Sie jedes Thema in ein vertontes Motion-Graphics-Erklärvideo, vollständig im Code gezeichnet" width="100%">
</p>

# topic2video

Verwandeln Sie jedes technische oder wissenschaftliche Thema in ein vertontes Motion-Graphics-Erklärvideo, vollständig im Code gezeichnet.

Geben Sie ein Thema (oder einen Artikel) vor, und es entsteht ein originales Erklärvideo auf **Chinesisch oder Englisch**: schwarze Leinwand, Sternfeld- oder Punktfeld-Hintergrund, weiße Linien-Grafiken mit lila Akzenten, TTS-Voice-over, Untertitel und eine Kapitel-Fortschrittsleiste. Jedes Bild wird mit [Remotion](https://www.remotion.dev/) (React) gezeichnet, daher ist das Video als Quelle reproduzierbar und bearbeitbar.

Dieses Repository ist eine **Claude-Code-Skill** (`SKILL.md`) mit Referenzdokumenten, Agenten-Protokollen und einer kompilierbaren Remotion-Projektvorlage.

## Inhalt des Repositorys

| Pfad | Inhalt |
|---|---|
| `SKILL.md` | Einstiegspunkt der Skill: harte Regeln, vier Bestätigungspunkte für den Nutzer, achtstufiger Ablauf, Dateiindex |
| `template/` | Kompilierbares Remotion-4-Projekt: gemeinsame Bewegungsbibliothek, UI-Primitive, Kapitel-/HUD-/Overlay-Komponenten, Schriften (OFL) sowie Skripte für TTS, Storyboard-Rendering, Standbilder, Vorschauen, Renderings und Prüfungen |
| `reference/` | Stilguide, Bewegungsvokabular, Regeln für Komposition und Licht, Format von Narration und Storyboard, Recherche-Briefing, Agenten-Prompts und Build-/QC-Protokolle, gesammelte Erkenntnisse |
| `examples/rag/` | Ein vollständiges Beispielvideo, *RAG and Knowledge Bases* (4′35″, chinesische Narration): Recherche, Narration, Storyboard, Quellcode jeder Einstellung, QC-Berichte und Frames. Als Qualitätsmaßstab verwenden |
| `examples/contrast/` | Vorher-nachher-Bildpaare, die Komposition- und Lichtregeln in der Praxis zeigen |

## Voraussetzungen

- Claude Code (zum Ausführen des Skill-Ablaufs)
- Node.js und npm (Remotion-Projekt)
- Python 3 (TTS-, Storyboard- und Metrik-Skripte)
- Etwa 2 GB Speicherplatz pro Videoprojekt

Die Kopfzeile von `template/scripts/tts_build.py` erklärt die Einrichtung der TTS-Engine.

## Schnellstart

1. Legen Sie diesen Ordner dorthin, wo Claude Code Skills lädt (zum Beispiel `~/.claude/skills/anything2explainer`).
2. Bitten Sie Claude Code um ein Erklärvideo, zum Beispiel *„Make a 4-minute explainer video about vector databases, in Chinese.“*
3. Claude folgt `SKILL.md`: Es fragt nach Dauer und Sprache und hält dann an den Bestätigungspunkten (Narration, Stimme und 30-Sekunden-Vorschau), bevor das vollständige Video entsteht.

Um ein Projekt von Hand aus der Vorlage zu erstellen:

```bash
template/scripts/new_project.sh <work-dir> <slug>
cd <work-dir>
npm run studio            # Remotion-Studio zur Vorschau öffnen
```

## Danksagungen und Drittanbieter-Komponenten

- **Visuelle Inspiration**: Der Look ist vom Douyin-Konto „图灵宇宙“ (Turing Universe) inspiriert. Alle Bilder werden im Code gezeichnet; es werden keine Aufnahmen oder Bilder anderer Videos verwendet.
- **Schriften**: Noto Sans SC, Orbitron, Exo 2 und Audiowide, alle unter der SIL Open Font License 1.1. Siehe [`template/public/fonts/LICENSE.md`](template/public/fonts/LICENSE.md).
- **Rendering**: [Remotion](https://www.remotion.dev/). Remotion hat eine eigene Lizenz, die nicht von der OSI anerkannt ist. Die Bedingungen verlangen für manche kommerzielle Nutzung eine Unternehmenslizenz; prüfen Sie sie vor einem geschäftlichen Einsatz.
- **Stimmen**: Die chinesische Standardstimme nutzt `edge-tts`, das den Online-Sprachdienst von Microsoft aufruft und dessen Bedingungen unterliegt. Die englische Standardstimme nutzt `kokoro-82m`, das unter Apache-2.0 steht. Sie können auch eine eigene Audiodatei bereitstellen.

## Lizenz

Code und Dokumentation sind unter der [MIT-Lizenz](LICENSE) veröffentlicht. Die Schriften behalten ihre OFL-Lizenz, und die oben genannten Drittanbieter-Werkzeuge behalten ihre eigenen Bedingungen.

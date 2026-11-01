[English](README.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [العربية](README.ar.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Italiano](README.it.md) · [Português](README.pt.md) · **Nederlands** · [Русский](README.ru.md) · [Polski](README.pl.md)

<p align="center">
  <img src="assets/banner.svg" alt="topic2video: maak van elk onderwerp een ingesproken motion-graphics uitlegvideo, volledig getekend in code" width="100%">
</p>

# topic2video

Maak van elk technisch of wetenschappelijk onderwerp een ingesproken motion-graphics uitlegvideo, volledig getekend in code.

Geef een onderwerp (of een artikel) en het maakt een originele uitlegvideo in **Chinees of Engels**: zwart canvas, achtergrond met een sterrenveld of puntenveld, witte lijngrafieken met paarse nadruk, TTS-voice-over, ondertitels en een voortgangsbalk per hoofdstuk. Elk frame wordt getekend met [Remotion](https://www.remotion.dev/) (React), dus de video is reproduceerbaar en als broncode te bewerken.

Deze repository is een **Claude Code-skill** (`SKILL.md`), met de referentiedocumenten, agentprotocollen en een compileerbaar Remotion-projectsjabloon die hij gebruikt.

## Inhoud van de repository

| Pad | Inhoud |
|---|---|
| `SKILL.md` | Startpunt van de skill: harde regels, vier bevestigingspunten voor de gebruiker, een werkproces in acht fasen, bestandsindex |
| `template/` | Compileerbaar Remotion 4-project: gedeelde bewegingsbibliotheek, UI-primitieven, hoofdstuk-/HUD-/overlaycomponenten, lettertypen (OFL), en scripts voor TTS, storyboardrendering, stills, previews, renders en controles |
| `reference/` | Stijlgids, bewegingsvocabulaire, regels voor compositie en licht, formaat van narratie/storyboard, onderzoeksbrief, agentprompts en build-/QC-protocollen, geleerde lessen |
| `examples/rag/` | Een compleet voorbeeldvideo, *RAG and Knowledge Bases* (4′35″, Chinese narratie): onderzoek, narratie, storyboard, broncode per shot, QC-rapporten en frames. Gebruik het als kwaliteitsmaatstaf |
| `examples/contrast/` | Paren van voor/na-frames die de compositie- en lichtregels in de praktijk tonen |

## Vereisten

- Claude Code (om de skill-workflow uit te voeren)
- Node.js en npm (Remotion-project)
- Python 3 (TTS-, storyboard- en metriekscripts)
- Ongeveer 2 GB schijfruimte per videoproject

Zie de kopcommentaar van `template/scripts/tts_build.py` voor het instellen van de TTS-engine.

## Snelstart

1. Zet deze map waar Claude Code skills laadt (bijvoorbeeld `~/.claude/skills/anything2explainer`).
2. Vraag Claude Code om een uitlegvideo, bijvoorbeeld *"Make a 4-minute explainer video about vector databases, in Chinese."*
3. Claude volgt `SKILL.md`: het vraagt naar de duur en de taal, en pauzeert dan bij de bevestigingspunten (narratie, stem en een preview van 30 seconden) voordat de volledige video wordt gebouwd.

Om handmatig een project uit het sjabloon te bouwen:

```bash
template/scripts/new_project.sh <work-dir> <slug>
cd <work-dir>
npm run studio            # opent de Remotion-studio voor de preview
```

## Dankbetuigingen en componenten van derden

- **Visuele inspiratie**: de look is geïnspireerd op het Douyin-account «图灵宇宙» (Turing Universe). Alle frames worden met code getekend; er wordt geen beeldmateriaal of frames uit andere video's gebruikt.
- **Lettertypen**: Noto Sans SC, Orbitron, Exo 2 en Audiowide, alle onder de SIL Open Font License 1.1. Zie [`template/public/fonts/LICENSE.md`](template/public/fonts/LICENSE.md).
- **Rendering**: [Remotion](https://www.remotion.dev/). Remotion heeft een eigen licentie, niet goedgekeurd door de OSI. De voorwaarden vereisen voor sommig commercieel gebruik een bedrijfslicentie, dus controleer die voordat je het zakelijk gebruikt.
- **Stemmen**: de standaard Chinese stem gebruikt `edge-tts`, dat de online spraakdienst van Microsoft aanroept en onder de voorwaarden daarvan valt. De standaard Engelse stem gebruikt `kokoro-82m`, dat Apache-2.0 is. Je kunt ook je eigen audiobestand aanleveren.

## Licentie

Code en documentatie worden uitgebracht onder de [MIT-licentie](LICENSE). De lettertypen behouden hun OFL-licentie, en de hierboven genoemde tools van derden behouden hun eigen voorwaarden.

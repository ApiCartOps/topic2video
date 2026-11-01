[English](README.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [العربية](README.ar.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · **Italiano** · [Português](README.pt.md) · [Nederlands](README.nl.md) · [Русский](README.ru.md) · [Polski](README.pl.md)

<p align="center">
  <img src="assets/banner.svg" alt="topic2video: trasforma qualsiasi argomento in un video esplicativo narrato in motion graphics, disegnato interamente con il codice" width="100%">
</p>

# topic2video

Trasforma qualsiasi argomento tecnico o scientifico in un video esplicativo narrato in motion graphics, disegnato interamente con il codice.

Dai un argomento (o un articolo) e produce un video esplicativo originale in **cinese o inglese**: sfondo nero, sfondo a campo di stelle o di punti, grafica a linee bianche con accenti viola, voce fuori campo TTS, sottotitoli e una barra di avanzamento per capitoli. Ogni fotogramma è disegnato con [Remotion](https://www.remotion.dev/) (React), quindi il video è riproducibile e modificabile come sorgente.

Questo repository è una **skill di Claude Code** (`SKILL.md`), insieme ai documenti di riferimento, ai protocolli degli agenti e a un modello di progetto Remotion compilabile che utilizza.

## Contenuto del repository

| Percorso | Contenuto |
|---|---|
| `SKILL.md` | Punto di ingresso della skill: regole fondamentali, quattro punti di conferma per l'utente, flusso di lavoro in otto fasi, indice dei file |
| `template/` | Progetto Remotion 4 compilabile: libreria di movimento comune, primitive dell'interfaccia, componenti di capitolo/HUD/overlay, font (OFL) e script per TTS, rendering dello storyboard, immagini fisse, anteprime, render e controlli |
| `reference/` | Guida allo stile, vocabolario del movimento, regole di composizione e illuminazione, formato di narrazione/storyboard, brief di ricerca, prompt degli agenti e protocolli di costruzione/QC, lezioni apprese |
| `examples/rag/` | Un video di esempio completo, *RAG and Knowledge Bases* (4′35″, narrazione in cinese): ricerca, narrazione, storyboard, codice sorgente di ogni inquadratura, report QC e fotogrammi. Usalo come riferimento di qualità |
| `examples/contrast/` | Coppie di fotogrammi prima/dopo che mostrano le regole di composizione e illuminazione in pratica |

## Requisiti

- Claude Code (per eseguire il flusso di lavoro della skill)
- Node.js e npm (progetto Remotion)
- Python 3 (script di TTS, storyboard e metriche)
- Circa 2 GB di spazio su disco per progetto video

Consulta il commento di intestazione di `template/scripts/tts_build.py` per configurare il motore TTS.

## Avvio rapido

1. Metti questa cartella dove Claude Code carica le skill (ad esempio `~/.claude/skills/anything2explainer`).
2. Chiedi a Claude Code un video esplicativo, ad esempio *«Make a 4-minute explainer video about vector databases, in Chinese.»*
3. Claude segue `SKILL.md`: chiede durata e lingua, poi si ferma nei punti di conferma (narrazione, voce e un'anteprima di 30 secondi) prima di costruire il video completo.

Per costruire un progetto a mano dal modello:

```bash
template/scripts/new_project.sh <work-dir> <slug>
cd <work-dir>
npm run studio            # apre lo studio Remotion per l'anteprima
```

## Crediti e componenti di terze parti

- **Ispirazione visiva**: l'aspetto è ispirato all'account Douyin «图灵宇宙» (Turing Universe). Tutti i fotogrammi sono disegnati con il codice; non si usano filmati o fotogrammi di altri video.
- **Font**: Noto Sans SC, Orbitron, Exo 2 e Audiowide, tutti sotto la SIL Open Font License 1.1. Vedi [`template/public/fonts/LICENSE.md`](template/public/fonts/LICENSE.md).
- **Rendering**: [Remotion](https://www.remotion.dev/). Remotion ha una propria licenza, non approvata dall'OSI. Le sue condizioni richiedono una licenza aziendale per alcuni usi commerciali, quindi verificale prima di usarlo in ambito professionale.
- **Voci**: la voce cinese predefinita usa `edge-tts`, che richiama il servizio vocale online di Microsoft ed è soggetto alle sue condizioni. La voce inglese predefinita usa `kokoro-82m`, con licenza Apache-2.0. Puoi anche fornire un tuo file audio.

## Licenza

Il codice e la documentazione sono rilasciati con la [licenza MIT](LICENSE). I font mantengono la loro licenza OFL, e gli strumenti di terze parti indicati sopra mantengono le proprie condizioni.

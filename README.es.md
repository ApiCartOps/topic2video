[English](README.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [العربية](README.ar.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · **Español** · [Italiano](README.it.md) · [Português](README.pt.md) · [Nederlands](README.nl.md) · [Русский](README.ru.md) · [Polski](README.pl.md)

<p align="center">
  <img src="assets/banner.svg" alt="topic2video: convierte cualquier tema en un video explicativo narrado de motion graphics, dibujado íntegramente con código" width="100%">
</p>

# topic2video

Convierte cualquier tema técnico o científico en un video explicativo narrado de motion graphics, dibujado íntegramente con código.

Dale un tema (o un artículo) y produce un video explicativo original en **chino o inglés**: lienzo negro, fondo de campo de estrellas o de puntos, gráficos de líneas blancas con énfasis morado, voz en off TTS, subtítulos y una barra de progreso por capítulos. Cada fotograma se dibuja con [Remotion](https://www.remotion.dev/) (React), así que el video es reproducible y editable como código fuente.

Este repositorio es una **skill de Claude Code** (`SKILL.md`), además de los documentos de referencia, los protocolos de agentes y una plantilla de proyecto Remotion compilable que utiliza.

## Contenido del repositorio

| Ruta | Contenido |
|---|---|
| `SKILL.md` | Punto de entrada de la skill: reglas estrictas, cuatro puntos de confirmación del usuario, flujo de trabajo de ocho etapas, índice de archivos |
| `template/` | Proyecto Remotion 4 compilable: biblioteca de movimiento común, primitivas de interfaz, componentes de capítulo/HUD/superposición, fuentes (OFL) y scripts de TTS, renderizado del storyboard, imágenes fijas, vistas previas, renderizados y comprobaciones |
| `reference/` | Guía de estilo, vocabulario de movimiento, reglas de composición e iluminación, formato de narración/storyboard, resumen de investigación, prompts de agentes y protocolos de construcción/QC, lecciones aprendidas |
| `examples/rag/` | Un video de ejemplo completo, *RAG and Knowledge Bases* (4′35″, narración en chino): investigación, narración, storyboard, código fuente de cada plano, informes de QC y fotogramas. Úsalo como referencia de calidad |
| `examples/contrast/` | Pares de fotogramas antes/después que muestran las reglas de composición e iluminación en la práctica |

## Requisitos

- Claude Code (para ejecutar el flujo de trabajo de la skill)
- Node.js y npm (proyecto Remotion)
- Python 3 (scripts de TTS, storyboard y métricas)
- Unos 2 GB de espacio en disco por proyecto de video

Consulta el comentario de cabecera de `template/scripts/tts_build.py` para configurar el motor TTS.

## Inicio rápido

1. Coloca esta carpeta donde Claude Code carga las skills (por ejemplo `~/.claude/skills/anything2explainer`).
2. Pídele a Claude Code un video explicativo, por ejemplo *«Make a 4-minute explainer video about vector databases, in Chinese.»*
3. Claude sigue `SKILL.md`: pregunta por la duración y el idioma, y luego se detiene en los puntos de confirmación (narración, voz y una vista previa de 30 segundos) antes de construir el video completo.

Para crear un proyecto a mano desde la plantilla:

```bash
template/scripts/new_project.sh <work-dir> <slug>
cd <work-dir>
npm run studio            # abre el estudio de Remotion para la vista previa
```

## Créditos y componentes de terceros

- **Inspiración visual**: el estilo se inspira en la cuenta de Douyin «图灵宇宙» (Turing Universe). Todos los fotogramas se dibujan con código; no se usan imágenes ni fotogramas de otros videos.
- **Fuentes**: Noto Sans SC, Orbitron, Exo 2 y Audiowide, todas bajo la SIL Open Font License 1.1. Consulta [`template/public/fonts/LICENSE.md`](template/public/fonts/LICENSE.md).
- **Renderizado**: [Remotion](https://www.remotion.dev/). Remotion tiene su propia licencia, que no está aprobada por la OSI. Sus condiciones exigen una licencia de empresa para algunos usos comerciales, así que revísalas antes de usarlo en un negocio.
- **Voces**: la voz china predeterminada usa `edge-tts`, que llama al servicio de voz en línea de Microsoft y está sujeto a sus condiciones. La voz inglesa predeterminada usa `kokoro-82m`, que tiene licencia Apache-2.0. También puedes aportar tu propio archivo de audio.

## Licencia

El código y la documentación se publican bajo la [licencia MIT](LICENSE). Las fuentes conservan su licencia OFL, y las herramientas de terceros mencionadas arriba mantienen sus propias condiciones.

[English](README.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [العربية](README.ar.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Italiano](README.it.md) · **Português** · [Nederlands](README.nl.md) · [Русский](README.ru.md) · [Polski](README.pl.md)

<p align="center">
  <img src="assets/banner.svg" alt="topic2video: transforme qualquer tema em um vídeo explicativo narrado em motion graphics, desenhado inteiramente em código" width="100%">
</p>

# topic2video

Transforme qualquer tema técnico ou científico em um vídeo explicativo narrado em motion graphics, desenhado inteiramente em código.

Dê um tema (ou um artigo) e ele produz um vídeo explicativo original em **chinês ou inglês**: fundo preto, plano de fundo com campo de estrelas ou de pontos, gráficos de linhas brancas com ênfase em roxo, narração TTS, legendas e uma barra de progresso por capítulo. Cada quadro é desenhado com [Remotion](https://www.remotion.dev/) (React), então o vídeo é reproduzível e editável como código-fonte.

Este repositório é uma **skill do Claude Code** (`SKILL.md`), junto com os documentos de referência, os protocolos de agentes e um modelo de projeto Remotion compilável que ela usa.

## Conteúdo do repositório

| Caminho | Conteúdo |
|---|---|
| `SKILL.md` | Ponto de entrada da skill: regras fixas, quatro pontos de confirmação do usuário, fluxo de trabalho em oito etapas, índice de arquivos |
| `template/` | Projeto Remotion 4 compilável: biblioteca de movimento comum, primitivas de interface, componentes de capítulo/HUD/sobreposição, fontes (OFL) e scripts de TTS, renderização do storyboard, quadros estáticos, pré-visualizações, renderizações e verificações |
| `reference/` | Guia de estilo, vocabulário de movimento, regras de composição e iluminação, formato de narração/storyboard, briefing de pesquisa, prompts de agentes e protocolos de construção/QC, lições aprendidas |
| `examples/rag/` | Um vídeo de exemplo completo, *RAG and Knowledge Bases* (4′35″, narração em chinês): pesquisa, narração, storyboard, código-fonte de cada plano, relatórios de QC e quadros. Use-o como referência de qualidade |
| `examples/contrast/` | Pares de quadros antes/depois que mostram as regras de composição e iluminação na prática |

## Requisitos

- Claude Code (para executar o fluxo de trabalho da skill)
- Node.js e npm (projeto Remotion)
- Python 3 (scripts de TTS, storyboard e métricas)
- Cerca de 2 GB de espaço em disco por projeto de vídeo

Veja o comentário de cabeçalho de `template/scripts/tts_build.py` para configurar o motor de TTS.

## Início rápido

1. Coloque esta pasta onde o Claude Code carrega as skills (por exemplo `~/.claude/skills/anything2explainer`).
2. Peça ao Claude Code um vídeo explicativo, por exemplo *«Make a 4-minute explainer video about vector databases, in Chinese.»*
3. O Claude segue o `SKILL.md`: pergunta a duração e o idioma, depois para nos pontos de confirmação (narração, voz e uma pré-visualização de 30 segundos) antes de construir o vídeo completo.

Para criar um projeto manualmente a partir do modelo:

```bash
template/scripts/new_project.sh <work-dir> <slug>
cd <work-dir>
npm run studio            # abre o estúdio Remotion para pré-visualização
```

## Créditos e componentes de terceiros

- **Inspiração visual**: o visual é inspirado na conta do Douyin «图灵宇宙» (Turing Universe). Todos os quadros são desenhados com código; nenhuma filmagem ou quadro de outros vídeos é usado.
- **Fontes**: Noto Sans SC, Orbitron, Exo 2 e Audiowide, todas sob a SIL Open Font License 1.1. Veja [`template/public/fonts/LICENSE.md`](template/public/fonts/LICENSE.md).
- **Renderização**: [Remotion](https://www.remotion.dev/). O Remotion tem licença própria, não aprovada pela OSI. Seus termos exigem uma licença empresarial para alguns usos comerciais, então verifique-os antes de usar em um negócio.
- **Vozes**: a voz chinesa padrão usa `edge-tts`, que chama o serviço de voz online da Microsoft e está sujeito aos seus termos. A voz inglesa padrão usa `kokoro-82m`, sob licença Apache-2.0. Você também pode fornecer seu próprio arquivo de áudio.

## Licença

O código e a documentação são publicados sob a [licença MIT](LICENSE). As fontes mantêm sua licença OFL, e as ferramentas de terceiros citadas acima mantêm seus próprios termos.

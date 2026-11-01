[English](README.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [العربية](README.ar.md) · **Français** · [Deutsch](README.de.md) · [Español](README.es.md) · [Italiano](README.it.md) · [Português](README.pt.md) · [Nederlands](README.nl.md) · [Русский](README.ru.md) · [Polski](README.pl.md)

<p align="center">
  <img src="assets/banner.svg" alt="topic2video : transformez n'importe quel sujet en vidéo explicative animée et commentée, entièrement dessinée en code" width="100%">
</p>

# topic2video

Transformez n'importe quel sujet technique ou scientifique en une vidéo explicative en motion graphics, commentée, entièrement dessinée en code.

Donnez un sujet (ou un article) et il produit une vidéo explicative originale en **chinois ou en anglais** : fond noir, arrière-plan à champ d'étoiles ou de points, graphismes en lignes blanches avec accent violet, voix off TTS, sous-titres et barre de progression par chapitre. Chaque image est dessinée avec [Remotion](https://www.remotion.dev/) (React), donc la vidéo est reproductible et modifiable comme source.

Ce dépôt est une **skill Claude Code** (`SKILL.md`), accompagnée des documents de référence, des protocoles d'agents et d'un modèle de projet Remotion compilable.

## Contenu du dépôt

| Chemin | Contenu |
|---|---|
| `SKILL.md` | Point d'entrée de la skill : règles essentielles, quatre points de confirmation utilisateur, flux de travail en huit étapes, index des fichiers |
| `template/` | Projet Remotion 4 compilable : bibliothèque d'animation commune, primitives d'interface, composants de chapitre/HUD/superposition, polices (OFL), et scripts de TTS, rendu du storyboard, images fixes, aperçus, rendus et contrôles |
| `reference/` | Guide de style, vocabulaire de mouvement, règles de composition et d'éclairage, format narration/storyboard, brief de recherche, prompts d'agents et protocoles de construction/QC, leçons apprises |
| `examples/rag/` | Vidéo exemple complète, *RAG and Knowledge Bases* (4′35″, narration en chinois) : recherche, narration, storyboard, code source de chaque plan, rapports QC et images. À utiliser comme référence de qualité |
| `examples/contrast/` | Paires d'images avant/après montrant les règles de composition et d'éclairage en pratique |

## Prérequis

- Claude Code (pour exécuter le flux de travail de la skill)
- Node.js et npm (projet Remotion)
- Python 3 (scripts TTS, storyboard et métriques)
- Environ 2 Go d'espace disque par projet vidéo

Voir le commentaire d'en-tête de `template/scripts/tts_build.py` pour configurer le moteur TTS.

## Démarrage rapide

1. Placez ce dossier là où Claude Code charge les skills (par exemple `~/.claude/skills/anything2explainer`).
2. Demandez à Claude Code une vidéo explicative, par exemple *« Make a 4-minute explainer video about vector databases, in Chinese. »*
3. Claude suit `SKILL.md` : il demande la durée et la langue, puis s'arrête aux points de confirmation (narration, voix et aperçu de 30 secondes) avant de construire la vidéo complète.

Pour construire un projet à la main à partir du modèle :

```bash
template/scripts/new_project.sh <work-dir> <slug>
cd <work-dir>
npm run studio            # ouvre le studio Remotion pour l'aperçu
```

## Crédits et composants tiers

- **Inspiration visuelle** : le rendu s'inspire du compte Douyin « 图灵宇宙 » (Turing Universe). Toutes les images sont dessinées en code ; aucune séquence ni image d'autres vidéos n'est utilisée.
- **Polices** : Noto Sans SC, Orbitron, Exo 2 et Audiowide, toutes sous SIL Open Font License 1.1. Voir [`template/public/fonts/LICENSE.md`](template/public/fonts/LICENSE.md).
- **Rendu** : [Remotion](https://www.remotion.dev/). Remotion a sa propre licence, non approuvée par l'OSI. Ses conditions exigent une licence d'entreprise pour certains usages commerciaux ; vérifiez-les avant toute utilisation professionnelle.
- **Voix** : la voix chinoise par défaut utilise `edge-tts`, qui appelle le service vocal en ligne de Microsoft et est soumis à ses conditions. La voix anglaise par défaut utilise `kokoro-82m`, sous licence Apache-2.0. Vous pouvez aussi fournir votre propre fichier audio.

## Licence

Le code et la documentation sont publiés sous [licence MIT](LICENSE). Les polices conservent leur licence OFL, et les outils tiers mentionnés ci-dessus conservent leurs propres conditions.

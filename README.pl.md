[English](README.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [العربية](README.ar.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Italiano](README.it.md) · [Português](README.pt.md) · [Nederlands](README.nl.md) · [Русский](README.ru.md) · **Polski**

<p align="center">
  <img src="assets/banner.svg" alt="topic2video: zamień dowolny temat w narrowany film wyjaśniający w stylu motion graphics, narysowany w całości kodem" width="100%">
</p>

# topic2video

Zamień dowolny temat techniczny lub naukowy w narrowany film wyjaśniający w stylu motion graphics, narysowany w całości kodem.

Podaj temat (lub artykuł), a powstanie oryginalny film wyjaśniający po **chińsku lub angielsku**: czarne płótno, tło z polem gwiazd lub kropek, białe grafiki liniowe z fioletowym akcentem, lektor TTS, napisy i pasek postępu rozdziałów. Każda klatka jest rysowana w [Remotion](https://www.remotion.dev/) (React), więc film jest powtarzalny i edytowalny jako kod źródłowy.

To repozytorium to **umiejętność (skill) Claude Code** (`SKILL.md`), wraz z dokumentami referencyjnymi, protokołami agentów i kompilowalnym szablonem projektu Remotion, z którego korzysta.

## Zawartość repozytorium

| Ścieżka | Zawartość |
|---|---|
| `SKILL.md` | Punkt wejścia umiejętności: twarde zasady, cztery punkty potwierdzenia dla użytkownika, ośmioetapowy przepływ pracy, indeks plików |
| `template/` | Kompilowalny projekt Remotion 4: wspólna biblioteka ruchu, prymitywy interfejsu, komponenty rozdziałów/HUD/nakładki, czcionki (OFL) oraz skrypty do TTS, renderowania storyboardu, klatek statycznych, podglądów, renderów i kontroli |
| `reference/` | Przewodnik po stylu, słownik ruchu, zasady kompozycji i oświetlenia, format narracji i storyboardu, zestawienie badań, prompty agentów i protokoły budowy/QC, wyciągnięte wnioski |
| `examples/rag/` | Kompletny przykładowy film, *RAG and Knowledge Bases* (4′35″, chińska narracja): badania, narracja, storyboard, kod źródłowy każdego ujęcia, raporty QC i klatki. Używaj go jako wzorca jakości |
| `examples/contrast/` | Pary klatek przed/po pokazujące zasady kompozycji i oświetlenia w praktyce |

## Wymagania

- Claude Code (do uruchomienia przepływu pracy umiejętności)
- Node.js i npm (projekt Remotion)
- Python 3 (skrypty TTS, storyboardu i metryk)
- Około 2 GB miejsca na dysku na projekt filmowy

Konfigurację silnika TTS opisuje komentarz nagłówkowy w `template/scripts/tts_build.py`.

## Szybki start

1. Umieść ten folder tam, gdzie Claude Code wczytuje umiejętności (na przykład `~/.claude/skills/anything2explainer`).
2. Poproś Claude Code o film wyjaśniający, na przykład *„Make a 4-minute explainer video about vector databases, in Chinese.”*
3. Claude postępuje według `SKILL.md`: pyta o czas trwania i język, a następnie zatrzymuje się w punktach potwierdzenia (narracja, głos i 30-sekundowy podgląd), zanim zbuduje pełny film.

Aby ręcznie zbudować projekt z szablonu:

```bash
template/scripts/new_project.sh <work-dir> <slug>
cd <work-dir>
npm run studio            # otwiera studio Remotion do podglądu
```

## Podziękowania i komponenty zewnętrzne

- **Inspiracja wizualna**: wygląd jest inspirowany kontem Douyin „图灵宇宙” (Turing Universe). Wszystkie klatki są rysowane kodem; nie używa się materiału filmowego ani klatek z innych filmów.
- **Czcionki**: Noto Sans SC, Orbitron, Exo 2 i Audiowide, wszystkie na licencji SIL Open Font License 1.1. Zobacz [`template/public/fonts/LICENSE.md`](template/public/fonts/LICENSE.md).
- **Renderowanie**: [Remotion](https://www.remotion.dev/). Remotion ma własną licencję, nieuznawaną przez OSI. Jej warunki wymagają licencji firmowej do niektórych zastosowań komercyjnych, więc sprawdź je przed użyciem w biznesie.
- **Głosy**: domyślny chiński głos używa `edge-tts`, który łączy się z internetową usługą mowy Microsoftu i podlega jej warunkom. Domyślny angielski głos używa `kokoro-82m`, na licencji Apache-2.0. Możesz też dostarczyć własny plik audio.

## Licencja

Kod i dokumentacja są udostępniane na [licencji MIT](LICENSE). Czcionki zachowują licencję OFL, a wymienione wyżej narzędzia zewnętrzne zachowują własne warunki.

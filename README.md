# ogarnijprawko

Serwis do nauki **teorii prawa jazdy** — oficjalne pytania egzaminacyjne WORD.
Statyczna strona (bez buildu), hosting GitHub Pages.

## Funkcje
- **3525 oficjalnych pytań** z bazy Ministerstwa Infrastruktury (gov.pl, domena publiczna)
- 12 kategorii (A, B, C, D, T, AM, …)
- Podział na **działy tematyczne** (auto-klasyfikacja)
- Tryb **nauki** (bez czasu, feedback od razu)
- **Symulator** egzaminu (punktacja 3/2/1, próg 68/74)
- **Egzamin państwowy 1:1** — wierny interfejs WORD
- 4 języki: PL · EN · DE · UA
- Model freemium: demo darmo, pełny dostęp 25 zł lifetime

## Struktura
- `index.html` · `kategoria.html` · `nauka.html` · `egzamin.html` · `egzamin-word.html` · `cennik.html`
- `app.js` — silnik (dane, i18n, egzamin, paywall)
- `style.css` — motyw
- `data/` — pytania (generowane z `_src/etl.py`)
- `media/img/` — zdjęcia (hostowane osobno, poza repo)

## Dane
Generowane z `_src/katalog.xlsx` (oficjalny katalog MI):
```
python _src/etl.py
```

## Licencja treści
Pytania, zdjęcia i filmy pochodzą z oficjalnej bazy Ministerstwa Infrastruktury
(gov.pl) — domena publiczna. Projekt edukacyjny, niepowiązany z WORD ani MI.

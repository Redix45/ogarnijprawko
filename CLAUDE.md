# ogarnijprawko — instrukcja projektu dla AI

Serwis do nauki **teorii prawa jazdy** (oficjalne pytania egzaminacyjne WORD).
Osobny projekt, siostrzany do ogarnijegzamin.pl. **Komunikacja po polsku.**
Marka: **ogarnijprawko**. Model: freemium — demo darmo, pełny dostęp 25 zł lifetime.

## Co to jest
Statyczna strona (bez buildu, czysty HTML/CSS/JS). Tryb nauki + symulator
egzaminu państwowego WORD. Pytania z **oficjalnej bazy Ministerstwa
Infrastruktury** (gov.pl) — domena publiczna, za darmo.

## Źródło danych (oficjalne, gov.pl)
- Baza pytań XLSX: `https://www.gov.pl/web/infrastruktura/prawo-jazdy`
  (plik `katalog_dla_kandydatów_na_kierowców_*.xlsx`, ~3,5 tys. pytań,
  PL/EN/DE/UA + PJM migowy).
- Multimedia ZIP ~8.8 GB (`multimedia_do_pytan.zip`) — 1103 filmy `.wmv`
  + 1535 zdjęć `.jpg`. **Filmy NIE są dostępne per-plik**, tylko w tym ZIP.
- ETL: `_src/etl.py` (openpyxl) → `data/`. Uruchom: `python _src/etl.py`
  (wymaga `_src/katalog.xlsx`). Wymusza UTF-8 (Windows cp1252!).

## Struktura
| Ścieżka | Co |
|---|---|
| `index.html` | landing — wybór kategorii (klik → kategoria.html) |
| `kategoria.html` | po wyborze kat: tryby + działy tematyczne (z kłódkami) |
| `nauka.html` | tryb nauki; param `?kat=B&dzial=znaki` (filtr działu) |
| `egzamin.html` | symulator (ciemny, 32 pyt, punkty 3/2/1, próg 68/74) |
| `egzamin-word.html` | **egzamin 1:1 WORD** (jasny motyw, self-contained, faza zapoznania/odpowiedzi) |
| `cennik.html` | paywall 25 zł lifetime + konfig Stripe + dev-unlock |
| `app.js` | silnik: data, i18n PL/EN/DE/UA, budowa egzaminu, media, **dostęp/paywall** |
| `style.css` | motyw ciemny (premium: aurora, glow, konfetti) |
| `data/pytania.json` | pełna baza (3525 pytań, pole `dzial`) |
| `data/index.json` | kategorie + liczniki + `dzialy[]` + `dzialNazwy` |
| `data/kat/<KAT>.json` | pytania per kategoria (lazy load) |
| `media/img/<plik>.jpg` | zdjęcia (hostowane u nas) — DO POBRANIA z ZIP |
| `_src/` | XLSX + etl.py (nie deployować) |

## Dostęp / paywall (app.js → ACCESS)
- DEMO (niezapłacone): kat **B** + dział **znaki** (slug `freeDzial`), tylko tryb nauki.
- PAID (`localStorage op_paid==='1'`): wszystko. Docelowo flaga z Firebase.
- Helpery: `isPaid/setPaid/canKat/canDzial/canTryb/gate`. `gate(ok,powod)` → redirect na cennik.
- Działy tematyczne: **auto-klasyfikacja** keyword w ETL (`classify_dzial`), pole `q.dzial`.
  Pokrycie ~67%, reszta `pozostale`. Do dostrojenia keywordów w `DZIALY`.

## Stripe (TODO — w cennik.html `STRIPE.paymentLink`)
1. Konto Stripe + włącz BLIK (PLN). 2. Payment Link 25 PLN → wklej URL.
3. Docelowo: webhook `checkout.session.completed` → Firebase Function ustawia `paid`.
4. Firebase Auth (Google) jak w ogarnijegzamin (`auth.js`) — do powiązania płatności z kontem.

## Model danych pytania
```
{id, typ:"podstawowy|specjalistyczny", tekst, poprawna:"T|N|A|B|C",
 punkty:1|2|3, kategorie:[...], media, mediaTyp:"image|video",
 odpowiedzi:{A,B,C}  // tylko specjalistyczne
 tl:{en:{tekst,odpowiedzi}, de:{...}, ua:{...}}}
```

## Reguły egzaminu WORD (w app.js → EXAM)
- 20 podstawowych (T/N): rozkład pkt 10×3 + 6×2 + 4×1; czas 20s czytanie + 15s odp.
- 12 specjalistycznych (A/B/C): 6×3 + 4×2 + 2×1; czas 50s/pyt.
- Max **74 pkt**, próg zaliczenia **68 pkt**. Jednoprzebiegowy, bez powrotu.

## TODO / kolejne kroki
1. **Zdjęcia** — pobrać ZIP 8.8 GB, wyciągnąć tylko `.jpg` → `media/img/`
   (lekkie, hostujemy u siebie). Lista plików: `_src/media_list.json`.
2. **Filmy** — transkod `.wmv`→`mp4/webm` (ffmpeg), host zewnętrzny
   (R2 free / YouTube unlisted). 1103 pliki. Placeholder działa do tego czasu.
3. **Ranking/konta** — Firebase (wzorzec z ogarnijegzamin: `auth.js` +
   `firebase-config.js`). Osobny projekt Firebase.
4. Domena + GitHub Pages + Actions deploy.

## Zasady pracy
- Bez buildu — edytuj, commituj, gotowo.
- Nie pushuj na `main`/live bez zgody właściciela (gdy będzie repo/hosting).
- `data/*.json` generowane z ETL — nie edytuj ręcznie, zmień `etl.py`.

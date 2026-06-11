# -*- coding: utf-8 -*-
"""ETL: katalog.xlsx (oficjalna baza MI) -> data/pytania.json + per-kategoria.
Bez zaleznosci poza openpyxl. Uruchom: python etl.py
"""
import openpyxl, json, os, re, collections

SRC = "katalog.xlsx"
OUT_DIR = os.path.join("..", "data")
os.makedirs(OUT_DIR, exist_ok=True)

def norm_struktura(v):
    if not v: return None
    s = str(v).strip().lower()
    if s.startswith("podstaw"): return "podstawowy"
    # 'specjalistyczny','specajlistyczny' (literowka w zrodle)
    if s.startswith("spec") or "listyczny" in s: return "specjalistyczny"
    return None

def media_type(fn):
    if not fn: return None
    e = str(fn).rsplit(".", 1)[-1].lower()
    if e in ("wmv", "mp4", "webm", "avi"): return "video"
    if e in ("jpg", "jpeg", "png", "gif"): return "image"
    return None

def cell(v):
    if v is None: return ""
    return str(v).strip()

# --- klasyfikator dzialow tematycznych (heurystyka slow kluczowych) ---
# UWAGA: oficjalna baza MI nie ma podzialu tematycznego. Przypisanie auto.
# Kolejnosc = priorytet (pierwszy trafiony wygrywa).
DZIALY = [
    ("pierwsza-pomoc", "Pierwsza pomoc", [
        "apteczk","poszkodowan","krwotok","oddech","reanimac","resuscytac","rko",
        "przytomn","opatrun","zlaman","oparzen","wstrzas","tetno","masaz serca",
        "ratown","uciski","akcji serca","pozycji bocznej","defibrylat"]),
    ("stan-kierujacego", "Stan kierującego", [
        "alkohol","promil","trzezw","nietrzezw","srodk odurz","narkot","lek ",
        "zmecz","senno","pod wplywem","stanu po uzyciu"]),
    ("pierwszenstwo", "Pierwszeństwo i skrzyżowania", [
        "pierwszenstw","ustapi","skrzyzowan","rondo","podporzadkow","rownorzedn",
        "z prawej","z lewej","ustapienia pierwsz"]),
    ("znaki", "Znaki i sygnały", [
        "znak ","znaku","znaki","znakiem","tablic","sygnaliz","sygnal swietl",
        "sygnal nadawan","sygnalu","czerwone swiat","zielone swiat","nadawany przez"]),
    ("predkosc", "Prędkość i hamowanie", [
        "predkos","km/h","kilometr","droga hamowan","hamowan","droge zatrzyman",
        "dopuszczaln predk"]),
    ("manewry", "Manewry", [
        "wyprzedz","omijan","wymijan","zawracan","cofan","parkow","postoj",
        "zmiany pasa","wlaczan do ruchu","wlaczaniu sie","zatrzymani pojazd",
        "skret","skrec"]),
    ("pieszi-rowery", "Piesi, rowery, przejazdy", [
        "piesz","przejsci dla","rower","hulajn","dziec","przejazd kolej",
        "przejazdu kolej","tramwaj","autobus szkoln","kolumn pieszych"]),
    ("dokumenty", "Przepisy i dokumenty", [
        "dowod rejestr","ubezpiecz","polis","prawo jazdy","mandat","punkt karn",
        "badani techn","uprawnien","dokument","zarejestrowan","tablic rejestr"]),
    ("technika", "Technika i eksploatacja", [
        "silnik","hamulc","opon","oswietl","akumulat","plyn ","cisnien",
        "uklad kierown","zawiesz","pas bezpiecz","fotelik","gasnic","oponach"]),
    ("ekologia", "Ekologia i ekonomia jazdy", [
        "srodowisk","spalin","emisj","ekologi","zuzyci paliw","oszczedn"]),
]
def classify_dzial(tekst):
    t = tekst.lower()
    # uproszczone usuniecie polskich znakow do dopasowania
    repl = str.maketrans("ąćęłńóśżźĄĆĘŁŃÓŚŻŹ","acelnoszzACELNOSZZ")
    t = t.translate(repl)
    for slug, _name, kws in DZIALY:
        for kw in kws:
            if kw in t:
                return slug
    return "pozostale"
DZIAL_NAZWY = {slug:name for slug,name,_ in DZIALY}
DZIAL_NAZWY["pozostale"] = "Pozostałe przepisy"
DZIAL_ORDER = [s for s,_,_ in DZIALY] + ["pozostale"]

def main():
    wb = openpyxl.load_workbook(SRC, read_only=True)
    ws = wb["katalog"]
    rows = ws.iter_rows(min_row=2, values_only=True)
    questions = []
    seen_ids = set()
    skipped = 0
    dups = 0
    for r in rows:
        # kolumny: 0 Lp,1 Numer,2 Pytanie,3 A,4 B,5 C,6 Poprawna,7 Media,
        # 8 Zakres,9 Punkty,10 Kategorie, 11-14 PJM, 15-18 EN, 19-22 DE, 23-26 UA
        if r[0] is None and r[1] is None:
            skipped += 1; continue
        num = cell(r[1])
        pytanie = cell(r[2])
        if not num or not pytanie:
            skipped += 1; continue
        struktura = norm_struktura(r[8])
        if struktura is None:
            skipped += 1; continue
        correct_raw = cell(r[6]).upper()
        media = cell(r[7]) or None
        try:
            punkty = int(str(r[9]).strip())
        except (TypeError, ValueError):
            punkty = 1
        kategorie = [c.strip() for c in cell(r[10]).split(",") if c.strip() and c.strip() != "None"]

        q = {
            "id": int(num) if num.isdigit() else num,
            "typ": "podstawowy" if struktura == "podstawowy" else "specjalistyczny",
            "tekst": pytanie,
            "poprawna": correct_raw,            # 'T'/'N' (podstawowy) lub 'A'/'B'/'C'
            "punkty": punkty,
            "kategorie": kategorie,
            "media": media,
            "mediaTyp": media_type(media),
            "dzial": classify_dzial(pytanie),
        }
        if struktura == "specjalistyczny":
            q["odpowiedzi"] = {"A": cell(r[3]), "B": cell(r[4]), "C": cell(r[5])}
        # tlumaczenia
        tl = {}
        for lang, base in (("en", 15), ("de", 19), ("ua", 23)):
            t_q = cell(r[base])
            if not t_q:
                continue
            entry = {"tekst": t_q}
            if struktura == "specjalistyczny":
                entry["odpowiedzi"] = {"A": cell(r[base+1]), "B": cell(r[base+2]), "C": cell(r[base+3])}
            tl[lang] = entry
        if tl:
            q["tl"] = tl

        if q["id"] in seen_ids:
            dups += 1
        seen_ids.add(q["id"])
        questions.append(q)

    # zapis: pelna baza
    full_path = os.path.join(OUT_DIR, "pytania.json")
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, separators=(",", ":"))

    # zapis: per kategoria (lazy load)
    per_cat = collections.defaultdict(list)
    for q in questions:
        for c in q["kategorie"]:
            per_cat[c].append(q["id"])
    cat_dir = os.path.join(OUT_DIR, "kat")
    os.makedirs(cat_dir, exist_ok=True)
    index = {}
    for cat, ids in per_cat.items():
        safe = cat.replace("/", "_")
        sub = [q for q in questions if q["id"] in set(ids)]
        with open(os.path.join(cat_dir, f"{safe}.json"), "w", encoding="utf-8") as f:
            json.dump(sub, f, ensure_ascii=False, separators=(",", ":"))
        pod = sum(1 for q in sub if q["typ"] == "podstawowy")
        spec = len(sub) - pod
        dz = collections.Counter(q["dzial"] for q in sub)
        dzialy = [{"slug": s, "nazwa": DZIAL_NAZWY[s], "liczba": dz[s]}
                  for s in DZIAL_ORDER if dz[s] > 0]
        index[cat] = {"plik": f"kat/{safe}.json", "razem": len(sub),
                      "podstawowe": pod, "specjalistyczne": spec, "dzialy": dzialy}

    with open(os.path.join(OUT_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"kategorie": index, "razem": len(questions),
                   "dzialNazwy": DZIAL_NAZWY}, f, ensure_ascii=False, indent=1)

    # raport pokrycia dzialow
    glob_dz = collections.Counter(q["dzial"] for q in questions)
    print("  DZIALY (globalnie):")
    for s in DZIAL_ORDER:
        if glob_dz[s]:
            print(f"    {DZIAL_NAZWY[s]:<32} {glob_dz[s]:>5}  ({glob_dz[s]*100//len(questions)}%)")

    # raport
    media_imgs = sorted({q["media"] for q in questions if q["mediaTyp"] == "image"})
    media_vids = sorted({q["media"] for q in questions if q["mediaTyp"] == "video"})
    with open("media_list.json", "w", encoding="utf-8") as f:
        json.dump({"obrazy": media_imgs, "filmy": media_vids}, f, ensure_ascii=False, indent=1)

    print(f"OK pytan={len(questions)} pominieto={skipped} duplikaty_id={dups}")
    print(f"  obrazy_unikalne={len(media_imgs)} filmy_unikalne={len(media_vids)}")
    print(f"  kategorie={len(index)}")
    print("  per-kat:", {k: v["razem"] for k, v in sorted(index.items())})

if __name__ == "__main__":
    main()

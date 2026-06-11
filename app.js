/* ogarnijprawko — silnik aplikacji (bez buildu, vanilla JS)
   Dane: data/index.json + data/kat/<KAT>.json  (ETL z oficjalnej bazy MI)
*/
"use strict";

const BRAND = "ogarnijprawko";

const APP = {
  lang: localStorage.getItem("pt_lang") || "pl",
  cats: null,          // index.json -> kategorie
  cache: {},           // kat -> [pytania]
};

/* ============ DOSTĘP / PAYWALL ============
   Model: DEMO darmo (kat B + 1 dział, tylko nauka). Reszta = 25 zł lifetime.
   Stan 'paid' trzymany w localStorage; docelowo nadpisywany przez Firebase. */
const ACCESS = {
  cena: 25,
  freeKat: "B",
  freeDzial: "znaki",       // jedyny darmowy dział w demo
};
function isPaid(){ return localStorage.getItem("op_paid") === "1"; }
function setPaid(v){ v ? localStorage.setItem("op_paid","1") : localStorage.removeItem("op_paid"); }
function canKat(kat){ return isPaid() || kat === ACCESS.freeKat; }
function canDzial(kat, dzial){ return isPaid() || (kat===ACCESS.freeKat && dzial===ACCESS.freeDzial); }
function canTryb(tryb){ return isPaid() || tryb === "nauka"; }  // egzamin/word tylko paid
/* przekierowanie na paywall jeśli brak dostępu; zwraca true gdy zablokowano */
function gate(ok, powod){
  if(ok) return false;
  location.href = "cennik.html" + (powod ? "?powod="+encodeURIComponent(powod) : "");
  return true;
}

/* ---- metadane kategorii (opis PL) ---- */
const CAT_META = {
  AM:{n:"Motorower, czterokołowiec lekki"},
  A1:{n:"Motocykl do 125 cm³"},
  A2:{n:"Motocykl do 35 kW"},
  A:{n:"Motocykl bez ograniczeń"},
  B1:{n:"Czterokołowiec"},
  B:{n:"Samochód osobowy"},
  C1:{n:"Samochód ciężarowy do 7,5 t"},
  C:{n:"Samochód ciężarowy"},
  D1:{n:"Autobus do 17 osób"},
  D:{n:"Autobus"},
  T:{n:"Ciągnik rolniczy"},
  PT:{n:"Tramwaj"},
};
const CAT_ORDER = ["B","A","A1","A2","AM","B1","C","C1","D","D1","T","PT"];

/* ---- WORD: budowa egzaminu ---- */
const EXAM = {
  podstawowe:{ liczba:20, rozklad:{3:10,2:6,1:4}, czas:{czytanie:20, odpowiedz:15} },
  specjalistyczne:{ liczba:12, rozklad:{3:6,2:4,1:2}, czas:50 },
  maxPkt:74, prog:68,
};

/* ---- i18n etykiet UI ---- */
const I18N = {
  pl:{tak:"TAK",nie:"NIE",dalej:"Dalej",sprawdz:"Sprawdź",zakoncz:"Zakończ egzamin",
      pyt:"Pytanie",pkt:"pkt",czas:"Czas",wynik:"Wynik",zdane:"ZDANE",niezdane:"NIEZDANE",
      jeszczeRaz:"Jeszcze raz",doStart:"Strona główna",ladowanie:"Ładowanie pytań…",
      filmWkrotce:"▶ Materiał wideo — wersja online wkrótce",odpA:"A",poprawna:"Poprawna odpowiedź"},
  en:{tak:"YES",nie:"NO",dalej:"Next",sprawdz:"Check",zakoncz:"Finish exam",
      pyt:"Question",pkt:"pts",czas:"Time",wynik:"Score",zdane:"PASSED",niezdane:"FAILED",
      jeszczeRaz:"Again",doStart:"Home",ladowanie:"Loading…",
      filmWkrotce:"▶ Video — online version coming soon",odpA:"A",poprawna:"Correct answer"},
  de:{tak:"JA",nie:"NEIN",dalej:"Weiter",sprawdz:"Prüfen",zakoncz:"Prüfung beenden",
      pyt:"Frage",pkt:"Pkt",czas:"Zeit",wynik:"Ergebnis",zdane:"BESTANDEN",niezdane:"NICHT BESTANDEN",
      jeszczeRaz:"Nochmal",doStart:"Start",ladowanie:"Laden…",
      filmWkrotce:"▶ Video — Online-Version bald",odpA:"A",poprawna:"Richtige Antwort"},
  ua:{tak:"ТАК",nie:"НІ",dalej:"Далі",sprawdz:"Перевірити",zakoncz:"Завершити",
      pyt:"Питання",pkt:"б",czas:"Час",wynik:"Результат",zdane:"СКЛАДЕНО",niezdane:"НЕ СКЛАДЕНО",
      jeszczeRaz:"Ще раз",doStart:"Головна",ladowanie:"Завантаження…",
      filmWkrotce:"▶ Відео — онлайн-версія незабаром",odpA:"A",poprawna:"Правильна відповідь"},
};
const t = k => (I18N[APP.lang]||I18N.pl)[k] || I18N.pl[k] || k;

/* ---- ładowanie danych ---- */
async function loadIndex(){
  if(APP.cats) return APP.cats;
  const r = await fetch("data/index.json");
  const j = await r.json();
  APP.cats = j;
  return j;
}
async function loadKat(kat){
  if(APP.cache[kat]) return APP.cache[kat];
  const meta = APP.cats.kategorie[kat];
  if(!meta) throw new Error("Brak kategorii "+kat);
  const r = await fetch("data/"+meta.plik);
  const j = await r.json();
  APP.cache[kat] = j;
  return j;
}

/* ---- lokalizacja treści pytania ---- */
function locQ(q){
  if(APP.lang==="pl" || !q.tl || !q.tl[APP.lang])
    return { tekst:q.tekst, odp:q.odpowiedzi };
  const tl = q.tl[APP.lang];
  return { tekst:tl.tekst||q.tekst, odp:tl.odpowiedzi||q.odpowiedzi };
}

/* ---- ścieżki mediów ---- */
function mediaHtml(q){
  if(!q.media) return "";
  if(q.mediaTyp==="image"){
    const base = q.media.replace(/\.(jpe?g|png|gif)$/i,"");
    return `<div class="qmedia"><img loading="lazy" alt=""
      src="media/img/${encodeURIComponent(q.media)}"
      onerror="this.onerror=null;this.parentElement.innerHTML='<div class=&quot;muted&quot; style=&quot;padding:30px&quot;>🖼️ ${base}</div>'"><span class="wm-top"></span></div>`;
  }
  // wideo: .wmv nie gra w przeglądarce — placeholder do czasu transkodu
  return `<div class="qmedia"><div class="muted center" style="padding:40px 20px">${t("filmWkrotce")}</div></div>`;
}

/* ---- losowanie ---- */
function shuffle(a){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}

function pickByPoints(pool, rozklad){
  const out=[]; const used=new Set();
  const byPts={1:[],2:[],3:[]};
  shuffle(pool.slice()).forEach(q=>{ if(byPts[q.punkty]) byPts[q.punkty].push(q); });
  for(const p of [3,2,1]){
    let need = rozklad[p]||0;
    while(need>0 && byPts[p].length){ const q=byPts[p].pop(); if(!used.has(q.id)){out.push(q);used.add(q.id);need--;} }
  }
  // dopełnij brakujące z dowolnej puli
  const total = Object.values(rozklad).reduce((a,b)=>a+b,0);
  if(out.length<total){
    for(const q of shuffle(pool.slice())){ if(out.length>=total) break; if(!used.has(q.id)){out.push(q);used.add(q.id);} }
  }
  return out;
}

/* ---- budowa egzaminu WORD ---- */
function buildExam(pytania){
  const pod = pytania.filter(q=>q.typ==="podstawowy");
  const spec = pytania.filter(q=>q.typ==="specjalistyczny");
  const a = pickByPoints(pod, EXAM.podstawowe.rozklad);
  const b = pickByPoints(spec, EXAM.specjalistyczne.rozklad);
  return a.concat(b); // kolejność WORD: najpierw podstawowe, potem specjalistyczne
}

/* ---- helpers UI ---- */
function langSwitch(onChange){
  const langs=["pl","en","de","ua"];
  const wrap=document.createElement("div"); wrap.className="lang";
  langs.forEach(l=>{
    const b=document.createElement("button"); b.textContent=l.toUpperCase();
    if(l===APP.lang) b.classList.add("on");
    b.onclick=()=>{APP.lang=l;localStorage.setItem("pt_lang",l);onChange&&onChange();};
    wrap.appendChild(b);
  });
  return wrap;
}
function qs(name){return new URLSearchParams(location.search).get(name);}
function fmtTime(s){const m=Math.floor(s/60),x=s%60;return m+":"+String(x).padStart(2,"0");}

window.APP=APP;
window.PT={loadIndex,loadKat,buildExam,locQ,mediaHtml,langSwitch,qs,fmtTime,shuffle,t,
  CAT_META,CAT_ORDER,EXAM,BRAND,ACCESS,
  isPaid,setPaid,canKat,canDzial,canTryb,gate};

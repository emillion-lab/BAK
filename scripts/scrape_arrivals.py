#!/usr/bin/env python3
"""ЦАС scraper v2 — пристигащи автобуси от centralnaavtogara.bg.
v2: валидация на часове (мин<60 — 15.80 е цена, не час), филтър на dropdown боклук,
опит за отделна страница 'Международни' с принудително intl=True.
Защитен: <3 реда -> НЕ презаписва последния добър файл."""
import urllib.request, json, re, sys
from datetime import datetime, timedelta, timezone
from html import unescape

BASE = "https://www.centralnaavtogara.bg/"
OUT = "bus-arrivals.json"
SOFIA = timezone(timedelta(hours=3))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36",
      "Accept-Language": "bg-BG,bg;q=0.9"}

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    for enc in ("utf-8", "windows-1251"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")

def find_tab_url(home_html, word):
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>([^<]*' + word + r'[^<]*)</a>', home_html, re.I):
        return m.group(1)
    for m in re.finditer(r'href="([^"]*)"[^>]*>\s*' + word, home_html, re.I):
        return m.group(1)
    return None

def absolute(url):
    if not url.startswith("http"):
        url = BASE.rstrip("/") + "/" + url.lstrip("/")
    return url

def clean(s):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def valid_time(c):
    m = re.fullmatch(r"(\d{1,2})[:.](\d{2})", c)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:   # 15.80 / 18.80 са цени в лева, не часове
        return None
    return f"{h:02d}:{mi:02d}"

BAD_ORIGIN = re.compile(r"изберете|спирка\s*-+|^-+|направление|дата|час[аъ]?т?\s*$", re.I)

INTL = ("СКОПИЕ","КИШИНЕВ","БЕЛГРАД","НИШ","СОЛУН","ИСТАНБУЛ","ОДРИН","АТИНА","БУКУРЕЩ",
        "ВИЕНА","ПАРИЖ","БЕРЛИН","МЮНХЕН","ПРАГА","БУДАПЕЩА","ЦЮРИХ","АМСТЕРДАМ","ЛОНДОН",
        "ОХРИД","БИТОЛЯ","ПРИЩИНА","ТИРАНА","ПОДГОРИЦА","ЗАГРЕБ","ЛЮБЛЯНА","БРАТИСЛАВА",
        "РИМ","МИЛАНО","МАДРИД","БРЮКСЕЛ","КИЕВ","ОДЕСА","ЛВОВ","ВАРШАВА","КРАКОВ",
        "ХАСКЬОЙ","ЧОРЛУ","АНКАРА","БУРСА","СТРУМИЦА","ГЕВГЕЛИ","КАВАЛА","ДРАМА","КСАНТИ")

def parse_rows(html, force_intl=False):
    arrivals = []
    # режем form/select блоковете преди парсване — там живее dropdown боклукът
    html = re.sub(r"<select\b.*?</select>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<option\b[^>]*>.*?</option>", " ", html, flags=re.S | re.I)
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL | re.IGNORECASE):
        cells = [clean(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.DOTALL | re.IGNORECASE)]
        cells = [c for c in cells if c]
        if len(cells) < 2:
            continue
        t = None
        for c in cells:
            t = valid_time(c)
            if t:
                time_cell = c
                break
        if not t:
            m = re.search(r"\b(\d{1,2}:\d{2})\b", " ".join(cells))
            if not m:
                continue
            t = valid_time(m.group(1))
            if not t:
                continue
            time_cell = m.group(1)
        others = [c for c in cells if time_cell not in c]
        if not others:
            continue
        sector = next((c for c in others if re.fullmatch(r"(?:[Сс]ектор\s*)?\d{1,2}", c) or re.match(r"[Сс]ектор", c)), None)
        rest = [c for c in others if c != sector]
        cyr = [c for c in rest
               if re.search(r"[А-Яа-я]", c) and 3 <= len(c) <= 45
               and not re.match(r"[Сс]ектор", c) and not BAD_ORIGIN.search(c)]
        if not cyr:
            continue
        origin = max(cyr, key=len)
        operator = next((c for c in rest if c != origin and re.search(r"[А-Яа-яA-Za-z]{3}", c)), None)
        intl = force_intl or any(k in origin.upper() for k in INTL)
        sec = ""
        if sector:
            m = re.search(r"\d{1,2}", sector)
            sec = m.group(0) if m else ""
        arrivals.append({"time": t, "from": origin[:60], "sector": sec,
                         "operator": (operator or "")[:60], "intl": intl})
    seen, out = set(), []
    for a in arrivals:
        key = (a["time"], a["from"], a.get("sector", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out

def main():
    now = datetime.now(SOFIA)
    home = fetch(BASE)

    best = []
    url = find_tab_url(home, r"[Пп]ристигащ")
    print("arrivals url:", url)
    candidates = []
    if url:
        url = absolute(url)
        candidates += [url + ("&" if "?" in url else "?") + "t=8", url]
    candidates += [BASE + "index.php?d=a&t=8", BASE + "index.php?d=p&t=8"]
    for c in candidates:
        try:
            rows = parse_rows(fetch(c))
        except Exception as e:
            print("  fail:", c[:80], e); continue
        print(f"  {c[:80]} → {len(rows)} rows")
        if len(rows) > len(best):
            best = rows
        if len(best) >= 5:
            break

    # отделна страница 'Международни' (ако има) -> intl=True принудително
    iurl = find_tab_url(home, r"[Мм]еждународ")
    print("intl url:", iurl)
    if iurl:
        try:
            irows = parse_rows(fetch(absolute(iurl)), force_intl=True)
            print(f"  intl → {len(irows)} rows")
            have = {(a['time'], a['from']) for a in best}
            for a in irows:
                if (a['time'], a['from']) not in have:
                    best.append(a)
        except Exception as e:
            print("  intl fail:", e)

    if len(best) < 3:
        print("⚠️ Парсирането върна твърде малко редове — запазвам последния добър файл.")
        sys.exit(0)

    json.dump({
        "updated": now.isoformat(),
        "source": "centralnaavtogara.bg",
        "window_hours": 8,
        "count": len(best),
        "intl_count": sum(1 for a in best if a["intl"]),
        "arrivals": sorted(best, key=lambda a: a["time"]),
    }, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"OK: {len(best)} пристигащи ({sum(1 for a in best if a['intl'])} международни).")

if __name__ == "__main__":
    main()

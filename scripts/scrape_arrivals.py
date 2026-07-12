#!/usr/bin/env python3
"""ЦАС scraper — пристигащи автобуси от centralnaavtogara.bg.
Пише bus-arrivals.json: [{time, from, operator}] за следващите N часа.
Защитен: ако парсирането върне <3 реда, НЕ презаписва последния добър файл.
"""
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

def find_arrivals_url(home_html):
    """Намери линка на таб 'Пристигащи' — динамично, за да не зависим от mod-хеша."""
    # href="...">Пристигащи<  или  Пристигащи в <a href=...>
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>([^<]*[Пп]ристигащ[^<]*)</a>', home_html):
        return m.group(1)
    for m in re.finditer(r'href="([^"]*)"[^>]*>\s*[Пп]ристигащи', home_html):
        return m.group(1)
    return None

def clean(s):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def parse_rows(html):
    """Извлича редове (час, откъде, превозвач) от таблиците на ЦАС."""
    arrivals = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL | re.IGNORECASE):
        cells = [clean(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.DOTALL | re.IGNORECASE)]
        cells = [c for c in cells if c]
        if len(cells) < 2:
            continue
        # намери клетка с час HH:MM
        time_cell = next((c for c in cells if re.fullmatch(r"\d{1,2}[:.]\d{2}", c)), None)
        if not time_cell:
            # понякога часът е вътре в текст
            m = re.search(r"\b(\d{1,2}[:.]\d{2})\b", " ".join(cells))
            if not m:
                continue
            time_cell = m.group(1)
        t = time_cell.replace(".", ":").zfill(5)
        others = [c for c in cells if time_cell not in c]
        if not others:
            continue
        # секторът е мястото на слизане — отделно поле, НЕ направление
        sector = next((c for c in others if re.fullmatch(r"(?:[Сс]ектор\s*)?\d{1,2}", c) or re.match(r"[Сс]ектор", c)), None)
        rest = [c for c in others if c != sector]
        # направление: най-дългата кирилска клетка от останалите
        cyr = [c for c in rest if re.search(r"[А-Яа-я]", c) and len(c) >= 3 and not re.match(r"[Сс]ектор", c)]
        if not cyr:
            continue
        origin = max(cyr, key=len)
        operator = next((c for c in rest if c != origin and re.search(r"[А-Яа-яA-Za-z]{3}", c)), None)
        INTL = ("СКОПИЕ","КИШИНЕВ","БЕЛГРАД","НИШ","СОЛУН","ИСТАНБУЛ","ОДРИН","АТИНА","БУКУРЕЩ",
                "ВИЕНА","ПАРИЖ","БЕРЛИН","МЮНХЕН","ПРАГА","БУДАПЕЩА","ЦЮРИХ","АМСТЕРДАМ","ЛОНДОН",
                "ОХРИД","БИТОЛЯ","ПРИЩИНА","ТИРАНА","ПОДГОРИЦА","ЗАГРЕБ","ЛЮБЛЯНА","БРАТИСЛАВА","РИМ","МИЛАНО","МАДРИД","БРЮКСЕЛ",
                "КИЕВ","ОДЕСА","ЛВОВ","ВАРШАВА","КРАКОВ","ХАСКЬОЙ","ЧОРЛУ","АНКАРА","БУРСА")
        intl = any(k in origin.upper() for k in INTL)
        sec = ""
        if sector:
            m = re.search(r"\d{1,2}", sector)
            sec = m.group(0) if m else ""
        arrivals.append({"time": t, "from": origin[:60], "sector": sec, "operator": (operator or "")[:60], "intl": intl})
    # дедуп
    seen, out = set(), []
    for a in arrivals:
        key = (a["time"], a["from"], a.get("sector",""))
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out

def main():
    now = datetime.now(SOFIA)
    home = fetch(BASE)
    url = find_arrivals_url(home)
    print("arrivals url:", url)
    candidates = []
    if url:
        if not url.startswith("http"):
            url = BASE.rstrip("/") + "/" + url.lstrip("/")
        candidates += [url + ("&" if "?" in url else "?") + "t=8", url]
    # fallback: пробвай познати параметри
    candidates += [BASE + "index.php?d=a&t=8", BASE + "index.php?d=p&t=8"]

    best = []
    for c in candidates:
        try:
            html = fetch(c)
        except Exception as e:
            print("  fail:", c[:80], e)
            continue
        rows = parse_rows(html)
        print(f"  {c[:80]} → {len(rows)} rows")
        if len(rows) > len(best):
            best = rows
        if len(best) >= 5:
            break

    if len(best) < 3:
        print("⚠️ Парсирането върна твърде малко редове — запазвам последния добър файл.")
        sys.exit(0)

    json.dump({
        "updated": now.isoformat(),
        "source": "centralnaavtogara.bg",
        "window_hours": 8,
        "count": len(best),
        "arrivals": sorted(best, key=lambda a: a["time"]),
    }, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"OK: {len(best)} пристигащи записани.")

if __name__ == "__main__":
    main()

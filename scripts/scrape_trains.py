#!/usr/bin/env python3
"""БДЖ live scraper — пристигащи влакове на София Централна от live.bdz.bg.
Пише train-arrivals.json + debug/bdz_live.html при провал (за да не гадаем).
Класификация по такси-потенциал: далечни (багаж) > регионални > крайградски."""
import urllib.request, urllib.parse, json, re, ssl, sys, os
from datetime import datetime, timedelta, timezone
from html import unescape

OUT = "train-arrivals.json"
SOFIA = timezone(timedelta(hours=3))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
      "Accept-Language": "bg-BG,bg;q=0.9,en;q=0.8",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
PROXY = "https://mvr-proxy.mihov-emil.workers.dev/scrape?url="
INSECURE = ssl._create_unverified_context()

FAR = ("БУРГАС", "BURGAS", "ВАРНА", "VARNA", "ПЛОВДИВ", "PLOVDIV", "РУСЕ", "RUSE",
       "ГОРНА", "GORNA", "ВИДИН", "VIDIN", "ШУМЕН", "SHUMEN", "СТАРА", "STARA",
       "КАРЛОВО", "KARLOVO", "СЛИВЕН", "SLIVEN", "ТЪРНОВО", "TARNOVO",
       "ДОБРИЧ", "DOBRICH", "СИЛИСТРА", "SILISTRA", "КУЛАТА", "KULATA",
       "ПЕТРИЧ", "PETRICH", "БЛАГОЕВГРАД", "BLAGOEVGRAD", "ДИМИТРОВГРАД", "DIMITROVGRAD")
NEAR = ("ПЕРНИК", "PERNIK", "СЛИВНИЦА", "SLIVNICA", "SLIVNITSA", "КОСТИНБРОД", "KOSTINBROD",
        "СОФИЯ-СЕВЕР", "SOFIA-SEVER", "ЛАКАТНИК", "LAKATNIK", "КОСТЕНЕЦ", "KOSTENEC",
        "ДОЛНО", "DOLNO", "ЕЛИН", "ELIN", "ИСКЪР", "ISKAR")

BG = {"Burgas": "Бургас", "Varna": "Варна", "Plovdiv": "Пловдив", "Ruse": "Русе",
      "Pernik": "Перник", "Blagoevgrad": "Благоевград", "Petrich": "Петрич",
      "Karlovo": "Карлово", "Vraca": "Враца", "Vratsa": "Враца", "Slivnica": "Сливница",
      "Kostinbrod": "Костинброд", "Kostenec": "Костенец", "Lakatnik": "Лакатник",
      "Sofia-Sever": "София-Север", "Dimitrovgrad": "Димитровград",
      "Dolno Kamarci": "Долно Камарци", "Vidin": "Видин", "Shumen": "Шумен",
      "Gorna Oryahovica": "Горна Оряховица", "Stara Zagora": "Стара Загора",
      "Sliven": "Сливен", "Dobrich": "Добрич", "Silistra": "Силистра", "Kulata": "Кулата"}


def fetch(url, timeout=25):
    last = "no attempt"
    for tag, tgt, ctx in (("direct", url, None), ("insecure", url, INSECURE),
                          ("proxy", PROXY + urllib.parse.quote(url, safe=""), None)):
        try:
            with urllib.request.urlopen(urllib.request.Request(tgt, headers=UA),
                                        timeout=timeout, context=ctx) as r:
                b = r.read()
            head = b[:3000].decode("ascii", "ignore").lower()
            if "1251" in head:
                body = b.decode("cp1251", "ignore")
            else:
                try:
                    body = b.decode("utf-8")
                except UnicodeDecodeError:
                    body = b.decode("cp1251", "ignore")
            print("  fetch %s via %s -> %db" % (url, tag, len(body)))
            return body
        except Exception as e:
            last = repr(e)[:140]
    print("  fetch FAIL %s :: %s" % (url, last))
    return None


def clean(s):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def classify(origin, code):
    o = (origin or "").upper()
    kind = (re.match(r"([A-ZА-Я]+)", (code or "").strip()) or [""])[0]
    if any(k in o for k in NEAR):
        return "near", 0.35
    if any(k in o for k in FAR):
        return "far", 1.0
    if kind in ("ICF", "IC", "БВ", "EN", "MBV"):
        return "far", 0.85
    if kind in ("REG", "PV", "ПВ"):
        return "mid", 0.55
    return "mid", 0.5


def parse(html):
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        cells = [clean(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
        cells = [c for c in cells if c]
        if len(cells) < 2:
            continue
        t = next((c for c in cells if re.fullmatch(r"\d{1,2}:\d{2}", c)), None)
        if not t:
            continue
        code = next((c for c in cells if re.fullmatch(r"[A-ZА-Я]{2,4}\s*\d{3,6}", c)), "")
        origin = next((c for c in cells
                       if c != t and c != code and len(c) >= 3
                       and not re.fullmatch(r"[\d\s:.]+", c)
                       and not re.match(r"(?i)delay|закъсн|перон|platform|коловоз", c)), "")
        delay = 0
        dm = re.search(r"(?:Delay|[Зз]акъсн\w*)\D{0,12}(\d{1,3})", tr)
        if dm:
            delay = int(dm.group(1))
        if origin:
            rows.append((t, origin, code, delay))
    print("    таблица: %d реда" % len(rows))

    if len(rows) < 3:
        txt = clean(html)
        for m in re.finditer(r"(\d{1,2}:\d{2})\s+([A-Za-zА-Яа-я\-\.\s]{3,28}?)\s+([A-ZА-Я]{2,4}\s?\d{3,6})", txt):
            t, origin, code = m.group(1), m.group(2).strip(), m.group(3)
            tail = txt[m.end():m.end() + 40]
            dm = re.search(r"(?:Delay|[Зз]акъсн\w*)\D{0,12}(\d{1,3})", tail)
            rows.append((t, origin, code, int(dm.group(1)) if dm else 0))
        print("    текстов fallback: общо %d реда" % len(rows))

    out, seen = [], set()
    for t, origin, code, delay in rows:
        h, mi = t.split(":")
        if int(h) > 23 or int(mi) > 59:
            continue
        t = "%02d:%s" % (int(h), mi)
        key = (t, origin)
        if key in seen:
            continue
        seen.add(key)
        origin_bg = BG.get(origin, origin)
        tier, weight = classify(origin_bg, code)
        out.append({"time": t, "from": origin_bg[:40], "train": re.sub(r"\s+", " ", code),
                    "delay": delay, "tier": tier, "weight": weight})
    return out


def main():
    now = datetime.now(SOFIA)
    best, dumps = [], []
    for url in ("https://live.bdz.bg/", "https://live.bdz.bg/en"):
        html = fetch(url)
        if not html:
            continue
        dumps.append((url, html))
        rows = parse(html)
        print("  %s -> %d влака" % (url, len(rows)))
        if len(rows) > len(best):
            best = rows
        if len(best) >= 8:
            break

    if len(best) < 3:
        os.makedirs("debug", exist_ok=True)
        for i, (url, html) in enumerate(dumps):
            slim = re.sub(r"<script\b.*?</script>", "<!--s-->", html, flags=re.S | re.I)
            slim = re.sub(r"<style\b.*?</style>", "<!--c-->", slim, flags=re.S | re.I)
            open("debug/bdz_live_%d.html" % i, "w", encoding="utf-8").write(slim[:60000])
        open("debug/bdz-parse-report.txt", "w", encoding="utf-8").write(
            "провал: %d реда · опитани: %s\n" % (len(best), [u for u, _ in dumps]))
        print("⚠️ Твърде малко редове — дъмпнах HTML в debug/, пазя стария файл.")
        sys.exit(0)

    best.sort(key=lambda r: r["time"])
    json.dump({
        "updated": now.isoformat(),
        "source": "live.bdz.bg",
        "station": "София Централна",
        "count": len(best),
        "far_count": sum(1 for r in best if r["tier"] == "far"),
        "arrivals": best,
    }, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("OK: %d влака (%d далечни)." % (len(best), sum(1 for r in best if r["tier"] == "far")))


if __name__ == "__main__":
    main()

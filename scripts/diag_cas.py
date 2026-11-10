#!/usr/bin/env python3
"""Еднократна проба (10.11.2026): структурата на новия centralnaavtogara.bg.

Старият парсър търси <tr>/<td>; новият сайт показва пристигащите като
блокове на /avtobusi?date=DD.MM.YYYY&hours=8. Пишем само откъс около
първите записи — колкото да се види разметката, не цялата страница.
"""
import urllib.request, re
from datetime import datetime, timedelta, timezone

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36",
      "Accept-Language": "bg-BG,bg;q=0.9"}
d = datetime.now(timezone(timedelta(hours=2))).strftime("%d.%m.%Y")
out = []
for url in (f"https://www.centralnaavtogara.bg/avtobusi?date={d}&hours=8",
            "https://www.centralnaavtogara.bg/avtobusi"):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "replace")
            status = r.status
    except Exception as e:
        out.append(f"== {url}\nГРЕШКА: {e}\n")
        continue
    out.append(f"== {url}\nHTTP {status}, {len(html)} знака")
    out.append(f"брой 'Пристига': {html.count('Пристига')}, '<tr': {html.lower().count('<tr')}, "
               f"'Сектор': {html.count('Сектор')}, '/schedule/': {html.count('/schedule/')}")
    i = html.find("/schedule/")
    if i < 0:
        out.append("няма 'Пристига' в HTML — вероятно се зарежда с JS")
        for m in re.finditer(r'(fetch\(|axios|/api/[^"\' ]+|data-url="[^"]+")', html):
            out.append("JS/API следа: " + html[max(0, m.start()-80):m.end()+120].replace("\n", " "))
        continue
    # назад до началото на блока, напред ~3 записа
    start = max(0, i - 2500)
    out.append("--- суров откъс около първия /schedule/ ---")
    out.append(html[start:i + 6000])
    break

open("debug/cas-probe.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out)[:3000])

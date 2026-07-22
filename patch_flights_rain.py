# -*- coding: utf-8 -*-
"""v2: Шенген/не-Шенген изходни прозорци в exit-now панела.
🇪🇺 Шенген: кацане +10–30 мин · 🛂 не-Шенген: +20–50 мин (паспортен контрол).
Целеви замени в append-натия блок + node --check + cache-bust."""
import re, subprocess, shutil

rep = []
src = open('app.js', encoding='utf-8').read()

if 'exit-now-v2' in src:
    rep.append('SKIP v2 вече е приложен')
elif 'exit-now-panel' not in src:
    rep.append('FAIL v1 блокът липсва — няма върху какво да патчна')
else:
    NS_RE = ("var NS=/(лондон|london|luton|stansted|manchester|edinburgh|birmingham|bristol|"
             "liverpool|glasgow|leeds|дъблин|dublin|истанбул|istanbul|sabiha|анталия|antalya|"
             "tel aviv|тел авив|dubai|дубай|abu dhabi|doha|доха|cairo|кайро|hurghada|хургада|"
             "sharm|шарм|belgrade|белград|skopje|скопие|chisinau|кишинев|tbilisi|тбилиси|"
             "kutaisi|кутаиси|yerevan|ереван|baku|баку|larnaca|ларнака|paphos|пафос|amman|"
             "аман|jeddah|riyadh|new york|ню йорк|kuwait|beirut|бейрут|tirana|тирана|"
             "podgorica|подгорица|sarajevo|сараево|amman)/i;"
             "var nonsch=NS.test((f.departure&&f.departure.airport)||'');"
             "var xs=lt+(nonsch?20:10)*60000, xe=lt+(nonsch?50:30)*60000;")
    repl = [
        ("var xs=lt+15*60000, xe=lt+40*60000;", NS_RE),
        ("term:a.terminal||'', st:f.flight_status}",
         "term:a.terminal||'', st:f.flight_status, ns:nonsch}"),
        ("'<b>ИЗЛИЗАТ СЕГА</b> · '+f.from+",
         "'<b>ИЗЛИЗАТ СЕГА</b> '+(f.ns?'🛂':'🇪🇺')+' · '+f.from+"),
        ("Изход = кацане +15–40 мин",
         "🇪🇺 Шенген: изход +10–30 мин · 🛂 не-Шенген: +20–50 мин"),
        ("// exit-now-panel", "// exit-now-panel exit-now-v2"),
    ]
    cand = src
    ok = True
    for old, new in repl:
        if cand.count(old) != 1:
            rep.append(f'FAIL replace count={cand.count(old)} за: {old[:50]}')
            ok = False
            break
        cand = cand.replace(old, new)
    if ok:
        open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
        r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
        if r.returncode == 0:
            shutil.move('/tmp/app.c.js', 'app.js')
            idx = open('index.html', encoding='utf-8').read()
            idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260722sg', idx)
            open('index.html', 'w', encoding='utf-8').write(idx)
            rep.append('OK Шенген v2 + node --check + cache-bust sg')
        else:
            rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

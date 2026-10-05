#!/usr/bin/env python3
"""Полети, част 2: живият отговор понякога носи само утрешния 12-часов
прозорец → допълваме от кеша; и разделител „УТРЕ“, за да не се бъркат дните.
Идемпотентен."""
import sys

EDITS = [
 ('сливане жив + кеш',
  "      window.__flightSource = 'живо · ' + data.data.length;\n      processFlights(data);",
  "      // Живият отговор понякога носи само единия 12-часов прозорец (утрешния).\n"
  "      // Допълваме дупките от кеша; ключ = номер + местна дата, защото\n"
  "      // ежедневните полети имат един и същ номер днес и утре.\n"
  "      return fetch('flight-cache.json?v='+Date.now())\n"
  "        .then(function(r){ return r.ok ? r.json() : null; })\n"
  "        .catch(function(){ return null; })\n"
  "        .then(function(cache){\n"
  "          var key = function(f){ return ((f.flight&&f.flight.iata)||'') + '|' + String((f.arrival&&f.arrival.scheduled)||'').slice(0,10); };\n"
  "          var seen = {}, liveN = data.data.length, added = 0;\n"
  "          data.data.forEach(function(f){ seen[key(f)] = 1; });\n"
  "          ((cache && cache.data) || []).forEach(function(f){\n"
  "            var k = key(f); if(seen[k] || !(f.flight&&f.flight.iata)) return;\n"
  "            seen[k] = 1; data.data.push(f); added++;\n"
  "          });\n"
  "          window.__flightSource = 'живо · ' + liveN + (added ? ' + кеш ' + added : '');\n"
  "          processFlights(data);\n"
  "        });",
  "+ кеш ' + added"),
 ('променлива за деня',
  "    let lastHour = -1;",
  "    let lastHour = -1, lastDay = null;\n"
  "    const _today = Math.floor((Date.now()+3*3600000)/86400000);",
  "lastDay = null"),
 ('разделител УТРЕ',
  "      if(f.exitFromH !== lastHour){",
  "      const _day = Math.floor((f.exitFromTs+3*3600000)/86400000);\n"
  "      if(_day !== lastDay){\n"
  "        if(lastDay !== null || _day !== _today){\n"
  "          const _lbl = _day===_today ? 'ДНЕС' : _day===_today+1 ? 'УТРЕ' : new Date(f.exitFromTs).toLocaleDateString('bg',{day:'numeric',month:'short'});\n"
  "          html+=`<div style=\"font-size:12px;font-weight:900;color:var(--cyan);margin:12px 0 4px;padding:4px 8px;border-top:2px solid var(--cyan);letter-spacing:.5px\">${_lbl}</div>`;\n"
  "        }\n"
  "        lastDay = _day; lastHour = -1;\n"
  "      }\n"
  "      if(f.exitFromH !== lastHour){",
  "const _day = Math.floor"),
]

s = open('app.js', encoding='utf-8').read(); log = []
for name, old, new, marker in EDITS:
    if marker in s: log.append(f'{name}: вече е приложено'); continue
    n = s.count(old)
    if n != 1: log.append(f'{name}: ГРЕШКА — {n} съвпадения'); continue
    s = s.replace(old, new); log.append(f'{name}: OK')
open('app.js', 'w', encoding='utf-8').write(s)

h = open('index.html', encoding='utf-8').read()
if 'v=20261005v164' in h: log.append('версия: вече е приложено')
elif h.count('app.js?v=20261005v163') == 1:
    h = h.replace('app.js?v=20261005v163', 'app.js?v=20261005v164'); log.append('версия: OK')
else: log.append('версия: ГРЕШКА')
open('index.html', 'w', encoding='utf-8').write(h)

open('flights-merge-report.txt', 'w', encoding='utf-8').write('\n'.join(log) + '\n')
print('\n'.join(log))
if any('ГРЕШКА' in l for l in log): sys.exit(1)

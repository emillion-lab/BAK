#!/usr/bin/env python3
"""Полети: оправя панела „Излизане на пасажери“.
Идемпотентен — всяка замяна се прави само ако още не е приложена."""
import re, sys

def patch(path, edits):
    s = open(path, encoding='utf-8').read()
    log = []
    for name, old, new, marker in edits:
        if marker in s:
            log.append(f'{name}: вече е приложено'); continue
        if s.count(old) != 1:
            log.append(f'{name}: ГРЕШКА — намерени {s.count(old)} съвпадения'); continue
        s = s.replace(old, new); log.append(f'{name}: OK')
    open(path, 'w', encoding='utf-8').write(s)
    return log

NS_OLD = "/tur|istanbul|sabiha|ankar|israel|ben.gurion|dubai|abu.dhabi|egypt|cairo|morocco|casablanca|london|heathrow|gatwick|stansted|luton|manchester|birmingham|usa|jfk|lax|china|beijing|shanghai|russia|moscow|georgia|tbilisi|armenia|yerevan|jordan|amman|serbia|belgrade|ukraine|kyiv|north.mac/"
NS_NEW = ("/turkey|t\u00fcrk|istanbul|sabiha|ankar|antalya|izmir|bodrum|dalaman|israel|tel.aviv|ben.gurion|dubai|abu.dhabi|doha|egypt|cairo|hurghada|sharm|"
          "morocco|marrakech|marrakesh|agadir|casablanca|tunis|larnaca|larnarca|paphos|cyprus|dublin|ireland|"
          "london|heathrow|gatwick|stansted|luton|manchester|birmingham|edinburgh|glasgow|bristol|liverpool|leeds|newcastle|bournemouth|east.midlands|"
          "usa|jfk|lax|china|beijing|shanghai|russia|moscow|georgia|tbilisi|kutaisi|baku|armenia|yerevan|jordan|amman|beirut|"
          "serbia|belgrade|ukraine|kyiv|tirana|podgorica|sarajevo|skopje|pristina|chisinau|north.mac/")

app_edits = [
 ('колони на реда',
  'display:grid;grid-template-columns:46px 1fr auto;align-items:center;gap:7px;',
  'display:grid;grid-template-columns:minmax(46px,max-content) minmax(0,1fr) auto;align-items:center;gap:9px;',
  'minmax(46px,max-content)'),
 ('контраст „Следващ“',
  '<b>Следващ: ${fmt(next.exitFromH,next.exitFromM)}</b>',
  '<b style="color:inherit">Следващ: ${fmt(next.exitFromH,next.exitFromM)}</b>',
  '<b style="color:inherit">Следващ'),
 ('дублирано време',
  '<span style="font-size:9.5px;opacity:.9"> ${fmt(f.schedH,f.schedM)}${',
  '<span style="font-size:9.5px;opacity:.9">${(f.schedH===f.landH&&f.schedM===f.landM)?\'\':\' \'+fmt(f.schedH,f.schedM)}${',
  "(f.schedH===f.landH&&f.schedM===f.landM)"),
 ('Шенген/извън',
  NS_OLD, NS_NEW, 'larnarca|paphos'),
 ('имена на градове',
  "const depAirport = f.departure?.airport||dep;",
  "const depAirport = (window.__fixCity||function(x){return x})(f.departure?.airport||dep);",
  '__fixCity'),
 ('жив → кеш при остарял прозорец',
  "if(!live || !live.arrivals || !live.arrivals.length) throw 0;",
  "if(!live || !live.arrivals || !live.arrivals.length) throw 0;\n"
  "      // жив отговор без нито едно скорошно/бъдещо кацане е безполезен → кешът\n"
  "      if(!live.arrivals.some(function(a){ var ts=new Date(String(a.revised||a.scheduled||'').replace(' ','T')).getTime(); return isFinite(ts) && ts > Date.now()-60*60000; })) throw 0;",
  'безполезен → кешът'),
]

# речник за показваните имена (само известни правописни грешки на източника)
FIXCITY = ("window.__fixCity = (function(){\n"
           "  var M = {'larnarca':'Larnaca','rodes island':'Rhodes'};\n"
           "  return function(n){ var k = String(n||'').trim().toLowerCase(); return M[k] || n; };\n"
           "})();\n")
log = patch('app.js', app_edits)

s = open('app.js', encoding='utf-8').read()
if 'window.__fixCity =' not in s:
    anchor = 'function loadFlights(){'
    assert s.count(anchor) == 1, 'loadFlights anchor'
    s = s.replace(anchor, FIXCITY + anchor); log.append('речник __fixCity: OK')
else:
    log.append('речник __fixCity: вече е приложено')
open('app.js', 'w', encoding='utf-8').write(s)

html_edits = [
 ('място за бутоните',
  '#airport-modal-body{ padding-right:12px !important; }',
  '#airport-modal-body{ padding-right:58px !important; }',
  'padding-right:58px'),
 ('версия на app.js',
  'app.js?v=20260801v162', 'app.js?v=20261005v163', 'v=20261005v163'),
]
log += patch('index.html', html_edits)

open('flights-fix-report.txt', 'w', encoding='utf-8').write('\n'.join(log) + '\n')
print('\n'.join(log))
if any('ГРЕШКА' in l for l in log): sys.exit(1)

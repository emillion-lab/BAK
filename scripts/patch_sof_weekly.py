#!/usr/bin/env python3
"""SOF: седмично разписание като резерва + видим източник на всеки полет.
Плюс: откритите басейни извън сезона не носят работа.

Идемпотентен — всяка замяна се прави само ако маркерът ѝ още липсва.
Връщане назад: workflow „restore-pre-sof“ (тагът pre-sof-weekly).
"""
import re, sys

MERGE_FN = r"""
// ═ SOF седмично разписание (резерва при радарни данни) ═
// Източници на всеки полет (f._src):
//   live    — AeroDataBox с разписание и терминал (нормалният случай)
//   radar   — AeroDataBox само по радар: без разписание, номерът е позивна
//   radar+  — радарен полет, разпознат в разписанието → истински номер и терминал
//   weekly  — само от sof-weekly.json (същият ден от предни седмици) = прогноза
//   cache   — от flight-cache.json
function __sofOffset(d){
  try{
    var s = new Intl.DateTimeFormat('en',{timeZone:'Europe/Sofia',timeZoneName:'shortOffset'})
      .formatToParts(d).find(function(p){ return p.type==='timeZoneName'; }).value;
    var m = s.match(/GMT([+-]\d+)/), h = m ? parseInt(m[1],10) : 3;
    return (h<0?'-':'+') + String(Math.abs(h)).padStart(2,'0') + ':00';
  }catch(e){ return '+03:00'; }
}
function __sofYmd(d){
  try{ return new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Sofia'}).format(d); }
  catch(e){ return new Date(d.getTime()+3*3600000).toISOString().slice(0,10); }
}
function __cityKey(s){ return String(s||'').toLowerCase().replace(/[^a-zа-я]/g,'').slice(0,5); }
function mergeWeekly(data){
  data = data || {data:[]}; data.data = data.data || [];
  return fetch('sof-weekly.json?v='+Date.now())
    .then(function(r){ return r.ok ? r.json() : null; })
    .catch(function(){ return null; })
    .then(function(wk){
      var now = Date.now();
      var tsOf = function(f){ return Date.parse(String((f.arrival&&(f.arrival.estimated||f.arrival.scheduled))||'').replace(' ','T')); };
      var ex = data.data.map(function(f){
        if(!f._src) f._src = (f.arrival&&f.arrival.terminal) ? 'live' : 'radar';
        return { f:f, ts:tsOf(f), fn:((f.flight&&f.flight.iata)||'').toUpperCase(), city:__cityKey(f.departure&&f.departure.airport), used:false };
      });
      var nW = 0, nMatch = 0;
      if(wk && wk.days){
        [0,1].forEach(function(off){
          var d = new Date(now + off*86400000), ymd = __sofYmd(d);
          var wd = new Date(ymd+'T12:00:00Z').getUTCDay();
          var tz = __sofOffset(new Date(ymd+'T12:00:00Z'));
          (wk.days[String(wd)] || []).forEach(function(r){
            var iso = ymd + 'T' + r.t + ':00' + tz, ts = Date.parse(iso);
            if(!(ts > now - 3*3600000 && ts < now + 21*3600000)) return;
            var fn = String(r.fn||'').toUpperCase(), ck = __cityKey(r.from);
            // 1) същият номер (днешното разписание вече го има)
            var hit = ex.find(function(e){ return e.fn===fn && Math.abs(e.ts-ts) < 3*3600000; });
            if(hit){
              if(!hit.f.arrival.terminal){ hit.f.arrival.terminal = r.term; }
              if(hit.f._src==='radar'){ hit.f._src = 'radar+'; hit.used = true; nMatch++; }
              return;
            }
            // 2) радарен полет от същия град ±40 мин → това е той
            hit = ex.find(function(e){ return !e.used && e.f._src==='radar' && e.city && e.city===ck && Math.abs(e.ts-ts) <= 40*60000; });
            if(hit){
              hit.used = true; nMatch++;
              hit.f._radarFn = hit.fn; hit.f.flight.iata = fn;
              hit.f.arrival.terminal = r.term; hit.f._src = 'radar+';
              return;
            }
            nW++;
            data.data.push({
              flight:{ iata: fn }, airline:{ name: r.airline||'' },
              arrival:{ scheduled: iso, estimated: iso, terminal: r.term },
              departure:{ airport: r.from||'' },
              flight_status:'scheduled', _delay:0, _statusRaw:'', _src:'weekly'
            });
          });
        });
      }
      // радарни без съвпадение: терминал по превозвач (Wizz → Т1, другите → Т2), с „?“
      ex.forEach(function(e){
        if(e.f._src!=='radar' || e.f.arrival.terminal) return;
        var al = ((e.f.airline&&e.f.airline.name)||'') + ' ' + e.fn;
        e.f.arrival.terminal = /wizz|^W6|\bW6/i.test(al) ? '1' : '2';
        e.f._termGuess = true;
      });
      var c = {live:0, radar:0, cache:0};
      data.data.forEach(function(f){ var s=f._src||'live'; if(s==='radar+') s='radar'; if(c[s]!==undefined) c[s]++; });
      var parts = [];
      if(c.live)  parts.push('✈️ живо ' + c.live);
      if(c.radar) parts.push('📡 радар ' + c.radar + (nMatch ? ' (' + nMatch + ' разпознати)' : ''));
      if(nW)      parts.push('📅 разписание ' + nW);
      if(c.cache) parts.push('🗄 кеш ' + c.cache);
      window.__flightSource = parts.join(' · ') || 'няма данни';
      return data;
    });
}
"""

EDITS = [
 ('функция mergeWeekly',
  "function loadFlights(){",
  MERGE_FN.lstrip('\n') + "function loadFlights(){",
  'function mergeWeekly(data)'),

 ('жив: източник',
  "          _statusRaw: a.status || ''\n        };",
  "          _statusRaw: a.status || '',\n          _src: a.terminal ? 'live' : 'radar'\n        };",
  "_src: a.terminal ? 'live' : 'radar'"),

 ('кеш: източник',
  "seen[k] = 1; data.data.push(f); added++;",
  "seen[k] = 1; f._src = (f.arrival&&f.arrival.terminal) ? 'cache' : 'radar'; data.data.push(f); added++;",
  "f._src = (f.arrival&&f.arrival.terminal) ? 'cache'"),

 ('жив+кеш → разписание',
  "          window.__flightSource = 'живо · ' + liveN + (added ? ' + кеш ' + added : '');\n          processFlights(data);",
  "          return mergeWeekly(data).then(processFlights);",
  "return mergeWeekly(data).then(processFlights);"),

 ('само кеш → разписание',
  "    .then(r=>{if(!r.ok)throw 0;return r.json();})\n    .then(processFlights)",
  "    .then(r=>{if(!r.ok)throw 0;return r.json();})\n    .then(function(d){ return mergeWeekly(d).then(processFlights); })",
  "return mergeWeekly(d).then(processFlights); })"),

 ('детайли: източник',
  "delay: f._delay || 0, statusRaw: f._statusRaw || '',",
  "delay: f._delay || 0, statusRaw: f._statusRaw || '',\n          src: f._src || 'live', termGuess: !!f._termGuess, radarFn: f._radarFn || '', landTs: t.getTime(),",
  "termGuess: !!f._termGuess"),

 ('значка за източник',
  "  const flag = f => f.nonSchengen ? '🛂' : '🇪🇺';",
  "  const flag = f => f.nonSchengen ? '🛂' : '🇪🇺';\n"
  "  const SRC = { live:['✈️','живо','#16a34a'], radar:['📡','радар','#0369a1'], 'radar+':['📡','радар','#0369a1'],\n"
  "                weekly:['📅','разписание','#b45309'], cache:['🗄','кеш','#6b7280'] };\n"
  "  const srcBadge = f => { const s = SRC[f.src] || SRC.live;\n"
  "    return `<span style=\"font-size:8.5px;font-weight:800;color:${s[2]};border:1px solid ${s[2]};border-radius:4px;padding:0 3px;margin-right:3px\">${s[0]} ${s[1]}</span>`; };",
  "const srcBadge = f =>"),

 ('ред: лява черта по източник',
  "margin-bottom:1px;${op}\">",
  "margin-bottom:1px;${op}${f.src==='weekly'?'border-left:3px dashed #b45309;':(f.src==='radar'||f.src==='radar+')?'border-left:3px solid #0369a1;':''}\">",
  "border-left:3px dashed #b45309"),

 ('ред: терминал с „?“ при догадка',
  "opacity:.85\">Т${f.term}</span>",
  "opacity:.85\">Т${f.term}${f.termGuess?'?':''}</span>",
  "Т${f.term}${f.termGuess?'?':''}"),

 ('ред: значка + „~кацна“',
  "white-space:nowrap;line-height:1.2\">🛬 ${fmt(f.landH,f.landM)}${\n"
  "            /arriv/i.test(f.statusRaw||'')   ? ' <span style=\"color:#16a34a\">кацна</span>' :\n"
  "            /approach|en.?route/i.test(f.statusRaw||'') ? ' <span style=\"color:#0369a1\">каца</span>' : ''",
  "white-space:nowrap;line-height:1.2\">${srcBadge(f)}🛬 ${fmt(f.landH,f.landM)}${\n"
  "            /arriv/i.test(f.statusRaw||'')   ? ' <span style=\"color:#16a34a\">кацна</span>' :\n"
  "            /approach|en.?route/i.test(f.statusRaw||'') ? ((f.landTs && f.landTs < Date.now()-15*60000) ? ' <span style=\"color:#16a34a;opacity:.75\">~кацна</span>' : ' <span style=\"color:#0369a1\">каца</span>') : ''",
  "${srcBadge(f)}🛬"),

 ('легенда: източници',
  "🔴 излизат сега · бледите още се точат</div>';",
  "🔴 излизат сега · бледите още се точат<br>✈️ живо · 📡 радар · 📅 разписание · 🗄 кеш</div>';",
  "<br>✈️ живо · 📡 радар · 📅 разписание · 🗄 кеш</div>';"),

 ('долен ред: източник',
  "Източник: AeroDataBox · ${flightDetails.length} пристигания",
  "Източник: ${window.__flightSource||'AeroDataBox'} · ${flightDetails.length} пристигания",
  "Източник: ${window.__flightSource"),

 # ── басейни: открит басейн извън сезона (16.09 – 31.05) е затворен ──
 ('басейни: сезон в оценката',
  "    var indoor = !!h[4];\n",
  "    var indoor = !!h[4];\n"
  "    // открит басейн извън сезона (16.09 – 31.05) е затворен → няма работа\n"
  "    var _mo = now.getMonth()+1, _dd = now.getDate();\n"
  "    if(!indoor && (_mo < 6 || _mo > 9 || (_mo === 9 && _dd > 15))) return 0;\n",
  "открит басейн извън сезона (16.09"),

 ('басейни: без предупреждение извън сезона',
  "  function alertTick(){\n    if(W.t === null) return;",
  "  function alertTick(){\n    if(W.t === null) return;\n"
  "    var _m = new Date().getMonth()+1, _d = new Date().getDate();\n"
  "    if(_m < 6 || _m > 9 || (_m === 9 && _d > 15)){ chip.style.display='none'; return; }",
  "if(_m < 6 || _m > 9 || (_m === 9 && _d > 15)){ chip.style.display='none'; return; }"),

 ('събития: летен сезон',
  "function dayMatches(ev) {\n",
  "function dayMatches(ev) {\n"
  "  if (ev.season === 'summer') {\n"
  "    const _m = new Date().getMonth()+1, _d = new Date().getDate();\n"
  "    if (_m < 6 || _m > 9 || (_m === 9 && _d > 15)) return false;\n"
  "  }\n",
  "ev.season === 'summer'"),
 ('басейни: извън сезона вън от картата и топа',
  "window.ZONES = ZONES;   // ползва се от бутоните за дестинации",
  "// Открити басейни извън сезона (16.09 – 31.05) са затворени → вън от картата и от топа.\n"
  "(function(){\n"
  "  var _m = new Date().getMonth()+1, _d = new Date().getDate();\n"
  "  if(!(_m < 6 || _m > 9 || (_m === 9 && _d > 15))) return;\n"
  "  var INDOOR = { pool_sportpalace:1, pool_infinity:1 };\n"
  "  for(var i = ZONES.length - 1; i >= 0; i--){\n"
  "    if(/^pool_/.test(ZONES[i].id) && !INDOOR[ZONES[i].id]) ZONES.splice(i, 1);\n"
  "  }\n"
  "})();\n"
  "window.ZONES = ZONES;   // ползва се от бутоните за дестинации",
  "Открити басейни извън сезона (16.09 – 31.05) са затворени"),
]


# ── 14.10: махната лента „само радар“ и съкратена легенда (стари версии от 13.10) ──
OLD_BANNER = ("  if(flightDetails.some(f=>f.src==='radar'||f.src==='radar+') && !flightDetails.some(f=>f.src==='live')){\n"
  "    html+='<div style=\"background:rgba(180,83,9,.10);border:1px solid #b45309;border-radius:8px;padding:6px 10px;margin-bottom:8px;font-size:12px;color:#b45309;line-height:1.4\">'\n"
  "        +'⚠️ AeroDataBox дава само <b>📡 радар</b> за SOF. Бъдещите са <b>📅 по разписание</b> от предни седмици — може да са отменени или преместени.</div>';\n"
  "  }\n")
OLD_LEGEND = "<br>✈️ живо · 📡 радар (без разписание) · 📅 по разписание от предни седмици (прогноза) · 🗄 кеш · Т? = терминалът е предположен</div>';"
NEW_LEGEND = "<br>✈️ живо · 📡 радар · 📅 разписание · 🗄 кеш</div>';"

s = open('app.js', encoding='utf-8').read()
log = []
if OLD_BANNER in s: s = s.replace(OLD_BANNER, ''); log.append('лента „само радар“: махната')
if OLD_LEGEND in s: s = s.replace(OLD_LEGEND, NEW_LEGEND); log.append('легенда: съкратена')
for name, old, new, marker in EDITS:
    if marker in s:
        log.append(f'{name}: вече е приложено'); continue
    n = s.count(old)
    if n != 1:
        log.append(f'{name}: ГРЕШКА — {n} съвпадения'); continue
    s = s.replace(old, new); log.append(f'{name}: OK')

# „лятно изтичане“ събитията получават season:"summer"
if 'лятно изтичане", ' in s and 'season:"summer"' not in s:
    s, n = re.subn(r'(лятно изтичане",[^}]*?repeat:"daily")', r'\1, season:"summer"', s)
    log.append(f'събития басейни: {n} маркирани' + ('' if n == 3 else ' — ГРЕШКА, очаквани 3'))
else:
    log.append('събития басейни: вече е приложено')

open('app.js', 'w', encoding='utf-8').write(s)

h = open('index.html', encoding='utf-8').read()
# нова версия само ако app.js се е променил, за да не остане старият в кеша на телефона
changed = any(l.endswith(': OK') or 'махната' in l or 'съкратена' in l or 'маркирани' in l for l in log)
if changed:
    stamp = 'app.js?v=' + __import__('datetime').date.today().strftime('%Y%m%d') + 's'
    h2, n = re.subn(r'app\.js\?v=[0-9A-Za-z]+', lambda m: stamp + str(int(__import__('time').time()) % 100000), h, count=1)
    log.append('версия: OK' if n == 1 else 'версия: ГРЕШКА — няма app.js?v= в index.html'); h = h2
else:
    log.append('версия: без промяна')
open('index.html', 'w', encoding='utf-8').write(h)

open('sof-weekly-report.txt', 'w', encoding='utf-8').write('\n'.join(log) + '\n')
print('\n'.join(log))
if any('ГРЕШКА' in l for l in log): sys.exit(1)

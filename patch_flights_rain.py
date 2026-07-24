# -*- coding: utf-8 -*-
"""v33: (1) цветовете пренаписани В ИЗТОЧНИКА (v24 слоят сменяше цвят, но не
           и fillAlpha -> кръговете си оставаха тъмни)
       (2) моловете имат под с реален поток по часове (Paradise в 19ч не е черен)
       (3) Студентски град — жилищен профил, не сесиен (петък > четвъртък)
       (4) надписи върху големите кръгове
       (5) десктоп/телефон оптимизация
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (1а) изключваме слоя от v24 ──
old24 = "if(typeof window.demandColor !== 'function') return;"
if old24 in cand:
    cand = cand.replace(old24, "return; // изключен от v33 — цветовете са в източника", 1)
    rep.append('OK   слоят от v24 изключен (двойно оцветяване)')

# ── (1б) нова скала директно в demandColor ──
NEW = '''if (score>=3.8) return {fill:"#ef4444",fillAlpha:0.62,stroke:"#ff8f8f",label:"ПИК 🔥"};
  if (score>=3.0) return {fill:"#f97316",fillAlpha:0.56,stroke:"#ffb070",label:"Висок ▲"};
  if (score>=2.4) return {fill:"#f59e0b",fillAlpha:0.52,stroke:"#ffd060",label:"Добър"};
  if (score>=1.8) return {fill:"#a3c23a",fillAlpha:0.48,stroke:"#cbe860",label:"Среден"};
  if (score>=1.2) return {fill:"#4cba52",fillAlpha:0.44,stroke:"#84e88f",label:"Нормален"};
  if (score>=0.7) return {fill:"#2fa88a",fillAlpha:0.40,stroke:"#63dcb8",label:"Слаб шанс"};
  if (score>=0.35) return {fill:"#3d8fb5",fillAlpha:0.34,stroke:"#74c4e2",label:"Минимален"};
  return               {fill:"#33415c",fillAlpha:0.15,stroke:"#4d5f80",label:"Тих"};'''

pat = re.compile(
    r'if \(score>=3\.2\) return \{fill:"#ef4444".*?return\s+\{fill:"#1a3050"[^}]*\};',
    re.S)
if pat.search(cand):
    cand = pat.sub(NEW, cand, count=1)
    rep.append('OK   нова скала в demandColor: 8 нива + по-плътни кръгове')
else:
    rep.append('⚠ старата скала не е намерена — цветовете остават както са')

# ── ZONES достъпни отвън (за надписите) ──
if 'window.__ZONES' not in cand:
    n = len(re.findall(r'const\s+ZONES\s*=\s*\[', cand))
    if n == 1:
        cand = re.sub(r'const\s+ZONES\s*=\s*\[', 'const ZONES = window.__ZONES = [', cand, count=1)
        rep.append('OK   ZONES изнесени в window (за надписите)')
    else:
        rep.append('SKIP ZONES (намерени %d)' % n)

# ── (2)(3)(4)(5) ──
if 'zones-tune-v33' in cand:
    rep.append('SKIP v33 вече е приложен')
else:
    cand += """

// ------ zones-tune-v33 ------
(function(){
  var MALLS = {
    paradise:1.18, ring_mall:1.12, the_mall:1.10, serdika:1.10,
    mall_sofia:1.0, bulgaria_mall:1.0, park_center:0.85
  };

  // моловете имат постоянен поток — под по часове (отваряне 10:00, затваряне 22:00)
  function mallFloor(zid){
    var w = MALLS[zid]; if(!w) return null;
    var d = new Date(), h = d.getHours() + d.getMinutes()/60;
    var wknd = (d.getDay() === 0 || d.getDay() === 6);
    var s;
    if(h < 9.5) s = 0.25;                        // затворен
    else if(h < 12) s = 0.9;                     // отваряне, рядко
    else if(h < 15) s = 1.35;                    // обедна вълна
    else if(h < 17.5) s = 1.5;
    else if(h < 20) s = 2.0;                     // следобеден/вечерен пик
    else if(h < 21.5) s = 2.3;                   // преди затваряне — най-силно
    else if(h < 22.4) s = 2.6;                   // изходната вълна
    else s = 0.3;
    if(wknd && h >= 11 && h <= 21) s *= 1.25;    // уикендът е по-силен
    return s * w;
  }

  // Студентски град: жилищен профил, не сесиен.
  // Живущи без коли (нови и чужденци) — като Кръстова вада.
  function studentskiScore(){
    var d = new Date(), h = d.getHours() + d.getMinutes()/60, day = d.getDay();
    var fri = (day === 5), sat = (day === 6), sun = (day === 0);
    var s;
    if(h < 6) s = (fri || sat) ? 1.9 : 0.8;      // нощем навън само в края на седмицата
    else if(h < 9.5) s = 1.5;                    // сутрин на работа/лекции
    else if(h < 16) s = 0.9;
    else if(h < 19) s = 1.3;                     // прибиране
    else if(h < 22) s = fri ? 2.1 : (sat ? 1.9 : 1.35);
    else s = fri ? 2.4 : (sat ? 2.2 : 1.2);      // излизане навън
    if(sun && h > 16) s += 0.4;                  // връщане в неделя вечер
    return s;
  }

  var prev = window.__applyLive;
  window.__applyLive = function(scores){
    try{ if(prev) prev(scores); }catch(e){}
    try{
      for(var zid in MALLS){
        if(typeof scores[zid] !== 'number') continue;
        var f = mallFloor(zid);
        if(f !== null) scores[zid] = Math.max(scores[zid], f);
      }
      if(typeof scores.studentski === 'number'){
        scores.studentski = studentskiScore();
      }
    }catch(e){}
  };

  // ---- надписи върху големите кръгове ----
  function shortName(z){
    var n = (z.name || '').replace(/\\([^)]*\\)/g, '').trim();
    n = n.replace(/^(жк|ЖК)\\s+/, '').replace(/^Мол\\s+/i, '').replace(/^Хотели\\s+/i, '');
    n = n.replace(/\\s*[–—-]\\s*.*$/, '');
    var words = n.split(/\\s+/).filter(Boolean);
    var out = words.slice(0, 2).join(' ');
    if(out.length > 15) out = words[0];
    if(out.length > 15) out = out.slice(0, 14) + '…';
    return out;
  }
  var LABEL_TYPES = {airport:1, transit:1, mall:1, residential:1, residential_lux:1,
                     hospital:1, university:1, venue:1};

  function addLabels(){
    try{
      var map = window.__leafletMap, Z = window.__ZONES;
      if(!map || !Z || !window.L) return;
      if(map.getZoom() < 12){ 
        if(window.__labelLayer){ map.removeLayer(window.__labelLayer); window.__labelLayer = null; }
        return;
      }
      if(window.__labelLayer) return;                 // вече са сложени
      var lg = L.layerGroup();
      Z.forEach(function(z){
        if(!z.radius || z.radius < 240) return;       // само големите
        if(!LABEL_TYPES[z.type]) return;
        var txt = shortName(z);
        if(!txt) return;
        lg.addLayer(L.marker([z.lat, z.lng], {
          interactive: false,
          icon: L.divIcon({
            className: '',
            html: '<div style="white-space:nowrap;font:600 11px/1.1 system-ui,sans-serif;'
                + 'color:#f2f6fc;text-shadow:0 1px 3px #000,0 0 6px #000;'
                + 'transform:translate(-50%,-50%);pointer-events:none">'
                + (z.icon || '') + ' ' + txt + '</div>',
            iconSize: [0, 0]
          })
        }));
      });
      lg.addTo(map);
      window.__labelLayer = lg;
    }catch(e){}
  }
  function refreshLabels(){
    try{
      var map = window.__leafletMap;
      if(!map) return;
      if(window.__labelLayer){ map.removeLayer(window.__labelLayer); window.__labelLayer = null; }
      addLabels();
    }catch(e){}
  }
  var t = setInterval(function(){
    if(window.__leafletMap && window.__ZONES){
      clearInterval(t);
      addLabels();
      try{ window.__leafletMap.on('zoomend', refreshLabels); }catch(e){}
    }
  }, 700);

  // ---- десктоп/телефон ----
  try{
    var st = document.createElement('style');
    st.id = 'responsive-v33';
    st.textContent =
      '@media (min-width:1024px){'
      + 'body{max-width:1400px;margin:0 auto;}'
      + '#map{height:62vh!important;min-height:520px!important;}'
      + '.leaflet-popup-content{font-size:14px!important;max-height:60vh!important;}'
      + '}'
      + '@media (max-width:480px){'
      + '.leaflet-popup-content{font-size:12.5px!important;}'
      + '.leaflet-popup-content-wrapper{border-radius:12px!important;}'
      + '}'
      + '@media (min-width:1400px){ #map{height:68vh!important;} }';
    document.head.appendChild(st);
  }catch(e){}
})();
"""
    rep.append('OK   молове: под по часове (Paradise/Ring/The Mall с тегло)')
    rep.append('OK   Студентски град: жилищен профил, петък > четвъртък')
    rep.append('OK   надписи върху кръговете с радиус >= 240 м')
    rep.append('OK   десктоп/мобилни стилове')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v33', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v33' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v33 + node --check + cache-bust v33')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

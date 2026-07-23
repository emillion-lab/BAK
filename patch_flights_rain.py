# -*- coding: utf-8 -*-
"""v20: ПОПРАВКА на фокуса от списъка.
Причина: <div id="map"> прави глобално `map` = DOM елементът, а Leaflet
картата е локална в DOMContentLoaded. Inline onclick вижда div-а -> setView гърми.
Решение: прихващаме L.map() при създаване и пазим инстанцията в window.__leafletMap,
после inline хендлърът вика window.__focusZone().
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── 1) кука върху L.map (най-отгоре, преди приложението да си направи картата) ──
if '__leafletMap-hook' in cand:
    rep.append('SKIP куката вече е сложена')
else:
    hook = """// __leafletMap-hook (v20) — прихваща Leaflet картата при създаване
(function(){
  try{
    if(window.L && typeof L.map === 'function'){
      var _origMap = L.map;
      L.map = function(){
        var m = _origMap.apply(this, arguments);
        try{ window.__leafletMap = m; }catch(e){}
        return m;
      };
      for(var k in _origMap){ try{ L.map[k] = _origMap[k]; }catch(e){} }
    }
  }catch(e){}
  // фокусиране на зона от списъка — вика се от inline onclick
  window.__focusZone = function(lat, lng, zoom){
    try{
      var el = document.getElementById('map');
      if(el && el.scrollIntoView) el.scrollIntoView({behavior:'smooth', block:'center'});
      var m = window.__leafletMap;
      if(!m || typeof m.setView !== 'function') return;
      setTimeout(function(){
        try{
          if(typeof m.invalidateSize === 'function') m.invalidateSize();
          m.setView([lat, lng], zoom || 15);
        }catch(e){}
      }, 220);
    }catch(e){}
  };
})();

"""
    cand = hook + cand
    rep.append('OK   кука върху L.map + window.__focusZone')

# ── 2) inline хендлърът вече вика __focusZone ──
old = ("setTimeout(()=>{var _m=document.getElementById('map');"
       "if(_m&&_m.scrollIntoView)_m.scrollIntoView({behavior:'smooth',block:'center'});"
       "if(map.invalidateSize)map.invalidateSize();"
       "map.setView([${z.lat},${z.lng}],'${zid}'==='airport'?14:15);")
new = "setTimeout(()=>{window.__focusZone(${z.lat},${z.lng},'${zid}'==='airport'?14:15);"
n = cand.count(old)
if n == 1:
    cand = cand.replace(old, new)
    rep.append('OK   inline фокус -> window.__focusZone')
else:
    rep.append('SKIP inline фокус (намерени %d) — търся общо' % n)
    # резервен вариант: всяко map.setView/invalidateSize в темплейт низ
    n2 = len(re.findall(r'map\.setView\(\[\$\{z\.lat\}', cand))
    if n2:
        cand = re.sub(r'if\(map\.invalidateSize\)map\.invalidateSize\(\);', '', cand)
        cand = re.sub(r'map\.setView\(\[\$\{z\.lat\},\$\{z\.lng\}\]',
                      'window.__focusZone(${z.lat},${z.lng}', cand)
        rep.append('OK   заменени %d общи map.setView в темплейт' % n2)

# ── 3) всяко останало голо map.setView/ invalidateSize в inline низове ──
leftover = len(re.findall(r'(?<!__leafletMap\.)(?<!m\.)\bmap\.(setView|invalidateSize|flyTo)\(', cand))
rep.append('остатъчни голи map.* обръщения: %d' % leftover)

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v20', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda mm: mm.group(1) + 'bak-v20' + mm.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v20 + node --check + cache-bust v20')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

# -*- coding: utf-8 -*-
"""v40: (1) точката за трафика на бул.България беше стара (в преките при
           Петко Тодоров) — синхронизира се със зоната
       (2) индикаторът "4/4 отсечки" се маха — заемаше мястото на автогарата
       (3) map.invalidateSize/setView: <div id='map'> получава методите на
           Leaflet картата, за да не гърми НИКЪДЕ повече
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (1) синхронизиране на точката ──
old = "{id:'jam_ndk',     lat:42.6745, lng:23.3028, name:'бул. България'}"
new = "{id:'jam_ndk',     lat:42.6655, lng:23.2895, name:'бул. България'}"
if old in cand:
    cand = cand.replace(old, new)
    rep.append('OK   точката за трафика на бул.България синхронизирана (беше 1.5 км встрани)')
else:
    n = len(re.findall(r"lat:42\.6745,\s*lng:23\.3028", cand))
    if n:
        cand = re.sub(r"lat:42\.6745,\s*lng:23\.3028", "lat:42.6655, lng:23.2895", cand)
        rep.append('OK   точката синхронизирана (%d места, резервен път)' % n)
    else:
        rep.append('SKIP старата точка не е намерена')

# ── (2) махаме индикатора за трафика ──
if 'bottom:240px' in cand:
    cand = cand.replace("chip.textContent = '🚦 трафик…';\n  document.body.appendChild(chip);",
                        "chip.textContent = '🚦 трафик…';\n  // v40: не се показва — заемаше мястото на автогарата")
    rep.append('OK   индикаторът "отсечки/линии" вече не се показва')
else:
    rep.append('SKIP индикаторът не е намерен')

# ── (3) шим: div#map получава методите на Leaflet картата ──
if 'map-div-shim-v40' in cand:
    rep.append('SKIP шимът вече е сложен')
else:
    shim = """// map-div-shim-v40 — <div id="map"> е глобалното `map` в браузъра, а Leaflet
// картата е в затворен обхват. Даваме на div-а методите на картата, за да не
// гърми никой inline onclick, който вика map.setView / map.invalidateSize.
(function(){
  var METHODS = ['invalidateSize','setView','flyTo','panTo','setZoom','zoomIn','zoomOut',
                 'fitBounds','getZoom','getCenter','getBounds','openPopup','closePopup',
                 'addLayer','removeLayer','eachLayer','locate','stop'];
  function attach(){
    try{
      var el = document.getElementById('map');
      if(!el || el.__mapShim) return;
      el.__mapShim = 1;
      METHODS.forEach(function(fn){
        if(typeof el[fn] !== 'undefined') return;      // не пипаме DOM методи
        el[fn] = function(){
          var m = window.__leafletMap;
          if(m && typeof m[fn] === 'function'){
            try{ return m[fn].apply(m, arguments); }catch(e){}
          }
          return undefined;
        };
      });
    }catch(e){}
  }
  attach();
  var t = setInterval(function(){ attach(); }, 1000);
  setTimeout(function(){ clearInterval(t); }, 30000);
})();

"""
    cand = shim + cand
    rep.append('OK   шим за div#map — map.setView/invalidateSize вече не гърмят никъде')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v40', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v40' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v40 + node --check + cache-bust v40')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

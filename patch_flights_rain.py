# -*- coding: utf-8 -*-
"""v36: (1) индикатор за трафика — показва дали изобщо идват данни и геометрия
       (2) Борисова градина: голям кръг, малко работа -> радиусът намалява
       (3) надписи и на по-малките зони при по-голям зуум + скор в надписа
       (4) закръгляне на числата (3.9999999 рейса -> 4.0)
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (2) Борисова: радиусът да отговаря на реалната работа ──
m = re.search(r'(\{\s*id:"borisova"[^}]*?radius:)(\d+)', cand)
if m:
    old_r = m.group(2)
    cand = cand[:m.start(2)] + '400' + cand[m.end(2):]
    rep.append('OK   borisova радиус %s -> 400 (паркът е голям, но курсове дава малко)' % old_r)
else:
    rep.append('SKIP borisova радиус не е намерен')

if 'ui-tune-v36' in cand:
    rep.append('SKIP v36 вече е приложен')
else:
    cand += """

// ------ ui-tune-v36 ------
(function(){

  // ═══ 1) индикатор за трафика ═══
  var chip = document.createElement('div');
  chip.style.cssText = 'position:fixed;left:8px;bottom:240px;z-index:1500;border-radius:10px;'
    + 'padding:6px 10px;font-family:sans-serif;font-size:12px;font-weight:800;cursor:pointer;'
    + 'box-shadow:0 2px 10px rgba(0,0,0,.5);background:#10233af0;color:#93c5fd;'
    + 'border:1px solid #3b82f6';
  chip.textContent = '🚦 трафик…';
  document.body.appendChild(chip);
  chip.onclick = function(){
    var D = window.__trafficData || [];
    var lines = D.map(function(s){
      var x = s.data || {};
      if(x.err) return s.name + ': грешка ' + x.err;
      var n = (x.coords || []).length;
      return s.name + ': ' + (x.cur != null ? x.cur + '/' + x.free + ' км/ч' : 'няма скорост')
           + ' · ' + n + ' точки';
    });
    alert('🚦 Трафик (TomTom)\\n\\n'
      + (lines.length ? lines.join('\\n') : 'НЯМА ДАННИ')
      + '\\n\\nкарта: ' + (window.__leafletMap ? 'да' : 'НЕ')
      + '\\nслой: ' + (window.__trafficLayerOn ? 'да' : 'НЕ')
      + (window.__trafficErr ? ('\\nгрешка: ' + window.__trafficErr) : ''));
  };
  setInterval(function(){
    var D = window.__trafficData || [];
    var ok = D.filter(function(s){ return s.data && !s.data.err; }).length;
    var geo = D.filter(function(s){ return s.data && (s.data.coords||[]).length > 1; }).length;
    if(!D.length){ chip.textContent = '🚦 няма данни'; chip.style.color = '#94a3b8'; return; }
    chip.textContent = '🚦 ' + ok + '/' + D.length + ' отсечки'
                     + (geo ? (' · ' + geo + ' линии') : ' · БЕЗ линии');
    chip.style.color = geo ? '#86efac' : '#fbbf24';
  }, 5000);

  // ═══ 2) закръгляне на дългите десетични числа ═══
  var LONG = /\\b(\\d+)\\.(\\d{3,})\\b/g;
  function roundText(s){
    return s.replace(LONG, function(all){
      var v = parseFloat(all);
      if(!isFinite(v)) return all;
      return (Math.abs(v - Math.round(v)) < 0.05) ? String(Math.round(v)) : v.toFixed(1);
    });
  }
  function roundIn(root){
    try{
      var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
      var n, todo = [];
      while((n = w.nextNode())){
        if(n.nodeValue && LONG.test(n.nodeValue)){ LONG.lastIndex = 0; todo.push(n); }
        LONG.lastIndex = 0;
      }
      todo.forEach(function(t){ t.nodeValue = roundText(t.nodeValue); });
    }catch(e){}
  }
  function roundPass(){
    ['[data-ticker-raw]', '#zone-list', '.zone-item', '.leaflet-popup-content', '#ticker', '.ticker']
      .forEach(function(sel){
        document.querySelectorAll(sel).forEach(roundIn);
      });
    // и суровият текст на тикера, за да не се върне при преизчисляване
    document.querySelectorAll('[data-ticker-raw]').forEach(function(el){
      if(el.dataset.tickerRaw) el.dataset.tickerRaw = roundText(el.dataset.tickerRaw);
    });
  }
  roundPass();
  setInterval(roundPass, 3000);
  try{ new MutationObserver(roundPass).observe(document.body, {childList:true, subtree:true, characterData:true}); }catch(e){}

  // ═══ 3) надписи и на по-малките зони при зуум ═══
  function minRadiusFor(z){
    if(z >= 15) return 0;      // всичко
    if(z >= 14) return 130;
    if(z >= 13) return 190;
    return 240;
  }
  function shortName(zn){
    var n = (zn.name || '').replace(/\\([^)]*\\)/g, '').trim();
    n = n.replace(/^(жк|ЖК)\\s+/, '').replace(/^Мол\\s+/i, '').replace(/^Хотели\\s+/i, '');
    n = n.replace(/\\s*[–—-]\\s*.*$/, '').replace(/[⚠🚦]/g, '').trim();
    var w = n.split(/\\s+/).filter(Boolean);
    var out = w.slice(0, 2).join(' ');
    if(out.length > 16) out = w[0];
    if(out.length > 16) out = out.slice(0, 15) + '…';
    return out;
  }
  function rebuild(){
    try{
      var map = window.__leafletMap, Z = window.__ZONES;
      if(!map || !Z || !window.L) return;
      if(window.__labelLayer){ map.removeLayer(window.__labelLayer); window.__labelLayer = null; }
      var zoom = map.getZoom();
      if(zoom < 12) return;
      var minR = minRadiusFor(zoom);
      var sc = (window.__lastScores || {});
      var lg = L.layerGroup();
      Z.forEach(function(zn){
        if((zn.radius || 0) < minR) return;
        var txt = shortName(zn);
        if(!txt) return;
        var s = sc[zn.id];
        var badge = (typeof s === 'number' && zoom >= 13)
          ? ('<span style="opacity:.85;font-weight:800"> ' + s.toFixed(1) + '</span>') : '';
        var size = zoom >= 14 ? 11.5 : 11;
        lg.addLayer(L.marker([zn.lat, zn.lng], {
          interactive: false,
          icon: L.divIcon({ className: '', iconSize: [0, 0],
            html: '<div style="white-space:nowrap;font:600 ' + size + 'px/1.1 system-ui,sans-serif;'
                + 'color:#f4f8ff;text-shadow:0 1px 3px #000,0 0 7px #000,0 0 3px #000;'
                + 'transform:translate(-50%,-50%);pointer-events:none">'
                + (zn.icon || '') + ' ' + txt + badge + '</div>' })
        }));
      });
      lg.addTo(map);
      window.__labelLayer = lg;
    }catch(e){}
  }
  var t = setInterval(function(){
    if(window.__leafletMap && window.__ZONES){
      clearInterval(t);
      rebuild();
      try{ window.__leafletMap.on('zoomend', rebuild); }catch(e){}
      setInterval(rebuild, 60000);
    }
  }, 700);

  // пазим последните скорове, за да ги показваме в надписите
  var prev = window.__applyLive;
  window.__applyLive = function(scores){
    try{ if(prev) prev(scores); }catch(e){}
    try{ window.__lastScores = scores; }catch(e){}
  };
})();
"""
    rep.append('OK   индикатор за трафика (цъкаемо — показва точките на всяка отсечка)')
    rep.append('OK   закръгляне на дългите десетични числа')
    rep.append('OK   надписи и на малките зони: z13 >=190м, z14 >=130м, z15 всички + скор')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v36', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v36' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v36 + node --check + cache-bust v36')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

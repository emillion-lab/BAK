# -*- coding: utf-8 -*-
"""v35: трафикът се рисува като ЛИНИЯ по булеварда, не като точка.
Геометрията идва от TomTom (реалната форма на пътя). Линията е двуслойна —
тъмна основа отдолу и цветна отгоре, за да се чете на светла карта."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

if 'traffic-lines-v35' in cand:
    rep.append('SKIP v35 вече е приложен')
else:
    cand += """

// ------ traffic-lines-v35: отсечките като линии по булеварда ------
(function(){
  var LAYER = null, BASE = null;

  function colOf(x){
    if(x.closed) return '#7f1d1d';
    var r = x.ratio;
    if(r === null || r === undefined) return '#64748b';
    if(r >= 0.85) return '#22c55e';
    if(r >= 0.65) return '#84cc16';
    if(r >= 0.45) return '#eab308';
    if(r >= 0.30) return '#f97316';
    return '#dc2626';
  }
  function txtOf(x){
    if(x.closed) return '⛔ ЗАТВОРЕН';
    var r = x.ratio;
    if(r >= 0.85) return '🟢 СВОБОДНО';
    if(r >= 0.65) return '🟡 ЛЕКО ЗАБАВЯНЕ';
    if(r >= 0.45) return '🟠 БАВНО';
    if(r >= 0.30) return '🔴 ЗАДРЪСТЕНО';
    return '🔴 ТЕЖКО';
  }

  // колко закъснение носи отсечката
  function delayTxt(x){
    if(!x.curT || !x.freeT) return '';
    var d = x.curT - x.freeT;
    if(d < 20) return '';
    return ' · +' + (d >= 60 ? Math.round(d/60) + ' мин' : d + ' сек');
  }

  function draw(){
    try{
      var map = window.__leafletMap;
      if(!map || !window.L) return;
      var D = window.__trafficData;
      if(!D || !D.length) return;

      if(LAYER){ map.removeLayer(LAYER); LAYER = null; }
      if(BASE){ map.removeLayer(BASE); BASE = null; }
      BASE = L.layerGroup();
      LAYER = L.layerGroup();

      D.forEach(function(seg){
        var x = seg.data;
        if(!x || x.err || !x.coords || x.coords.length < 2) return;
        var col = colOf(x);
        // тъмна основа — за контраст върху светла карта
        BASE.addLayer(L.polyline(x.coords, {
          color:'#0f172a', weight:11, opacity:0.55, lineCap:'round', interactive:false
        }));
        var pl = L.polyline(x.coords, {
          color: col, weight: 7, opacity: 0.95, lineCap:'round'
        });
        pl.bindPopup(
          '<div style="font-family:sans-serif;min-width:180px">'
          + '<b style="font-size:14px">🚦 ' + seg.name + '</b><br>'
          + '<span style="color:' + col + ';font-weight:900">' + txtOf(x) + '</span>'
          + delayTxt(x) + '<br>'
          + '<span style="font-size:13px">' + (x.cur != null ? x.cur : '?') + ' км/ч '
          + 'при нормални ' + (x.free != null ? x.free : '?') + ' км/ч</span><br>'
          + '<span style="font-size:12px;opacity:.7">'
          + Math.round((x.ratio || 0) * 100) + '% от нормалната скорост</span>'
          + '<div style="font-size:11px;opacity:.55;margin-top:4px">TomTom · на 3 мин</div></div>'
        );
        LAYER.addLayer(pl);
      });

      BASE.addTo(map);
      LAYER.addTo(map);
      LAYER.bringToFront && LAYER.bringToFront();
    }catch(e){}
  }

  // чакаме данните от v34 и картата
  var t = setInterval(function(){
    if(window.__leafletMap && window.__trafficData){ draw(); }
  }, 5000);

  window.__redrawTraffic = draw;
})();
"""
    rep.append('OK   линии по булевардите (двуслойни, с popup)')

# ── v34 да публикува данните с геометрия ──
old = """        (d.data || []).forEach(function(x, i){
          if(!x || x.err || !SEG[i]) return;
          LIVE[SEG[i].id] = x;
        });
        LAST = Date.now();"""
new = """        var pub = [];
        (d.data || []).forEach(function(x, i){
          if(!x || !SEG[i]) return;
          if(!x.err) LIVE[SEG[i].id] = x;
          pub.push({id:SEG[i].id, name:SEG[i].name, data:x});
        });
        window.__trafficData = pub;
        LAST = Date.now();
        try{ if(window.__redrawTraffic) window.__redrawTraffic(); }catch(e){}"""
if cand.count(old) == 1:
    cand = cand.replace(old, new, 1)
    rep.append('OK   данните с геометрия се публикуват за рисуване')
else:
    rep.append('⚠ не намерих къде v34 приема данните (%d) — линиите ще чакат таймера' % cand.count(old))

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v35', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v35' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v35 + node --check + cache-bust v35')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

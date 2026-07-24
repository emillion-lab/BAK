# -*- coding: utf-8 -*-
"""v45 ВИЗУАЛЕН РЕМОНТ:
1) БЪГ: в списъка със събития се виждаше буквално \\n вместо нови редове
2) Евлоги беше залепнал на Васил Левски — отместен на юг по реката;
   отделната отсечка Васил Левски отпада (дублираше го и трупаше картата)
3) надписите се появяват по-късно — картата спира да е претрупана
4) КЪРК банерът не покрива заглавието и не се крие зад бутоните
5) бутон за скриване на надписите и линиите (когато искаш чиста карта)
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (1) буквалното \n в съобщението за събития ──
fixes = [
    ("'\\\\n   🚕 pickup '", "'\\n   🚕 pickup '"),
    (".join('\\\\n')", ".join('\\n')"),
    ("'\\\\n\\\\nИзточник: SEV ('", "'\\n\\nИзточник: SEV ('"),
    ("+'\\\\n\\\\nИзточник: SEV (", "+'\\n\\nИзточник: SEV ("),
]
n_fixed = 0
for old, new in fixes:
    if old in cand:
        cand = cand.replace(old, new)
        n_fixed += 1
if n_fixed:
    rep.append('OK   поправени %d места с буквално \\n в съобщенията' % n_fixed)
else:
    # общо: всяко \\n вътре в alert(...) низ
    before = cand.count('\\\\n')
    if before:
        cand = cand.replace('\\\\n', '\\n')
        rep.append('OK   поправени %d места с буквално \\n (общо)' % before)
    else:
        rep.append('SKIP буквалното \\n не е намерено')

# ── (2) Евлоги надолу по реката, Васил Левски отпада ──
old_ev = "{id:'jam_evlogi',  lat:42.6867, lng:23.3293, name:'Евлоги Георгиев'}"
new_ev = "{id:'jam_evlogi',  lat:42.6845, lng:23.3245, name:'Евлоги Георгиев'}"
if old_ev in cand:
    cand = cand.replace(old_ev, new_ev, 1)
    rep.append('OK   Евлоги -> 42.6845,23.3245 (беше залепнал за Васил Левски)')

old_evb = "{id:'jam_evlogi_b', lat:42.6870, lng:23.3287, name:'Хр. Георгиев (обратно)'}"
new_evb = "{id:'jam_evlogi_b', lat:42.6849, lng:23.3239, name:'Хр. Георгиев (обратно)'}"
if old_evb in cand:
    cand = cand.replace(old_evb, new_evb, 1)
    rep.append('OK   Хр. Георгиев (обратно) -> 42.6849,23.3239')

pat_lev = re.compile(r",\s*\{id:'jam_levski',[^}]*\}")
if pat_lev.search(cand):
    cand = pat_lev.sub('', cand, count=1)
    rep.append('OK   отсечката Васил Левски отпада (дублираше Евлоги)')

# ── (3)(4)(5) визуален ремонт ──
if 'visual-v45' in cand:
    rep.append('SKIP v45 вече е приложен')
else:
    cand += """

// ------ visual-v45 ------
(function(){
  // ═══ надписите се появяват по-късно ═══
  window.__labelMinRadius = function(z){
    if(z >= 16) return 0;        // всичко
    if(z >= 15) return 150;
    if(z >= 14) return 260;
    if(z >= 13) return 380;
    return 520;                  // z12 — само най-големите
  };

  // ═══ КЪРК банерът: под заглавието, над картата ═══
  try{
    var st = document.createElement('style');
    st.id = 'v45-style';
    st.textContent =
      '#karyk-banner{position:relative!important;z-index:5!important;'
      + 'max-width:100%!important;box-sizing:border-box!important;'
      + 'transform:none!important;opacity:1!important;'
      + 'margin:4px 6px!important;padding:6px 9px!important;'
      + 'font-size:11.5px!important;line-height:1.35!important;'
      + 'border-radius:8px!important;}'
      + '#karyk-btn{transform:scale(.75)!important;transform-origin:left bottom!important;'
      + 'z-index:1200!important;}'
      // popup: събитията се отделят по-ясно
      + '.leaflet-popup-content>div{margin-bottom:5px!important;}'
      + '.leaflet-popup-content hr{border:0!important;border-top:1px solid rgba(148,163,184,.28)!important;'
      + 'margin:7px 0!important;}';
    document.head.appendChild(st);
  }catch(e){}

  // ═══ бутон за чиста карта ═══
  var clean = false;
  var btn = document.createElement('div');
  btn.textContent = '👁 чисто';
  btn.style.cssText = 'position:fixed;right:8px;top:50%;z-index:1400;background:#0b1220e0;'
    + 'color:#cbd5e1;border:1px solid #475569;border-radius:9px;padding:6px 9px;'
    + 'font:700 11px system-ui,sans-serif;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.5)';
  btn.onclick = function(){
    clean = !clean;
    btn.textContent = clean ? '👁 всичко' : '👁 чисто';
    btn.style.background = clean ? '#1e3a5fe0' : '#0b1220e0';
    try{
      var map = window.__leafletMap;
      if(!map) return;
      if(clean){
        if(window.__labelLayer){ map.removeLayer(window.__labelLayer); window.__labelLayer = null; }
        window.__labelsOff = true;
      } else {
        window.__labelsOff = false;
      }
    }catch(e){}
  };
  document.body.appendChild(btn);

  // ═══ пренаписване на надписите с новите прагове ═══
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
      if(window.__labelsOff) return;
      var zoom = map.getZoom();
      if(zoom < 12) return;
      var minR = window.__labelMinRadius(zoom);
      var sc = (window.__lastScores || {});
      var lg = L.layerGroup();
      Z.forEach(function(zn){
        if((zn.radius || 0) < minR) return;
        var txt = shortName(zn);
        if(!txt) return;
        var s = sc[zn.id];
        // скорът се показва само отблизо и само ако си заслужава
        var badge = (typeof s === 'number' && zoom >= 15 && s >= 1.2)
          ? ('<span style="opacity:.9"> ' + s.toFixed(1) + '</span>') : '';
        lg.addLayer(L.marker([zn.lat, zn.lng], {
          interactive: false,
          icon: L.divIcon({ className: '', iconSize: [0, 0],
            html: '<div style="white-space:nowrap;font:600 11px/1.1 system-ui,sans-serif;'
                + 'color:#f4f8ff;text-shadow:0 1px 3px #000,0 0 7px #000;'
                + 'transform:translate(-50%,-50%);pointer-events:none">'
                + (zn.icon || '') + ' ' + txt + badge + '</div>' })
        }));
      });
      lg.addTo(map);
      window.__labelLayer = lg;
    }catch(e){}
  }
  window.__rebuildLabels = rebuild;
  var t = setInterval(function(){
    if(window.__leafletMap && window.__ZONES){
      clearInterval(t);
      rebuild();
      try{ window.__leafletMap.on('zoomend', rebuild); }catch(e){}
      setInterval(rebuild, 60000);
    }
  }, 700);
})();
"""
    rep.append('OK   надписи: z13>=380м, z14>=260м, z15>=150м, z16 всичко')
    rep.append('OK   скорът в надписа само при зуум 15+ и стойност над 1.2')
    rep.append('OK   КЪРК банерът не покрива заглавието')
    rep.append('OK   бутон "👁 чисто" за скриване на надписите')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v45', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v45' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    segs = len(re.findall(r"\{id:'jam_[a-z_]+',\s*lat:", cand))
    rep.append('отсечки: %d · разход ~%d от 2500' % (segs, segs * 125))
    rep.append('OK v45 + node --check + cache-bust v45')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

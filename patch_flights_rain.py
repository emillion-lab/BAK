# -*- coding: utf-8 -*-
"""v28: (1) МАХА дублирането — приложението вече има свой списък с пристигащи
           на ЦАС (с международните вътре), моят от v26 беше излишен
       (2) popup-ите се ограничават по височина и се скролват — вече не заемат
           целия екран и се вижда и горе, и долу
       (3) НОВА зона: международни автобуси, отделно кръгче до ЦАС
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (1) изключваме моя дублиращ блок от v26 ──
old_guard = "if(!/Централна автогара/i.test(txt)) return;"
new_guard = ("if(!/Централна автогара/i.test(txt)) return;\n"
             "      // приложението вече си има списък с пристигащи -> не дублираме\n"
             "      if(/по час на пристигане|модел на превозвача|Пристигащи на ЦАС/i.test(txt)) return;")
if cand.count(old_guard) == 1:
    cand = cand.replace(old_guard, new_guard)
    rep.append('OK   v26 вече не дублира собствения списък на приложението')
else:
    rep.append('SKIP guard за ЦАС (намерени %d)' % cand.count(old_guard))

# ── (2) popup: ограничена височина + скрол ──
if 'popup-scroll-v28' not in cand:
    css = ("/*popup-scroll-v28*/"
           ".leaflet-popup-content{max-height:52vh!important;overflow-y:auto!important;"
           "overflow-x:hidden!important;-webkit-overflow-scrolling:touch;}"
           ".leaflet-popup-content::-webkit-scrollbar{width:5px}"
           ".leaflet-popup-content::-webkit-scrollbar-thumb{background:rgba(120,140,170,.55);border-radius:3px}"
           ".leaflet-popup-content-wrapper{max-height:56vh!important;}")
    cand += """

// ------ popup-scroll-v28: popup-ите да не заемат целия екран ------
(function(){
  try{
    var st = document.createElement('style');
    st.textContent = %s;
    document.head.appendChild(st);
  }catch(e){}
})();
""" % repr(css).replace('"', "'")
    rep.append('OK   popup-ите: макс. 52%% височина + скрол')

# ── (3) нова зона за международните автобуси ──
if 'cas_intl' in cand:
    rep.append('SKIP зоната cas_intl вече съществува')
else:
    m = re.search(r'\{\s*id:"cab_north"[^}]*\}', cand)
    if m:
        obj = m.group(0)
        ztype = (re.search(r'type:"([^"]+)"', obj) or [None, 'transit'])[1]
        newz = ('{ id:"cas_intl", name:"🌍 Международни автобуси (ЦАС, сектори 36–41)", '
                'icon:"🌍", lat:42.7110, lng:23.3247, radius:170, type:"%s", '
                'wazeName:"Централна автогара София международни линии" }' % ztype)
        cand = cand.replace(obj, obj + ',\n  ' + newz, 1)
        rep.append('OK   нова зона cas_intl 42.7110,23.3247 (до ЦАС, отделно кръгче)')
    else:
        rep.append('SKIP cab_north не е намерена — не мога да закача новата зона')

# ── деманд за новата зона: само от международните линии ──
if 'cas-intl-score-v28' not in cand:
    cand += """

// ------ cas-intl-score-v28: скор на международната зона ------
(function(){
  var SCHED = null, LIVE = [];
  fetch('bus-schedule.json?v='+Date.now()).then(function(r){return r.json()})
    .then(function(d){ SCHED = d; }).catch(function(){});
  function pullLive(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 4*3600000;
      LIVE = fresh ? (d.arrivals||[]).filter(function(a){ return a.intl; }) : [];
    }).catch(function(){});
  }
  pullLive(); setInterval(pullLive, 180000);

  function intlNow(){
    var now = new Date(), nowMin = now.getHours()*60 + now.getMinutes();
    var recent = 0, soon = 0, names = [];
    LIVE.forEach(function(a){
      var m = /^(\\d{1,2}):(\\d{2})$/.exec(a.time||''); if(!m) return;
      var d = (+m[1])*60 + (+m[2]) - nowMin;
      if(d <= 0 && d >= -25){ recent++; names.push(a.from); }
      else if(d > 0 && d <= 40){ soon++; names.push(a.from); }
    });
    if(SCHED && SCHED.routes){
      SCHED.routes.forEach(function(rt){
        if(!rt.intl) return;
        var dur = rt.duration_min || 0;
        (rt.departures||[]).forEach(function(dep){
          var m = /^(\\d{1,2}):(\\d{2})$/.exec(dep); if(!m) return;
          var t = (+m[1])*60 + (+m[2]) + dur;
          var d = t - nowMin;
          if(d < -180) d += 1440;
          var nm = (rt.name||'').replace(/\\s*→.*/,'');
          if(d <= 0 && d >= -25){ recent++; names.push(nm); }
          else if(d > 0 && d <= 40){ soon++; names.push(nm); }
        });
      });
    }
    return {recent:recent, soon:soon, names:names.slice(0,3)};
  }

  var prev = window.__applyLive;
  window.__applyLive = function(scores){
    try{ if(prev) prev(scores); }catch(e){}
    try{
      if(typeof scores.cas_intl !== 'number') return;
      var c = intlNow();
      // международните носят багаж и почти винаги взимат такси
      var s = c.recent*1.5 + c.soon*0.9;
      scores.cas_intl = s > 0 ? Math.min(5, 0.6 + s) : 0.3;
      window.__intlInfo = c;
    }catch(e){}
  };
})();
"""
    rep.append('OK   скор на международната зона (само intl линии, тежест x1.5)')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    ids = re.findall(r'\{\s*id:"([^"]+)"\s*,\s*name:', cand)
    rep.append('зони: %d' % len(ids))
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v28', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda mm: mm.group(1) + 'bak-v28' + mm.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v28 + node --check + cache-bust v28')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

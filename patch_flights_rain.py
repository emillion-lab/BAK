# -*- coding: utf-8 -*-
"""v34: РЕАЛЕН ТРАФИК от TomTom вместо разписание.
Скоростта на отсечката се сравнява с нормалната за нея; кръгът и статусът
се оцветяват по реалното забавяне. Ключът е Worker secret, не в кода."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

if 'traffic-live-v34' in cand:
    rep.append('SKIP v34 вече е приложен')
else:
    cand += """

// ------ traffic-live-v34: реален трафик (TomTom през mvr-proxy) ------
(function(){
  var EP = 'https://mvr-proxy.mihov-emil.workers.dev/traffic?pts=';
  // отсечките, които следим (същите точки като зоните)
  var SEG = [
    {id:'jam_orl',     lat:42.6906, lng:23.3374, name:'Орлов мост'},
    {id:'jam_tsar',    lat:42.6752, lng:23.3587, name:'Цариградско (Плиска)'},
    {id:'jam_ndk',     lat:42.6745, lng:23.3028, name:'бул. България'},
    {id:'jam_serdika', lat:42.7049, lng:23.3239, name:'бул. Сливница'}
  ];
  var LIVE = {};      // id -> {cur, free, ratio, closed}
  var LAST = 0, FAILED = 0;

  function pull(){
    if(FAILED >= 3) return;                       // не дъним при липсващ ключ
    var pts = SEG.map(function(s){ return s.lat + ',' + s.lng; }).join(';');
    fetch(EP + encodeURIComponent(pts))
      .then(function(r){ return r.json(); })
      .then(function(d){
        if(d && d.error){ FAILED++; window.__trafficErr = d.error; return; }
        FAILED = 0;
        (d.data || []).forEach(function(x, i){
          if(!x || x.err || !SEG[i]) return;
          LIVE[SEG[i].id] = x;
        });
        LAST = Date.now();
      })
      .catch(function(){ FAILED++; });
  }
  pull(); setInterval(pull, 180000);              // на 3 мин (кешът в worker-а е също 3)

  // забавяне -> скор
  function scoreOf(x){
    if(!x) return null;
    if(x.closed) return 4.8;
    var r = x.ratio;
    if(r === null || r === undefined) return null;
    if(r >= 0.85) return 0.4;
    if(r >= 0.65) return 1.2;
    if(r >= 0.45) return 2.2;
    if(r >= 0.30) return 3.2;
    return 4.2;
  }
  function label(x){
    if(x.closed) return {t:'⛔ ЗАТВОРЕН УЧАСТЪК', c:'#ef4444'};
    var r = x.ratio;
    if(r >= 0.85) return {t:'🟢 СВОБОДНО', c:'#22c55e'};
    if(r >= 0.65) return {t:'🟡 ЛЕКО ЗАБАВЯНЕ', c:'#eab308'};
    if(r >= 0.45) return {t:'🟠 БАВНО', c:'#f97316'};
    if(r >= 0.30) return {t:'🔴 ЗАДРЪСТЕНО', c:'#ef4444'};
    return {t:'🔴 ТЕЖКО ЗАДРЪСТВАНЕ', c:'#dc2626'};
  }

  // скоровете на зоните следват реалния трафик
  var prev = window.__applyLive;
  window.__applyLive = function(scores){
    try{ if(prev) prev(scores); }catch(e){}
    try{
      if(Date.now() - LAST > 15*60000) return;     // данните са стари -> оставяме модела
      SEG.forEach(function(s){
        var sc = scoreOf(LIVE[s.id]);
        if(sc !== null && typeof scores[s.id] === 'number') scores[s.id] = sc;
      });
    }catch(e){}
  };

  // popup: истински числа вместо прогноза по час
  function fix(el){
    try{
      if(!el) return;
      var txt = el.textContent || '';
      var hit = null;
      for(var i = 0; i < SEG.length; i++){
        var key = SEG[i].name.split(' ')[0];
        if(txt.indexOf(key) >= 0 && /Задръстване|ЗАДРЪСТЕНО|СВОБОДНО|Пик:/i.test(txt)){ hit = SEG[i]; break; }
      }
      if(!hit) return;
      var x = LIVE[hit.id];
      var stamp = x ? ('live' + Math.round((x.ratio||0)*100)) : 'nolive';
      if(el.dataset && el.dataset.tr34 === stamp) return;
      if(el.dataset) el.dataset.tr34 = stamp;

      var old = el.querySelector('.tr34');
      if(old) old.remove();

      var html;
      if(!x || Date.now() - LAST > 15*60000){
        html = '<div class="tr34" style="margin-top:6px;padding:5px 8px;border-radius:6px;'
             + 'background:rgba(148,163,184,.12);border-left:3px solid #94a3b8;font-size:11px;'
             + 'color:#64748b">📡 Няма живи данни за трафика — показаното е по модел</div>';
      } else {
        var L = label(x);
        var pct = Math.round((x.ratio || 0) * 100);
        html = '<div class="tr34" style="margin-top:6px;padding:7px 9px;border-radius:7px;'
             + 'background:rgba(2,6,23,.35);border-left:3px solid ' + L.c + ';font-size:12px">'
             + '<b style="color:' + L.c + '">' + L.t + '</b><br>'
             + '<span style="opacity:.85">' + (x.cur != null ? x.cur : '?') + ' км/ч '
             + 'при нормални ' + (x.free != null ? x.free : '?') + ' км/ч · <b>' + pct + '%</b></span>'
             + '<div style="opacity:.55;font-size:10px;margin-top:3px">TomTom · живо, обновява се на 3 мин</div></div>';
        // старият статус по разписание вече е излишен
        el.innerHTML = el.innerHTML
          .replace(/🔴\\s*ЗАДРЪСТЕНО СЕГА/g, '')
          .replace(/🟢\\s*СВОБОДНО \\(извън пиков час\\)/g, '')
          .replace(/🟢\\s*В МОМЕНТА СВОБОДНО/g, '');
      }
      el.insertAdjacentHTML('beforeend', html);
    }catch(e){}
  }
  function scan(){
    try{ document.querySelectorAll('.leaflet-popup-content').forEach(fix); }catch(e){}
  }
  scan(); setInterval(scan, 4000);
  try{ new MutationObserver(scan).observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();
"""
    rep.append('OK   реален трафик: 4 отсечки, скор по забавяне, живи числа в popup-а')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v34', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v34' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v34 + node --check + cache-bust v34')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

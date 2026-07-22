# -*- coding: utf-8 -*-
"""v5: (1) клик от списъка -> скролва картата във фокус (+ invalidateSize)
       (2) Централна автогара: live скор от реалните пристигания (не е зелена,
           когато преди 12 мин са слезли хора или след 18 мин идват 2 автобуса)
       (3) ЖП гара: честен статус вместо тишина"""
import re, subprocess, shutil

rep = []
src = open('app.js', encoding='utf-8').read()

if 'bak-v5' in src:
    rep.append('SKIP v5 вече е приложен')
else:
    # --- (1) фокус на картата при клик от списъка ---
    old = ("setTimeout(()=>{map.setView([${z.lat},${z.lng}],'${zid}'==='airport'?14:15);")
    new = ("setTimeout(()=>{var _m=document.getElementById('map');"
           "if(_m&&_m.scrollIntoView)_m.scrollIntoView({behavior:'smooth',block:'center'});"
           "if(map.invalidateSize)map.invalidateSize();"
           "map.setView([${z.lat},${z.lng}],'${zid}'==='airport'?14:15);")
    if src.count(old) != 1:
        rep.append('FAIL zone-list onclick count=%d' % src.count(old))
        cand = None
    else:
        cand = src.replace(old, new)
        rep.append('OK (1) map focus при клик от списъка')

    if cand:
        cand += """

// ------ bak-v5 ------
// (2) Централна автогара: реален деманд от пристигащите автобуси
(function(){
  var busState = {recent:0, soon:0, ts:0};

  function pull(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 100*60000;
      if(!fresh){ busState={recent:0,soon:0,ts:Date.now()}; return; }
      var now=new Date(), nowMin=now.getHours()*60+now.getMinutes();
      var recent=0, soon=0;
      (d.arrivals||[]).forEach(function(a){
        var m=/^(\\d{1,2}):(\\d{2})$/.exec(a.time||''); if(!m) return;
        var delta=(+m[1])*60+(+m[2])-nowMin;
        if(delta<=0 && delta>=-15) recent++;        // слезли са преди <=15 мин
        else if(delta>0 && delta<=25) soon++;       // идват до 25 мин
      });
      busState={recent:recent, soon:soon, ts:Date.now()};
    }).catch(function(e){});
  }
  pull(); setInterval(pull, 120000);

  if(typeof computeScores === 'function'){
    var _origCompute = computeScores;
    computeScores = function(h){
      var s = _origCompute(h);
      try{
        if(s && typeof s['cab_north'] === 'number'){
          // всеки току-що слязъл автобус тежи най-много (хората са на място СЕГА)
          var boost = Math.min(2.6, busState.recent*0.85 + busState.soon*0.65);
          if(boost>0) s['cab_north'] = s['cab_north'] + boost;
        }
      }catch(e){}
      return s;
    };
  }

  // видим маркер защо е горещо — малък надпис в списъка на автогарата
  setInterval(function(){
    var items=document.querySelectorAll('#zone-list .zone-item');
    Array.prototype.slice.call(items).forEach(function(it){
      var nm=it.querySelector('.zone-name');
      if(!nm || nm.textContent.indexOf('Централна автогара')<0) return;
      var sub=it.querySelector('.zone-sub');
      var txt='';
      if(busState.recent) txt='🚌 '+busState.recent+' слезли <15 мин';
      if(busState.soon) txt+=(txt?' · ':'')+busState.soon+' идват <25 мин';
      if(!txt) return;
      if(!sub){
        sub=document.createElement('div');
        sub.className='zone-sub';
        nm.parentElement.appendChild(sub);
      }
      sub.textContent=txt;
    });
  }, 15000);
})();

// (3) ЖП гара: честен статус, докато няма разписание
(function(){
  if(typeof showTransitPopup !== 'function') return;
  var _origTransit = showTransitPopup;
  showTransitPopup = function(zid){
    var r = _origTransit(zid);
    if(zid==='cjp'){
      setTimeout(function(){
        var pops=document.querySelectorAll('.leaflet-popup-content');
        if(!pops.length) return;
        var p=pops[pops.length-1];
        if(p.innerHTML.indexOf('bdz-note')>=0) return;
        p.innerHTML += '<div class="bdz-note" style="margin-top:8px;padding:7px 9px;border-radius:7px;'+
          'background:rgba(56,189,248,.08);border-left:3px solid #38bdf8;font-size:12px;color:#94a3b8">'+
          '🚂 Живо разписание на БДЖ — предстои.<br>Засега: пиковете са ~07:30, 13:00, 18:30, 21:40 '+
          '(пристигания от Пловдив/Варна/Бургас).</div>';
      }, 200);
    }
    return r;
  };
})();
"""
        open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
        r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
        if r.returncode == 0:
            shutil.move('/tmp/app.c.js', 'app.js')
            idx = open('index.html', encoding='utf-8').read()
            idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260722v5', idx)
            open('index.html', 'w', encoding='utf-8').write(idx)
            rep.append('OK v5 пълен + node --check + cache-bust v5')
        else:
            rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

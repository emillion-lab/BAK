# -*- coding: utf-8 -*-
"""v6: (1) FIX на v5 — computeScores връща {scores,activeEvents}; boost-овете
           се прилагат вътре чрез window.__applyLive
       (2) КЪРК с реални сигнали: летище (полети), автогара (автобуси), ЖП (влакове)
           + наказание за разстояние — вече не праща сляпо на Борово
       (3) влаковете влизат в деманда на Централна ЖП гара"""
import re, subprocess, shutil

rep = []
src = open('app.js', encoding='utf-8').read()

if 'bak-v6' in src:
    rep.append('SKIP v6 вече е приложен')
else:
    cand = src

    # --- A: закачаме live boost навсякъде, където се четат scores ---
    pairs = [
        ("const {scores,activeEvents}=computeScores(hour);",
         "const {scores,activeEvents}=computeScores(hour); if(window.__applyLive)window.__applyLive(scores);"),
        ("const {scores,activeEvents}=computeScores(currentHour);",
         "const {scores,activeEvents}=computeScores(currentHour); if(window.__applyLive)window.__applyLive(scores);"),
    ]
    for old, new in pairs:
        n = cand.count(old)
        rep.append('A "%s..." x%d' % (old[:38], n))
        if n:
            cand = cand.replace(old, new)

    n = cand.count("const {scores}=computeScores(currentHour);")
    rep.append('A2 {scores}=computeScores(currentHour) x%d' % n)
    cand = cand.replace("const {scores}=computeScores(currentHour);",
                        "const {scores}=computeScores(currentHour); if(window.__applyLive)window.__applyLive(scores);")

    # --- B: КЪРК кандидатите включват хъбовете ---
    old_f = "ZONES.filter(z=>z.type==='karyk'||z.type==='residential_lux'||z.type==='residential')"
    new_f = ("ZONES.filter(z=>z.type==='karyk'||z.type==='residential_lux'||z.type==='residential'"
             "||(window.__liveDemand&&window.__liveDemand.hub&&window.__liveDemand.hub[z.id]!==undefined))")
    nf = cand.count(old_f)
    rep.append('B filter x%d' % nf)
    if nf == 1:
        cand = cand.replace(old_f, new_f)

    old_m = ".map(z=>({z,ks:computeKarykScore(z.id,scores)}))"
    new_m = (".map(z=>({z,ks:(window.__karykLive?window.__karykLive(z,computeKarykScore(z.id,scores),"
             "typeof userLat==='number'?userLat:null,typeof userLng==='number'?userLng:null)"
             ":computeKarykScore(z.id,scores))}))")
    nm = cand.count(old_m)
    rep.append('B map x%d' % nm)
    if nm == 1:
        cand = cand.replace(old_m, new_m)

    if nf != 1 or nm != 1:
        rep.append('WARN КЪРК замените не са уникални — пропускам ги')
        cand = src if (nf > 1 or nm > 1) else cand

    # --- C: живият мост (отвън, чрез window) ---
    cand += """

// ------ bak-v6: жив мост към вътрешния scope ------
(function(){
  window.__liveDemand = {hub:{}, boost:{}};

  function num(x){ return typeof x==='number' && isFinite(x) ? x : 0; }

  function pullFlights(){
    fetch('flight-cache.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var now=Date.now(), soon=0;
      (d.data||[]).forEach(function(f){
        if(f.flight_status==='cancelled') return;
        var a=f.arrival||{}, land=a.estimated||a.scheduled;
        if(!land) return;
        var lt=new Date(land).getTime(); if(isNaN(lt)) return;
        var xs=lt+12*60000;                       // начало на изходния прозорец
        if(xs>now-20*60000 && xs<now+75*60000) soon++;
      });
      window.__liveDemand.hub.airport = soon ? Math.min(5, 1.0 + soon*0.6) : 0;
      window.__liveDemand.flights = soon;
    }).catch(function(e){});
  }

  function pullBuses(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 100*60000;
      if(!fresh){ window.__liveDemand.hub.cab_north=0; window.__liveDemand.boost.cab_north=0; return; }
      var now=new Date(), nowMin=now.getHours()*60+now.getMinutes(), recent=0, soon=0;
      (d.arrivals||[]).forEach(function(a){
        var m=/^(\\d{1,2}):(\\d{2})$/.exec(a.time||''); if(!m) return;
        var delta=(+m[1])*60+(+m[2])-nowMin;
        if(delta<=0 && delta>=-15) recent++;
        else if(delta>0 && delta<=25) soon++;
      });
      window.__liveDemand.boost.cab_north = Math.min(2.6, recent*0.85 + soon*0.65);
      window.__liveDemand.hub.cab_north   = (recent+soon) ? Math.min(4.5, 1.0 + recent*0.9 + soon*0.7) : 0;
      window.__liveDemand.buses = {recent:recent, soon:soon};
    }).catch(function(e){});
  }

  function pullTrains(){
    fetch('train-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 120*60000;
      if(!fresh){ window.__liveDemand.hub.cjp=0; window.__liveDemand.boost.cjp=0; return; }
      var now=new Date(), nowMin=now.getHours()*60+now.getMinutes(), w=0, n=0;
      (d.arrivals||[]).forEach(function(a){
        var m=/^(\\d{1,2}):(\\d{2})$/.exec(a.time||''); if(!m) return;
        var delta=(+m[1])*60+(+m[2])+num(a.delay)-nowMin;
        if(delta>=-15 && delta<=30){ w += num(a.weight)||0.5; n++; }
      });
      window.__liveDemand.boost.cjp = Math.min(2.4, w*1.05);
      window.__liveDemand.hub.cjp   = n ? Math.min(4.5, 1.0 + w*1.15) : 0;
      window.__liveDemand.trains = n;
    }).catch(function(e){});
  }

  function pull(){ pullFlights(); pullBuses(); pullTrains(); }
  pull(); setInterval(pull, 120000);

  // прилага живите boost-ове върху нормалните demand точки
  window.__applyLive = function(scores){
    try{
      var b = window.__liveDemand.boost || {};
      if(typeof scores.cab_north === 'number' && b.cab_north) scores.cab_north += b.cab_north;
      if(typeof scores.cjp === 'number' && b.cjp) scores.cjp += b.cjp;
    }catch(e){}
  };

  // КЪРК: хъбовете се състезават с кварталите + наказание за разстояние
  window.__karykLive = function(z, baseKs, ulat, ulng){
    var ks = num(baseKs);
    try{
      var h = (window.__liveDemand.hub||{})[z.id];
      if(typeof h === 'number' && h > 0) ks = Math.max(ks, h);
      if(typeof ulat === 'number' && typeof ulng === 'number'){
        var dx=(z.lat-ulat)*111, dy=(z.lng-ulng)*82;
        var km=Math.sqrt(dx*dx+dy*dy);
        if(km > 5) ks -= Math.min(1.3, (km-5)*0.11);   // далече = губиш време на празно
      }
    }catch(e){}
    return ks;
  };

  // подсказка защо е горещо — в КЪРК банера
  setInterval(function(){
    var el=document.getElementById('karyk-hint');
    if(!el || !document.body.classList.contains('karyk-active')) return;
    var L=window.__liveDemand||{}, bits=[];
    if(L.flights) bits.push('✈️ '+L.flights+' изхода');
    if(L.buses && (L.buses.recent+L.buses.soon)) bits.push('🚌 '+(L.buses.recent+L.buses.soon));
    if(L.trains) bits.push('🚂 '+L.trains);
    if(!bits.length) return;
    if(el.dataset.live === bits.join()) return;
    el.dataset.live = bits.join();
    var tag=el.querySelector('.live-tag');
    if(!tag){ tag=document.createElement('span'); tag.className='live-tag';
              tag.style.cssText='margin-left:8px;font-size:12px;opacity:.85'; el.appendChild(tag); }
    tag.textContent='· '+bits.join(' · ');
  }, 10000);
})();
"""

    open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
    r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
    if r.returncode == 0:
        shutil.move('/tmp/app.c.js', 'app.js')
        idx = open('index.html', encoding='utf-8').read()
        idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260722v6', idx)
        open('index.html', 'w', encoding='utf-8').write(idx)
        rep.append('OK v6 + node --check + cache-bust v6')
    else:
        rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

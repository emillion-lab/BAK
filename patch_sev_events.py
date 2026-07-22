# -*- coding: utf-8 -*-
"""Добавя SEV events слой в app.js (append-only): чете /SEV/events.json,
показва 🎫 маркери + чип 'N събития днес' с dropoff/pickup прозорци.
Старият theatre-events-layer остава (той е dormant - датата му не съвпада)."""
import re, subprocess, shutil

rep = []
src = open('app.js', encoding='utf-8').read()

if 'sev-events-layer' in src:
    rep.append('SKIP вече е добавено')
else:
    block = """

// ------ SEV събития (/SEV/events.json): 🎫 маркери + чип с demand прозорци ------
// sev-events-layer
(function(){
  function ready(cb){
    var t=setInterval(function(){ if(window.map&&window.L){clearInterval(t);cb();} },500);
    setTimeout(function(){clearInterval(t)},30000);
  }
  function hm(d){return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'});}
  ready(function(){
    fetch('/SEV/events.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      if(!d.events||!d.events.length) return;
      var now=Date.now(), DUR=150*60000, POST=45*60000, PRE=2*3600000;
      var todayEnd=new Date(); todayEnd.setHours(23,59,59,999);
      var evs=d.events.map(function(e){
        var s=new Date(e.start).getTime();
        return {n:e.name,v:e.venue,lat:e.lat,lon:e.lon,cap:e.cap||600,s:s,e:s+DUR,src:e.src};
      }).filter(function(e){
        return e.e+POST>now && e.s<=todayEnd.getTime()+36*3600000; // до утре вечер
      }).sort(function(a,b){return a.s-b.s});
      if(!evs.length) return;
      var layer=L.layerGroup();
      evs.forEach(function(e){
        if(!e.lat) return;
        var big=e.cap>=8000, mid=e.cap>=2500;
        var col=big?'#f85149':(mid?'#d29922':'#3fb950');
        var mk=L.marker([e.lat,e.lon],{icon:L.divIcon({className:'',
          html:'<div style=\\"font-size:'+(big?26:20)+'px;filter:drop-shadow(0 1px 3px rgba(0,0,0,.7))\\">🎫</div>',
          iconSize:[26,26],iconAnchor:[13,13]})});
        var s=new Date(e.s),en=new Date(e.e);
        mk.bindPopup('<div style=\\"font-family:sans-serif;min-width:190px\\">'+
          '<b style=\\"font-size:14px\\">'+e.n+'</b>'+
          '<div style=\\"color:#64748b;font-size:12px;margin:3px 0\\">'+e.v+' · ~'+e.cap.toLocaleString('bg')+' души</div>'+
          '<div style=\\"font-size:13px\\">Начало '+hm(s)+' · Край ~'+hm(en)+'</div>'+
          '<div style=\\"font-size:13px;color:'+col+';font-weight:900;margin-top:4px\\">'+
          '🚕 Dropoff '+hm(new Date(e.s-PRE))+'–'+hm(s)+'<br>🚕 Pickup '+hm(en)+'–'+hm(new Date(e.e+POST))+'</div></div>');
        layer.addLayer(mk);
      });
      layer.addTo(window.map);
      var chip=document.createElement('div');
      chip.style.cssText='position:fixed;left:8px;bottom:174px;z-index:1500;background:#0c1f2ef0;color:#bae6fd;border:1px solid #38bdf8;border-radius:10px;padding:7px 11px;font-family:sans-serif;font-size:13px;font-weight:900;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5)';
      chip.textContent='🎫 '+evs.length+' събития';
      chip.onclick=function(){
        alert(evs.map(function(e){
          var en=new Date(e.e);
          return hm(new Date(e.s))+' '+e.n.slice(0,40)+' @ '+(e.v||'?')+'\\\\n   🚕 pickup '+hm(en)+'–'+hm(new Date(e.e+45*60000));
        }).join('\\\\n')+'\\\\n\\\\nИзточник: SEV ('+(d.sources_ok||[]).join('+')+')');
      };
      document.body.appendChild(chip);
    }).catch(function(e){});
  });
})();
"""
    cand = src + block
    open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
    r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
    if r.returncode == 0:
        shutil.move('/tmp/app.c.js', 'app.js')
        idx = open('index.html', encoding='utf-8').read()
        idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260722sev', idx)
        open('index.html', 'w', encoding='utf-8').write(idx)
        rep.append('OK добавено + node --check + cache-bust sev')
    else:
        rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('sev-events-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

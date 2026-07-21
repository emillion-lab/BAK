# -*- coding: utf-8 -*-
"""Добавя theatre events слой в app.js (append-only) + cache-bust. Пише events-ui-report.txt винаги."""
import re, subprocess, shutil

rep = []
src = open('app.js', encoding='utf-8').read()

if 'theatre-events-layer' in src:
    rep.append('SKIP вече е добавено')
else:
    block = """

// ------ Театрални събития (events.json): 🎭 маркери + чип "кога свършват" ------
// theatre-events-layer
(function(){
  function ready(cb){
    var t=setInterval(function(){ if(window.map&&window.L){clearInterval(t);cb();} },500);
    setTimeout(function(){clearInterval(t)},30000);
  }
  ready(function(){
    fetch('events.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var today=new Date().toISOString().slice(0,10);
      if(d.date!==today || !d.events || !d.events.length) return;
      var layer=L.layerGroup();
      d.events.forEach(function(e){
        var mk=L.marker([e.lat,e.lng],{icon:L.divIcon({className:'',html:'<div style=\"font-size:22px;filter:drop-shadow(0 1px 2px rgba(0,0,0,.6))\">🎭</div>',iconSize:[24,24],iconAnchor:[12,12]})});
        mk.bindPopup('<div style=\"font-family:sans-serif;min-width:180px\"><b style=\"font-size:14px\">'+e.t+'</b>'+
          '<div style=\"color:#64748b;font-size:12px;margin:3px 0\">'+e.v+'</div>'+
          '<div style=\"font-size:13px\">Начало: '+e.start+' · Край: ~'+e.end+'</div>'+
          '<div style=\"font-size:14px;font-weight:900;color:#f59e0b;margin-top:4px\">🚕 Бъди там: '+e.target+'</div></div>');
        layer.addLayer(mk);
      });
      layer.addTo(window.map);
      var chip=document.createElement('div');
      chip.style.cssText='position:fixed;left:8px;bottom:130px;z-index:1500;background:#1a1029f0;color:#e9d5ff;border:1px solid #a855f7;border-radius:10px;padding:7px 11px;font-family:sans-serif;font-size:13px;font-weight:900;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5)';
      chip.textContent='🎭 '+d.events.length+' довечера';
      chip.onclick=function(){
        alert(d.events.map(function(e){return e.target+' → '+e.t+' ('+e.v+')'}).join('\\n')+'\\n\\n🚕 Час = кога да си там (12 мин преди края)');
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
        idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260721ev', idx)
        open('index.html', 'w', encoding='utf-8').write(idx)
        rep.append('OK добавено + node --check + cache-bust ev')
    else:
        rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('events-ui-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

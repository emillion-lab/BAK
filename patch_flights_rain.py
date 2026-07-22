# -*- coding: utf-8 -*-
"""BAK: (1) ☔ прогноза кога ЩЕ вали (Open-Meteo, следващите 12ч)
        (2) 🛬 панел 'излизат сега': кацане -> изходен прозорец, фокус върху моментните
Append-only + node --check + cache-bust. Пише flights-rain-report.txt."""
import re, subprocess, shutil

rep = []
src = open('app.js', encoding='utf-8').read()

if 'rain-forecast-chip' in src and 'exit-now-panel' in src:
    rep.append('SKIP вече е добавено')
else:
    block = """

// ------ ☔ Прогноза за дъжд (следващите 12ч, Open-Meteo) ------
// rain-forecast-chip
(function(){
  function hm(d){return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'});}
  fetch('https://api.open-meteo.com/v1/forecast?latitude=42.695&longitude=23.406&hourly=precipitation_probability,precipitation&forecast_days=2&timezone=Europe%2FSofia')
  .then(function(r){return r.json()}).then(function(d){
    var t=d.hourly.time,p=d.hourly.precipitation,pp=d.hourly.precipitation_probability;
    var now=Date.now(), hit=null;
    for(var i=0;i<t.length;i++){
      var ts=new Date(t[i]+':00+03:00').getTime();
      if(ts<now-3600000) continue;
      if(ts>now+12*3600000) break;
      if((pp[i]>=50&&p[i]>=0.1)||p[i]>=0.4){ hit={ts:ts,pr:pp[i],mm:p[i]}; break; }
    }
    var chip=document.createElement('div');
    chip.style.cssText='position:fixed;left:8px;bottom:218px;z-index:1500;border-radius:10px;padding:6px 10px;font-family:sans-serif;font-size:12px;font-weight:900;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5)';
    if(hit){
      var mins=Math.round((hit.ts-now)/60000);
      var when=mins<=0?'сега':(mins<60?('след '+mins+' мин'):('след '+Math.floor(mins/60)+'ч '+(mins%60)+'м'));
      chip.textContent='☔ Дъжд от '+hm(new Date(hit.ts))+' ('+when+')';
      var urgent=mins<90;
      chip.style.background=urgent?'#3a2510f0':'#10233af0';
      chip.style.color=urgent?'#fbbf24':'#93c5fd';
      chip.style.border='1px solid '+(urgent?'#f59e0b':'#3b82f6');
    } else {
      chip.textContent='☀️ Без дъжд 12ч';
      chip.style.background='#111827d0'; chip.style.color='#9ca3af'; chip.style.border='1px solid #374151';
    }
    chip.onclick=function(){ chip.style.display='none'; };
    document.body.appendChild(chip);
  }).catch(function(e){});
})();

// ------ 🛬 Излизат сега: кацане -> изходен прозорец (кацане+15 до +40 мин) ------
// exit-now-panel
(function(){
  function hm(d){return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'});}
  var chip=document.createElement('div');
  chip.style.cssText='position:fixed;left:8px;bottom:262px;z-index:1500;background:#0f2818f0;color:#86efac;border:1px solid #22c55e;border-radius:10px;padding:7px 11px;font-family:sans-serif;font-size:13px;font-weight:900;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5);display:none';
  document.body.appendChild(chip);
  var panel=document.createElement('div');
  panel.style.cssText='position:fixed;left:8px;right:8px;bottom:80px;max-height:55vh;overflow-y:auto;z-index:2500;background:#0b1220f8;color:#e5e7eb;border:1px solid #334155;border-radius:14px;padding:12px;font-family:sans-serif;font-size:13px;display:none;box-shadow:0 6px 30px rgba(0,0,0,.7)';
  document.body.appendChild(panel);
  chip.onclick=function(){ panel.style.display = panel.style.display==='none'?'block':'none'; };
  function refresh(){
    fetch('flight-cache.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var now=Date.now(), out=[], soon=[];
      (d.data||[]).forEach(function(f){
        if(f.flight_status==='cancelled') return;
        var a=f.arrival||{}, land=a.estimated||a.scheduled;
        if(!land) return;
        var lt=new Date(land).getTime();
        if(isNaN(lt)) return;
        var xs=lt+15*60000, xe=lt+40*60000;
        var item={land:lt,xs:xs,xe:xe,from:(f.departure&&f.departure.airport)||'?',
                  num:(f.flight&&f.flight.iata)||'', term:a.terminal||'', st:f.flight_status};
        if(now>=xs&&now<=xe) out.push(item);
        else if(xs>now&&xs<=now+60*60000) soon.push(item);
      });
      out.sort(function(a,b){return a.xe-b.xe}); soon.sort(function(a,b){return a.xs-b.xs});
      if(!out.length&&!soon.length){ chip.style.display='none'; panel.style.display='none'; return; }
      chip.style.display='block';
      chip.textContent='🛬 '+(out.length?out.length+' излизат СЕГА':'')+(out.length&&soon.length?' · ':'')+(soon.length?soon.length+' до 1ч':'');
      var html='<div style=\\"font-weight:900;font-size:14px;margin-bottom:8px\\">🛬 Изходи Терминал 1/2</div>';
      out.forEach(function(f){
        html+='<div style=\\"background:#14532d80;border-left:3px solid #22c55e;border-radius:6px;padding:6px 8px;margin:5px 0\\">'+
          '<b>ИЗЛИЗАТ СЕГА</b> · '+f.from+' '+(f.term?('· T'+f.term):'')+'<br>'+
          '<span style=\\"color:#9ca3af\\">Кацна '+hm(new Date(f.land))+'</span> → изход <b>'+hm(new Date(f.xs))+'–'+hm(new Date(f.xe))+'</b> · '+f.num+'</div>';
      });
      soon.forEach(function(f){
        html+='<div style=\\"background:#1e293b80;border-left:3px solid #64748b;border-radius:6px;padding:6px 8px;margin:5px 0\\">'+
          f.from+' '+(f.term?('· T'+f.term):'')+'<br>'+
          '<span style=\\"color:#9ca3af\\">Кацане '+hm(new Date(f.land))+(f.st==='landed'?' ✓':'')+'</span> → изход <b>'+hm(new Date(f.xs))+'–'+hm(new Date(f.xe))+'</b> · '+f.num+'</div>';
      });
      html+='<div style=\\"color:#64748b;font-size:11px;margin-top:6px\\">Изход = кацане +15–40 мин · опресн. на 60 сек</div>';
      panel.innerHTML=html;
    }).catch(function(e){});
  }
  refresh(); setInterval(refresh, 60000);
})();
"""
    cand = src + block
    open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
    r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
    if r.returncode == 0:
        shutil.move('/tmp/app.c.js', 'app.js')
        idx = open('index.html', encoding='utf-8').read()
        idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260722fx', idx)
        open('index.html', 'w', encoding='utf-8').write(idx)
        rep.append('OK добавено + node --check + cache-bust fx')
    else:
        rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

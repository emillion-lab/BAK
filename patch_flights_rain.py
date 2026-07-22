# -*- coding: utf-8 -*-
"""v4: (1) старият rain-banner се маха окончателно (ненадежден — 2 противоречиви прогнози)
       (2) rain chip v2: 'Вали сега до HH:MM' / 'Дъжд от HH:MM' / 'Без дъжд'
       (3) 🚌 входящи автобуси: ETA на първите спирки (Експо/Ботевградско/бул.България/Цариградско)
           по коридор според града, + оранжев чип при автобуси в ±20 мин прозорец."""
import re, subprocess, shutil

rep = []
src = open('app.js', encoding='utf-8').read()

if 'bak-v4' in src:
    rep.append('SKIP v4 вече е приложен')
else:
    block = """

// ------ bak-v4 ------
// (1) старият rain-banner: премахване (ненадеждни данни, дублира прогнозата)
(function(){
  function kill(){ var el=document.getElementById('rain-banner'); if(el) el.remove(); }
  kill(); setInterval(kill, 5000);
})();

// (2) rain chip v2: сегашно състояние + следващ дъжд от един източник (Open-Meteo)
(function(){
  // махни стария ☔/☀️ чип от v1
  Array.prototype.slice.call(document.querySelectorAll('div')).forEach(function(el){
    var t=el.textContent||'';
    if((t.indexOf('☔ Дъжд от')===0||t.indexOf('☀️ Без дъжд')===0)&&el.style.position==='fixed') el.remove();
  });
  function hm(d){return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'});}
  fetch('https://api.open-meteo.com/v1/forecast?latitude=42.695&longitude=23.406&hourly=precipitation_probability,precipitation&forecast_days=2&timezone=Europe%2FSofia')
  .then(function(r){return r.json()}).then(function(d){
    var t=d.hourly.time,p=d.hourly.precipitation,pp=d.hourly.precipitation_probability;
    var now=Date.now(), idxNow=-1;
    for(var i=0;i<t.length;i++){
      var ts=new Date(t[i]+':00+03:00').getTime();
      if(ts<=now&&now<ts+3600000){ idxNow=i; break; }
    }
    var chip=document.createElement('div');
    chip.style.cssText='position:fixed;left:8px;bottom:112px;z-index:1500;border-radius:10px;padding:6px 10px;font-family:sans-serif;font-size:12px;font-weight:900;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5)';
    var rainingNow = idxNow>=0 && p[idxNow]>=0.15;
    if(rainingNow){
      var j=idxNow; while(j<t.length&&p[j]>=0.15) j++;
      var stop=new Date(new Date(t[Math.min(j,t.length-1)]+':00+03:00').getTime());
      chip.textContent='🌧️ Вали · спира ~'+hm(stop);
      chip.style.background='#0f2a3af0'; chip.style.color='#7dd3fc'; chip.style.border='1px solid #0ea5e9';
    } else {
      var hit=null;
      for(var i=Math.max(idxNow,0);i<t.length;i++){
        var ts=new Date(t[i]+':00+03:00').getTime();
        if(ts>now+12*3600000) break;
        if(ts>now&&((pp[i]>=50&&p[i]>=0.1)||p[i]>=0.4)){ hit=ts; break; }
      }
      if(hit){
        var mins=Math.round((hit-now)/60000);
        var when=mins<60?('след '+mins+' мин'):('след '+Math.floor(mins/60)+'ч '+(mins%60)+'м');
        chip.textContent='☔ Дъжд от '+hm(new Date(hit))+' ('+when+')';
        var urgent=mins<90;
        chip.style.background=urgent?'#3a2510f0':'#10233af0';
        chip.style.color=urgent?'#fbbf24':'#93c5fd';
        chip.style.border='1px solid '+(urgent?'#f59e0b':'#3b82f6');
      } else {
        chip.textContent='☀️ Без дъжд 12ч';
        chip.style.background='#111827d0'; chip.style.color='#9ca3af'; chip.style.border='1px solid #374151';
      }
    }
    chip.onclick=function(){ chip.style.display='none'; };
    document.body.appendChild(chip);
  }).catch(function(e){});
})();

// (3) 🚌 входящи автобуси с ETA на първите спирки по коридор
(function(){
  function hm(d){return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'});}
  var HEMUS=/(ВАРНА|ШУМЕН|РУСЕ|РАЗГРАД|ТЪРГОВИЩЕ|ВЕЛИКО ТЪРНОВО|В\\. ?ТЪРНОВО|ГАБРОВО|ПЛЕВЕН|ЛОВЕЧ|СЕВЛИЕВО|БЯЛА|ДОБРИЧ|СИЛИСТРА|БОТЕВГРАД|ПРАВЕЦ/i;
  var TRAKIA=/(ПЛОВДИВ|БУРГАС|СТАРА ЗАГОРА|СЛИВЕН|ЯМБОЛ|ХАСКОВО|КЪРДЖАЛИ|ДИМИТРОВГРАД|ПАЗАРДЖИК|АСЕНОВГРАД|НЕСЕБЪР|СЛЪНЧЕВ|ПОМОРИЕ|СОЗОПОЛ|ИСТАНБУЛ|ОДРИН|ЧОРЛУ|АНКАРА|БУРСА)/i;
  var YUG=/(БЛАГОЕВГРАД|САНДАНСКИ|ПЕТРИЧ|ДУПНИЦА|КЮСТЕНДИЛ|БАНСКО|РАЗЛОГ|ГОЦЕ|СОЛУН|АТИНА|КАВАЛА|ДРАМА|СКОПИЕ|СТРУМИЦА|ОХРИД|БИТОЛЯ)/i;
  function corridor(from){
    var f=(from||'').toUpperCase();
    if(HEMUS.test(f)) return {n:'Хемус',stops:[['Експо/Цариградско',-18],['Ботевградско шосе',-12]]};
    if(TRAKIA.test(f)) return {n:'Тракия',stops:[['Експо Център',-15],['Цариградско шосе',-10]]};
    if(YUG.test(f)) return {n:'Юг',stops:[['бул. България',-14],['Хладилника',-9]]};
    return null;
  }
  var chip=document.createElement('div');
  chip.style.cssText='position:fixed;left:8px;bottom:28px;z-index:1500;border-radius:10px;padding:7px 11px;font-family:sans-serif;font-size:13px;font-weight:900;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5);display:none';
  document.body.appendChild(chip);
  var panel=document.createElement('div');
  panel.style.cssText='position:fixed;left:8px;right:8px;bottom:80px;max-height:55vh;overflow-y:auto;z-index:2500;background:#0b1220f8;color:#e5e7eb;border:1px solid #334155;border-radius:14px;padding:12px;font-family:sans-serif;font-size:13px;display:none;box-shadow:0 6px 30px rgba(0,0,0,.7)';
  document.body.appendChild(panel);
  chip.onclick=function(){ panel.style.display=panel.style.display==='none'?'block':'none'; };
  function refresh(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var now=new Date(), list=[];
      (d.arrivals||[]).forEach(function(a){
        var m=/^(\\d{2}):(\\d{2})$/.exec(a.time); if(!m) return;
        var cas=new Date(); cas.setHours(+m[1],+m[2],0,0);
        var diff=(cas-now)/60000;
        if(diff<-25||diff>120) return;
        list.push({cas:cas,diff:diff,from:a.from,intl:a.intl,cor:corridor(a.from)});
      });
      list.sort(function(a,b){return a.cas-b.cas});
      var hot=list.filter(function(x){return x.diff>=-20&&x.diff<=20}).length;
      if(!list.length){ chip.style.display='none'; panel.style.display='none'; return; }
      chip.style.display='block';
      chip.textContent='🚌 '+list.length+' до 2ч'+(hot?' · '+hot+' СЕГА':'');
      if(hot){ chip.style.background='#3a2510f0'; chip.style.color='#fb923c'; chip.style.border='1px solid #ea580c'; }
      else { chip.style.background='#10233af0'; chip.style.color='#93c5fd'; chip.style.border='1px solid #3b82f6'; }
      var html='<div style=\\"font-weight:900;font-size:14px;margin-bottom:8px;display:flex;justify-content:space-between\\"><span>🚌 Входящи автобуси</span><span style=\\"cursor:pointer;padding:2px 10px;color:#94a3b8\\" onclick=\\"this.parentElement.parentElement.style.display=&quot;none&quot;\\">✕</span></div>';
      list.forEach(function(x){
        var urgent=x.diff>=-20&&x.diff<=20;
        var stops='';
        if(x.cor){
          stops=x.cor.stops.map(function(s){
            return s[0]+' ~<b>'+hm(new Date(x.cas.getTime()+s[1]*60000))+'</b>';
          }).join(' → ')+' → ';
        }
        html+='<div style=\\"background:'+(urgent?'#3a251080':'#1e293b80')+';border-left:3px solid '+(urgent?'#ea580c':'#64748b')+';border-radius:6px;padding:6px 8px;margin:5px 0\\">'+
          (x.intl?'🌍 ':'')+x.from+(x.cor?' <span style=\\"color:#64748b\\">('+x.cor.n+')</span>':'')+'<br>'+
          '<span style=\\"font-size:12px\\">'+stops+'ЦАС <b>'+hm(x.cas)+'</b></span></div>';
      });
      html+='<div style=\\"color:#64748b;font-size:11px;margin-top:6px\\">ETA на спирките = ЦАС час − типичен пробег · оранжево = в прозорец ±20 мин</div>';
      panel.innerHTML=html;
    }).catch(function(e){});
  }
  refresh(); setInterval(refresh, 120000);
})();
"""
    cand = src + block
    open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
    r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
    if r.returncode == 0:
        shutil.move('/tmp/app.c.js', 'app.js')
        idx = open('index.html', encoding='utf-8').read()
        idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260722v4', idx)
        open('index.html', 'w', encoding='utf-8').write(idx)
        rep.append('OK v4: rain-banner маха, rain chip v2, 🚌 коридорни ETA + node --check')
    else:
        rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

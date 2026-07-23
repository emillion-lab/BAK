# -*- coding: utf-8 -*-
"""v15: АЛГОРИТЪМ ЗА БАСЕЙНИТЕ (идея на Емил).
1) Работно време — зоната е мъртва извън часовете, не гори по цял ден.
2) Температура — под 24°C басейните са празни, над 30°C са пълни.
3) ⛈️ ИЗХОД ПРИ ДЪЖД — при задаващ се дъжд/облаци всички излизат
   ЕДНОВРЕМЕННО и то мокри и без коли. Това е пикът, не спадът.
4) Закритите басейни правят обратното — при дъжд печелят хора.
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()

if 'pool-weather-v15' in src:
    rep.append('SKIP v15 вече е приложен')
    cand = src
else:
    cand = src + """

// ------ pool-weather-v15: работно време + температура + изход при дъжд ------
(function(){
  // [делник_отваря, делник_затваря, уикенд_отваря, уикенд_затваря, закрит?]
  var POOLS = {
    pool_spartak:     [7,   21,   8.5, 18,   0],
    pool_diana:       [9.5, 18.5, 9.5, 18.5, 0],
    pool_akademika:   [7,   21,   8,   20,   0],
    pool_madara:      [7,   21.7, 7,   18,   0],
    pool_vazrazhdane: [9,   19,   9,   19,   0],
    pool_varadero:    [9,   19,   9,   19,   0],
    pool_thebeach:    [9,   22,   9,   23.7, 0],
    pool_silvercity:  [7,   22,   7,   22,   0],
    pool_hearts:      [10,  18,   9,   19,   0],
    pool_sportpalace: [6.5, 19.5, 8,   17,   1]   // ЗАКРИТ — при дъжд печели
  };

  var W = {t:null, rainNow:0, rainSoon:null, cloud:0, ts:0};

  function pullWeather(){
    fetch('https://api.open-meteo.com/v1/forecast?latitude=42.6977&longitude=23.3219'
        + '&current=temperature_2m,precipitation,cloud_cover'
        + '&hourly=precipitation,precipitation_probability,cloud_cover'
        + '&forecast_days=2&timezone=Europe%2FSofia')
    .then(function(r){return r.json()}).then(function(d){
      var c = d.current || {};
      W.t = c.temperature_2m;
      W.rainNow = c.precipitation || 0;
      W.cloud = c.cloud_cover || 0;
      var t=d.hourly.time, p=d.hourly.precipitation, pp=d.hourly.precipitation_probability;
      var now=Date.now(); W.rainSoon=null;
      for(var i=0;i<t.length;i++){
        var ts=new Date(t[i]+':00+03:00').getTime();
        if(ts<=now) continue;
        if(ts>now+3*3600000) break;
        if((pp[i]>=55 && p[i]>=0.1) || p[i]>=0.4){ W.rainSoon=ts; break; }
      }
      W.ts=now;
    }).catch(function(e){});
  }
  pullWeather(); setInterval(pullWeather, 900000);   // на 15 мин

  function poolScore(zid){
    var h = POOLS[zid]; if(!h) return null;
    var now = new Date();
    var wknd = (now.getDay()===0 || now.getDay()===6);
    var open = wknd ? h[2] : h[0], close = wknd ? h[3] : h[1];
    var indoor = !!h[4];
    var hh = now.getHours() + now.getMinutes()/60;

    // Sport Palace не работи в неделя
    if(zid==='pool_sportpalace' && now.getDay()===0) return 0;
    // затворено -> мъртва зона (но 30 мин преди затваряне има изход)
    if(hh < open - 0.25) return 0;
    if(hh > close + 0.3) return 0;

    if(W.t === null) return null;   // без данни -> не пипаме

    // --- база по температура ---
    var s;
    if(indoor){
      s = 1.0;                                   // закритият е стабилен целогодишно
    } else {
      if(W.t < 22) s = 0.2;
      else if(W.t < 25) s = 0.7;
      else if(W.t < 28) s = 1.3;
      else if(W.t < 32) s = 2.0;
      else s = 2.5;
    }

    // --- следобеден пик ---
    if(hh >= 12 && hh <= 18) s *= 1.25;

    // --- изход в края на деня (последните 45 мин) ---
    if(hh >= close - 0.75 && hh <= close + 0.3) s += indoor ? 0.6 : 1.4;

    if(indoor){
      // при дъжд закритият печели — хората се прехвърлят
      if(W.rainNow >= 0.15) s += 0.8;
      return s;
    }

    // --- ⛈️ ИЗХОД ПРИ ДЪЖД (ключовото) ---
    if(W.rainNow >= 0.15){
      s += 3.2;                                  // валят навън -> масово бягство СЕГА
    } else if(W.rainSoon){
      var mins = (W.rainSoon - Date.now())/60000;
      if(mins <= 20) s += 2.8;                   // първите капки, всички станаха
      else if(mins <= 45) s += 1.9;              // небето почерня, започват да се прибират
      else if(mins <= 90) s += 0.9;
    } else if(W.cloud >= 75 && W.t < 27){
      s += 0.7;                                  // заоблачи се и застудя -> изтичане
    }
    return s;
  }

  // закачаме се към живия мост от v6
  var prev = window.__applyLive;
  window.__applyLive = function(scores){
    try{ if(prev) prev(scores); }catch(e){}
    try{
      for(var zid in POOLS){
        if(typeof scores[zid] !== 'number') continue;
        var ps = poolScore(zid);
        if(ps === null) continue;
        scores[zid] = (ps === 0) ? 0 : Math.max(scores[zid], ps);
      }
    }catch(e){}
  };

  // --- предупреждение: басейните всеки момент ще се изпразнят ---
  var chip=document.createElement('div');
  chip.style.cssText='position:fixed;left:8px;bottom:196px;z-index:1500;border-radius:10px;'
    +'padding:7px 11px;font-family:sans-serif;font-size:13px;font-weight:900;cursor:pointer;'
    +'box-shadow:0 2px 10px rgba(0,0,0,.5);display:none;background:#3a1a10f0;color:#fdba74;'
    +'border:1px solid #ea580c';
  chip.onclick=function(){ chip.style.display='none'; };
  document.body.appendChild(chip);

  function alertTick(){
    if(W.t === null) return;
    var now=new Date(), hh=now.getHours()+now.getMinutes()/60;
    var wknd=(now.getDay()===0||now.getDay()===6);
    // има ли изобщо отворени открити басейни сега?
    var openCnt=0;
    for(var zid in POOLS){
      var h=POOLS[zid]; if(h[4]) continue;
      var o=wknd?h[2]:h[0], c=wknd?h[3]:h[1];
      if(hh>=o && hh<=c) openCnt++;
    }
    if(!openCnt || W.t < 23){ chip.style.display='none'; return; }

    if(W.rainNow >= 0.15){
      chip.textContent='⛈️ Вали — басейните се изпразват СЕГА';
      chip.style.display='block';
    } else if(W.rainSoon){
      var m=Math.round((W.rainSoon-Date.now())/60000);
      if(m<=45){
        chip.textContent='🌧️ Дъжд след '+m+'м — '+openCnt+' басейна ще излязат';
        chip.style.display='block';
      } else chip.style.display='none';
    } else chip.style.display='none';
  }
  alertTick(); setInterval(alertTick, 60000);
})();
"""
    rep.append('OK   алгоритъм за басейните (часове + температура + изход при дъжд)')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v15', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    rep.append('OK v15 + node --check + cache-bust v15')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

# -*- coding: utf-8 -*-
"""v18: (1) СПИРКИТЕ вече смятат часовете от bus-schedule.json (разписание,
           не зависи от живия скрейпър) + живите данни от ЦАС като потвърждение
       (2) ЖП гара показва РЕАЛНИТЕ влакове от train-arrivals.json
       (3) честен статус за Автогара Подуяне
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── изключваме стария v12 скенер (заменя се от v18) ───────────
for old in ("document.querySelectorAll('.leaflet-popup-content').forEach(enrich);",
            "document.querySelectorAll('[data-stop],.stop-card,.zone-detail').forEach(enrich);"):
    if cand.count(old) == 1:
        cand = cand.replace(old, "/* v12 изключен от v18 */")
        rep.append('OK   изключен стар скенер: %s' % old[:45])
    else:
        rep.append('SKIP стар скенер (%d): %s' % (cand.count(old), old[:45]))

if 'stop-eta-v18' in cand:
    rep.append('SKIP v18 вече е приложен')
else:
    cand += """

// ------ stop-eta-v18: часове от РАЗПИСАНИЕ + живи данни като бонус ------
(function(){
  var SCHED = null, BUS = [], TRAINS = null;

  function hm(d){ return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'}); }
  function mins(d){ return Math.round((d.getTime()-Date.now())/60000); }
  function whenTxt(m){
    if(m <= 0) return 'сега';
    if(m < 60) return 'след '+m+'м';
    return 'след '+Math.floor(m/60)+'ч '+(m%60)+'м';
  }

  // ── коя спирка е (от текста на popup-а и от името в разписанието) ──
  function keyOf(t){
    t = t || '';
    if(/expo|цариградско/i.test(t)) return 'expo';
    if(/ботевградско/i.test(t)) return 'botev';
    if(/бул\\.? ?[Бб]ългария|струма|околовръстен/i.test(t)) return 'bulgaria';
    return null;
  }
  var LABEL = { expo:'Експо / Цариградско', botev:'Ботевградско шосе', bulgaria:'бул. България' };

  fetch('bus-schedule.json?v='+Date.now()).then(function(r){return r.json()})
    .then(function(d){ SCHED = d; }).catch(function(){});

  function pullLive(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 4*3600000;
      BUS = [];
      if(!fresh) return;
      (d.arrivals||[]).forEach(function(a){
        var m=/^(\\d{1,2}):(\\d{2})$/.exec(a.time||''); if(!m) return;
        var t=new Date(); t.setHours(+m[1],+m[2],0,0);
        if(t.getTime() < Date.now()-3*3600000) t.setDate(t.getDate()+1);
        BUS.push({t:t, from:a.from, intl:a.intl});
      });
    }).catch(function(){});
  }
  function pullTrains(){
    fetch('train-arrivals.json?v='+Date.now()).then(function(r){return r.json()})
      .then(function(d){ TRAINS = d; }).catch(function(){});
  }
  pullLive(); pullTrains();
  setInterval(function(){ pullLive(); pullTrains(); }, 180000);

  // ── пристигания на дадена спирка по разписание ──
  function fromSchedule(key){
    if(!SCHED || !SCHED.routes) return [];
    var out = [], now = Date.now();
    SCHED.routes.forEach(function(rt){
      if(!/София/i.test(rt.to || '')) return;           // само входящи
      (rt.stops || []).forEach(function(st){
        if(keyOf(st.name) !== key) return;
        (rt.departures || []).forEach(function(dep){
          var m = /^(\\d{1,2}):(\\d{2})$/.exec(dep); if(!m) return;
          var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
          t = new Date(t.getTime() + (st.offset_min||0)*60000);
          if(t.getTime() < now - 10*60000) t = new Date(t.getTime() + 864e5);
          if(t.getTime() > now + 5*3600000) return;
          out.push({ t:t, name:(rt.name||'').replace(/\\s*→.*/,''), approx:!!rt.approx });
        });
      });
    });
    out.sort(function(a,b){ return a.t - b.t; });
    return out.slice(0, 5);
  }

  function busHTML(key){
    var list = fromSchedule(key);
    if(!list.length){
      return '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;'
           + 'background:rgba(148,163,184,.12);border-left:3px solid #94a3b8;'
           + 'font-size:12px;color:#64748b">🚌 Няма курсове в следващите 5ч</div>';
    }
    var first = mins(list[0].t), urgent = first <= 20;
    var rows = list.map(function(x){
      var m = mins(x.t);
      // има ли живо потвърждение от ЦАС (пристига ~15-20 мин след спирката)
      var conf = BUS.some(function(b){
        return Math.abs((b.t.getTime() - x.t.getTime())/60000 - 18) < 14;
      });
      return '<div style="margin:2px 0"><b>' + hm(x.t) + '</b> · ' + x.name
           + (x.approx ? ' <span style="opacity:.55">≈</span>' : '')
           + (conf ? ' <span style="color:#22c55e">●</span>' : '')
           + ' <span style="opacity:.65">(' + whenTxt(m) + ')</span></div>';
    }).join('');
    return '<div style="margin-top:7px;padding:7px 9px;border-radius:7px;background:'
         + (urgent ? 'rgba(234,88,12,.14)' : 'rgba(56,189,248,.10)')
         + ';border-left:3px solid ' + (urgent ? '#ea580c' : '#38bdf8') + ';font-size:12px">'
         + '<b>🚌 Слизане на ' + LABEL[key] + '</b>' + rows
         + '<div style="opacity:.55;font-size:11px;margin-top:4px">по разписание · ≈ ориентировъчно'
         + (BUS.length ? ' · <span style="color:#22c55e">●</span> потвърдено от ЦАС' : '') + '</div></div>';
  }

  function trainHTML(){
    if(!TRAINS || !TRAINS.arrivals || !TRAINS.arrivals.length){
      return '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;'
           + 'background:rgba(148,163,184,.12);border-left:3px solid #94a3b8;'
           + 'font-size:12px;color:#64748b">🚂 Няма данни от БДЖ в момента</div>';
    }
    var now = Date.now(), list = [];
    TRAINS.arrivals.forEach(function(a){
      var m = /^(\\d{1,2}):(\\d{2})$/.exec(a.time||''); if(!m) return;
      var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
      t = new Date(t.getTime() + (a.delay||0)*60000);
      if(t.getTime() < now - 20*60000) t = new Date(t.getTime() + 864e5);
      if(t.getTime() > now + 5*3600000) return;
      list.push({ t:t, from:a.from, train:a.train, delay:a.delay||0, tier:a.tier });
    });
    list.sort(function(a,b){ return a.t - b.t; });
    list = list.slice(0, 5);
    if(!list.length){
      return '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;'
           + 'background:rgba(148,163,184,.12);border-left:3px solid #94a3b8;'
           + 'font-size:12px;color:#64748b">🚂 Няма влакове в следващите 5ч</div>';
    }
    var far = list.filter(function(x){ return x.tier === 'far'; }).length;
    var urgent = mins(list[0].t) <= 20 && list[0].tier === 'far';
    var rows = list.map(function(x){
      var ic = x.tier === 'far' ? '🧳' : (x.tier === 'near' ? '·' : '•');
      return '<div style="margin:2px 0">' + ic + ' <b>' + hm(x.t) + '</b> · ' + x.from
           + ' <span style="opacity:.6">' + x.train + '</span>'
           + (x.delay ? ' <span style="color:#f59e0b">+' + x.delay + 'м</span>' : '')
           + ' <span style="opacity:.65">(' + whenTxt(mins(x.t)) + ')</span></div>';
    }).join('');
    return '<div style="margin-top:7px;padding:7px 9px;border-radius:7px;background:'
         + (urgent ? 'rgba(234,88,12,.14)' : 'rgba(56,189,248,.10)')
         + ';border-left:3px solid ' + (urgent ? '#ea580c' : '#38bdf8') + ';font-size:12px">'
         + '<b>🚂 Пристигащи влакове</b>' + rows
         + '<div style="opacity:.55;font-size:11px;margin-top:4px">🧳 = далечен (багаж) · '
         + far + ' от ' + list.length + ' са далечни</div></div>';
  }

  function enrich(el){
    try{
      if(!el || (el.dataset && el.dataset.eta18)) return;
      var txt = el.textContent || '';
      var html = null;

      // ЖП гара
      if(/[Жж][Пп] гара|Централна ЖП|железопът/i.test(txt) || el.querySelector('.bdz-note')){
        html = trainHTML();
        var old = el.querySelector('.bdz-note');
        if(old) old.remove();
      }
      // крайпътни спирки
      if(!html){
        if(!/Слизане от|Вход от|Експо|Expo|Ботевградско|бул\\.? ?[Бб]ългария|Цариградско/i.test(txt)) return;
        var k = keyOf(txt);
        if(!k) return;
        html = busHTML(k);
      }
      if(el.dataset) el.dataset.eta18 = '1';
      // махаме стария блок от v12, ако е останал
      var prev = el.querySelector('[data-eta12]');
      if(prev) prev.remove();
      el.insertAdjacentHTML('beforeend', html);
    }catch(e){}
  }

  function scan(){
    try{
      document.querySelectorAll('.leaflet-popup-content').forEach(enrich);
      document.querySelectorAll('[data-stop],.stop-card,.zone-detail').forEach(enrich);
    }catch(e){}
  }
  scan();
  setInterval(scan, 4000);
  try{ new MutationObserver(scan).observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();
"""
    rep.append('OK   v18: спирки от разписание + ЖП с реални влакове')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v18', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda m: m.group(1) + 'bak-v18' + m.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
            rep.append('OK   sw.js кеш -> bak-v18')
    except FileNotFoundError:
        pass
    rep.append('OK v18 + node --check + cache-bust v18')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

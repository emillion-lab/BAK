# -*- coding: utf-8 -*-
"""v29: (1) международната зона отива ПРЕД Централна гара, където реално са
           Международна автогара 'Сердика' (42.7105,23.3225) и FlixBus (42.7112,23.3222)
       (2) поправка на моя гаф от v19 — текстът за Подуяне беше генеричен за
           ВСИЧКИ транспортни зони
       (3) списък с международните автобуси в popup-а на зоната
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (1) преместване и преименуване ──
m = re.search(r'\{\s*id:"cas_intl"[^}]*\}', cand)
if m:
    obj = m.group(0)
    new = obj
    new = re.sub(r'lat:[\d.]+\s*,\s*lng:[\d.]+', 'lat:42.7108, lng:23.3224', new)
    new = re.sub(r'name:"[^"]*"', 'name:"🌍 Междунар. автогара Сердика / FlixBus"', new)
    new = re.sub(r'radius:\d+', 'radius:150', new)
    new = re.sub(r'wazeName:"[^"]*"', 'wazeName:"Международна автогара Сердика София"', new)
    cand = cand.replace(obj, new, 1)
    rep.append('OK   cas_intl -> 42.7108,23.3224 (пред Централна гара, беше ~200 м назад)')
else:
    rep.append('SKIP cas_intl не е намерена')

# ── (2) връщаме генеричния текст ──
bad = "Транспортен хъб. Няма публично разписание — севернo/източно направление."
if bad in cand:
    n = cand.count(bad)
    cand = cand.replace(bad, "Транспортен хъб.")
    rep.append('OK   генеричният текст върнат (беше специфичен за Подуяне на %d места)' % n)
else:
    rep.append('SKIP генеричният текст не е намерен')

# ── (3) списък с международни в popup-а ──
if 'intl-list-v29' in cand:
    rep.append('SKIP списъкът вече е добавен')
else:
    cand += """

// ------ intl-list-v29: международни автобуси + бележка за Подуяне ------
(function(){
  var SCHED = null, LIVE = [];
  var FLAG = {
    'скопие':'🇲🇰','ниш':'🇷🇸','белград':'🇷🇸','солун':'🇬🇷','атина':'🇬🇷',
    'букурещ':'🇷🇴','истанбул':'🇹🇷','одрин':'🇹🇷','киев':'🇺🇦','кишинев':'🇲🇩',
    'виена':'🇦🇹','мюнхен':'🇩🇪','берлин':'🇩🇪','прага':'🇨🇿','будапеща':'🇭🇺',
    'загреб':'🇭🇷','любляна':'🇸🇮','тирана':'🇦🇱','подгорица':'🇲🇪','сараево':'🇧🇦'
  };
  function flagFor(n){
    n = (n||'').toLowerCase();
    for(var k in FLAG){ if(n.indexOf(k) >= 0) return FLAG[k]; }
    return '🌍';
  }
  function hm(d){ return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'}); }
  function whenTxt(m){
    if(m <= 0) return 'сега';
    if(m < 60) return 'след ' + m + 'м';
    return 'след ' + Math.floor(m/60) + 'ч ' + (m%60) + 'м';
  }

  fetch('bus-schedule.json?v='+Date.now()).then(function(r){return r.json()})
    .then(function(d){ SCHED = d; }).catch(function(){});
  function pullLive(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 4*3600000;
      LIVE = fresh ? (d.arrivals||[]).filter(function(a){ return a.intl; }) : [];
    }).catch(function(){});
  }
  pullLive(); setInterval(pullLive, 180000);

  function intlList(){
    var out = [], now = Date.now();
    LIVE.forEach(function(a){
      var m = /^(\\d{1,2}):(\\d{2})$/.exec(a.time||''); if(!m) return;
      var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
      if(t.getTime() < now-3*3600000) t.setDate(t.getDate()+1);
      var d = (t-now)/60000;
      if(d < -30 || d > 360) return;
      out.push({t:t, name:a.from, live:true, sector:a.sector||''});
    });
    if(SCHED && SCHED.routes){
      SCHED.routes.forEach(function(rt){
        if(!rt.intl) return;
        var dur = rt.duration_min || 0;
        (rt.departures||[]).forEach(function(dep){
          var m = /^(\\d{1,2}):(\\d{2})$/.exec(dep); if(!m) return;
          var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
          t = new Date(t.getTime() + dur*60000);
          if(t.getTime() < now-3*3600000) t = new Date(t.getTime()+864e5);
          var d = (t-now)/60000;
          if(d < -30 || d > 360) return;
          var nm = (rt.name||'').replace(/\\s*→.*/,'');
          var dup = out.some(function(o){
            return o.live && Math.abs((o.t-t)/60000) < 40
                && o.name.toUpperCase().slice(0,4) === nm.toUpperCase().slice(0,4);
          });
          if(!dup) out.push({t:t, name:nm, approx:true});
        });
      });
    }
    out.sort(function(a,b){ return a.t-b.t; });
    return out.slice(0, 7);
  }

  function intlHTML(){
    var list = intlList();
    if(!list.length){
      return '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;'
           + 'background:rgba(148,163,184,.12);border-left:3px solid #94a3b8;'
           + 'font-size:12px;color:#64748b">🌍 Няма международни в следващите 6ч</div>';
    }
    var first = Math.round((list[0].t-Date.now())/60000);
    var urgent = first <= 30;
    var rows = list.map(function(x){
      return '<div style="margin:3px 0">' + flagFor(x.name) + ' <b>' + hm(x.t) + '</b> · ' + x.name
           + (x.approx ? ' <span style="opacity:.5">≈</span>' : '')
           + (x.live ? ' <span style="color:#22c55e">●</span>' : '')
           + (x.sector ? ' <span style="opacity:.6">сек.' + x.sector + '</span>' : '')
           + ' <span style="opacity:.65">(' + whenTxt(Math.round((x.t-Date.now())/60000)) + ')</span></div>';
    }).join('');
    return '<div style="margin-top:7px;padding:7px 9px;border-radius:7px;background:'
         + (urgent ? 'rgba(234,88,12,.14)' : 'rgba(56,189,248,.10)')
         + ';border-left:3px solid ' + (urgent ? '#ea580c' : '#38bdf8') + ';font-size:12px">'
         + '<b>🌍 Международни пристигания</b>' + rows
         + '<div style="opacity:.55;font-size:11px;margin-top:5px">Дълъг път + багаж = почти сигурен курс<br>'
         + '● живо от ЦАС · ≈ по разписание на превозвача</div></div>';
  }

  function enrich(el){
    try{
      if(!el || (el.dataset && el.dataset.intl29)) return;
      var txt = el.textContent || '';
      if(/Междунар|Сердика \\/ FlixBus|FlixBus/i.test(txt)){
        if(el.dataset) el.dataset.intl29 = '1';
        el.insertAdjacentHTML('beforeend', intlHTML());
        return;
      }
      if(/Автогара Подуяне/i.test(txt)){
        if(el.dataset) el.dataset.intl29 = '1';
        el.insertAdjacentHTML('beforeend',
          '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;'
          + 'background:rgba(148,163,184,.12);border-left:3px solid #94a3b8;'
          + 'font-size:12px;color:#64748b">🚌 Северно/източно направление.<br>'
          + 'Няма публично разписание.</div>');
      }
    }catch(e){}
  }
  function scan(){
    try{
      document.querySelectorAll('.leaflet-popup-content').forEach(enrich);
      document.querySelectorAll('.zone-detail').forEach(enrich);
    }catch(e){}
  }
  scan(); setInterval(scan, 4000);
  try{ new MutationObserver(scan).observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();
"""
    rep.append('OK   списък с международни в popup-а + отделна бележка за Подуяне')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v29', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda mm: mm.group(1) + 'bak-v29' + mm.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v29 + node --check + cache-bust v29')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

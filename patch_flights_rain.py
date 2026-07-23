# -*- coding: utf-8 -*-
"""v26: (1) МЕЖДУНАРОДНИТЕ автобуси стават видими — popup-ът на Централна
           автогара показва пристигащите, с флагче за чуждите линии
       (2) дъмп на всички надписи с 'Влак', за да оправим посоката точно
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (2) къде се пише "Влак ..." ──
os.makedirs('debug', exist_ok=True)
ctx = []
for m in re.finditer(r'Влак', cand):
    ln = cand.count('\n', 0, m.start()) + 1
    ctx.append('--- ред %d ---\n%s' % (ln, cand[max(0, m.start()-320):m.start()+240]))
open('debug/vlak.txt', 'w', encoding='utf-8').write(
    ('\n\n'.join(ctx[:12]) or 'НЯМА "Влак" в app.js') + '\n')
rep.append('"Влак": %d срещания -> debug/vlak.txt' % len(ctx))

# опит за автоматична поправка на посоката: "Влак София X" -> "X → София"
fixed = 0
def swap(m):
    global fixed
    fixed += 1
    return '%s → София' % m.group(1)
cand2 = re.sub(r'Влак\s+София\s+([А-ЯЁ][А-Яа-яё\.\- ]{2,20}?)(?=[\s`"\'<,\)\}])', swap, cand)
if fixed:
    cand = cand2
    rep.append('OK   поправена посока на %d надписа ("Влак София X" -> "X → София")' % fixed)
else:
    rep.append('SKIP шаблонът "Влак София X" не е намерен — виж дъмпа')

# ── (1) международните автобуси в popup-а на автогарата ──
if 'cas-intl-v26' in cand:
    rep.append('SKIP v26 вече е приложен')
else:
    cand += """

// ------ cas-intl-v26: пристигащи на Централна автогара, вкл. МЕЖДУНАРОДНИ ------
(function(){
  var SCHED = null, LIVE = [];
  var FLAG = {
    'скопие':'🇲🇰','ниш':'🇷🇸','белград':'🇷🇸','солун':'🇬🇷','атина':'🇬🇷',
    'букурещ':'🇷🇴','истанбул':'🇹🇷','одрин':'🇹🇷','киев':'🇺🇦','кишинев':'🇲🇩',
    'виена':'🇦🇹','мюнхен':'🇩🇪','берлин':'🇩🇪','прага':'🇨🇿','будапеща':'🇭🇺'
  };
  function flagFor(name){
    var n = (name||'').toLowerCase();
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
      LIVE = [];
      if(!fresh) return;
      (d.arrivals||[]).forEach(function(a){
        var m = /^(\\d{1,2}):(\\d{2})$/.exec(a.time||''); if(!m) return;
        var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
        if(t.getTime() < Date.now()-3*3600000) t.setDate(t.getDate()+1);
        LIVE.push({t:t, from:a.from, intl:!!a.intl, sector:a.sector||''});
      });
    }).catch(function(){});
  }
  pullLive(); setInterval(pullLive, 180000);

  function casArrivals(){
    var out = [], now = Date.now();
    // 1) живи данни от ЦАС (най-точни)
    LIVE.forEach(function(b){
      var diff = (b.t.getTime()-now)/60000;
      if(diff < -25 || diff > 180) return;
      out.push({t:b.t, name:b.from, intl:b.intl, sector:b.sector, live:true});
    });
    // 2) разписание (винаги налично)
    if(SCHED && SCHED.routes){
      SCHED.routes.forEach(function(rt){
        if(!/София/i.test(rt.to||'')) return;
        var dur = rt.duration_min || 0;
        (rt.departures||[]).forEach(function(dep){
          var m = /^(\\d{1,2}):(\\d{2})$/.exec(dep); if(!m) return;
          var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
          t = new Date(t.getTime() + dur*60000);
          var diff = (t.getTime()-now)/60000;
          if(diff < -180) { t = new Date(t.getTime()+864e5); diff += 1440; }
          if(diff < -20 || diff > 180) return;
          var nm = (rt.name||'').replace(/\\s*→.*/,'');
          // без дублиране с живите
          var dup = out.some(function(o){
            return o.live && Math.abs((o.t-t)/60000) < 25
                   && o.name.toUpperCase().indexOf(nm.toUpperCase().slice(0,4)) >= 0;
          });
          if(dup) return;
          out.push({t:t, name:nm, intl:!!rt.intl, approx:!!rt.approx, live:false});
        });
      });
    }
    out.sort(function(a,b){ return a.t - b.t; });
    return out;
  }

  function casHTML(){
    var list = casArrivals();
    if(!list.length){
      return '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;'
           + 'background:rgba(148,163,184,.12);border-left:3px solid #94a3b8;'
           + 'font-size:12px;color:#64748b">🚌 Няма пристигащи в следващите 3ч</div>';
    }
    var intl = list.filter(function(x){ return x.intl; });
    var top = list.slice(0, 6);
    var first = Math.round((top[0].t-Date.now())/60000);
    var urgent = first <= 20;
    var rows = top.map(function(x){
      var m = Math.round((x.t-Date.now())/60000);
      return '<div style="margin:2px 0">' + (x.intl ? flagFor(x.name)+' ' : '🚌 ')
           + '<b>' + hm(x.t) + '</b> · ' + x.name
           + (x.approx ? ' <span style="opacity:.5">≈</span>' : '')
           + (x.live ? ' <span style="color:#22c55e">●</span>' : '')
           + (x.sector ? ' <span style="opacity:.6">сек.' + x.sector + '</span>' : '')
           + ' <span style="opacity:.65">(' + whenTxt(m) + ')</span></div>';
    }).join('');
    var intlNote = intl.length
      ? '<div style="margin-top:5px;padding-top:5px;border-top:1px solid rgba(148,163,184,.25);'
        + 'font-size:11px;color:#93c5fd">🌍 <b>' + intl.length + ' международни</b> в следващите 3ч — '
        + 'багаж, дълъг път, почти сигурен курс</div>'
      : '';
    return '<div style="margin-top:7px;padding:7px 9px;border-radius:7px;background:'
         + (urgent ? 'rgba(234,88,12,.14)' : 'rgba(56,189,248,.10)')
         + ';border-left:3px solid ' + (urgent ? '#ea580c' : '#38bdf8') + ';font-size:12px">'
         + '<b>🚌 Пристигащи на ЦАС</b>' + rows + intlNote
         + '<div style="opacity:.5;font-size:11px;margin-top:4px">● живо от ЦАС · ≈ ориентировъчно</div></div>';
  }

  function enrich(el){
    try{
      if(!el || (el.dataset && el.dataset.cas26)) return;
      var txt = el.textContent || '';
      if(!/Централна автогара/i.test(txt)) return;
      if(/Слизане от|Вход от/i.test(txt)) return;   // това е спирка, не автогарата
      if(el.dataset) el.dataset.cas26 = '1';
      el.insertAdjacentHTML('beforeend', casHTML());
    }catch(e){}
  }
  function scan(){
    try{
      document.querySelectorAll('.leaflet-popup-content').forEach(enrich);
      document.querySelectorAll('.zone-detail,[data-stop]').forEach(enrich);
    }catch(e){}
  }
  scan(); setInterval(scan, 4000);
  try{ new MutationObserver(scan).observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();
"""
    rep.append('OK   международните автобуси в popup-а на ЦАС (с флагчета)')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v26', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda mm: mm.group(1) + 'bak-v26' + mm.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v26 + node --check + cache-bust v26')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

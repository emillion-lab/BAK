# -*- coding: utf-8 -*-
"""v19: (1) летищната точка — беше 720 м северно от терминалите
       (2) Централна автогара смята деманд от РАЗПИСАНИЕТО, не от стария скрейпър
       (3) Подуяне — маха обещанието за разписание
       (4) дъмп на кода за кръговете и посоката (за следващата поправка)
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (1) летище: между Т1 (42.6889,23.4031) и Т2 (42.6880,23.4134) ──
pat = re.compile(r'(\{\s*id:"airport"[^}]*?lat:)([\d.]+)(\s*,\s*lng:)([\d.]+)')
m = pat.search(cand)
if m:
    old_lat, old_lng = float(m.group(2)), float(m.group(4))
    cand = pat.sub(lambda x: x.group(1) + '42.6885' + x.group(3) + '23.4082', cand, count=1)
    d = ((42.6885 - old_lat) * 111000) ** 2 + ((23.4082 - old_lng) * 82000) ** 2
    rep.append('OK   airport %.4f,%.4f -> 42.6885,23.4082 (беше на %d м, вече е между Т1 и Т2)'
               % (old_lat, old_lng, int(d ** 0.5)))
else:
    rep.append('SKIP airport зоната не е намерена')

# ── (3) Подуяне: без обещания ──
for old, new in [
    ("Зона за транспортен хъб. Очаквайте разписания.",
     "Транспортен хъб. Няма публично разписание — севернo/източно направление."),
    ("Очаквайте разписания.", "Няма публично разписание."),
]:
    if old in cand:
        cand = cand.replace(old, new)
        rep.append('OK   махнато обещание: "%s"' % old[:40])
        break

# ── (2) автогара от разписанието ──
if 'cas-sched-v19' in cand:
    rep.append('SKIP v19 автогара вече е добавена')
else:
    cand += """

// ------ cas-sched-v19: Централна автогара смята деманд от РАЗПИСАНИЕТО ------
(function(){
  var SCHED = null;
  fetch('bus-schedule.json?v='+Date.now()).then(function(r){return r.json()})
    .then(function(d){ SCHED = d; }).catch(function(){});

  // пристигания на ЦАС по разписание в прозорец [-20, +30] мин
  function casNow(){
    if(!SCHED || !SCHED.routes) return {recent:0, soon:0, names:[]};
    var now = Date.now(), recent = 0, soon = 0, names = [];
    SCHED.routes.forEach(function(rt){
      if(!/София/i.test(rt.to || '')) return;
      var dur = rt.duration_min || 0;
      (rt.departures || []).forEach(function(dep){
        var m = /^(\\d{1,2}):(\\d{2})$/.exec(dep); if(!m) return;
        var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
        t = new Date(t.getTime() + dur*60000);
        var diff = (t.getTime() - now) / 60000;
        if(diff < -180) diff += 1440;          // за вчерашни нощни курсове
        if(diff <= 0 && diff >= -20){ recent++; names.push((rt.name||'').replace(/\\s*→.*/,'')); }
        else if(diff > 0 && diff <= 30){ soon++; names.push((rt.name||'').replace(/\\s*→.*/,'')); }
      });
    });
    return {recent:recent, soon:soon, names:names.slice(0,4)};
  }

  var prev = window.__applyLive;
  window.__applyLive = function(scores){
    try{ if(prev) prev(scores); }catch(e){}
    try{
      var c = casNow();
      if(typeof scores.cab_north === 'number' && (c.recent || c.soon)){
        // слезлите преди малко тежат най-много — те са на място СЕГА
        var boost = Math.min(3.0, c.recent*0.9 + c.soon*0.55);
        scores.cab_north = Math.max(scores.cab_north, 1.0 + boost);
        window.__casInfo = c;
      }
    }catch(e){}
  };

  // подсказка в списъка защо гори
  setInterval(function(){
    try{
      var c = window.__casInfo; if(!c) return;
      var items = document.querySelectorAll('#zone-list .zone-item, .zone-item');
      Array.prototype.slice.call(items).forEach(function(it){
        var nm = it.querySelector('.zone-name') || it;
        if((nm.textContent||'').indexOf('Централна автогара') < 0) return;
        if(it.dataset && it.dataset.cas === (c.recent+'/'+c.soon)) return;
        if(it.dataset) it.dataset.cas = c.recent+'/'+c.soon;
        var sub = it.querySelector('.cas-sub');
        if(!sub){
          sub = document.createElement('div');
          sub.className = 'cas-sub';
          sub.style.cssText = 'font-size:11px;opacity:.75;margin-top:2px';
          nm.parentElement.appendChild(sub);
        }
        var bits = [];
        if(c.recent) bits.push('🚌 ' + c.recent + ' слезли <20м');
        if(c.soon) bits.push(c.soon + ' идват <30м');
        sub.textContent = bits.join(' · ') + (c.names.length ? ' (' + c.names.join(', ') + ')' : '');
      });
    }catch(e){}
  }, 12000);
})();
"""
    rep.append('OK   Централна автогара: деманд от разписанието + подсказка в списъка')

# ── (4) диагностика за кръговете и посоката ──
os.makedirs('debug', exist_ok=True)
diag = []
for kw in ['circleMap', 'L.circle', 'fillOpacity', 'direction-hint', 'КЪМ ЛЕТИЩЕТО', 'Карай']:
    idx2 = cand.find(kw)
    if idx2 < 0:
        diag.append('--- %s: НЕ Е НАМЕРЕН ---' % kw)
        continue
    ln = cand.count('\n', 0, idx2) + 1
    diag.append('--- %s (ред %d) ---\n%s' % (kw, ln, cand[max(0, idx2-500):idx2+700]))
open('debug/ui-diag2.txt', 'w', encoding='utf-8').write('\n\n'.join(diag)[:14000] + '\n')
rep.append('OK   дъмп за кръгове/посока -> debug/ui-diag2.txt')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v19', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda mm: mm.group(1) + 'bak-v19' + mm.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v19 + node --check + cache-bust v19')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

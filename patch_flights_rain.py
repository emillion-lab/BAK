# -*- coding: utf-8 -*-
"""v30: скролващият тикер показва САМО предстоящи точки (следващите ~5ч),
без вече минали часове. Плюс дъмп на кода му, за да го оправим в източника,
ако DOM филтърът не е достатъчен."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── дъмп на тикер кода ──
os.makedirs('debug', exist_ok=True)
dump, seen = [], []
for kw in ['ticker', 'Ticker', 'marquee', 'buildTicker', 'renderTicker', 'scroll-text', 'event-strip']:
    for m in re.finditer(re.escape(kw), cand):
        ln = cand.count('\n', 0, m.start()) + 1
        if any(abs(ln - s) < 40 for s in seen):
            continue
        seen.append(ln)
        dump.append('--- %s (ред %d) ---\n%s' % (kw, ln, cand[max(0, m.start()-500):m.start()+800]))
        if len(dump) >= 6:
            break
    if len(dump) >= 6:
        break
open('debug/ticker.txt', 'w', encoding='utf-8').write(
    ('\n\n'.join(dump) or 'НЕ Е НАМЕРЕН тикер по ключовите думи')[:13000] + '\n')
rep.append('тикер: %d фрагмента -> debug/ticker.txt' % len(dump))

# ── DOM филтър: маха миналите точки от лентата ──
if 'ticker-future-v30' in cand:
    rep.append('SKIP v30 вече е приложен')
else:
    cand += """

// ------ ticker-future-v30: само предстоящи точки (напред ~5ч) ------
(function(){
  var HORIZON_H = 5;      // колко часа напред показваме
  var GRACE_MIN = 10;     // толкова минути след часа още се брои за "сега"

  function nowMin(){ var d = new Date(); return d.getHours()*60 + d.getMinutes(); }

  function ahead(hhmm){
    var m = /^(\\d{1,2}):(\\d{2})$/.exec(hhmm);
    if(!m) return null;
    var t = (+m[1])*60 + (+m[2]);
    var d = t - nowMin();
    if(d < -180) d += 1440;          // явно е за утре
    return d;
  }

  function keep(seg){
    var times = seg.match(/\\b\\d{1,2}:\\d{2}\\b/g);
    if(!times || !times.length) return true;      // без час — оставяме
    for(var i = 0; i < times.length; i++){
      var a = ahead(times[i]);
      if(a === null) continue;
      if(a >= -GRACE_MIN && a <= HORIZON_H*60) return true;
    }
    return false;
  }

  function findTicker(){
    var best = null, bestLen = 0;
    var sel = ['#ticker','.ticker','#event-ticker','.event-ticker','#marquee','.marquee',
               '#scroll-text','.scroll-text','#event-strip','.event-strip'];
    for(var i = 0; i < sel.length; i++){
      var el = document.querySelector(sel[i]);
      if(el && (el.textContent||'').length > bestLen){ best = el; bestLen = el.textContent.length; }
    }
    if(best) return best;
    var all = document.querySelectorAll('div,span,p');
    for(var j = 0; j < all.length; j++){
      var e = all[j], t = e.textContent || '';
      if(t.length < 40 || t.length > 3000) continue;
      if(e.children.length > 3) continue;
      var dots = (t.match(/·/g)||[]).length, tm = (t.match(/\\b\\d{1,2}:\\d{2}\\b/g)||[]).length;
      if(dots >= 2 && tm >= 2 && t.length > bestLen){ best = e; bestLen = t.length; }
    }
    return best;
  }

  function clean(){
    try{
      var el = findTicker();
      if(!el) return;
      var raw = el.dataset.tickerRaw;
      if(!raw){
        raw = el.textContent || '';
        if(raw.length < 30) return;
        el.dataset.tickerRaw = raw;
      }
      var parts = raw.split(/\\s*·\\s*/).filter(function(s){ return s.trim().length; });
      if(parts.length < 2) return;
      var kept = parts.filter(keep);
      if(!kept.length) kept = ['— няма събития в следващите ' + HORIZON_H + 'ч —'];
      var out = kept.join('  ·  ');
      if(el.textContent.trim() !== out.trim()) el.textContent = out;
    }catch(e){}
  }

  clean();
  setInterval(clean, 60000);
  try{
    var mo = new MutationObserver(function(muts){
      for(var i = 0; i < muts.length; i++){
        var t = muts[i].target;
        if(t && t.dataset && t.dataset.tickerRaw && t.textContent &&
           t.textContent.indexOf('·') >= 0 &&
           t.textContent.length > (t.dataset.tickerRaw.length * 0.9)){
          t.dataset.tickerRaw = t.textContent;
        }
      }
      clean();
    });
    mo.observe(document.body, {childList:true, subtree:true, characterData:true});
  }catch(e){}
})();
"""
    rep.append('OK   тикерът показва само предстоящи точки (напред 5ч, 10 мин гратис)')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v30', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda mm: mm.group(1) + 'bak-v30' + mm.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v30 + node --check + cache-bust v30')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

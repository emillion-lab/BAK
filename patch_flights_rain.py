# -*- coding: utf-8 -*-
"""v23: одит на inline хендлърите в index.html.
closeEventAlert я няма никъде в app.js -> вика се от HTML, но не е дефинирана.
Намираме ВСИЧКИ такива и им даваме работеща реализация (затваря съответния блок).
"""
import re, subprocess, shutil, os

rep = []
app = open('app.js', encoding='utf-8').read()
idx = open('index.html', encoding='utf-8').read()
os.makedirs('debug', exist_ok=True)

# ── 1) кои функции вика index.html ──
called = set()
for m in re.finditer(r'\bon(?:click|change|input|submit|mouseover|touchstart|focus|blur)\s*=\s*["\']([^"\']{0,120})["\']', idx):
    body = m.group(1)
    for c in re.finditer(r'([A-Za-z_$][\w$]*)\s*\(', body):
        called.add(c.group(1))
called -= {'function', 'return', 'this', 'event', 'alert', 'confirm', 'if', 'setTimeout'}
rep.append('index.html вика: %s' % (', '.join(sorted(called)) or 'няма'))

# ── 2) кои от тях реално съществуват ──
defined, undefined_ = [], []
for n in sorted(called):
    has = (re.search(r'(?<![\w.$])function\s+%s\s*\(' % re.escape(n), app)
           or re.search(r'window\.%s\s*=' % re.escape(n), app)
           or re.search(r'(?<![\w.$])(?:const|let|var)\s+%s\s*=' % re.escape(n), app)
           or re.search(r'(?<![\w.$])function\s+%s\s*\(' % re.escape(n), idx))
    (defined if has else undefined_).append(n)
rep.append('дефинирани: %s' % (', '.join(defined) or 'няма'))
rep.append('⚠ НЕдефинирани: %s' % (', '.join(undefined_) or 'няма'))

# ── 3) контекст на липсващите, за да знаем какво затварят ──
ctx = []
for n in undefined_:
    for m in re.finditer(re.escape(n), idx):
        ln = idx.count('\n', 0, m.start()) + 1
        ctx.append('--- %s (index.html ред %d) ---\n%s' % (n, ln, idx[max(0, m.start()-400):m.start()+160]))
        break
open('debug/undefined-inline.txt', 'w', encoding='utf-8').write(
    ('\n\n'.join(ctx) or 'няма липсващи') + '\n')

# ── 4) универсална реализация: затваря блока, от който е бутонът ──
if undefined_ and 'inline-closer-v23' not in app:
    names = repr(undefined_).replace("'", '"')
    closer = """// inline-closer-v23 — работещи реализации за inline хендлъри от index.html
(function(){
  function hideOwner(){
    try{
      var ev = window.event;
      var t = ev && (ev.target || ev.srcElement);
      if(t){
        var n = t;
        for(var i = 0; i < 7 && n; i++){
          n = n.parentElement;
          if(!n) break;
          var cls = (n.className || '').toString();
          if(n.id || /alert|event|banner|toast|popup|hint|modal|box/i.test(cls)){
            n.style.display = 'none';
            return true;
          }
        }
        if(t.parentElement){ t.parentElement.style.display = 'none'; return true; }
      }
      var ids = ['event-alert','eventAlert','event-banner','alert-box',
                 'bakshish-box','direction-hint','karyk-banner','rain-banner'];
      for(var k = 0; k < ids.length; k++){
        var e = document.getElementById(ids[k]);
        if(e && e.offsetParent !== null){ e.style.display = 'none'; return true; }
      }
    }catch(err){}
    return false;
  }
  var N = __NAMES__;
  N.forEach(function(n){
    if(typeof window[n] === 'function') return;
    window[n] = hideOwner;
  });
})();

""".replace('__NAMES__', names)
    app = closer + app
    rep.append('OK   реализирани: %s (затварят блока, от който е бутонът)' % ', '.join(undefined_))

open('/tmp/app.c.js', 'w', encoding='utf-8').write(app)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v23', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda mm: mm.group(1) + 'bak-v23' + mm.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v23 + node --check + cache-bust v23')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

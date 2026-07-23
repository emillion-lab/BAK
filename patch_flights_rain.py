# -*- coding: utf-8 -*-
"""v16 SPASITEL: показва реалната грешка на екрана + не позволява на
една счупена секция да убие цялото приложение.

1) window.onerror -> червена лента с файл:ред и съобщение (можеш да я снимаш)
2) обвива DOMContentLoaded хендлърите в try/catch, така че грешка в
   средата да не спира останалото (картата/зоните/времето продължават)
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()

if 'bak-rescue-v16' in src:
    rep.append('SKIP v16 вече е приложен')
    cand = src
else:
    guard = """// bak-rescue-v16 — ловец на грешки (вмъкнат НАЙ-ОТГОРЕ)
(function(){
  var shown = 0;
  function show(msg, extra){
    if (shown >= 3) return;
    shown++;
    try{
      var d = document.createElement('div');
      d.style.cssText = 'position:fixed;left:0;right:0;top:0;z-index:99999;'
        + 'background:#7f1d1d;color:#fff;font:12px/1.35 monospace;padding:8px 30px 8px 10px;'
        + 'white-space:pre-wrap;word-break:break-word;box-shadow:0 2px 8px rgba(0,0,0,.6)';
      d.textContent = '⚠ ' + msg + (extra ? ('\\n' + extra) : '');
      var x = document.createElement('span');
      x.textContent = '✕';
      x.style.cssText = 'position:absolute;right:8px;top:6px;cursor:pointer;font-size:16px';
      x.onclick = function(){ d.remove(); };
      d.appendChild(x);
      (document.body || document.documentElement).appendChild(d);
    }catch(e){}
  }
  window.addEventListener('error', function(ev){
    var f = (ev.filename||'').split('/').pop();
    show((ev.message||'грешка'), f + ':' + ev.lineno + ':' + ev.colno);
  });
  window.addEventListener('unhandledrejection', function(ev){
    var r = ev.reason;
    show('Promise: ' + ((r && (r.message||r)) || 'отхвърлен'), '');
  });
  // защита: грешка в един DOMContentLoaded хендлър да не спира другите
  var origAdd = document.addEventListener.bind(document);
  document.addEventListener = function(ev, fn, opt){
    if (ev === 'DOMContentLoaded' && typeof fn === 'function'){
      var wrapped = function(e){
        try { return fn.call(this, e); }
        catch(err){
          show('DOMContentLoaded: ' + (err && err.message),
               ((err && err.stack)||'').split('\\n')[1] || '');
          throw err;
        }
      };
      return origAdd(ev, wrapped, opt);
    }
    return origAdd(ev, fn, opt);
  };
})();

"""
    cand = guard + src
    rep.append('OK   ловец на грешки вмъкнат най-отгоре')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v16', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    rep.append('OK v16 + node --check + cache-bust v16')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

# вдигаме и версията на service worker-а, за да не сервира стар кеш
try:
    sw = open('sw.js', encoding='utf-8').read()
    new_sw, n = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                        lambda m: m.group(1) + 'bak-v16' + m.group(3), sw, count=1)
    if n:
        open('sw.js', 'w', encoding='utf-8').write(new_sw)
        rep.append('OK   sw.js кеш име -> bak-v16 (изхвърля стария кеш)')
    else:
        rep.append('SKIP sw.js: не намерих име на кеша')
except FileNotFoundError:
    rep.append('SKIP sw.js липсва')

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

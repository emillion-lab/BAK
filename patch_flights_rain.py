# -*- coding: utf-8 -*-
"""v3: (1) ✕ + авто-скриване на стария rain-banner (виси часове след дъжда)
       (2) ✕ на exit-now панела
       (3) преместване на моите чипове под КЪРК бутона (180px) — край на застъпването
Целеви замени + append + node --check + cache-bust."""
import re, subprocess, shutil

rep = []
src = open('app.js', encoding='utf-8').read()

if 'ui-fix-v3' in src:
    rep.append('SKIP v3 вече е приложен')
else:
    header_old = "var html='<div style=\\\"font-weight:900;font-size:14px;margin-bottom:8px\\\">🛬 Изходи Терминал 1/2</div>';"
    header_new = ("var html='<div style=\\\"font-weight:900;font-size:14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center\\\">"
                  "<span>🛬 Изходи Терминал 1/2</span>"
                  "<span style=\\\"cursor:pointer;padding:2px 10px;font-size:16px;color:#94a3b8\\\" "
                  "onclick=\\\"this.parentElement.parentElement.style.display=&quot;none&quot;\\\">✕</span></div>';")
    repl = [
        ("bottom:174px", "bottom:154px"),   # SEV чип
        ("bottom:218px", "bottom:112px"),   # ☔ чип
        ("bottom:262px", "bottom:70px"),    # 🛬 чип
        (header_old, header_new),
    ]
    cand = src
    ok = True
    for old, new in repl:
        if cand.count(old) != 1:
            rep.append(f'FAIL count={cand.count(old)} за: {old[:60]}')
            ok = False
            break
        cand = cand.replace(old, new)
    if ok:
        cand += """

// ------ rain-banner: ✕ бутон + авто-скриване след края на дъжда ------
// ui-fix-v3 rain-toast-x
(function(){
  function tend(txt){
    var m=/до\\s+(\\d{1,2}):(\\d{2})/.exec(txt||'');
    if(!m) return null;
    var d=new Date(); d.setHours(+m[1],+m[2],0,0);
    return d.getTime();
  }
  function tick(){
    var el=document.getElementById('rain-banner');
    if(!el) return;
    var end=tend(el.textContent);
    if(end && Date.now()>end+10*60000){ el.remove(); return; }
    if(!el.dataset.rx){
      el.dataset.rx='1';
      var x=document.createElement('span');
      x.textContent=' ✕';
      x.style.cssText='cursor:pointer;padding:0 4px 0 10px;opacity:.85';
      x.onclick=function(ev){ev.stopPropagation();el.remove();};
      el.appendChild(x);
    }
  }
  tick(); setInterval(tick, 30000);
})();
"""
        open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
        r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
        if r.returncode == 0:
            shutil.move('/tmp/app.c.js', 'app.js')
            idx = open('index.html', encoding='utf-8').read()
            idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260722v3', idx)
            open('index.html', 'w', encoding='utf-8').write(idx)
            rep.append('OK v3: rain ✕/авто-скриване, панел ✕, чипове 70/112/154 + node --check')
        else:
            rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

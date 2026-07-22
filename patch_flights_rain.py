# -*- coding: utf-8 -*-
"""v7: (1) rain-banner убит окончателно — по ID, по КЛАС и по текст
           (предишният опит търсеше само getElementById и не го е хващал)
       (2) ZONES се изнасят в debug/zones.json за одит на координатите"""
import re, json, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()

# ---------- (2) изнасяне на ZONES за одит ----------
try:
    m = re.search(r'const\s+ZONES\s*=\s*\[', src)
    if m:
        i = src.index('[', m.start())
        depth, j = 0, i
        while j < len(src):
            if src[j] == '[':
                depth += 1
            elif src[j] == ']':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        body = src[i:j + 1]
        zones = []
        for zm in re.finditer(
                r'id:"([^"]+)"\s*,\s*name:"([^"]+)"\s*,\s*icon:"([^"]*)"\s*,\s*'
                r'lat:([\d.]+)\s*,\s*lng:([\d.]+)\s*,\s*radius:(\d+)\s*,\s*type:"([^"]+)"'
                r'(?:\s*,\s*wazeName:"([^"]*)")?', body):
            zones.append({"id": zm.group(1), "name": zm.group(2), "icon": zm.group(3),
                          "lat": float(zm.group(4)), "lng": float(zm.group(5)),
                          "radius": int(zm.group(6)), "type": zm.group(7),
                          "wazeName": zm.group(8) or ""})
        os.makedirs('debug', exist_ok=True)
        json.dump(zones, open('debug/zones.json', 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        rep.append('ZONES изнесени: %d зони -> debug/zones.json' % len(zones))
    else:
        rep.append('ZONES не бяха намерени')
except Exception as e:
    rep.append('ZONES грешка: %r' % e)

# ---------- (1) убиване на rain-banner ----------
if 'bak-v7' in src:
    rep.append('SKIP v7 вече е приложен')
else:
    cand = src + """

// ------ bak-v7: rain-banner окончателно ------
// Предишният опит търсеше само #rain-banner. Ако е клас или без id,
// не го хващаше. Сега: по id, по клас И по текстово съдържание.
(function(){
  var RX = /Дъжд\\s+около|Дъжд\\s+\\d{1,2}:\\d{2}\\s+до/;
  function kill(){
    var hits = [];
    var byId = document.getElementById('rain-banner');
    if(byId) hits.push(byId);
    Array.prototype.push.apply(hits, document.querySelectorAll('.rain-banner,#rain-banner,[data-rain]'));
    // текстов лов: fixed елемент в горната част на екрана с дъждовен текст
    Array.prototype.slice.call(document.querySelectorAll('div,span,section')).forEach(function(el){
      if(el.children.length > 2) return;
      var t = el.textContent || '';
      if(t.length > 90 || !RX.test(t)) return;
      var cs = window.getComputedStyle(el);
      if(cs.position === 'fixed' || cs.position === 'absolute' ||
         (el.parentElement && window.getComputedStyle(el.parentElement).position === 'fixed')) {
        hits.push(el);
      }
    });
    hits.forEach(function(el){ try{ el.remove(); }catch(e){ el.style.display='none'; } });
  }
  kill();
  setInterval(kill, 3000);
  // и при всяка промяна в DOM-а (ако се пресъздава)
  try{
    new MutationObserver(function(){ kill(); })
      .observe(document.body, {childList:true, subtree:true});
  }catch(e){}
})();
"""
    open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
    r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
    if r.returncode == 0:
        shutil.move('/tmp/app.c.js', 'app.js')
        idx = open('index.html', encoding='utf-8').read()
        idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260722v7', idx)
        open('index.html', 'w', encoding='utf-8').write(idx)
        rep.append('OK v7: rain-banner по id+клас+текст+MutationObserver')
    else:
        rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

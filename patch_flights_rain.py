# -*- coding: utf-8 -*-
"""v47: довършва showZonePopup.
Детекторът от v46 не я хвана — значи се вика по шаблон, който не разпознахме.
Тук я търсим директно и ако съществува, я изнасяме; ако не — даваме
работеща заместваща реализация, която фокусира зоната и отваря popup-а ѝ."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── диагностика: къде се среща ──
os.makedirs('debug', exist_ok=True)
ctx = []
for m in re.finditer(r'showZonePopup', cand):
    ln = cand.count('\n', 0, m.start()) + 1
    ctx.append('--- ред %d ---\n%s' % (ln, cand[max(0, m.start()-300):m.start()+220]))
open('debug/showZonePopup.txt', 'w', encoding='utf-8').write(
    ('\n\n'.join(ctx[:8]) or 'НЯМА в app.js') + '\n')
rep.append('showZonePopup: %d срещания в app.js' % len(ctx))

# и в index.html
try:
    html = open('index.html', encoding='utf-8').read()
    rep.append('showZonePopup в index.html: %d' % html.count('showZonePopup'))
except FileNotFoundError:
    pass

# ── изнасяне, ако е декларирана ──
done = False
decl = re.compile(r'(?<![\w.$])function\s+showZonePopup\s*\(')
if len(decl.findall(cand)) == 1:
    cand = decl.sub('window.showZonePopup = function showZonePopup(', cand, count=1)
    rep.append('OK   showZonePopup изнесена в window')
    done = True
else:
    vdecl = re.compile(r'(?<![\w.$])(?:const|let|var)\s+showZonePopup\s*=')
    if len(vdecl.findall(cand)) == 1:
        cand = vdecl.sub('window.showZonePopup = ', cand, count=1)
        rep.append('OK   showZonePopup изнесена (променлива)')
        done = True

# ── заместваща реализация, ако липсва ──
if not done and 'showzonepopup-fallback-v47' not in cand:
    fb = """// showzonepopup-fallback-v47 — функцията се вика от inline onclick,
// но живее в затворен обхват (или изобщо липсва). Даваме работещ заместник:
// намира зоната по id, центрира картата и отваря popup-а на нейния кръг.
(function(){
  if(typeof window.showZonePopup === 'function') return;
  window.showZonePopup = function(zid){
    try{
      var Z = window.__ZONES || [];
      var z = null;
      for(var i = 0; i < Z.length; i++){
        if(Z[i].id === zid){ z = Z[i]; break; }
      }
      if(!z && typeof zid === 'string'){
        // подадено е име, не id
        for(var j = 0; j < Z.length; j++){
          if((Z[j].name || '').indexOf(zid) >= 0){ z = Z[j]; break; }
        }
      }
      if(!z) return;
      if(window.__focusZone) window.__focusZone(z.lat, z.lng, 15);
      var map = window.__leafletMap;
      if(!map) return;
      // намираме кръга на тази зона и му отваряме popup-а
      setTimeout(function(){
        try{
          map.eachLayer(function(l){
            if(!l || typeof l.getLatLng !== 'function') return;
            if(typeof l.getRadius !== 'function') return;
            var ll = l.getLatLng();
            if(!ll) return;
            var dx = (ll.lat - z.lat) * 111000, dy = (ll.lng - z.lng) * 82000;
            if(Math.sqrt(dx*dx + dy*dy) < 60 && l.openPopup) l.openPopup();
          });
        }catch(e){}
      }, 300);
    }catch(e){}
  };
})();

"""
    cand = fb + cand
    rep.append('OK   заместваща showZonePopup (фокус + отваряне на popup)')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v47', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v47' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v47 + node --check + cache-bust v47')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

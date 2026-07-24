# -*- coding: utf-8 -*-
"""v38: (1) Борово, Павлово, Младост 1 по линковете на Емил + Младост 4
       (2) Oval Business Center — премахнат, обектът не съществува
       (3) точката на бул.България отива на проверено място върху булеварда
       (4) старите лилави точки за трафика се махат (линиите ги заместиха)
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

def move(zid, lat, lng, newname=None, note=''):
    global cand
    pat = re.compile(r'(\{\s*id:"%s"\s*,\s*name:")([^"]*)("[^}]*?lat:)([\d.]+)(\s*,\s*lng:)([\d.]+)'
                     % re.escape(zid))
    m = pat.search(cand)
    if not m:
        rep.append('SKIP %-12s не е намерена' % zid)
        return
    ol, og = float(m.group(4)), float(m.group(6))
    d = int((((lat-ol)*111000)**2 + ((lng-og)*82000)**2) ** 0.5)
    nm = newname if newname else m.group(2)
    cand = pat.sub(lambda x: x.group(1)+nm+x.group(3)+str(lat)+x.group(5)+str(lng), cand, count=1)
    rep.append('OK   %-12s -> %.4f,%.4f  (беше на %d м) %s' % (zid, lat, lng, d, note))

# (1) по линковете
move('k_borovo', 42.6687, 23.2897, None, 'по линка на Емил')
move('k_pavlovo', 42.6678, 23.2658, None, 'трамвайна спирка кв.Павлово')
move('mladost',  42.6542, 23.3719, 'жк Младост 1', 'метростанция Младост 1')

# Младост 4
if 'mladost4' not in cand:
    anchor = '{ id:"mladost2",'
    if cand.count(anchor) == 1:
        z = ('{ id:"mladost4", name:"жк Младост 4", icon:"🏘", lat:42.6285, lng:23.3793, '
             'radius:320, type:"residential", wazeName:"жк Младост 4 София" },\n  ')
        cand = cand.replace(anchor, z + anchor, 1)
        rep.append('OK   mladost4     + 42.6285, 23.3793 (по линка)')
    else:
        rep.append('SKIP котва mladost2 x%d' % cand.count(anchor))

# (2) Oval не съществува
pat_oval = re.compile(r'\s*\{\s*id:"oval".*?\}\s*,?', re.S)
if pat_oval.search(cand):
    cand = pat_oval.sub('\n  ', cand, count=1)
    rep.append('OK   oval ПРЕМАХНАТ (обектът не съществува)')
    # и събитията-сираци към него
    ev = re.compile(r'\s*\{[^{}]*zone:\s*"oval"[^{}]*\}\s*,?')
    n = len(ev.findall(cand))
    if n:
        cand = ev.sub('\n  ', cand)
        rep.append('OK   премахнати %d събития към oval' % n)

# (3) бул. България — точка ВЪРХУ булеварда (при Мол България, сверено)
move('jam_ndk', 42.6655, 23.2895,
     '⚠ Задръстване бул.България (при Мол България)',
     'беше в преките до Петко Тодоров')

# (4) старите точки за трафика
if 'kill-jam-markers-v38' not in cand:
    cand += """

// ------ kill-jam-markers-v38: махаме старите точки, линиите ги заместиха ------
(function(){
  var PTS = [
    [42.6906, 23.3374], [42.6752, 23.3587], [42.6655, 23.2895], [42.7049, 23.3239]
  ];
  function near(a, b){
    var dx = (a[0]-b[0])*111000, dy = (a[1]-b[1])*82000;
    return Math.sqrt(dx*dx + dy*dy) < 120;
  }
  function sweep(){
    try{
      var map = window.__leafletMap;
      if(!map) return;
      var kill = [];
      map.eachLayer(function(l){
        if(!l || typeof l.getLatLng !== 'function') return;
        if(typeof l.getRadius === 'function') return;      // кръговете остават
        if(l.__isTrafficLine) return;
        var ll = l.getLatLng();
        if(!ll) return;
        for(var i = 0; i < PTS.length; i++){
          if(near([ll.lat, ll.lng], PTS[i])){
            // пазим надписите (те са с iconSize 0)
            var ic = l.options && l.options.icon;
            var sz = ic && ic.options && ic.options.iconSize;
            if(sz && sz[0] === 0 && sz[1] === 0) return;
            kill.push(l);
            return;
          }
        }
      });
      kill.forEach(function(l){ try{ map.removeLayer(l); }catch(e){} });
    }catch(e){}
  }
  sweep();
  setInterval(sweep, 4000);
})();
"""
    rep.append('OK   старите точки за трафика се махат (линиите остават)')

ids = re.findall(r'\{\s*id:"([^"]+)"\s*,\s*name:', cand)
dups = sorted({i for i in ids if ids.count(i) > 1})
rep.append('зони: %d · дубликати: %s' % (len(ids), ', '.join(dups) if dups else 'няма'))

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v38', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v38' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v38 + node --check + cache-bust v38')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

# -*- coding: utf-8 -*-
"""v37: одит на кварталите — всички сверени с Google Places.
Овча купел, Изток, Изгрев, Борово, Борисова, НДК дубликат, Младост разделен.
НЕ пипам Павлово и Oval — не намерих надежден източник."""
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
        rep.append('SKIP %-14s не е намерена' % zid)
        return
    ol, og = float(m.group(4)), float(m.group(6))
    d = int((((lat-ol)*111000)**2 + ((lng-og)*82000)**2) ** 0.5)
    nm = newname if newname else m.group(2)
    cand = pat.sub(lambda x: x.group(1)+nm+x.group(3)+str(lat)+x.group(5)+str(lng), cand, count=1)
    rep.append('OK   %-14s -> %.4f,%.4f  (беше на %d м) %s' % (zid, lat, lng, d, note))

# ── кварталите ──
move('ovcha_kupel', 42.6900, 23.2541, None, 'беше в Манастирски ливади')
move('k_izgrev',    42.6705, 23.3487, None, '')
move('k_iztok',     42.6702, 23.3649, None, 'беше в Гео Милев')
move('k_borovo',    42.6692, 23.2797, None, 'беше в Стрелбище')
move('borisova',    42.6805, 23.3420, 'Борисова градина (към Цариградско)', 'преместена на север')

# ── Младост: 1/2/3 в една зона -> три отделни ──
m = re.search(r'\{\s*id:"mladost"[^}]*\}', cand)
if m:
    obj = m.group(0)
    ztype = (re.search(r'type:"([^"]+)"', obj) or [None, 'residential'])[1]
    rad = (re.search(r'radius:(\d+)', obj) or [None, '350'])[1]
    m1 = re.sub(r'lat:[\d.]+\s*,\s*lng:[\d.]+', 'lat:42.6498, lng:23.3722', obj)
    m1 = re.sub(r'name:"[^"]*"', 'name:"жк Младост 1"', m1)
    m1 = re.sub(r'radius:\d+', 'radius:300', m1)
    m1 = re.sub(r'wazeName:"[^"]*"', 'wazeName:"жк Младост 1 София"', m1)
    m2 = ('{ id:"mladost2", name:"жк Младост 2", icon:"🏘", lat:42.6422, lng:23.3689, '
          'radius:300, type:"%s", wazeName:"жк Младост 2 София" }' % ztype)
    m3 = ('{ id:"mladost3", name:"жк Младост 3", icon:"🏘", lat:42.6421, lng:23.3808, '
          'radius:300, type:"%s", wazeName:"жк Младост 3 София" }' % ztype)
    cand = cand.replace(obj, m1 + ',\n  ' + m2 + ',\n  ' + m3, 1)
    rep.append('OK   Младост разделен на 1 (42.6498,23.3722), 2 (42.6422,23.3689), 3 (42.6421,23.3808)')
    rep.append('     ⚠ Младост 1 е по метростанцията — потвърди дали е добре')
else:
    rep.append('SKIP зоната mladost не е намерена')

# ── двойното НДК: hotels_ndk стои върху самото НДК ──
mh = re.search(r'\{\s*id:"hotels_ndk"[^}]*\}', cand)
mn = re.search(r'\{\s*id:"ndk"[^}]*lat:([\d.]+)\s*,\s*lng:([\d.]+)', cand)
if mh and mn:
    hlat = float(re.search(r'lat:([\d.]+)', mh.group(0)).group(1))
    hlng = float(re.search(r'lng:([\d.]+)', mh.group(0)).group(1))
    nlat, nlng = float(mn.group(1)), float(mn.group(2))
    dist = int((((hlat-nlat)*111000)**2 + ((hlng-nlng)*82000)**2) ** 0.5)
    if dist < 150:
        move('hotels_ndk', 42.6829, 23.3195, 'Хотел Hilton (бул.България 1)',
             'беше върху НДК (%d м) — Kempinski вече е Маринела' % dist)
    else:
        rep.append('SKIP hotels_ndk е на %d м от НДК — не е дубликат' % dist)

# ── Автогара Юг: работно време в popup-а ──
if 'ag-yug-v37' not in cand:
    cand += """

// ------ ag-yug-v37: работно време на Автогара Юг ------
(function(){
  function enrich(el){
    try{
      if(!el || (el.dataset && el.dataset.agyug)) return;
      var t = el.textContent || '';
      if(!/Автогара Юг/i.test(t)) return;
      if(el.dataset) el.dataset.agyug = '1';
      var now = new Date(), h = now.getHours() + now.getMinutes()/60;
      var open = (h >= 7.5 && h <= 18.5);
      el.insertAdjacentHTML('beforeend',
        '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;'
        + 'background:rgba(56,189,248,.10);border-left:3px solid #38bdf8;font-size:12px">'
        + '<b>🚌 Автогара Юг</b><br>'
        + 'Работи <b>07:30–18:30</b> · ' + (open ? '<span style="color:#22c55e">отворена</span>'
                                                 : '<span style="color:#94a3b8">затворена</span>')
        + '<br><span style="opacity:.7">Направление Самоков · Боровец · Рила<br>'
        + 'Няма публично разписание · плащане в брой</span></div>');
    }catch(e){}
  }
  function scan(){ try{ document.querySelectorAll('.leaflet-popup-content').forEach(enrich); }catch(e){} }
  scan(); setInterval(scan, 4000);
  try{ new MutationObserver(scan).observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();
"""
    rep.append('OK   Автогара Юг: работно време 07:30–18:30 + направления')

rep.append('')
rep.append('⚠ НЕ пипнах (няма надежден източник — прати линк):')
rep.append('   · Павлово — Google не върна квартала')
rep.append('   · Oval Business Center — не се намира по това име')

ids = re.findall(r'\{\s*id:"([^"]+)"\s*,\s*name:', cand)
dups = sorted({i for i in ids if ids.count(i) > 1})
rep.append('зони: %d · дубликати: %s' % (len(ids), ', '.join(dups) if dups else 'няма'))

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v37', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v37' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v37 + node --check + cache-bust v37')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('debug/coords-audit-3.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

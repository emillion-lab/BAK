# -*- coding: utf-8 -*-
"""v31: (1) + басейн Корали и Infinity SPA (Панчарево, Самоковско шосе 211)
       (2) задръстванията — точките отиват на реални ориентири по съответното
           трасе и имената казват че са ОТСЕЧКИ, не точки
       (3) край на противоречието "1.5 Нормален" + "ЗАДРЪСТЕНО СЕГА" —
           статусът се сверява с показания пиков час
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (1) новите басейни ──
NEW = [
    ('pool_korali', 'Басейн Корали (Панчарево) ☀лято', 42.6027, 23.4039, 200,
     'Korali Pool Самоковско шосе 211 Панчарево'),
    ('pool_infinity', 'Infinity SPA (Панчарево)', 42.6019, 23.4035, 180,
     'Infinity SPA Самоковско шосе 211 Панчарево'),
]
anchor = '{ id:"pool_spartak",'
if cand.count(anchor) == 1:
    block = ''
    for zid, name, lat, lng, rad, waze in NEW:
        if zid in cand:
            rep.append('SKIP %s вече съществува' % zid)
            continue
        block += ('{ id:"%s", name:"%s", icon:"🏊", lat:%s, lng:%s, radius:%d, '
                  'type:"leisure", wazeName:"%s" },\n  ' % (zid, name, lat, lng, rad, waze))
        rep.append('OK   %-14s + %.4f, %.4f' % (zid, lat, lng))
    if block:
        cand = cand.replace(anchor, block + anchor, 1)
else:
    rep.append('SKIP котва pool_spartak x%d' % cand.count(anchor))

# работно време в модела от v15
old_sp = 'pool_sportpalace: [6.5, 19.5, 8,   17,   1]'
if old_sp in cand and 'pool_korali:' not in cand:
    new_sp = ('pool_korali:      [9,   19,   9,   19,   0],\n'
              '    pool_infinity:    [9,   20,   9,   20,   1],\n'
              '    ' + old_sp)
    cand = cand.replace(old_sp, new_sp, 1)
    rep.append('OK   работно време: Корали 9–19, Infinity 9–20 (пон. почивен)')

# ── (2) задръстванията на реални ориентири ──
JAMS = [
    ('jam_serdika', 42.7049, 23.3239,
     '⚠ Задръстване бул.Сливница (при Лъвов мост)'),
    ('jam_tsar',    42.6752, 23.3587,
     '⚠ Задръстване Цариградско (при хотел Плиска)'),
    ('jam_ndk',     42.6745, 23.3028,
     '⚠ Задръстване бул.България (НДК → Мол България)'),
]
for zid, lat, lng, name in JAMS:
    pat = re.compile(r'(\{\s*id:"%s"\s*,\s*name:")([^"]*)("[^}]*?lat:)([\d.]+)(\s*,\s*lng:)([\d.]+)'
                     % re.escape(zid))
    m = pat.search(cand)
    if not m:
        rep.append('SKIP %s не е намерена' % zid)
        continue
    ol, og = float(m.group(4)), float(m.group(6))
    d = int((((lat-ol)*111000)**2 + ((lng-og)*82000)**2) ** 0.5)
    cand = pat.sub(lambda x: x.group(1)+name+x.group(3)+str(lat)+x.group(5)+str(lng), cand, count=1)
    rep.append('OK   %-12s %.4f,%.4f -> %.4f,%.4f (беше на %d м)' % (zid, ol, og, lat, lng, d))

# ── (3) статусът да не противоречи на пиковия час ──
if 'jam-status-v31' in cand:
    rep.append('SKIP статусът вече е поправен')
else:
    cand += """

// ------ jam-status-v31: "ЗАДРЪСТЕНО СЕГА" само ако наистина е пиков час ------
(function(){
  function inPeak(txt){
    // чете реда "⏰ Пик: 07:30–09:30 делнични" от самия popup
    var m = txt.match(/Пик:\\s*([\\d:–\\-\\s и]+)/);
    if(!m) return null;
    var now = new Date();
    var wknd = (now.getDay() === 0 || now.getDay() === 6);
    if(/делнич/i.test(txt) && wknd) return false;      // само в делник
    var cur = now.getHours()*60 + now.getMinutes();
    var ranges = m[1].match(/(\\d{1,2}):(\\d{2})\\s*[–\\-]\\s*(\\d{1,2}):(\\d{2})/g) || [];
    if(!ranges.length) return null;
    for(var i = 0; i < ranges.length; i++){
      var p = ranges[i].match(/(\\d{1,2}):(\\d{2})\\s*[–\\-]\\s*(\\d{1,2}):(\\d{2})/);
      var a = (+p[1])*60 + (+p[2]), b = (+p[3])*60 + (+p[4]);
      if(cur >= a && cur <= b) return true;
    }
    return false;
  }

  function fix(el){
    try{
      if(!el || (el.dataset && el.dataset.jam31)) return;
      var txt = el.textContent || '';
      if(txt.indexOf('Пик:') < 0) return;
      if(!/ЗАДРЪСТЕНО СЕГА|В МОМЕНТА СВОБОДНО/.test(txt)) return;
      var peak = inPeak(txt);
      if(peak === null) return;
      if(el.dataset) el.dataset.jam31 = '1';
      var html = el.innerHTML;
      if(!peak){
        // извън пиков час: статусът става зелен, а съветът за обратна посока пада
        html = html.replace(/🔴\\s*ЗАДРЪСТЕНО СЕГА/g, '🟢 СВОБОДНО (извън пиков час)');
        html = html.replace(/<div[^>]*>💡[^<]*<\\/div>/g, '');
      } else {
        html = html.replace(/🟢\\s*В МОМЕНТА СВОБОДНО/g, '🔴 ЗАДРЪСТЕНО СЕГА');
        html = html.replace(/💡\\s*Карай\\s*([←→↔↑↓])\\s*обратно\\s*—\\s*стигаш по-бързо!/g,
                            '💡 Насрещното платно $1 е свободно');
      }
      // отсечка, не точка
      if(html.indexOf('отсечка') < 0){
        html = html.replace(/(⏰\\s*Пик:)/,
          '<div style="font-size:11px;color:#64748b;margin:3px 0">'
          + '📍 Маркерът е ориентир за цялата отсечка, не точно място</div>$1');
      }
      el.innerHTML = html;
    }catch(e){}
  }
  function scan(){
    try{ document.querySelectorAll('.leaflet-popup-content').forEach(fix); }catch(e){}
  }
  scan(); setInterval(scan, 3000);
  try{ new MutationObserver(scan).observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();
"""
    rep.append('OK   статусът се сверява с пиковия час + бележка че е отсечка')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    ids = re.findall(r'\{\s*id:"([^"]+)"\s*,\s*name:', cand)
    rep.append('зони: %d' % len(ids))
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v31', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda mm: mm.group(1) + 'bak-v31' + mm.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v31 + node --check + cache-bust v31')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

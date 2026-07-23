# -*- coding: utf-8 -*-
"""v14: + 3 проверени басейна с реален такси потенциал.
Съзнателно ПРОПУСНАТИ от Google резултатите:
  · 'Басейни intex онлайн' (GStroy) — магазин за надуваеми басейни, не басейн
  · 138 СУ и др. училищни — няма външна публика
  · Villa Spaggo — вила за събития, не публичен басейн
  · Аквапарк София (Божурище) / Аквабанкя — извън града, друг тип курс
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

NEW = [
    # id, име, lat, lng, радиус, waze, бележка
    ('pool_silvercity', 'Басейн Silver City (Хладилника)', 42.6558, 23.1331, 180,
     'Silver City басейн София', 'ЗАПАЗЕН МЕСТОДЪРЖАТЕЛ — виж корекцията долу'),
    ('pool_sportpalace', 'Sport Palace Pool (В.Левски 75) 🏠целогодишен', 42.6903, 23.3312, 160,
     'Sport Palace Pool София', 'закрит, работи и зимата'),
    ('pool_hearts', 'Hearts in Love Pool Club ☀лято', 42.6271, 23.4238, 200,
     'Hearts in Love Pool Club София', 'извън града, уикенд дестинация'),
]
# коригирана координата за Silver City (правилна дължина)
NEW[0] = ('pool_silvercity', 'Басейн Silver City (Хладилника) ☀до 22ч', 42.6558, 23.3131, 180,
          'Silver City басейн София', 'работи 7:00–22:00 всеки ден')

anchor = '{ id:"pool_spartak",'
if cand.count(anchor) != 1:
    rep.append('SKIP котва pool_spartak x%d' % cand.count(anchor))
else:
    block = ''
    for zid, name, lat, lng, rad, waze, note in NEW:
        if zid in cand:
            rep.append('SKIP %-18s вече съществува' % zid)
            continue
        block += ('{ id:"%s", name:"%s", icon:"🏊", lat:%s, lng:%s, radius:%d, '
                  'type:"leisure", wazeName:"%s" },\n  ' % (zid, name, lat, lng, rad, waze))
        rep.append('OK   %-18s + %.4f, %.4f  (%s)' % (zid, lat, lng, note))
    if block:
        cand = cand.replace(anchor, block + anchor, 1)

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v14', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    ids = re.findall(r'\{\s*id:"([^"]+)"\s*,\s*name:', cand)
    pools = [i for i in ids if i.startswith('pool_')]
    rep.append('басейни общо: %d · зони: %d' % (len(pools), len(ids)))
    rep.append('OK v14 + node --check + cache-bust v14')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

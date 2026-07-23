# -*- coding: utf-8 -*-
"""v13: + басейн The Beach (бул.Рожен 25Е, Военна рампа) — посочен от Емил,
сверен: 4.0★ / 444 отзива, работи 09:00–22:00 (нед. до 23:45).
Отваря късно -> ценна нощна зона, каквато другите басейни не дават."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

if 'pool_thebeach' in cand:
    rep.append('SKIP pool_thebeach вече съществува')
else:
    anchor = '{ id:"pool_spartak",'
    if cand.count(anchor) == 1:
        newzone = ('{ id:"pool_thebeach", name:"Басейн The Beach (бул.Рожен 25Е) ☀лято", '
                   'icon:"🏊", lat:42.7361, lng:23.3144, radius:200, type:"leisure", '
                   'wazeName:"Pool The Beach бул Рожен 25Е София" },\n  ')
        cand = cand.replace(anchor, newzone + anchor, 1)
        rep.append('OK   pool_thebeach + 42.7361, 23.3144  (Военна рампа, отваря до 22:00)')
    else:
        rep.append('SKIP котва pool_spartak x%d' % cand.count(anchor))

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v13', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    ids = re.findall(r'\{\s*id:"([^"]+)"\s*,\s*name:', cand)
    rep.append('зони: %d' % len(ids))
    rep.append('OK v13 + node --check + cache-bust v13')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

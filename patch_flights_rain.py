# -*- coding: utf-8 -*-
"""v43: (1) Евлоги и Христо Георгиев — точката отива в средата на реалната
           отсечка (Попа -> Орлов мост), по линка на Емил
       (2) втора точка на Ал. Малинов (южна част, към Бизнес парка)
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# (1) Евлоги: средата на отсечката Попа -> Орлов мост
old = "{id:'jam_evlogi',  lat:42.6914, lng:23.3472, name:'Евлоги Георгиев'}"
new = "{id:'jam_evlogi',  lat:42.6867, lng:23.3293, name:'Евлоги Георгиев'}"
if old in cand:
    cand = cand.replace(old, new, 1)
    rep.append('OK   Евлоги Георгиев -> 42.6867,23.3293 (беше на 1.6 км, при Военна академия)')
else:
    rep.append('SKIP старата точка на Евлоги не е намерена')

# (2) втора точка на Малинов
old2 = "{id:'jam_malinov', lat:42.6469, lng:23.3761, name:'Ал. Малинов'}"
new2 = ("{id:'jam_malinov', lat:42.6469, lng:23.3761, name:'Ал. Малинов (метро)'},\n"
        "    {id:'jam_malinov_s', lat:42.6369, lng:23.3773, name:'Ал. Малинов (юг)'}")
if old2 in cand:
    cand = cand.replace(old2, new2, 1)
    rep.append('OK   + Ал. Малинов юг 42.6369,23.3773 (към Бизнес парка)')
else:
    rep.append('SKIP точката на Малинов не е намерена')

# синхронизиране на списъка за чистене на стари маркери
oldp = "[42.6914, 23.3472], [42.6469, 23.3761]"
if oldp in cand:
    cand = cand.replace(oldp, "[42.6867, 23.3293], [42.6469, 23.3761], [42.6369, 23.3773]", 1)
    rep.append('OK   списъкът за чистене синхронизиран')

# сметка за квотата
segs = len(re.findall(r"\{id:'jam_[a-z_]+',\s*lat:", cand))
day = segs * 15 * 17
night = segs * 2 * 7
rep.append('')
rep.append('отсечки: %d · разход: %d (ден) + %d (нощ) = %d от 2500' % (segs, day, night, day + night))
if day + night > 2200:
    rep.append('⚠ НАД предпазителя от 2200 — трябва по-дълъг кеш')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v43', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v43' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v43 + node --check + cache-bust v43')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

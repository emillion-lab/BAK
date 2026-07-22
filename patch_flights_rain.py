# -*- coding: utf-8 -*-
"""v9: ДУБЛИКАТИ — премахва втората дефиниция на всеки дублиран id
(тя създава осиротял кръг, който никога не се преоцветява),
запазва първата (нея ползват find/popup/КЪРК) и ѝ поправя координатите.
Стойностите са сверени с Google Places."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()

# id -> (верен lat, верен lng, отклонение)
DUP_FIX = {
    "opera":        (42.6975, 23.3305, "беше на 700 м"),
    "nat_theatre":  (42.6944, 23.3261, "беше на 305 м"),
    "sv_ekaterina": (42.6851, 23.3125, "беше на 197 м"),
}

cand = src
for zid, (lat, lng, note) in DUP_FIX.items():
    pat = re.compile(r'\{\s*id:"%s"\s*,[^{}]*\}\s*,' % re.escape(zid))
    matches = list(pat.finditer(cand))
    rep.append('%-14s намерени %d дефиниции' % (zid, len(matches)))
    if len(matches) < 1:
        continue

    # 1) махаме всички освен първата (обратно, за да не местим индексите)
    for m in reversed(matches[1:]):
        start = m.start()
        # изяждаме и водещото празно място/нов ред
        while start > 0 and cand[start - 1] in ' \t':
            start -= 1
        if start > 0 and cand[start - 1] == '\n':
            start -= 1
        cand = cand[:start] + cand[m.end():]
        rep.append('   премахнат дубликат (осиротял кръг)')

    # 2) поправяме координатите на оцелялата
    pat1 = re.compile(r'(\{\s*id:"%s"\s*,[^{}]*?lat:)([\d.]+)(\s*,\s*lng:)([\d.]+)'
                      % re.escape(zid))
    if len(pat1.findall(cand)) == 1:
        cand = pat1.sub(lambda m: '%s%s%s%s' % (m.group(1), lat, m.group(3), lng), cand, count=1)
        rep.append('   -> %.4f, %.4f  (%s)' % (lat, lng, note))
    else:
        rep.append('   ⚠️ координатите не бяха поправени (нееднозначен мач)')

# контрола: остават ли дубликати
ids = re.findall(r'\{\s*id:"([^"]+)"\s*,\s*name:', cand)
left = sorted({i for i in ids if ids.count(i) > 1})
rep.append('след чистката: %d зони, дубликати: %s' % (len(ids), left or 'няма'))

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260722v9', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    rep.append('OK v9 + node --check + cache-bust v9')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('debug/dedup-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

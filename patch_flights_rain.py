# -*- coding: utf-8 -*-
"""v10: втора вълна одит — 6 поправки, всички сверени с Google Places.
Проверени и потвърдени за верни (не се пипат): arena, capital_fort,
garitage, millennium."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()

FIXES = [
    ("iec",            42.6491, 23.3952, "IEC / Интер Експо Център (Цариградско 147)", "беше на 2.5 км"),
    ("ag_yug",         42.6689, 23.3526, None, "беше на 1.5 км"),
    ("ag_pod",         42.7034, 23.3601, None, "беше на 1.3 км"),
    ("hotel_marinela", 42.6724, 23.3190, "Хотел Маринела (Джеймс Баучер 100)", "беше на 1.1 км + грешна улица"),
    ("pirogov",        42.6901, 23.3072, None, "беше на 930 м"),
    ("bpark",          42.6269, 23.3784, None, "беше на 500 м"),
]
VERIFIED_OK = ["arena", "capital_fort", "garitage", "millennium"]

cand = src
for zid, lat, lng, newname, note in FIXES:
    pat = re.compile(r'(\{\s*id:"%s"\s*,\s*name:")([^"]*)("[^}]*?lat:)([\d.]+)(\s*,\s*lng:)([\d.]+)'
                     % re.escape(zid))
    hits = pat.findall(cand)
    if len(hits) != 1:
        rep.append('SKIP %-15s (намерени %d)' % (zid, len(hits)))
        continue

    def sub(m):
        name = newname if newname else m.group(2)
        return '%s%s%s%s%s%s' % (m.group(1), name, m.group(3), lat, m.group(5), lng)

    cand = pat.sub(sub, cand, count=1)
    rep.append('OK   %-15s -> %.4f, %.4f  (%s)' % (zid, lat, lng, note))

rep.append('проверени и ВЕРНИ (непипнати): %s' % ', '.join(VERIFIED_OK))

ids = re.findall(r'\{\s*id:"([^"]+)"\s*,\s*name:', cand)
dups = sorted({i for i in ids if ids.count(i) > 1})
rep.append('зони: %d · дубликати: %s' % (len(ids), ', '.join(dups) if dups else 'няма'))
rep.append('одитирани досега: 19 от %d зони' % len(ids))

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260722v10', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    rep.append('OK v10 + node --check + cache-bust v10')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('debug/coords-audit-2.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

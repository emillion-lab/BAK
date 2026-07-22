# -*- coding: utf-8 -*-
"""v8: ОДИТ НА КООРДИНАТИТЕ — поправка на 6 зони с грешки >1 км,
2 грешни имена, разделяне на двете места на Софарма, и доклад за дубликати.
Всички стойности са сверени с Google Places, не по памет."""
import re, json, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()

# (id, нов lat, нов lng, ново име или None, коментар)
FIXES = [
    ("sopharma_bc",  42.6661, 23.3571, "Sopharma Business Towers (Лъчезар Станчев 5)",
     "беше на 6.9 км, при Рожен"),
    ("kardiologia",  42.7062, 23.2874, None, "беше на 3.8 км"),
    ("sv_sofia_h",   42.6599, 23.2849, None, "беше на 2.4 км"),
    ("theatre_199",  42.6932, 23.3279, "Театър 199 Валентин Стойчев", "беше на 2.1 км"),
    ("lozenets_h",   42.6644, 23.3113, None, "беше на 2.0 км"),
    ("vma",          42.6842, 23.3045, "ВМА (Георги Софийски 3)", "беше на 1.2 км"),
    ("isul",         42.7008, 23.3391, "ИСУЛ – Царица Йоанна (Бяло море 8)", "грешен адрес в името"),
    ("satira",       42.6917, 23.3263, "Сатиричен театър Алеко Константинов", "грешно име + 350 м"),
    ("youth_theatre",42.6978, 23.3269, None, "фина корекция 130 м"),
]

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

# --- добавяне на втората Софарма (бул. Рожен 16) като отделна зона ---
if 'sopharma_rozhen' not in cand:
    anchor = '{ id:"telus",'
    if cand.count(anchor) == 1:
        newzone = ('{ id:"sopharma_rozhen", name:"Sopharma Trading (бул.Рожен 16)", '
                   'icon:"🏢", lat:42.7289, lng:23.3133, radius:180, type:"office", '
                   'wazeName:"Sopharma Trading бул Рожен 16 София" },\n  ')
        cand = cand.replace(anchor, newzone + anchor, 1)
        rep.append('OK   sopharma_rozhen добавена като отделна зона')
    else:
        rep.append('SKIP sopharma_rozhen (котвата telus x%d)' % cand.count(anchor))

# --- доклад за дублирани id-та ---
ids = re.findall(r'\{\s*id:"([^"]+)"\s*,\s*name:', cand)
dups = sorted({i for i in ids if ids.count(i) > 1})
if dups:
    rep.append('⚠️ ДУБЛИРАНИ id: %s (втората дефиниция засенчва първата)' % ', '.join(dups))
rep.append('общо зони: %d' % len(ids))

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260722v8', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    rep.append('OK v8 + node --check + cache-bust v8')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('debug/coords-audit.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

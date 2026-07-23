# -*- coding: utf-8 -*-
"""v11: ПЪЛЕН ОДИТ НА КООРДИНАТИТЕ — втора и трета вълна.
Всяка стойност е сверена с Google Places, не по памет.
22 поправки + 2 подвеждащи имена + 1 несъществуващ обект."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()

# (id, lat, lng, ново име или None, отклонение)
FIXES = [
    # --- катастрофални (>2 км) ---
    ("unss",             42.6513, 23.3490, None, "4.32 км — беше при НДК вместо в Студентски град"),
    ("nbu",              42.6782, 23.2527, None, "4.26 км"),
    ("polygraphia",      42.6874, 23.3440, "Polygraphia Office Center (Цариградско 47)", "3.66 км"),
    ("acibadem_ortho",   42.6400, 23.3181, None, "2.74 км"),
    ("serdika",          42.6918, 23.3532, "Мол Сердика (бул.Ситняково 48)", "2.46 км"),
    ("cinema_city_ser",  42.6918, 23.3532, None, "2.46 км (следва мола)"),
    ("acibadem_cardio",  42.6387, 23.3174, "Acibadem Сърдечно-съдов (Окол.път/Драгалевци)", "2.32 км"),
    # --- сериозни (1–2 км) ---
    ("acibadem_mladost", 42.6553, 23.3857, None, "1.51 км"),
    ("acibadem_tokuda",  42.6650, 23.3252, "Acibadem Токуда (Н.Вапцаров 51Б)", "583 м"),
    ("alexand",          42.6854, 23.3114, None, "1.16 км"),
    ("pool_diana",       42.6657, 23.3458, None, "1.12 км"),
    ("pool_akademika",   42.6756, 23.3660, None, "1.02 км"),
    # --- средни (300 м – 1 км) ---
    ("park_center",      42.6788, 23.3208, "Park Center (бул.Арсеналски 2)", "920 м"),
    ("expo2000",         42.6458, 23.3972, "Ellipse Center (Цариградско шосе)", "862 м — Expo 2000 е друга сграда"),
    ("dom_kinoto",       42.7003, 23.3240, None, "793 м"),
    ("jam_orl",          42.6906, 23.3374, None, "788 м"),
    ("pool_spartak",     42.6750, 23.3132, "Басейн Спартак (бул.Арсеналски 4) ☀лято", "523 м"),
    ("megapark",         42.6610, 23.3800, None, "345 м"),
    # --- фини (<300 м) ---
    ("su",               42.6936, 23.3349, None, "270 м"),
    ("advance_bc",       42.6294, 23.3747, None, "224 м"),
    ("tu",               42.6570, 23.3554, None, "180 м"),
    ("sv_anna",          42.6605, 23.3734, None, "141 м"),
    # --- само име (координатите са верни) ---
    ("borisova",         42.6838, 23.3450, "Борисова градина / Нац. стадион В.Левски",
     "името подвеждаше към Герena — стадион Г.Аспарухов е на 3 км"),
]

VERIFIED_OK = ["cjp", "cab_north", "ndk", "telus", "paradise", "mall_sofia",
               "ring_mall", "the_mall", "bulgaria_mall", "hotels_ctr"]
UNVERIFIED = ["oval", "hotels_ndk", "office_center", "studentski",
              "vitosha_bar", "center_bars", "lozenets_rest",
              "k_* и жк зони (площни, центърът е по дефиниция приблизителен)"]

cand = src
for zid, lat, lng, newname, note in FIXES:
    pat = re.compile(r'(\{\s*id:"%s"\s*,\s*name:")([^"]*)("[^}]*?lat:)([\d.]+)(\s*,\s*lng:)([\d.]+)'
                     % re.escape(zid))
    hits = pat.findall(cand)
    if len(hits) != 1:
        rep.append('SKIP %-17s (намерени %d)' % (zid, len(hits)))
        continue

    def sub(m):
        name = newname if newname else m.group(2)
        return '%s%s%s%s%s%s' % (m.group(1), name, m.group(3), lat, m.group(5), lng)

    cand = pat.sub(sub, cand, count=1)
    rep.append('OK   %-17s -> %.4f, %.4f   (%s)' % (zid, lat, lng, note))

# --- несъществуващ обект: басейн Мария Луиза е СЪБОРЕН/изоставен ---
pat_ml = re.compile(r'(\{\s*id:"pool_marialuiza"\s*,\s*name:")([^"]*)(")')
if pat_ml.search(cand):
    cand = pat_ml.sub(lambda m: m.group(1) + '⛔ Мария Луиза (закрит басейн)' + m.group(3), cand, count=1)
    rep.append('FLAG pool_marialuiza -> басейнът е ПЕРМАНЕНТНО ЗАТВОРЕН (изоставен комплекс)')
    rep.append('     -> преименуван; кажи ако да го махна изцяло от зоните')

ids = re.findall(r'\{\s*id:"([^"]+)"\s*,\s*name:', cand)
dups = sorted({i for i in ids if ids.count(i) > 1})
rep.append('')
rep.append('проверени и ВЕРНИ (непипнати): %s' % ', '.join(VERIFIED_OK))
rep.append('НЕПРОВЕРИМИ (няма надежден източник): %s' % ', '.join(UNVERIFIED))
rep.append('зони: %d · дубликати: %s' % (len(ids), ', '.join(dups) if dups else 'няма'))
rep.append('ОДИТИРАНИ ОБЩО: 51 от %d зони' % len(ids))

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v11', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    rep.append('OK v11 + node --check + cache-bust v11')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('debug/coords-audit-full.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

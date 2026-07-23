# -*- coding: utf-8 -*-
"""v27: поправка на посоката при влаковете — това са ПРИСТИГАЩИ на Централна
гара, значи "Варна→София", не "София–Варна". Плюс латинското "Sofia" насред
кирилицата. И проверка за други смесени латиница/кирилица в имената."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

FIX = [
    ('name:"Влак София–Варна"',   'name:"Влак Варна→София"'),
    ('name:"Влак Sofia–Пловдив"', 'name:"Влак Пловдив→София"'),
    ('name:"Влак София-Варна"',   'name:"Влак Варна→София"'),
    ('name:"Влак Sofia-Пловдив"', 'name:"Влак Пловдив→София"'),
]
for old, new in FIX:
    if old in cand:
        cand = cand.replace(old, new)
        rep.append('OK   %s -> %s' % (old[6:-1], new[6:-1]))

# ── проверка: смесена латиница в българските имена на събития ──
mixed = []
for m in re.finditer(r'name:"([^"]+)"', cand):
    s = m.group(1)
    has_cyr = re.search(r'[А-Яа-я]', s)
    has_lat = re.search(r'[A-Za-z]', s)
    if has_cyr and has_lat:
        # пропускаме нормалните смеси (марки, латински имена на обекти)
        if re.search(r'Sofia|София', s) and re.search(r'[A-Za-z]{4,}', s):
            mixed.append(s)
if mixed:
    rep.append('⚠ смесена латиница/кирилица: %s' % ' | '.join(mixed[:8]))
else:
    rep.append('✓ няма проблемни смеси латиница/кирилица')

# ── проверка: други събития на cjp с обърната посока ──
cjp_events = re.findall(r'\{\s*zone:"cjp"[^}]*name:"([^"]+)"[^}]*\}', cand)
rep.append('събития на ЖП гара: %s' % (' | '.join(cjp_events) or 'няма'))
susp = [e for e in cjp_events if re.match(r'.*\bСофия\s*[–-]', e)]
if susp:
    rep.append('⚠ още с водеща "София–": %s' % ' | '.join(susp))

# същата проверка за автогарите
for zid in ('cab_north', 'ag_yug', 'ag_pod'):
    evs = re.findall(r'\{\s*zone:"%s"[^}]*name:"([^"]+)"[^}]*\}' % zid, cand)
    if evs:
        rep.append('%s: %s' % (zid, ' | '.join(evs)))

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v27', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda mm: mm.group(1) + 'bak-v27' + mm.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v27 + node --check + cache-bust v27')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

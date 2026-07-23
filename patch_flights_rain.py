# -*- coding: utf-8 -*-
"""v17 ПОПРАВКА: BAK беше долу заради МОЯ грешка в v12 —
махнах зоната pool_marialuiza, но не и събитията, които сочат към нея.
activeEvents[ev.zone] ставаше undefined -> .push гърмеше -> целият
computeScores падаше -> нямаше зони, графика и време.

1) прави ред 414 защитен (никога повече да не пада от липсваща зона)
2) намира и премахва ВСИЧКИ събития-сираци (зона, която не съществува)
3) защитава typeBonus[z.type] (липсват cinema/nightlife/traffic -> NaN)
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── 1) защита на .push ────────────────────────────────────────
old = "activeEvents[ev.zone].push({name:ev.name, f});"
new = "(activeEvents[ev.zone] = activeEvents[ev.zone] || []).push({name:ev.name, f});"
if cand.count(old) == 1:
    cand = cand.replace(old, new)
    rep.append('OK   ред 414 защитен — липсваща зона вече не събаря приложението')
else:
    rep.append('SKIP .push (намерени %d)' % cand.count(old))

# ── 2) събития-сираци ─────────────────────────────────────────
def array_body(text, name):
    m = re.search(r'const\s+%s\s*=\s*\[' % name, text)
    if not m:
        return None, None, None
    start = text.index('[', m.start())
    d, i = 0, start
    while i < len(text):
        if text[i] == '[':
            d += 1
        elif text[i] == ']':
            d -= 1
            if d == 0:
                break
        i += 1
    return start, i + 1, text[start:i + 1]

zs, ze, zbody = array_body(cand, 'ZONES')
zone_ids = set(re.findall(r'\{\s*id:"([^"]+)"', zbody or ''))
rep.append('зони: %d' % len(zone_ids))

es, ee, ebody = array_body(cand, 'EVENTS')
if ebody is None:
    rep.append('SKIP EVENTS не е намерен')
else:
    refs = re.findall(r'zone:\s*"([^"]+)"', ebody)
    orphans = sorted({r for r in refs if r not in zone_ids})
    rep.append('събития: %d · сираци: %s' % (len(refs), ', '.join(orphans) if orphans else 'няма'))
    if orphans:
        newe = ebody
        removed = 0
        for orph in orphans:
            pat = re.compile(r'\s*\{[^{}]*zone:\s*"%s"[^{}]*\}\s*,?' % re.escape(orph))
            found = len(pat.findall(newe))
            newe = pat.sub('\n  ', newe)
            removed += found
            rep.append('  премахнати %d събития за "%s"' % (found, orph))
        cand = cand[:es] + newe + cand[ee:]
        rep.append('OK   общо премахнати събития-сираци: %d' % removed)

# ── 3) typeBonus защита ───────────────────────────────────────
n = len(re.findall(r'(?<![|\w])typeBonus\[z\.type\](?!\s*\|\|)', cand))
if n:
    cand = re.sub(r'(?<![|\w])typeBonus\[z\.type\](?!\s*\|\|)', '(typeBonus[z.type]||0)', cand)
    rep.append('OK   typeBonus защитен на %d места (cinema/nightlife/traffic даваха NaN)' % n)

# ── проверка ──────────────────────────────────────────────────
open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v17', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda m: m.group(1) + 'bak-v17' + m.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
            rep.append('OK   sw.js кеш -> bak-v17')
    except FileNotFoundError:
        pass
    rep.append('OK v17 + node --check + cache-bust v17')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

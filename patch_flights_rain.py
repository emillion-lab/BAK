# -*- coding: utf-8 -*-
"""v9: чистка на дублираните зони.
Правило: премахва по-късния дубликат САМО ако е идентичен с първия.
Ако се различават — НЕ пипа нищо и докладва разликите за ръчно решение.
Причина: ZONES.find() ползва ПЪРВАТА дефиниция, но circleMap[id] се презаписва
от ВТОРАТА -> първият кръг остава сирак (рисуван, но никога обновяван)."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()

m = re.search(r'const\s+ZONES\s*=\s*\[', src)
if not m:
    rep.append('FAIL ZONES не е намерен')
    cand = None
else:
    start = src.index('[', m.start())
    depth, j = 0, start
    while j < len(src):
        if src[j] == '[':
            depth += 1
        elif src[j] == ']':
            depth -= 1
            if depth == 0:
                break
        j += 1
    end = j + 1
    body = src[start:end]

    obj = re.compile(r'\{\s*id:"([^"]+)"[^{}]*\}')
    matches = list(obj.finditer(body))
    rep.append('намерени %d зонови обекта' % len(matches))

    def norm(s):
        return re.sub(r'\s+', ' ', s).strip()

    first = {}
    to_remove = []
    for mm in matches:
        zid = mm.group(1)
        if zid not in first:
            first[zid] = mm
            continue
        a, b = norm(first[zid].group(0)), norm(mm.group(0))
        if a == b:
            to_remove.append(mm)
            rep.append('ДУБЛИКАТ %-15s идентичен -> махам по-късния' % zid)
        else:
            rep.append('ДУБЛИКАТ %-15s РАЗЛИЧЕН -> НЕ пипам, решаваш ти:' % zid)
            rep.append('   първи : %s' % a[:190])
            rep.append('   втори : %s' % b[:190])

    if to_remove:
        newbody = body
        for mm in sorted(to_remove, key=lambda x: -x.start()):
            s, e = mm.start(), mm.end()
            # изяж следващата запетая и празното пространство
            k = e
            while k < len(newbody) and newbody[k] in ' \t\r\n':
                k += 1
            if k < len(newbody) and newbody[k] == ',':
                k += 1
            # и водещото празно пространство преди обекта
            p = s
            while p > 0 and newbody[p - 1] in ' \t':
                p -= 1
            if p > 0 and newbody[p - 1] == '\n':
                p -= 1
            newbody = newbody[:p] + newbody[k:]
        cand = src[:start] + newbody + src[end:]
        left = len(obj.findall(newbody))
        rep.append('зони след чистката: %d (махнати %d)' % (left, len(to_remove)))
    else:
        cand = src
        rep.append('няма какво да се маха')

if cand:
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
open('debug/dupes-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

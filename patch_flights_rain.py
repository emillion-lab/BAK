# -*- coding: utf-8 -*-
"""v48 СПЕШНА ПОПРАВКА: v46/v47 счупиха приложението.

Причина: превърнах декларации във функционални изрази —
    function X(...)  ->  window.X = function X(...)
Това маха hoisting-а (функцията не съществува преди своя ред) и създава
риск от слепване със следващия блок при липсваща точка и запетая.

Решение: връщаме декларациите и изнасяме с отделен ред ПРЕДИ тях.
Работи, защото декларациите се вдигат в началото на обхвата:
    window.X = X;
    function X(...) { ... }
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

pat = re.compile(r'window\.(\w+)\s*=\s*function\s+\1\s*\(')
found = pat.findall(cand)
rep.append('намерени счупени изнасяния: %s' % (', '.join(found) or 'няма'))

if found:
    def fix(m):
        n = m.group(1)
        return 'window.%s = %s;\nfunction %s(' % (n, n, n)
    cand = pat.sub(fix, cand)
    rep.append('OK   върнати декларации + отделен ред за изнасяне (%d бр.)' % len(found))

# същото за променливите, ако сме ги пипали
pat2 = re.compile(r'window\.(\w+)\s*=\s*(?=function\s*\()')
# (оставяме анонимните функционални изрази както са — при тях няма декларация)

# проверка: няма ли останали изрази без точка и запетая след затваряща скоба
risky = len(re.findall(r'\}\s*\n\s*\(function', cand))
rep.append('блокове "}\\n(function" (риск от слепване): %d' % risky)

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v48', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v48' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v48 + node --check + cache-bust v48')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

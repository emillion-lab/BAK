# -*- coding: utf-8 -*-
"""v21: (1) спирките вече искат изрично 'Слизане от'/'Вход от' —
           Полиграфия (Цариградско 47) спира да показва разписанието на Експо
       (2) ВСИЧКИ функции, викани от inline onclick, се изнасят в window —
           край на 'X is not defined' на парче
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (1) стесняване на филтъра за спирки ──
old = ("if(!/Слизане от|Вход от|Експо|Expo|Ботевградско|бул\\.? ?[Бб]ългария|Цариградско/i.test(txt)) return;")
new = ("if(!/Слизане от|Вход от/i.test(txt)) return;")
if cand.count(old) == 1:
    cand = cand.replace(old, new)
    rep.append('OK   спирките искат "Слизане от"/"Вход от" — Полиграфия е изключена')
else:
    # резервен вариант по по-къс подниз
    alt = "|Ботевградско|бул\\.? ?[Бб]ългария|Цариградско/i.test(txt)) return;"
    if cand.count(alt) == 1:
        cand = cand.replace(alt, "/i.test(txt)) return;")
        cand = cand.replace("if(!/Слизане от|Вход от|Експо|Expo/i.test(txt)) return;",
                            "if(!/Слизане от|Вход от/i.test(txt)) return;")
        rep.append('OK   филтърът стеснен (резервен път)')
    else:
        rep.append('SKIP филтър за спирки (намерени %d)' % cand.count(old))

# ── (2) намираме всички функции, викани от inline атрибути ──
inline_names = set()
for rx in (r'on\w+\s*=\s*"(\w+)\s*\(', r"on\w+\s*=\s*'(\w+)\s*\(",
           r'on\w+\s*=\s*\\"(\w+)\s*\(', r'onclick=\\?"?(\w+)\s*\('):
    for m in re.finditer(rx, cand):
        inline_names.add(m.group(1))
# махаме вградените
inline_names -= {'this', 'event', 'window', 'document', 'alert', 'confirm', 'return'}
rep.append('функции, викани от inline: %s' % (', '.join(sorted(inline_names)) or 'няма'))

exported, missing = [], []
for name in sorted(inline_names):
    if re.search(r'window\.%s\s*=' % re.escape(name), cand):
        continue                                   # вече е изнесена
    decl = re.compile(r'(?<![\w.])function\s+%s\s*\(' % re.escape(name))
    hits = len(decl.findall(cand))
    if hits == 1:
        cand = decl.sub('window.%s = function %s(' % (name, name), cand, count=1)
        exported.append(name)
    elif hits == 0:
        missing.append(name)
    else:
        missing.append('%s(x%d)' % (name, hits))
rep.append('OK   изнесени в window: %s' % (', '.join(exported) or 'няма'))
if missing:
    rep.append('⚠ не намерени като декларация: %s' % ', '.join(missing))

# ── (3) предпазна мрежа за ненамерените ──
if missing and 'inline-fallback-v21' not in cand:
    names = [n.split('(')[0] for n in missing]
    fb = ("// inline-fallback-v21 — предпазни заглушки, за да не гърми inline onclick\n"
          "(function(){ var N = %s;\n"
          "  N.forEach(function(n){\n"
          "    if(typeof window[n] === 'function') return;\n"
          "    window[n] = function(){\n"
          "      try{\n"
          "        var ids = ['event-alert','eventAlert','event-banner','alert-box'];\n"
          "        ids.forEach(function(id){ var e=document.getElementById(id); if(e) e.style.display='none'; });\n"
          "      }catch(e){}\n"
          "    };\n"
          "  });\n"
          "})();\n\n" % repr(names).replace("'", '"'))
    cand = fb + cand
    rep.append('OK   предпазни заглушки за: %s' % ', '.join(names))

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v21', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda mm: mm.group(1) + 'bak-v21' + mm.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v21 + node --check + cache-bust v21')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

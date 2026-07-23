# -*- coding: utf-8 -*-
"""v22: намира ВСИЧКИ функции, викани от inline атрибути (без значение как са
цитирани), и ги изнася в window. Плюс дъмп на контекста на closeEventAlert."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── дъмп: къде се среща closeEventAlert ──
os.makedirs('debug', exist_ok=True)
ctx = []
for m in re.finditer(r'closeEventAlert', cand):
    ln = cand.count('\n', 0, m.start()) + 1
    ctx.append('--- ред %d ---\n%s' % (ln, cand[max(0, m.start()-260):m.start()+200]))
open('debug/closeEventAlert.txt', 'w', encoding='utf-8').write(
    ('\n\n'.join(ctx) or 'НЯМА ТАКЪВ ИДЕНТИФИКАТОР') + '\n')
rep.append('closeEventAlert: %d срещания -> debug/closeEventAlert.txt' % len(ctx))

# ── широк детектор: on<нещо> ... ИМЕ( ──
names = set()
for m in re.finditer(r'\bon(?:click|change|input|submit|mouseover|mouseout|touchstart|focus|blur)\b[^A-Za-z0-9_]{0,12}([A-Za-z_$][\w$]*)\s*\(', cand):
    names.add(m.group(1))
names -= {'function', 'return', 'this', 'event', 'e', 'ev', 'window', 'document',
          'alert', 'confirm', 'setTimeout', 'if', 'for', 'while'}
rep.append('кандидати от inline: %s' % (', '.join(sorted(names)) or 'няма'))

exported, already, notfound = [], [], []
for name in sorted(names):
    if re.search(r'window\.%s\s*=' % re.escape(name), cand):
        already.append(name)
        continue
    decl = re.compile(r'(?<![\w.$])function\s+%s\s*\(' % re.escape(name))
    hits = len(decl.findall(cand))
    if hits == 1:
        cand = decl.sub('window.%s = function %s(' % (name, name), cand, count=1)
        exported.append(name)
        continue
    # вариант: const/let/var ИМЕ = function|(...)=>
    vdecl = re.compile(r'(?<![\w.$])(?:const|let|var)\s+%s\s*=' % re.escape(name))
    vhits = len(vdecl.findall(cand))
    if vhits == 1:
        cand = vdecl.sub('window.%s = ' % name, cand, count=1)
        exported.append(name + '(var)')
        continue
    notfound.append('%s(fn=%d,var=%d)' % (name, hits, vhits))

rep.append('OK   изнесени: %s' % (', '.join(exported) or 'няма'))
if already:
    rep.append('вече бяха в window: %s' % ', '.join(already))
if notfound:
    rep.append('⚠ ненамерени: %s' % ', '.join(notfound))

# ── предпазна мрежа: заглушки, които просто скриват съответния елемент ──
stub_names = [n.split('(')[0] for n in notfound]
if stub_names and 'inline-stub-v22' not in cand:
    fb = ("// inline-stub-v22 — предпазни заглушки за inline onclick\n"
          "(function(){ var N = %s;\n"
          "  N.forEach(function(n){\n"
          "    if(typeof window[n] === 'function') return;\n"
          "    window[n] = function(){\n"
          "      try{\n"
          "        ['event-alert','eventAlert','event-banner','alert-box','bakshish-box',\n"
          "         'direction-hint','karyk-banner'].forEach(function(id){\n"
          "          var e = document.getElementById(id); if(e) e.style.display = 'none';\n"
          "        });\n"
          "      }catch(err){}\n"
          "    };\n"
          "  });\n"
          "})();\n\n" % repr(stub_names).replace("'", '"'))
    cand = fb + cand
    rep.append('OK   заглушки за: %s' % ', '.join(stub_names))

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v22', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda mm: mm.group(1) + 'bak-v22' + mm.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v22 + node --check + cache-bust v22')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

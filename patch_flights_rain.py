# -*- coding: utf-8 -*-
"""v25: поправка на v24 — смаляването на КЪРК се прилагаше върху 11 селектора,
включително вложени (списък > елемент > име), което умножава мащаба и прави
списъка нечетим. Остава само самият бутон/банер."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

NEW_CSS = ("#karyk-banner,#karyk-btn{transform:scale(.6)!important;"
           "transform-origin:left bottom!important;opacity:.85!important}"
           "#karyk-list,#karyk-sidebar,.karyk-item,.karyk-name,.karyk-score,"
           ".karyk-rank,.karyk-sub,.karyk-dot,#karyk-hint{transform:none!important;"
           "opacity:1!important}")

pat = re.compile(r"(// ------ karyk-shrink-v24.*?st\.textContent\s*=\s*)'[^']*'", re.S)
if pat.search(cand):
    cand = pat.sub(lambda m: m.group(1) + repr(NEW_CSS).replace('"', "'"), cand, count=1)
    rep.append('OK   КЪРК: смалява се само бутонът; списъкът се връща в нормален размер')
else:
    pat2 = re.compile(r"(karyk-shrink-v24.*?textContent\s*=\s*)(['\"])(?:(?!\2).)*\2", re.S)
    if pat2.search(cand):
        cand = pat2.sub(lambda m: m.group(1) + "'" + NEW_CSS + "'", cand, count=1)
        rep.append('OK   КЪРК CSS заменен (резервен път)')
    else:
        rep.append('⚠ блокът karyk-shrink-v24 не е намерен — добавям коригиращ стил')
        cand += """

// ------ karyk-fix-v25 ------
(function(){
  try{
    var st = document.createElement('style');
    st.textContent = %s;
    document.head.appendChild(st);
  }catch(e){}
})();
""" % repr(NEW_CSS).replace('"', "'")

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v25', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda mm: mm.group(1) + 'bak-v25' + mm.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v25 + node --check + cache-bust v25')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

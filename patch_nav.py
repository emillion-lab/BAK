# -*- coding: utf-8 -*-
"""BAK: (1) летищна тежест от излизащи полети, (2) по-силна насочваща стрелка към всяка добра зона.
Append + точков patch, node --check gate, self-report."""
import re, subprocess, shutil

rep=[]
src=open('app.js',encoding='utf-8').read()

# ── 1) Летищна тежест: брой излизащи полети → boost на зона 'airport' в computeScores ──
# Вкарваме глобална променлива и я ползваме след weather boost.
if 'window.__airportExiting' not in src:
    # 1a) добавяме буфер + инжекция в computeScores преди 'return {scores'
    inject = (
        "  // Летищна вълна: излизащи полети вдигат скора на летището (силно — 10 полета≈3.6)\n"
        "  try{ var _ax = window.__airportExiting|0; if(_ax>0 && scores['airport']!==undefined){ scores['airport'] += Math.min(4.0, _ax*0.36); } }catch(e){}\n"
        "  return {scores, activeEvents};")
    old_ret = "  return {scores, activeEvents};"
    assert src.count(old_ret)==1, 'computeScores return x%d'%src.count(old_ret)
    src = src.replace(old_ret, inject)
    rep.append('OK airport weight injected')
else:
    rep.append('SKIP airport weight')

# ── 2) По-силна насочваща стрелка: sub-текст "карай на ПОСОКА Xм към ИМЕ (скор)" ──
old_addr = "  document.getElementById('dh-addr').textContent=`${DIRS[Math.round(bear/45)%8]} · ${distTxt}`;"
if old_addr in src:
    new_addr = "  document.getElementById('dh-addr').textContent=`\\u{1F697} \u041a\u0430\u0440\u0430\u0439 ${DIRS[Math.round(bear/45)%8]} \u00b7 ${distTxt} \u00b7 \u0441\u043a\u043e\u0440 ${bs.toFixed(1)}`;"
    src = src.replace(old_addr, new_addr)
    rep.append('OK arrow subtext')
else:
    rep.append('WARN arrow addr line not found (пропускам)')

# 2b) прагът за стрелка вече е 1.6 — сваляме на 1.3 да сочи по-често към "всяка добра зона"
old_thr = "    const s=scores[z.id]||0; if(s<1.6) return;"
if old_thr in src:
    src = src.replace(old_thr, "    const s=scores[z.id]||0; if(s<1.3) return;")
    rep.append('OK arrow threshold 1.6->1.3')
else:
    rep.append('WARN arrow threshold not found')

# ── 3) Захранване на __airportExiting: закачаме към showAirportSchedule ──
# Търсим где се смята nowCnt (добавен по-рано) и записваме глобално.
hook = "  const nowCnt = shownList.filter(f=>f._state==='now').length;"
if hook in src and 'window.__airportExiting = ' not in src:
    src = src.replace(hook, hook + "\n  try{ window.__airportExiting = visible.filter(f=>f._state==='now').length; }catch(e){}")
    rep.append('OK airport exiting hook')
else:
    rep.append('SKIP/така airport hook')

# Валидация
open('/tmp/a.js','w',encoding='utf-8').write(src)
r=subprocess.run(['node','--check','/tmp/a.js'],capture_output=True,text=True)
if r.returncode==0:
    shutil.move('/tmp/a.js','app.js')
    idx=open('index.html',encoding='utf-8').read()
    idx=re.sub(r'app\.js\?v=[0-9a-z]+','app.js?v=20260721nav',idx)
    open('index.html','w',encoding='utf-8').write(idx)
    rep.append('OK node --check + cache-bust nav')
else:
    rep.append('FAIL node --check :: '+(r.stderr or '')[:400])

open('nav-report.txt','w',encoding='utf-8').write('\n'.join(rep)+'\n')
print('\n'.join(rep))

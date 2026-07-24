# -*- coding: utf-8 -*-
"""v44: 16 отсечки общо + адаптивно опресняване по часове.
Всички нови точки са сверени с Google Places по адрес на конкретна сграда
върху съответния булевард, не по предположение."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── новите отсечки ──
NEW = [
    # (id, lat, lng, име, ориентир по който е сверена)
    ("jam_evlogi_b",  42.6870, 23.3287, "Хр. Георгиев (обратно)", "срещуположното платно"),
    ("jam_malinov_n", 42.6542, 23.3719, "Ал. Малинов (север)",    "метро Младост 1"),
    ("jam_luiza",     42.7000, 23.3218, "бул. Мария Луиза",       "Централни хали"),
    ("jam_tsankov",   42.6703, 23.3510, "бул. Драган Цанков",     "Интерпред WTC"),
    ("jam_botev",     42.6980, 23.3157, "бул. Христо Ботев",      "Хр. Ботев 52"),
    ("jam_bg_north",  42.6813, 23.3197, "бул. България (север)",  "хотел Хилтън"),
    ("jam_levski",    42.6861, 23.3322, "бул. Васил Левски",      "метро Стадион"),
    ("jam_tsar_air",  42.6500, 23.3945, "Цариградско (към летище)", "Интер Експо"),
    ("jam_cherni",    42.6580, 23.3155, "бул. Черни връх",        "Paradise Center"),
]

anchor = "{id:'jam_malinov_s', lat:42.6369, lng:23.3773, name:'Ал. Малинов (юг)'}"
if anchor in cand:
    block = anchor
    for zid, lat, lng, name, ref in NEW:
        if "'" + zid + "'" in cand:
            rep.append('SKIP %-16s вече съществува' % zid)
            continue
        block += ",\n    {id:'%s', lat:%s, lng:%s, name:'%s'}" % (zid, lat, lng, name)
        rep.append('OK   %-16s %.4f,%.4f  (%s)' % (zid, lat, lng, ref))
    cand = cand.replace(anchor, block, 1)
else:
    rep.append('SKIP котвата jam_malinov_s не е намерена')

# ── адаптивно опресняване и в приложението ──
old_sched = """  function isNight(){ var h = new Date().getHours(); return (h >= 23 || h < 6); }
  pull();
  (function schedule(){
    var wait = isNight() ? 1800000 : 180000;    // 30 мин нощем, 3 мин денем
    setTimeout(function(){ pull(); schedule(); }, wait);
  })();"""
new_sched = """  // опресняването следва графика на worker-а
  function waitMs(){
    var h = new Date().getHours();
    if(h >= 23 || h < 6) return 3600000;                 // нощ: 60 мин
    if(h >= 21) return 1800000;                          // късна вечер: 30 мин
    if((h >= 8 && h < 10) || (h >= 17 && h < 19)) return 300000;   // пик: 5 мин
    return 600000;                                       // ден: 10 мин
  }
  pull();
  (function schedule(){
    setTimeout(function(){ pull(); schedule(); }, waitMs());
  })();"""
if old_sched in cand:
    cand = cand.replace(old_sched, new_sched, 1)
    rep.append('OK   приложението следва същия график (пик 5м / ден 10м / вечер 30м / нощ 60м)')
else:
    rep.append('⚠ старият график не е намерен — приложението остава на предишния ритъм')

# ── бележката за нощния режим става обща ──
cand = cand.replace('🌙 нощен режим — данните се обновяват на 30 мин',
                    '🌙 нощен режим — данните се обновяват на час')

# ── сметка ──
segs = len(re.findall(r"\{id:'jam_[a-z_]+',\s*lat:", cand))
# 6ч нощ x1 + 2ч x6 + 2ч пик x12 + 7ч x6 + 2ч пик x12 + 2ч x6 + 2ч x2 + 1ч x1
per = 6*1 + 2*6 + 2*12 + 7*6 + 2*12 + 2*6 + 2*2 + 1*1
total = segs * per
rep.append('')
rep.append('отсечки: %d · %d заявки на отсечка/ден · общо %d от 2500' % (segs, per, total))
if total > 2400:
    rep.append('⚠ НАД предпазителя от 2400')
else:
    rep.append('запас: %d заявки' % (2400 - total))

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v44', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v44' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v44 + node --check + cache-bust v44')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

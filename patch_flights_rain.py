# -*- coding: utf-8 -*-
"""v42: нощен режим и в приложението — 23:00–06:00 се пита на 30 минути
вместо на 3. Спестява квота и батерия; при нужда се опреснява при отваряне."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

old = "  pull(); setInterval(pull, 180000);              // на 3 мин (кешът в worker-а е също 3)"
new = """  // нощем (23:00–06:00) питаме рядко — пътищата са свободни, пестим квота
  function isNight(){ var h = new Date().getHours(); return (h >= 23 || h < 6); }
  pull();
  (function schedule(){
    var wait = isNight() ? 1800000 : 180000;    // 30 мин нощем, 3 мин денем
    setTimeout(function(){ pull(); schedule(); }, wait);
  })();"""

if old in cand:
    cand = cand.replace(old, new, 1)
    rep.append('OK   нощен режим: 30 мин между заявките от 23:00 до 06:00')
else:
    pat = re.compile(r"  pull\(\); setInterval\(pull, 180000\);[^\n]*")
    if pat.search(cand):
        cand = pat.sub(new, cand, count=1)
        rep.append('OK   нощен режим (резервен път)')
    else:
        rep.append('SKIP таймерът за трафика не е намерен')

# бележка в popup-а, че нощем данните са по-редки
if 'night-note-v42' not in cand:
    cand += """

// ------ night-note-v42: честна бележка за нощния режим ------
(function(){
  function isNight(){ var h = new Date().getHours(); return (h >= 23 || h < 6); }
  function mark(){
    try{
      if(!isNight()) return;
      document.querySelectorAll('.tr34, .leaflet-popup-content').forEach(function(el){
        var t = el.textContent || '';
        if(!/км\\/ч|СВОБОДНО|ЗАДРЪСТЕНО|ЗАБАВЯНЕ|БАВНО/.test(t)) return;
        if(el.dataset && el.dataset.night42) return;
        if(el.dataset) el.dataset.night42 = '1';
        el.insertAdjacentHTML('beforeend',
          '<div style="font-size:10.5px;opacity:.5;margin-top:3px">'
          + '🌙 нощен режим — данните се обновяват на 30 мин</div>');
      });
    }catch(e){}
  }
  setInterval(mark, 5000);
})();
"""
    rep.append('OK   бележка в popup-а през нощта')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v42', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v42' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v42 + node --check + cache-bust v42')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

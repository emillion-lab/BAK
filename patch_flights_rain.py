# -*- coding: utf-8 -*-
"""v32: (1) ЗНАМЕНАТА обратно — emoji флагчетата се заменят с картинки
           (устройството ти ги рисува като букви EU/BG)
       (2) тикерът — четим текст вместо сиво на черно
       (3) Истанбул/Одрин/Анкара излизат от ВЪТРЕШНИТЕ линии
       (4) международната зона вече разпознава чуждите линии по име,
           не само по флага в разписанието (затова беше зелена)
       (5) дъмп на demandColor и скоровете на моловете за следващата партида
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (3) Истанбул и другите турски вън от вътрешния коридор ──
n = cand.count('|ИСТАНБУЛ|ОДРИН|ЧОРЛУ|АНКАРА|БУРСА')
if n:
    cand = cand.replace('|ИСТАНБУЛ|ОДРИН|ЧОРЛУ|АНКАРА|БУРСА', '')
    rep.append('OK   Истанбул/Одрин/Чорлу/Анкара/Бурса махнати от вътрешните (%d места)' % n)
else:
    rep.append('SKIP турските градове не са намерени във вътрешния коридор')

# ── (4) международните се разпознават и по име ──
INTL_RX = ("/СКОПИЕ|НИШ|БЕЛГРАД|СОЛУН|АТИНА|БУКУРЕЩ|ИСТАНБУЛ|ОДРИН|ЧОРЛУ|АНКАРА|БУРСА|"
           "КИЕВ|КИШИНЕВ|ВИЕНА|МЮНХЕН|БЕРЛИН|ПРАГА|БУДАПЕЩА|ЗАГРЕБ|ЛЮБЛЯНА|ТИРАНА|"
           "ПОДГОРИЦА|САРАЕВО|ОХРИД|БИТОЛЯ|СТРУМИЦА|КАВАЛА|ДРАМА/i")
k = cand.count('if(!rt.intl) return;')
if k:
    cand = cand.replace('if(!rt.intl) return;',
                        'if(!rt.intl && !%s.test(rt.name||"")) return;' % INTL_RX)
    rep.append('OK   международните се разпознават и по име (%d места)' % k)
else:
    rep.append('SKIP проверката rt.intl не е намерена')

# ── (1)+(2) знамена като картинки + четим тикер ──
if 'flags-ticker-v32' in cand:
    rep.append('SKIP v32 вече е приложен')
else:
    cand += """

// ------ flags-ticker-v32: истински знамена + четим тикер ------
(function(){
  // --- 1) emoji флагчета -> картинки (устройството ги рисува като букви) ---
  var RI_LOW = 0x1F1E6, RI_HIGH = 0x1F1FF;
  function pairToCode(s){
    try{
      var a = s.codePointAt(0), b = s.codePointAt(2);
      if(a < RI_LOW || a > RI_HIGH || b < RI_LOW || b > RI_HIGH) return null;
      return String.fromCharCode(97 + (a - RI_LOW)) + String.fromCharCode(97 + (b - RI_LOW));
    }catch(e){ return null; }
  }
  var FLAG_RX = /[\\uD83C][\\uDDE6-\\uDDFF][\\uD83C][\\uDDE6-\\uDDFF]/g;

  function imgFor(code){
    return '<img src="https://flagcdn.com/20x15/' + code + '.png" '
         + 'width="20" height="15" alt="' + code.toUpperCase() + '" '
         + 'style="vertical-align:-2px;border-radius:2px;box-shadow:0 0 0 1px rgba(0,0,0,.25)" '
         + 'onerror="this.replaceWith(document.createTextNode(this.alt))">';
  }

  function swapFlags(root){
    try{
      var sel = '.leaflet-popup-content, .zone-detail, [data-eta18], [data-intl29], '
              + '[data-cas26], .exit-panel, .bus-panel';
      var nodes = (root || document).querySelectorAll(sel);
      Array.prototype.forEach.call(nodes, function(el){
        if(el.dataset && el.dataset.flagged === '1') return;
        var h = el.innerHTML;
        if(!h || !FLAG_RX.test(h)) return;
        FLAG_RX.lastIndex = 0;
        el.innerHTML = h.replace(FLAG_RX, function(m){
          var c = pairToCode(m);
          return c ? imgFor(c) : m;
        });
        if(el.dataset) el.dataset.flagged = '1';
      });
    }catch(e){}
  }

  // --- 2) тикерът: четим текст ---
  function styleTicker(){
    try{
      if(document.getElementById('ticker-style-v32')) return;
      var st = document.createElement('style');
      st.id = 'ticker-style-v32';
      st.textContent =
        '[data-ticker-raw]{color:#e2ecf8!important;font-weight:600!important;'
        + 'text-shadow:0 1px 2px rgba(0,0,0,.55)!important;opacity:1!important;'
        + 'letter-spacing:.2px!important;}'
        + '[data-ticker-raw] *{color:inherit!important;opacity:1!important;}';
      document.head.appendChild(st);
    }catch(e){}
  }

  function tick(){ styleTicker(); swapFlags(); }
  tick();
  setInterval(tick, 2500);
  try{ new MutationObserver(function(){ tick(); })
        .observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();
"""
    rep.append('OK   знамената стават картинки (с връщане към букви при липса на мрежа)')
    rep.append('OK   тикерът: светъл текст със сянка')

# ── (5) дъмп за следващата партида ──
os.makedirs('debug', exist_ok=True)
dump = []
for kw in ['function demandColor', 'demandColor', 'mall', 'studentski', 'typeBonus']:
    i = cand.find(kw)
    if i < 0:
        dump.append('--- %s: НЯМА ---' % kw)
        continue
    ln = cand.count('\n', 0, i) + 1
    dump.append('--- %s (ред %d) ---\n%s' % (kw, ln, cand[max(0, i-400):i+1400]))
open('debug/colors-malls.txt', 'w', encoding='utf-8').write('\n\n'.join(dump)[:15000] + '\n')
rep.append('OK   дъмп demandColor/молове/студентски -> debug/colors-malls.txt')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v32', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v32' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v32 + node --check + cache-bust v32')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

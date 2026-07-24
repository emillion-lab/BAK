# -*- coding: utf-8 -*-
"""v41: (1) + 2 булеварда: Евлоги и Христо Георгиев, Александър Малинов
       (2) чипът "1 довечера" се маха (дублира "2 събития", което е по-описателно)
       (3) чиповете се разреждат, за да не лежат един върху друг
       (4) Advance BC / Business Park / Младост 4 — по-малки радиуси, спират да се застъпват
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (1) двата нови булеварда ──
old = "{id:'jam_serdika', lat:42.7049, lng:23.3239, name:'бул. Сливница'}"
new = ("{id:'jam_serdika', lat:42.7049, lng:23.3239, name:'бул. Сливница'},\n"
       "    {id:'jam_evlogi',  lat:42.6914, lng:23.3472, name:'Евлоги Георгиев'},\n"
       "    {id:'jam_malinov', lat:42.6469, lng:23.3761, name:'Ал. Малинов'}")
if old in cand:
    cand = cand.replace(old, new, 1)
    rep.append('OK   + Евлоги Георгиев (42.6914,23.3472) и Ал.Малинов (42.6469,23.3761)')
else:
    rep.append('SKIP списъкът с отсечки не е намерен')

# и в списъка за чистене на стари маркери
oldp = "[42.6906, 23.3374], [42.6752, 23.3587], [42.6655, 23.2895], [42.7049, 23.3239]"
if oldp in cand:
    cand = cand.replace(oldp, oldp + ',\n    [42.6914, 23.3472], [42.6469, 23.3761]', 1)
    rep.append('OK   новите точки влизат и в чистенето на стари маркери')

# ── (4) радиуси, за да не се застъпват ──
def radius(zid, val):
    global cand
    pat = re.compile(r'(\{\s*id:"%s"[^}]*?radius:)(\d+)' % re.escape(zid))
    m = pat.search(cand)
    if not m:
        rep.append('SKIP радиус %s' % zid)
        return
    old_r = m.group(2)
    cand = cand[:m.start(2)] + str(val) + cand[m.end(2):]
    rep.append('OK   радиус %-10s %s -> %d' % (zid, old_r, val))

radius('advance_bc', 190)
radius('bpark', 220)
radius('mladost4', 240)

# ── (2)+(3) чиповете ──
if 'chips-tidy-v41' in cand:
    rep.append('SKIP v41 вече е приложен')
else:
    cand += """

// ------ chips-tidy-v41: маха дублиращия чип и разрежда останалите ------
(function(){
  function tidy(){
    try{
      var chips = [];
      Array.prototype.forEach.call(document.querySelectorAll('div'), function(el){
        if(el.children.length > 2) return;
        var cs = window.getComputedStyle(el);
        if(cs.position !== 'fixed') return;
        var t = (el.textContent || '').trim();
        if(!t || t.length > 46) return;
        if(parseFloat(cs.left) > 220) return;              // само лявата колона
        chips.push({el:el, t:t, bottom:parseFloat(cs.bottom) || 0});
      });

      // 1) махаме "N довечера" — дублира по-описателното "N събития"
      var hasEvents = chips.some(function(c){ return /\\d+\\s*събити/i.test(c.t); });
      chips = chips.filter(function(c){
        if(hasEvents && /довечера/i.test(c.t)){
          try{ c.el.remove(); }catch(e){ c.el.style.display = 'none'; }
          return false;
        }
        return true;
      });

      // 2) разреждаме — 46px стъпка отдолу нагоре
      chips.sort(function(a, b){ return a.bottom - b.bottom; });
      var y = 26;
      chips.forEach(function(c){
        if(c.el.style.display === 'none') return;
        c.el.style.bottom = y + 'px';
        c.el.style.marginBottom = '0';
        y += 46;
      });
    }catch(e){}
  }
  tidy();
  setInterval(tidy, 3000);
  try{ new MutationObserver(tidy).observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();
"""
    rep.append('OK   "довечера" се маха при наличие на "събития"; чиповете на 46px стъпка')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v41', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v41' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v41 + node --check + cache-bust v41')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

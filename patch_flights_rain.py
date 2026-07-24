# -*- coding: utf-8 -*-
"""v39: летищният панел — излизащите СЕГА отиват най-отгоре (без скролване),
имената на градовете не се режат."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

if 'airport-panel-v39' in cand:
    rep.append('SKIP v39 вече е приложен')
else:
    cand += """

// ------ airport-panel-v39: червените най-отгоре + цели имена ------
(function(){
  var CSS = '/*airport-panel-v39*/'
    + '.leaflet-popup-content{font-size:12.5px!important;}'
    + '.leaflet-popup-content *{text-overflow:clip!important;overflow:visible!important;'
    + 'max-width:none!important;}'
    + '.v39-hot{order:-1;}'
    + '.v39-head{font:800 11px/1.3 system-ui,sans-serif;color:#fca5a5;'
    + 'padding:4px 2px 2px;letter-spacing:.3px;}';
  try{
    if(!document.getElementById('v39-style')){
      var st = document.createElement('style');
      st.id = 'v39-style';
      st.textContent = CSS;
      document.head.appendChild(st);
    }
  }catch(e){}

  var HOT = /ИЗЛИЗАТ\\s+\\d{1,2}:\\d{2}/;

  function isRow(el){
    var t = el.textContent || '';
    if(!HOT.test(t)) return false;
    if(t.length > 160) return false;          // това е контейнер, не ред
    // редът съдържа номер на полет
    return /[A-Z]{2}\\d{3,4}|W6\\d{3,4}|FR\\d{3,4}/.test(t);
  }

  function lift(panel){
    try{
      if(!panel || (panel.dataset && panel.dataset.v39 === '1')) return;
      var all = panel.querySelectorAll('div,li,tr,section');
      var rows = [];
      Array.prototype.forEach.call(all, function(el){
        if(isRow(el)){
          // взимаме най-външния ред, не вложените парчета
          var p = el.parentElement;
          var outer = el;
          while(p && p !== panel && isRow(p)){ outer = p; p = p.parentElement; }
          if(rows.indexOf(outer) < 0) rows.push(outer);
        }
      });
      if(!rows.length) return;

      // общият родител на редовете
      var parent = rows[0].parentElement;
      if(!parent) return;
      var same = rows.every(function(r){ return r.parentElement === parent; });
      if(!same){
        parent = rows[0].parentElement;
        rows = rows.filter(function(r){ return r.parentElement === parent; });
      }
      if(rows.length < 1) return;

      // заглавие + преместване най-отгоре, в същия ред помежду им
      if(!parent.querySelector('.v39-head')){
        var h = document.createElement('div');
        h.className = 'v39-head';
        h.textContent = '⬤ ИЗЛИЗАТ СЕГА — ' + rows.length + ' полета';
        parent.insertBefore(h, parent.firstChild);
      }
      var anchor = parent.querySelector('.v39-head');
      rows.slice().reverse().forEach(function(r){
        try{ parent.insertBefore(r, anchor.nextSibling); }catch(e){}
      });

      if(panel.dataset) panel.dataset.v39 = '1';
      // и панелът се връща най-горе
      try{ panel.scrollTop = 0; }catch(e){}
    }catch(e){}
  }

  function scan(){
    try{
      document.querySelectorAll('.leaflet-popup-content').forEach(function(el){
        var t = el.textContent || '';
        if(/Излизане на пасажери|Изходи Терминал/i.test(t)) lift(el);
      });
    }catch(e){}
  }
  scan();
  setInterval(scan, 2000);
  try{ new MutationObserver(scan).observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();
"""
    rep.append('OK   излизащите СЕГА отиват най-отгоре + заглавие с брой')
    rep.append('OK   имената на градовете не се режат (clip вместо ellipsis)')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v39', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v39' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v39 + node --check + cache-bust v39')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

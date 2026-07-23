# -*- coding: utf-8 -*-
"""v24 РЕМОНТ:
1) ЦВЕТОВЕ — сиво само при реално нула; цвят започва рано, за да си правиш
   маршрут по зоните с някакъв шанс, не само по пиковете
2) КЪРК бутонът — смален, за да не закрива картата
3) Борисова градина и стадион В.Левски стават ДВЕ зони (бяха на 1 км разстояние
   и стояха в един кръг по средата — грешно и за двете)
4) чистка на излишната заглушка getElementById от v23
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (4) чистка на фалшивата заглушка ──
cand = cand.replace('"getElementById",', '').replace(',"getElementById"', '').replace('"getElementById"', '')
rep.append('OK   махната излишната заглушка getElementById')

# ── (3) разделяне на Борисова и стадиона ──
m = re.search(r'\{\s*id:"borisova"[^}]*\}', cand)
if m:
    obj = m.group(0)
    ztype = (re.search(r'type:"([^"]+)"', obj) or [None, 'venue'])[1]
    # Борисова градина -> реалният център на парка
    newpark = re.sub(r'lat:[\d.]+\s*,\s*lng:[\d.]+', 'lat:42.6748, lng:23.3394', obj)
    newpark = re.sub(r'name:"[^"]*"', 'name:"Борисова градина (парк)"', newpark)
    newpark = re.sub(r'radius:\d+', 'radius:750', newpark)
    newpark = re.sub(r'wazeName:"[^"]*"', 'wazeName:"Борисова градина София"', newpark)
    stadium = ('{ id:"vl_stadium", name:"Нац. стадион Васил Левски", icon:"🏟️", '
               'lat:42.6882, lng:23.3346, radius:320, type:"%s", '
               'wazeName:"Национален стадион Васил Левски София" }' % ztype)
    cand = cand.replace(obj, newpark + ',\n  ' + stadium, 1)
    rep.append('OK   borisova -> 42.6748,23.3394 (парк) + НОВА зона vl_stadium 42.6882,23.3346')
    rep.append('     (бяха 1 км една от друга, зоната стоеше по средата)')
else:
    rep.append('SKIP borisova не е намерена')

# ── (1) цветовете: изнасяме demandColor и я обгръщаме ──
n = len(re.findall(r'(?<![\w.$])function\s+demandColor\s*\(', cand))
if n == 1:
    cand = re.sub(r'(?<![\w.$])function\s+demandColor\s*\(',
                  'window.demandColor = function demandColor(', cand, count=1)
    rep.append('OK   demandColor изнесена в window')
elif re.search(r'window\.demandColor\s*=', cand):
    rep.append('SKIP demandColor вече е изнесена')
else:
    rep.append('⚠ demandColor не е намерена (намерени %d)' % n)

if 'color-scale-v24' in cand:
    rep.append('SKIP цветовата скала вече е сменена')
else:
    cand += """

// ------ color-scale-v24: цвят още при малък шанс за клиент ------
(function(){
  if(typeof window.demandColor !== 'function') return;
  var orig = window.demandColor;

  // праг -> цвят. Сиво САМО при реално нула.
  var SCALE = [
    [0.35, '#8b95a5', 0.10],   // мъртво — бледо сиво, да не прави каша
    [0.80, '#4aa3c7', 0.20],   // минимален шанс — студено синьо
    [1.30, '#2fa88a', 0.28],   // има шанс — тюркоаз
    [1.90, '#4cba52', 0.34],   // приличен — зелено
    [2.50, '#a3c23a', 0.40],   // добър — жълто-зелено
    [3.10, '#e0a020', 0.46],   // силен — кехлибар
    [3.80, '#ef7a1a', 0.54],   // много силен — оранж
    [99,   '#e33b2e', 0.62]    // пик — червено
  ];

  function pick(s){
    for(var i = 0; i < SCALE.length; i++){
      if(s < SCALE[i][0]) return SCALE[i];
    }
    return SCALE[SCALE.length - 1];
  }

  window.demandColor = function(s, type){
    var out;
    try{ out = orig.apply(this, arguments); }catch(e){ out = {}; }
    try{
      var num = (typeof s === 'number') ? s : parseFloat(s) || 0;
      var p = pick(num), col = p[1], op = p[2];
      if(!out || typeof out !== 'object') out = {};
      // болниците си пазят собствения червен код
      if(type === 'hospital') return out;
      ['fill','color','stroke','border','fillColor','bg'].forEach(function(k){
        if(k in out) out[k] = col;
      });
      if(!('fill' in out)) out.fill = col;
      ['op','opacity','fillOpacity','alpha'].forEach(function(k){
        if(k in out && typeof out[k] === 'number') out[k] = op;
      });
    }catch(e){}
    return out;
  };
})();
"""
    rep.append('OK   нова цветова скала: 8 нива, цвят от 0.35 нагоре')

# ── (2) КЪРК бутонът: намираме имената и го смаляваме ──
karyk_ids = set(re.findall(r'id="(karyk[\w-]*)"', src, re.I))
karyk_ids |= set(re.findall(r"getElementById\('(karyk[\w-]*)'\)", src, re.I))
karyk_cls = set(re.findall(r'class="([^"]*karyk[\w-]*)"', src, re.I))
try:
    html = open('index.html', encoding='utf-8').read()
    karyk_ids |= set(re.findall(r'id="(karyk[\w-]*)"', html, re.I))
    karyk_cls |= set(re.findall(r'class="([^"]*\bkaryk[\w-]*)"', html, re.I))
except FileNotFoundError:
    html = ''
sel = ['#' + i for i in sorted(karyk_ids)]
for c in sorted(karyk_cls):
    for part in c.split():
        if 'karyk' in part.lower():
            sel.append('.' + part)
sel = sorted(set(sel))
rep.append('КЪРК селектори: %s' % (', '.join(sel) or 'няма'))

if sel and 'karyk-shrink-v24' not in cand:
    css = (', '.join(sel) +
           '{transform:scale(.62)!important;transform-origin:left bottom!important;'
           'opacity:.82!important;}')
    cand += """

// ------ karyk-shrink-v24: КЪРК бутонът да не закрива картата ------
(function(){
  try{
    var st = document.createElement('style');
    st.textContent = %s;
    document.head.appendChild(st);
  }catch(e){}
})();
""" % repr(css)
    rep.append('OK   КЪРК смален до 62%% (двойно по-малко площ)')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    ids = re.findall(r'\{\s*id:"([^"]+)"\s*,\s*name:', cand)
    rep.append('зони: %d' % len(ids))
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v24', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, k = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                         lambda mm: mm.group(1) + 'bak-v24' + mm.group(3), sw, count=1)
        if k:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v24 + node --check + cache-bust v24')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

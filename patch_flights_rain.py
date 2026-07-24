# -*- coding: utf-8 -*-
"""v46: (1) БЪГ: showZonePopup не е глобална -> гърми при избор на зона.
           Изнасяме нея и всяка друга функция, викана от inline onclick.
       (2) отсечката при метро Младост 1 се измества по Малинов към Цариградско
           (беше паднала на ул. Липчев)
       (3) КЪРК: собствен списък с местата + бутон на видимо място
"""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ── (1) изнасяне на всички inline функции ──
names = set()
for rx in (r'\bon(?:click|change|input|submit|mouseover|touchstart|focus|blur)\b[^A-Za-z0-9_]{0,14}([A-Za-z_$][\w$]*)\s*\(',
           r'onclick=\\?["\']?([A-Za-z_$][\w$]*)\s*\('):
    for m in re.finditer(rx, cand):
        names.add(m.group(1))
try:
    html = open('index.html', encoding='utf-8').read()
    for m in re.finditer(r'\bon\w+\s*=\s*["\']([^"\']{0,140})["\']', html):
        for c in re.finditer(r'([A-Za-z_$][\w$]*)\s*\(', m.group(1)):
            names.add(c.group(1))
except FileNotFoundError:
    pass
names -= {'function','return','this','event','e','ev','window','document','alert',
          'confirm','setTimeout','if','for','while','getElementById','querySelector'}

exported, already, missing = [], [], []
for n in sorted(names):
    if re.search(r'window\.%s\s*=' % re.escape(n), cand):
        already.append(n); continue
    decl = re.compile(r'(?<![\w.$])function\s+%s\s*\(' % re.escape(n))
    if len(decl.findall(cand)) == 1:
        cand = decl.sub('window.%s = function %s(' % (n, n), cand, count=1)
        exported.append(n); continue
    vdecl = re.compile(r'(?<![\w.$])(?:const|let|var)\s+%s\s*=' % re.escape(n))
    if len(vdecl.findall(cand)) == 1:
        cand = vdecl.sub('window.%s = ' % n, cand, count=1)
        exported.append(n + '(var)'); continue
    missing.append(n)

rep.append('OK   изнесени: %s' % (', '.join(exported) or 'няма'))
if already: rep.append('     вече бяха: %s' % ', '.join(already))
if missing: rep.append('     ⚠ ненамерени: %s' % ', '.join(missing))

# ── (2) Малинов към Цариградско ──
old = "{id:'jam_malinov_n', lat:42.6542, lng:23.3719, name:'Ал. Малинов (север)'}"
new = "{id:'jam_malinov_n', lat:42.6570, lng:23.3705, name:'Ал. Малинов (към Цариградско)'}"
if old in cand:
    cand = cand.replace(old, new, 1)
    rep.append('OK   Малинов север -> 42.6570,23.3705 (беше паднал на ул. Липчев)')

# ── (3) КЪРК списък ──
if 'karyk-list-v46' in cand:
    rep.append('SKIP v46 вече е приложен')
else:
    cand += """

// ------ karyk-list-v46: собствен списък за КЪРК режим ------
(function(){
  var open = false;

  var btn = document.createElement('div');
  btn.textContent = '🥉 КЪРК';
  btn.style.cssText = 'position:fixed;right:8px;top:calc(50% + 46px);z-index:1400;'
    + 'background:#2a1a05e8;color:#fbbf24;border:1px solid #b45309;border-radius:9px;'
    + 'padding:6px 9px;font:800 11px system-ui,sans-serif;cursor:pointer;'
    + 'box-shadow:0 2px 8px rgba(0,0,0,.55)';
  document.body.appendChild(btn);

  var panel = document.createElement('div');
  panel.style.cssText = 'position:fixed;left:8px;right:8px;bottom:70px;max-height:58vh;'
    + 'overflow-y:auto;z-index:2600;background:#0b1220f8;color:#e5e7eb;'
    + 'border:1px solid #b45309;border-radius:14px;padding:12px;'
    + 'font-family:system-ui,sans-serif;font-size:13px;display:none;'
    + 'box-shadow:0 6px 30px rgba(0,0,0,.75)';
  document.body.appendChild(panel);

  function dist(lat, lng){
    var la = window.userLat, ln = window.userLng;
    if(typeof la !== 'number' || typeof ln !== 'number') return null;
    var dx = (lat - la) * 111, dy = (lng - ln) * 82;
    return Math.sqrt(dx*dx + dy*dy);
  }

  function build(){
    var Z = window.__ZONES || [], S = window.__lastScores || {};
    var rows = [];
    Z.forEach(function(z){
      var s = S[z.id];
      if(typeof s !== 'number' || s <= 0) return;
      if(/^jam_/.test(z.id)) return;                    // задръстванията не са цел
      var d = dist(z.lat, z.lng);
      rows.push({z:z, s:s, d:d});
    });
    // подредба: скор, намален с наказание за разстояние
    rows.forEach(function(r){
      r.rank = r.s - (r.d !== null && r.d > 5 ? Math.min(1.3, (r.d - 5) * 0.11) : 0);
    });
    rows.sort(function(a, b){ return b.rank - a.rank; });
    return rows.slice(0, 14);
  }

  function colorFor(s){
    if(s >= 3.8) return '#ef4444';
    if(s >= 3.0) return '#f97316';
    if(s >= 2.4) return '#f59e0b';
    if(s >= 1.8) return '#a3c23a';
    if(s >= 1.2) return '#4cba52';
    if(s >= 0.7) return '#2fa88a';
    return '#3d8fb5';
  }

  function render(){
    var rows = build();
    var html = '<div style="display:flex;justify-content:space-between;align-items:center;'
      + 'margin-bottom:8px"><b style="font-size:14px;color:#fbbf24">🥉 КЪРК — къде да ида</b>'
      + '<span id="karyk46-x" style="cursor:pointer;padding:2px 10px;color:#94a3b8;'
      + 'font-size:16px">✕</span></div>';
    if(!rows.length){
      html += '<div style="opacity:.6">Няма данни за зоните в момента.</div>';
    } else {
      rows.forEach(function(r, i){
        var c = colorFor(r.s);
        var km = r.d !== null ? (r.d < 1 ? Math.round(r.d * 1000) + ' м' : r.d.toFixed(1) + ' км') : '';
        html += '<div class="k46row" data-lat="' + r.z.lat + '" data-lng="' + r.z.lng + '" '
          + 'style="display:flex;align-items:center;gap:8px;padding:6px 4px;cursor:pointer;'
          + 'border-bottom:1px solid rgba(148,163,184,.14)">'
          + '<span style="opacity:.5;width:18px;font-size:11px">#' + (i + 1) + '</span>'
          + '<span style="width:9px;height:9px;border-radius:50%;background:' + c + ';flex:0 0 auto"></span>'
          + '<span style="flex:1;min-width:0">' + (r.z.icon || '') + ' ' + r.z.name + '</span>'
          + (km ? '<span style="opacity:.6;font-size:11px;white-space:nowrap">' + km + '</span>' : '')
          + '<b style="color:' + c + ';white-space:nowrap">' + r.s.toFixed(1) + '</b></div>';
      });
      html += '<div style="opacity:.5;font-size:11px;margin-top:7px">'
        + 'Подредено по скор минус загубата от разстоянието. Цъкни ред за фокус на картата.</div>';
    }
    panel.innerHTML = html;
    var x = document.getElementById('karyk46-x');
    if(x) x.onclick = function(){ open = false; panel.style.display = 'none'; };
    Array.prototype.forEach.call(panel.querySelectorAll('.k46row'), function(el){
      el.onclick = function(){
        var la = parseFloat(el.dataset.lat), ln = parseFloat(el.dataset.lng);
        if(window.__focusZone) window.__focusZone(la, ln, 15);
        open = false; panel.style.display = 'none';
      };
    });
  }

  btn.onclick = function(){
    open = !open;
    panel.style.display = open ? 'block' : 'none';
    if(open) render();
  };
  setInterval(function(){ if(open) render(); }, 20000);
})();
"""
    rep.append('OK   КЪРК списък: 14 места, скор, разстояние, цъкане за фокус')
    rep.append('OK   бутонът е фиксиран вдясно под "чисто"')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idxh = open('index.html', encoding='utf-8').read()
    idxh = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260724v46', idxh)
    open('index.html', 'w', encoding='utf-8').write(idxh)
    try:
        sw = open('sw.js', encoding='utf-8').read()
        sw2, kk = re.subn(r"(CACHE[_A-Z]*\s*=\s*['\"])([^'\"]+)(['\"])",
                          lambda mm: mm.group(1) + 'bak-v46' + mm.group(3), sw, count=1)
        if kk:
            open('sw.js', 'w', encoding='utf-8').write(sw2)
    except FileNotFoundError:
        pass
    rep.append('OK v46 + node --check + cache-bust v46')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

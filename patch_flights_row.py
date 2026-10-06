#!/usr/bin/env python3
"""Полети, част 3: редът не се мачка.
- статусът (ИЗЛИЗА / ???) и флагът слизат ПОД часовете → градът получава място
- градът е по-едър, по-контрастен и може на два реда вместо да се реже
- отстъпът за страничните бутони 58px → 46px
Идемпотентен."""
import sys

L = []
def edit(s, name, old, new, marker):
    if marker in s: L.append(f'{name}: вече е приложено'); return s
    n = s.count(old)
    if n != 1: L.append(f'{name}: ГРЕШКА — {n} съвпадения'); return s
    L.append(f'{name}: OK'); return s.replace(old, new)

s = open('app.js', encoding='utf-8').read()

# дясната колона: часове горе, флаг + статус отдолу
s = edit(s, 'дясна колона на два реда',
  '<span style="display:flex;align-items:center;gap:5px;white-space:nowrap">\n          <span style="font-size:12px">${flag(f)}</span>',
  '<span class="fl-right" style="display:flex;flex-direction:column;align-items:flex-end;gap:1px;white-space:nowrap">\n'
  '          <span style="font-weight:800;font-size:11.5px;color:${col}">${fmt(f.exitFromH,f.exitFromM)}–${fmt(f.exitToH,f.exitToM)}</span>\n'
  '          <span style="display:flex;align-items:center;gap:4px">\n'
  '          <span style="font-size:11px">${flag(f)}</span>',
  'class="fl-right"')

# старият ред с часовете в края на колоната → затваря вътрешния ред
s = edit(s, 'часове преместени горе',
  '\n\n          <span style="font-weight:800;font-size:11.5px;color:${col}">${fmt(f.exitFromH,f.exitFromM)}–${fmt(f.exitToH,f.exitToM)}</span>\n        </span>',
  '\n          </span>\n        </span>',
  '\n          </span>\n        </span>\n      </div>`;')

# градът: едър, контрастен, пренася се
s = edit(s, 'град по-видим',
  '<span style="display:block;font-size:11px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;line-height:1.25">${(f.depAirport||\'\').slice(0,18)}',
  '<span class="fl-city" style="display:block;font-size:12.5px;font-weight:700;color:var(--text);white-space:normal;overflow-wrap:anywhere;line-height:1.15">${(f.depAirport||\'\').slice(0,24)}',
  'class="fl-city"')
open('app.js', 'w', encoding='utf-8').write(s)

h = open('index.html', encoding='utf-8').read()
h = edit(h, 'отстъп 46px',
  '#airport-modal-body{ padding-right:58px !important; }',
  '#airport-modal-body{ padding-right:46px !important; }',
  'padding-right:46px')
h = edit(h, 'версия', 'app.js?v=20261005v164', 'app.js?v=20261006v165', 'v=20261006v165')
open('index.html', 'w', encoding='utf-8').write(h)

open('flights-row-report.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))
if any('ГРЕШКА' in l for l in L): sys.exit(1)

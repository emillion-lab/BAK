#!/usr/bin/env python3
"""Полети, част 4: редовете стигат до десния ръб (отстъп 46px → 12px). Идемпотентен."""
import sys
h = open('index.html', encoding='utf-8').read(); L = []
for name, old, new, marker in [
  ('отстъп 12px', '#airport-modal-body{ padding-right:46px !important; }',
   '#airport-modal-body{ padding-right:12px !important; }', 'padding-right:12px !important; }\n/* последната'),
  ('версия', 'app.js?v=20261006v165', 'app.js?v=20261006v166', 'v=20261006v166'),
]:
    if marker in h: L.append(f'{name}: вече е приложено'); continue
    n = h.count(old)
    if n != 1: L.append(f'{name}: ГРЕШКА — {n} съвпадения'); continue
    h = h.replace(old, new); L.append(f'{name}: OK')
open('index.html', 'w', encoding='utf-8').write(h)
open('flights-edge-report.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))
if any('ГРЕШКА' in l for l in L): sys.exit(1)

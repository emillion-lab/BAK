#!/usr/bin/env python3
"""Маркерът „Струма“ стоеше в Бояна (бул. България), където рейсът не минава.
Местим го на Автогара Овча купел (Запад) — OSM/Nominatim: 42.67274, 23.27193.
Рейсът: АМ Струма → възел Люлин → Автогара Овча купел. Идемпотентен."""
import sys
L = []
s = open('app.js', encoding='utf-8').read()
OLD = "{lat:42.6520, lng:23.2800, short:'🚌 Струма', pop:'<b style=\"color:#0284c7\">🚌 Бул. България</b><br><small>Вход от Струма: Благоевград · ЮЗ България</small>'},"
NEW = "{lat:42.67274, lng:23.27193, short:'🚌 Овча купел', pop:'<b style=\"color:#0284c7\">🚌 Автогара Овча купел (Запад)</b><br><small>Рейсове от Струма: Благоевград · Перник · Дупница · ЮЗ България<br>Влизат по АМ Струма през възел Люлин</small>'},"
if 'lat:42.67274, lng:23.27193' in s: L.append('маркер: вече е приложено')
elif s.count(OLD) == 1: s = s.replace(OLD, NEW); L.append('маркер: OK')
else: L.append(f'маркер: ГРЕШКА — {s.count(OLD)} съвпадения')
open('app.js', 'w', encoding='utf-8').write(s)

h = open('index.html', encoding='utf-8').read()
if 'v=20261007v167' in h: L.append('версия: вече е приложено')
else:
    import re
    m = re.findall(r'app\.js\?v=\w+', h)
    if len(m) == 1: h = h.replace(m[0], 'app.js?v=20261007v167'); L.append(f'версия: OK ({m[0]})')
    else: L.append(f'версия: ГРЕШКА — {len(m)} съвпадения')
open('index.html', 'w', encoding='utf-8').write(h)

open('struma-fix-report.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))
if any('ГРЕШКА' in l for l in L): sys.exit(1)

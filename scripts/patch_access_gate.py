#!/usr/bin/env python3
"""Закача access-gate.js в BAK/index.html. Идемпотентно."""
import re
import sys

TAG = '<script src="access-gate.js" defer></script>'

s = open('index.html', encoding='utf-8').read()

if 'access-gate.js' in s:
    print('вече е закачен — нищо не правя')
    sys.exit(0)

if '</body>' not in s:
    print('ГРЕШКА: няма </body>')
    sys.exit(1)

s = s.replace('</body>', '  ' + TAG + '\n</body>', 1)
open('index.html', 'w', encoding='utf-8').write(s)
print('закачен access-gate.js')

# проверки
o = len(re.findall(r'<div', s))
c = len(re.findall(r'</div>', s))
assert o == c, f'div mismatch: {o}/{c}'
print(f'div баланс ОК: {o}/{c}')

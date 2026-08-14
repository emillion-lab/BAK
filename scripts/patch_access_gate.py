#!/usr/bin/env python3
"""Закача access-gate.js в BAK/index.html. Идемпотентно.

Бележка: не проверявам баланса на div-овете — в index.html има несдвоен
</div> отпреди това, а моята промяна не добавя нито един div.
"""
import sys

TAG = '<script src="access-gate.js?v=2" defer></script>'

s = open('index.html', encoding='utf-8').read()

if 'access-gate.js' in s:
    print('вече е закачен — нищо не правя')
    sys.exit(0)

if '</body>' not in s:
    print('ГРЕШКА: няма </body>')
    sys.exit(1)

s = s.replace('</body>', TAG + '\n</body>', 1)
open('index.html', 'w', encoding='utf-8').write(s)
print('закачен access-gate.js')

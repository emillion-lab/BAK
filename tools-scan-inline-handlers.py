import re, sys

src   = open('app.js', encoding='utf-8').read()
html  = open('index.html', encoding='utf-8').read()
lines = src.split('\n')

def depth_map(text):
    """дълбочина на скобите в началото на всеки ред (игнорира низове и коментари)"""
    out, depth, in_s, in_blk = [], 0, None, False
    for l in text.split('\n'):
        out.append(depth)
        j = 0
        while j < len(l):
            c = l[j]
            if in_blk:
                if c == '*' and j+1 < len(l) and l[j+1] == '/': in_blk = False; j += 2; continue
            elif in_s:
                if c == '\\': j += 2; continue
                if c == in_s: in_s = None
            elif c in '"\'`': in_s = c
            elif c == '/' and j+1 < len(l) and l[j+1] == '/': break
            elif c == '/' and j+1 < len(l) and l[j+1] == '*': in_blk = True; j += 2; continue
            elif c == '{': depth += 1
            elif c == '}': depth -= 1
            j += 1
        in_s = None
    return out

dm = depth_map(src)

# --- какво Е глобално ---
globals_ = set()
for i, l in enumerate(lines):
    if dm[i] != 0:
        continue
    m = re.match(r'\s*function\s+([A-Za-z_$][\w$]*)', l)
    if m: globals_.add(m.group(1))
    m = re.match(r'\s*(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:function|\()', l)
    if m: globals_.add(m.group(1))
for m in re.finditer(r'window\.([A-Za-z_$][\w$]*)\s*=', src):
    globals_.add(m.group(1))
# динамични заглушки:  var N = ["a","b"];  N.forEach(...{ window[n] = ... })
for m in re.finditer(r'var\s+(\w+)\s*=\s*\[([^\]]*)\]\s*;\s*\1\.forEach', src, re.S):
    body = src[m.end():m.end()+400]
    if re.search(r'window\[\s*\w+\s*\]\s*=', body):
        for s in re.findall(r'["\']([A-Za-z_$][\w$]*)["\']', m.group(2)):
            globals_.add(s)

KEYWORDS = {'if','for','while','switch','catch','function','return','typeof','new','do','else','try','var','let','const'}
BUILTIN = {'alert','confirm','prompt','open','close','print','event','this','window','document',
           'console','Math','JSON','Date','Number','String','Array','Object','parseInt','parseFloat',
           'setTimeout','setInterval','fetch','encodeURIComponent','decodeURIComponent','isNaN','navigator','location'}

# --- какво се ВИКА от inline handler-и ---
calls = {}   # име -> списък с примери
def collect(text, origin):
    for m in re.finditer(r'\bon[a-z]+\s*=\s*(["\'])(.*?)\1', text, re.S):
        code = m.group(2)
        for c in re.finditer(r'([.\w$]?)\b([A-Za-z_$][\w$]*)\s*\(', code):
            if c.group(1) == '.': continue          # метод, не глобална функция
            n = c.group(2)
            if n in BUILTIN or n in KEYWORDS: continue
            calls.setdefault(n, set()).add(origin)

collect(html, 'index.html')
# onclick вътре в JS низове (template literals и конкатенации)
collect(src, 'app.js (генериран HTML)')

missing = {n: o for n, o in calls.items() if n not in globals_}

print(f'глобални функции: {len(globals_)}   |   викани от inline handler-и: {len(calls)}')
print()
if missing:
    print('❌ ВИКАТ СЕ, НО НЕ СА ГЛОБАЛНИ:')
    for n in sorted(missing):
        ln = next((i+1 for i,l in enumerate(lines) if re.match(rf'\s*function\s+{re.escape(n)}\b', l)), None)
        where = f'дефинирана на ред {ln}, вложеност {dm[ln-1]}' if ln else 'НЕ Е ДЕФИНИРАНА НИКЪДЕ'
        print(f'   {n:26s} ← {", ".join(sorted(missing[n]))}  ({where})')
    sys.exit(1)
else:
    print('✅ всички викани от inline handler-и функции са достъпни глобално')

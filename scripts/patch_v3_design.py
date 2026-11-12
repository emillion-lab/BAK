#!/usr/bin/env python3
"""BAK · закача дизайна v3 и пазача за демо (12.11.2026). Идемпотентен.

index.html:
  - <script src="bak-guard.js"> веднага след <meta charset> (преди app.js)
  - <link rel="stylesheet" href="bak-v3.css"> последен в <head>
  - theme-color и status bar → тъмни
  - access-gate.js?v=2 → ?v=3 (новият текст и презареждане след вход)
  - неоновото синьо в CSS → жълто такси (само цветът, правилата остават)
sw.js: нова версия на кеша, за да се изтеглят новите файлове.
Маркер: BAK-V3-DESIGN
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
IDX, SW = ROOT / 'index.html', ROOT / 'sw.js'
MARK = 'BAK-V3-DESIGN'

h = IDX.read_text(encoding='utf-8')
if MARK in h:
    print('index.html: вече е закачено')
else:
    n0 = len(h)
    a = '<meta charset="UTF-8">\n'
    assert h.count(a) == 1, 'няма <meta charset>'
    h = h.replace(a, a + '<!-- ' + MARK + ' --><script src="bak-guard.js?v=1"></script>\n', 1)

    assert h.count('</head>') == 1, 'няма </head>'
    h = h.replace('</head>', '<link rel="stylesheet" href="bak-v3.css?v=1">\n</head>', 1)

    h = h.replace('<meta name="theme-color" content="#0284c7">', '<meta name="theme-color" content="#0e1012">', 1)
    h = h.replace('<meta name="apple-mobile-web-app-status-bar-style" content="default">',
                  '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">', 1)

    assert 'access-gate.js?v=2' in h, 'няма access-gate.js?v=2'
    h = h.replace('access-gate.js?v=2', 'access-gate.js?v=3', 1)

    # само в <style> блоковете: циан → жълто такси
    def recolor(m):
        css = m.group(0)
        css = css.replace('rgba(34,211,238,', 'rgba(230,195,106,')
        css = re.sub(r'#22d3ee\b', '#e6c36a', css, flags=re.I)
        css = re.sub(r'#67e8f9\b', '#efd79a', css, flags=re.I)
        css = css.replace('rgba(0,229,255,', 'rgba(230,195,106,')
        return css
    h, k = re.subn(r'<style>.*?</style>', recolor, h, flags=re.S)
    print('style блокове:', k)

    for need in ('bak-guard.js?v=1', 'bak-v3.css?v=1', 'access-gate.js?v=3', 'app.js?v='):
        assert need in h, 'липсва ' + need
    # пазачът трябва да е преди app.js
    assert h.index('bak-guard.js') < h.index('src="app.js'), 'пазачът е след app.js'
    IDX.write_text(h, encoding='utf-8')
    print('index.html: %d → %d байта' % (n0, len(h)))

s = SW.read_text(encoding='utf-8')
m = re.search(r"const CACHE_NAME = 'bakshishapp-bak-v(\d+)';", s)
if not m:
    sys.exit('sw.js: няма CACHE_NAME')
if "'/BAK/bak-v3.css'" in s:
    print('sw.js: вече е обновен')
else:
    v = int(m.group(1)) + 1
    s = s.replace(m.group(0), "const CACHE_NAME = 'bakshishapp-bak-v%d';" % v, 1)
    s = s.replace("  '/BAK/manifest.json',\n", "  '/BAK/manifest.json',\n  '/BAK/bak-v3.css',\n  '/BAK/bak-guard.js',\n", 1)
    assert "'/BAK/bak-v3.css'" in s, 'sw.js: STATIC_FILES не е намерен'
    SW.write_text(s, encoding='utf-8')
    print('sw.js: кеш v%d' % v)

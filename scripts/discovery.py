#!/usr/bin/env python3
"""DISCOVERY — Phase 1 по методологията от гиста.
Не пише нито един скрейпър. Само установява КОЙ метод работи за кой източник.
Проверява по приоритет: REST API > платформено API > JSON блоб > JSON-LD > HTML.
Резултат: debug/discovery-report.md
"""
import json, re, ssl, sys, os
from urllib.request import Request, urlopen
from urllib.parse import quote, urlsplit

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
      "Accept-Language": "bg-BG,bg;q=0.9,en;q=0.8"}
PROXY = "https://mvr-proxy.mihov-emil.workers.dev/scrape?url="
INSECURE = ssl._create_unverified_context()
ROWS = []

try:
    from curl_cffi import requests as ccf
    HAVE_CCF = True
except Exception as e:
    HAVE_CCF = False
    print("curl_cffi недостъпен:", e)


def note(src, method, endpoint, ok, clean_json, detail):
    ROWS.append({"src": src, "method": method, "endpoint": endpoint,
                 "ok": ok, "json": clean_json, "detail": detail[:150]})
    print(("  ✓" if ok else "  ✗"), src, "|", method, "|", detail[:90])


def plain_get(url, timeout=15, use_proxy=False):
    tgt = PROXY + quote(url, safe="") if use_proxy else url
    for ctx in (None, INSECURE):
        try:
            with urlopen(Request(tgt, headers=UA), timeout=timeout, context=ctx) as r:
                b = r.read()
            head = b[:2000].decode("ascii", "ignore").lower()
            if "1251" in head:
                return b.decode("cp1251", "ignore"), None
            try:
                return b.decode("utf-8"), None
            except UnicodeDecodeError:
                return b.decode("cp1251", "ignore"), None
        except Exception as e:
            err = repr(e)[:120]
    return None, err


def cffi_get(url, timeout=20, imp="chrome131"):
    if not HAVE_CCF:
        return None, "curl_cffi липсва"
    try:
        r = ccf.get(url, headers=UA, impersonate=imp, timeout=timeout)
        return r.text, ("HTTP %d" % r.status_code if r.status_code >= 400 else None)
    except Exception as e:
        return None, repr(e)[:120]


# ═══ 1) ПЛАТФОРМЕНИ API (WordPress / Drupal) ═══
print("\n=== 1. Платформени API ===")
WP_TARGETS = [
    ("Арена 8888", "https://arenaarmeecsofia.net"),
    ("visitsofia", "https://www.visitsofia.bg"),
    ("НДК", "https://www.ndk.bg"),
    ("theatre.art.bg", "https://theatre.art.bg"),
]
for name, base in WP_TARGETS:
    hit = False
    for path, label in (("/wp-json/wp/v2/posts?per_page=5", "WordPress REST"),
                        ("/jsonapi/node/article?page[limit]=5", "Drupal JSON:API")):
        body, err = plain_get(base + path)
        if body is None:
            body, err = plain_get(base + path, use_proxy=True)
        if body and body.lstrip()[:1] in "[{":
            try:
                data = json.loads(body)
                n = len(data) if isinstance(data, list) else len(data.get("data", []))
                if n:
                    note(name, label, base + path, True, True, "%d записа чист JSON" % n)
                    hit = True
                    break
            except Exception:
                pass
    if not hit:
        note(name, "WordPress/Drupal API", base + "/wp-json/", False, False, "няма платформено API")

# ═══ 2) JSON БЛОБОВЕ В HTML ═══
print("\n=== 2. JSON блобове в HTML ===")
BLOB_TARGETS = [
    ("bilet.bg", "https://bilet.bg/"),
    ("visitsofia", "https://www.visitsofia.bg/bg/kalendar"),
    ("Eventim HTML", "https://www.eventim.bg/city/%D1%81%D0%BE%D1%84%D0%B8%D1%8F-7510/"),
    ("Арена 8888", "https://arenaarmeecsofia.net/"),
]
PATTERNS = [
    (r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', "__NEXT_DATA__ (Next.js)"),
    (r'window\.__NUXT__\s*=\s*(.+?);?\s*</script>', "__NUXT__ (Nuxt)"),
    (r'window\.__INITIAL_STATE__\s*=\s*(.+?);\s*</script>', "__INITIAL_STATE__ (Vue SSR)"),
    (r'<script[^>]*data-sveltekit-fetched[^>]*>(.*?)</script>', "SvelteKit"),
    (r'window\.__remixContext\s*=\s*(.+?);\s*</script>', "Remix"),
]
for name, url in BLOB_TARGETS:
    body, err = plain_get(url, timeout=20)
    if body is None:
        body, err = plain_get(url, timeout=20, use_proxy=True)
    if body is None:
        note(name, "JSON блоб", url, False, False, "не се зарежда: %s" % err)
        continue
    found = False
    for rx, label in PATTERNS:
        m = re.search(rx, body, re.S)
        if m:
            try:
                json.loads(m.group(1))
                note(name, label, url, True, True, "валиден JSON, %d знака" % len(m.group(1)))
            except Exception:
                note(name, label, url, True, False, "намерен, но не парсва директно")
            found = True
            break
    # JSON-LD Event
    lds = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', body, re.S)
    ev = 0
    for b in lds:
        try:
            d = json.loads(b)
            items = d if isinstance(d, list) else d.get("@graph", [d])
            ev += sum(1 for i in items if isinstance(i, dict) and "Event" in str(i.get("@type", "")))
        except Exception:
            pass
    if ev:
        note(name, "JSON-LD Event", url, True, True, "%d събития в ld+json" % ev)
        found = True
    if not found:
        note(name, "JSON блоб/LD", url, False, False,
             "нищо структурирано (%d ld+json блока, %db)" % (len(lds), len(body)))

# ═══ 3) TLS ОТПЕЧАТЪК — curl_cffi срещу 403 ═══
print("\n=== 3. curl_cffi (TLS импърсонация) ===")
CCF_TARGETS = [
    ("Eventim API v1", "https://public-api.eventim.com/websearch/search/api/exploration/v1/products"
                       "?webId=web__eventim-bg&language=bg&retail_partner=EVE"
                       "&city_names=%D0%A1%D0%BE%D1%84%D0%B8%D1%8F&sort=DateAsc&page=1"),
    ("Eventim API v2", "https://public-api.eventim.com/websearch/search/api/exploration/v2/productGroups"
                       "?webId=web__eventim-bg&language=bg&retail_partner=EVE"
                       "&city_names=%D0%A1%D0%BE%D1%84%D0%B8%D1%8F&sort=DateAsc&page=1"),
    ("БДЖ live", "https://live.bdz.bg/"),
    ("Eventim HTML", "https://www.eventim.bg/city/%D1%81%D0%BE%D1%84%D0%B8%D1%8F-7510/"),
]
for name, url in CCF_TARGETS:
    # първо: обикновено urllib (за сравнение)
    p_body, p_err = plain_get(url, timeout=15)
    plain_ok = p_body is not None
    # после: curl_cffi
    c_body, c_err = cffi_get(url)
    if c_body and not c_err:
        is_json = c_body.lstrip()[:1] in "[{"
        extra = ""
        if is_json:
            try:
                d = json.loads(c_body)
                k = list(d.keys())[:6] if isinstance(d, dict) else ["list"]
                extra = " ключове: %s" % k
            except Exception:
                is_json = False
        note(name, "curl_cffi chrome131", url[:60], True, is_json,
             "%db%s | urllib: %s" % (len(c_body), extra, "OK" if plain_ok else "БЛОКИРАН"))
    else:
        note(name, "curl_cffi chrome131", url[:60], False, False,
             "%s | urllib: %s" % (c_err or "празен", "OK" if plain_ok else "блокиран"))

# ═══ ДОКЛАД ═══
os.makedirs("debug", exist_ok=True)
lines = ["# Discovery Report — източници за BAK/SEV", ""]
lines.append("curl_cffi наличен: **%s**" % ("да" if HAVE_CCF else "НЕ"))
lines.append("")
lines.append("| Източник | Метод | Работи | Чист JSON | Детайли |")
lines.append("|---|---|:--:|:--:|---|")
for r in ROWS:
    lines.append("| %s | %s | %s | %s | %s |" % (
        r["src"], r["method"], "✅" if r["ok"] else "❌",
        "✅" if r["json"] else "—", r["detail"].replace("|", "/")))
lines.append("")
wins = [r for r in ROWS if r["ok"] and r["json"]]
lines.append("## Печеливши комбинации (чист JSON): %d" % len(wins))
for r in wins:
    lines.append("- **%s** → %s — `%s`" % (r["src"], r["method"], r["endpoint"]))
if not wins:
    lines.append("- няма; остава HTML парсване")

open("debug/discovery-report.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines[-12:]))

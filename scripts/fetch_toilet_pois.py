#!/usr/bin/env python3
"""Бързи тоалетни за шофьора: всички Kaufland и Praktiker в София (от OSM),
плюс ръчно избрани места. Пише toilets.json за слоя 🚻 в BAK.

Моловете НЕ влизат нарочно — паркиране + влизане + излизане отнема твърде много.
Ръчните места са в EXTRA; добавяй там, когато провериш, че има свободна тоалетна.
"""
import json, sys, time, urllib.request, urllib.parse

BBOX = '42.55,23.15,42.82,23.55'          # София и околностите
QUERY = f"""[out:json][timeout:90];
(
  nwr["brand"~"^(Kaufland|Praktiker)$"]({BBOX});
  nwr["shop"]["name"~"Kaufland|Кауфланд|Praktiker|Практикер",i]({BBOX});
  nwr["shop"]["name"~"Decathlon|Декатлон",i]({BBOX});
  nwr["name"~"Business Park Sofia|Бизнес парк София",i](42.615,23.35,42.64,23.385);
  nwr["building"]["addr:housenumber"="10"](42.620,23.360,42.635,23.380);
);
out center tags;"""

MIRRORS = ['https://overpass-api.de/api/interpreter',
           'https://overpass.private.coffee/api/interpreter',
           'https://maps.mail.ru/osm/tools/overpass/api/interpreter']

def fetch():
    body = urllib.parse.urlencode({'data': QUERY}).encode()
    for url in MIRRORS:
        try:
            req = urllib.request.Request(url, data=body, headers={
                'User-Agent': 'emillion-lab-BAK/1.0 (taxi helper; github.com/emillion-lab/BAK)',
                'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:
            print(f'{url}: {e}')
            time.sleep(3)
    sys.exit('всички Overpass огледала отказаха')

raw = fetch()
open('toilets-osm-raw.json', 'w', encoding='utf-8').write(json.dumps(raw, ensure_ascii=False, indent=1))

def pos(e):
    if 'lat' in e: return e['lat'], e['lon']
    c = e.get('center') or {}
    return c.get('lat'), c.get('lon')

out, seen = [], []
for e in raw.get('elements', []):
    t = e.get('tags', {})
    name = t.get('name') or t.get('brand') or ''
    low = (name + ' ' + t.get('brand', '')).lower()
    if 'kaufland' in low or 'кауфланд' in low: kind = 'kaufland'
    elif 'praktiker' in low or 'практикер' in low: kind = 'praktiker'
    else: continue                                    # Decathlon/Business Park → само в суровия файл
    if not t.get('shop'): continue                    # паркинг, бензиностанция и т.н. с марката
    lat, lon = pos(e)
    if lat is None: continue
    # една и съща сграда може да е и node, и way → пазим по-близкото от двете само веднъж
    if any(abs(lat - a) < 0.0015 and abs(lon - b) < 0.002 and k == kind for a, b, k in seen):
        continue
    seen.append((lat, lon, kind))
    addr = ' '.join(x for x in [t.get('addr:street', ''), t.get('addr:housenumber', '')] if x)
    out.append({'kind': kind, 'name': name, 'addr': addr, 'lat': round(lat, 6), 'lng': round(lon, 6),
                'hours': t.get('opening_hours', ''), 'osm': f"{e['type']}/{e['id']}"})

out.sort(key=lambda x: (x['kind'], x['lng']))
json.dump({'built': time.strftime('%Y-%m-%d'), 'osm': out}, open('toilets-osm.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f"Kaufland: {sum(1 for x in out if x['kind']=='kaufland')} · Praktiker: {sum(1 for x in out if x['kind']=='praktiker')}")
for x in out: print(x['kind'], x['name'], '|', x['addr'], x['lat'], x['lng'])
print('други (Decathlon / Business Park):')
for e in raw.get('elements', []):
    t = e.get('tags', {}); n = t.get('name', '')
    if any(k in n.lower() for k in ('decathlon', 'декатлон', 'business park', 'бизнес парк')) or t.get('addr:housenumber') == '10':
        lat, lon = pos(e); print(' ', e['type'], e['id'], n, '|', t.get('addr:street', ''), t.get('addr:housenumber', ''), lat, lon)

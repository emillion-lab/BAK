#!/usr/bin/env python3
"""Седмично разписание на пристиганията в SOF от историята на flight-cache.json.

Защо: от 12.10.2026 AeroDataBox връща за SOF само радарни полети (без
разписание, без терминали). Повечето полети се повтарят всяка седмица в
същия ден и час, а git историята на flight-cache.json пази пълното
разписание от преди това. Оттук панелът взима бъдещите полети и терминалите.

Само записи С ТЕРМИНАЛ влизат — радарните записи идват без терминал,
така че отпадат сами и не замърсяват разписанието.

Изход: sof-weekly.json
  { built, weeks, from, to,
    days: { "0".."6" (0 = неделя, местно време):
            [ {fn, from, t:"HH:MM", term, airline, seen, last} ] } }
"""
import json, subprocess, sys, datetime as dt
from collections import defaultdict

WEEKS = 8                      # колко седмици назад гледаме (с резерв, ако разписанието липсва дълго)
TODAY = dt.date.today()
SINCE = TODAY - dt.timedelta(days=WEEKS * 7)

log = subprocess.check_output(
    ['git', 'log', f'--since={SINCE.isoformat()}', '--format=%H', '--', 'flight-cache.json'],
    text=True).split()

# (дата, номер) -> запис; по-новият commit печели (git log е от нов към стар)
seen = {}
for h in log:
    try:
        raw = subprocess.check_output(['git', 'show', f'{h}:flight-cache.json'],
                                      stderr=subprocess.DEVNULL)
        data = json.loads(raw).get('data') or []
    except Exception:
        continue
    for f in data:
        arr = f.get('arrival') or {}
        fn = ((f.get('flight') or {}).get('iata') or '').replace(' ', '')
        sch = arr.get('scheduled') or ''
        term = arr.get('terminal')
        if not (fn and term and len(sch) >= 16):
            continue
        day = sch[:10]
        if day < SINCE.isoformat() or day >= TODAY.isoformat():
            continue
        k = (day, fn)
        if k in seen:
            continue
        seen[k] = {
            'fn': fn,
            'from': (f.get('departure') or {}).get('airport') or '',
            't': sch[11:16],
            'term': str(term),
            'airline': (f.get('airline') or {}).get('name') or '',
            'day': day,
        }

# ден от седмицата -> номер -> всички появявания
by = defaultdict(lambda: defaultdict(list))
for (day, fn), r in seen.items():
    wd = (dt.date.fromisoformat(day).weekday() + 1) % 7      # 0 = неделя
    by[wd][fn].append(r)

# „Последните 2 седмици“ се мерят от последния ден С разписание, не от днес:
# ако AeroDataBox спре разписанието за дълго, старото остава, вместо да изтлее.
NEWEST = max((d for d, _ in seen), default=TODAY.isoformat())
CUTOFF = (dt.date.fromisoformat(NEWEST) - dt.timedelta(days=14)).isoformat()

days = {}
for wd in range(7):
    rows = []
    for fn, occ in by[wd].items():
        occ.sort(key=lambda r: r['day'])
        last = occ[-1]                                        # най-новото появяване
        # не е летял в този ден последните 2 седмици -> вероятно е спрян
        if last['day'] < CUTOFF:
            continue
        rows.append({'fn': fn, 'from': last['from'], 't': last['t'],
                     'term': last['term'], 'airline': last['airline'],
                     'seen': len(occ), 'last': last['day']})
    rows.sort(key=lambda r: r['t'])
    days[str(wd)] = rows

out = {'built': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
       'weeks': WEEKS, 'from': SINCE.isoformat(), 'to': TODAY.isoformat(), 'newest': NEWEST,
       'days': days}
json.dump(out, open('sof-weekly.json', 'w', encoding='utf-8'),
          ensure_ascii=False, separators=(',', ':'))

total = sum(len(v) for v in days.values())
names = ['нед', 'пон', 'вт', 'ср', 'чет', 'пет', 'съб']
summary = ' · '.join(f'{names[i]} {len(days[str(i)])}' for i in range(7))
print(f'sof-weekly.json: {total} полета ({summary}), commits: {len(log)}')
if total < 50:
    print('ГРЕШКА: твърде малко полети — историята не е изтеглена цялата?')
    sys.exit(1)

# -*- coding: utf-8 -*-
"""v12: (1) маха несъществуващия басейн Мария Луиза
       (2) добавя 3 РАБОТЕЩИ басейна (сверени: Мадара, Възраждане, Варадеро)
       (3) 🚌 ЧАСОВЕ НА СПИРКИТЕ — инжектира ETA направо в popup-ите на
           крайпътните спирки (Експо/Цариградско, Ботевградско, бул.България),
           вместо да ги крие в отделния панел."""
import re, subprocess, shutil, os

rep = []
src = open('app.js', encoding='utf-8').read()
cand = src

# ---------- (1) премахване на несъществуващия обект ----------
pat_ml = re.compile(r'\s*\{\s*id:"pool_marialuiza".*?\}\s*,?', re.S)
if pat_ml.search(cand):
    cand = pat_ml.sub('\n  ', cand, count=1)
    rep.append('OK   pool_marialuiza ПРЕМАХНАТ (комплексът е съборен/изоставен)')
else:
    rep.append('SKIP pool_marialuiza не е намерен')

# ---------- (2) нови, проверени басейни ----------
NEW_POOLS = [
    ('pool_madara', 'Басейн Мадара (НСА) ☀лято', 42.6873, 23.3114, 180,
     'Плувен басейн Мадара София'),
    ('pool_vazrazhdane', 'Аква парк Възраждане ☀лято', 42.6953, 23.3055, 200,
     'Аква парк Възраждане София'),
    ('pool_varadero', 'Комплекс Варадеро ☀лято', 42.7124, 23.3820, 220,
     'Варадеро басейни София'),
]
anchor = '{ id:"pool_spartak",'
if cand.count(anchor) == 1:
    block = ''
    for zid, name, lat, lng, rad, waze in NEW_POOLS:
        if zid in cand:
            rep.append('SKIP %s вече съществува' % zid)
            continue
        block += ('{ id:"%s", name:"%s", icon:"🏊", lat:%s, lng:%s, radius:%d, '
                  'type:"leisure", wazeName:"%s" },\n  ' % (zid, name, lat, lng, rad, waze))
        rep.append('OK   %-18s + %.4f, %.4f  (нов, сверен)' % (zid, lat, lng))
    cand = cand.replace(anchor, block + anchor, 1)
else:
    rep.append('SKIP нови басейни (котва pool_spartak x%d)' % cand.count(anchor))

# ---------- (3) часове на спирките ----------
if 'stop-eta-v12' in cand:
    rep.append('SKIP часове на спирките вече са добавени')
else:
    cand += """

// ------ stop-eta-v12: ЧАСОВЕ на крайпътните спирки ------
// Инжектира ETA направо в popup-а на спирката, вместо в отделен панел.
(function(){
  var BUS = {list:[], ts:0};
  var HEMUS=/(ВАРНА|ШУМЕН|РУСЕ|РАЗГРАД|ТЪРГОВИЩЕ|ТЪРНОВО|ГАБРОВО|ПЛЕВЕН|ЛОВЕЧ|СЕВЛИЕВО|БЯЛА|ДОБРИЧ|СИЛИСТРА|БОТЕВГРАД|ПРАВЕЦ)/i;
  var TRAKIA=/(ПЛОВДИВ|БУРГАС|СТАРА ЗАГОРА|СТ\\. ?ЗАГОРА|СЛИВЕН|ЯМБОЛ|ХАСКОВО|КЪРДЖАЛИ|ДИМИТРОВГРАД|ПАЗАРДЖИК|АСЕНОВГРАД|НЕСЕБЪР|СЛЪНЧЕВ|ПОМОРИЕ|СОЗОПОЛ|ИСТАНБУЛ|ОДРИН|ЧОРЛУ|АНКАРА|БУРСА)/i;
  var YUG=/(БЛАГОЕВГРАД|САНДАНСКИ|ПЕТРИЧ|ДУПНИЦА|КЮСТЕНДИЛ|БАНСКО|РАЗЛОГ|ГОЦЕ|СОЛУН|АТИНА|КАВАЛА|ДРАМА|СКОПИЕ|СТРУМИЦА|ОХРИД|БИТОЛЯ)/i;

  function corr(from){
    var f=(from||'').toUpperCase();
    if(HEMUS.test(f)) return 'хемус';
    if(TRAKIA.test(f)) return 'тракия';
    if(YUG.test(f)) return 'юг';
    return null;
  }
  function hm(d){return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'});}

  function pull(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 150*60000;
      var out=[];
      if(fresh){
        (d.arrivals||[]).forEach(function(a){
          var m=/^(\\d{1,2}):(\\d{2})$/.exec(a.time||''); if(!m) return;
          var cas=new Date(); cas.setHours(+m[1],+m[2],0,0);
          // ако часът е минал с повече от 3ч, значи е за утре
          if(cas.getTime() < Date.now()-3*3600000) cas.setDate(cas.getDate()+1);
          out.push({cas:cas, from:a.from, c:corr(a.from), intl:a.intl});
        });
      }
      out.sort(function(a,b){return a.cas-b.cas});
      BUS={list:out, ts:Date.now()};
    }).catch(function(e){});
  }
  pull(); setInterval(pull, 180000);

  // коя спирка е и колко минути ПРЕДИ ЦАС минава автобусът оттам
  function stopInfo(txt){
    var t=(txt||'');
    if(/[Ee]xpo|Експо|метро Цариградско|Цариградско шосе/i.test(t)) return {n:'Експо/Цариградско', off:15};
    if(/Ботевградско/i.test(t)) return {n:'Ботевградско шосе', off:12};
    if(/бул\\.? ?България|Хладилника/i.test(t)) return {n:'бул. България', off:14};
    return null;
  }
  // кой коридор се обслужва — от самия текст на popup-а
  function stopCorr(txt){
    var t=(txt||'');
    if(/Тракия/i.test(t)) return 'тракия';
    if(/Хемус/i.test(t)) return 'хемус';
    if(/Юг|Струма/i.test(t)) return 'юг';
    return null;
  }

  function enrich(el){
    try{
      if(!el || el.dataset && el.dataset.eta) return;
      var txt = el.textContent || '';
      if(!/Слизане от|Експо|Ботевградско|бул\\.? ?България|Цариградско/i.test(txt)) return;
      var si = stopInfo(txt); if(!si) return;
      var sc = stopCorr(txt);
      var now = Date.now();
      var hits = BUS.list.filter(function(b){
        if(sc && b.c !== sc) return false;
        if(!sc && !b.c) return false;
        var pass = b.cas.getTime() - si.off*60000;   // минава през спирката
        return pass > now-12*60000 && pass < now+150*60000;
      }).slice(0,4);

      var html;
      if(!BUS.list.length){
        html = '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;background:rgba(148,163,184,.12);'
             + 'border-left:3px solid #94a3b8;font-size:12px;color:#64748b">🚌 Няма пресни данни от ЦАС</div>';
      } else if(!hits.length){
        html = '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;background:rgba(148,163,184,.12);'
             + 'border-left:3px solid #94a3b8;font-size:12px;color:#64748b">🚌 Няма автобуси в следващите 2.5ч</div>';
      } else {
        var soon = hits[0].cas.getTime()-si.off*60000;
        var mins = Math.round((soon-now)/60000);
        var urgent = mins <= 20;
        var rows = hits.map(function(b){
          var pass = new Date(b.cas.getTime()-si.off*60000);
          var m = Math.round((pass.getTime()-now)/60000);
          var when = m<=0 ? 'сега' : ('след '+m+'м');
          return '<div style="margin:2px 0"><b>'+hm(pass)+'</b> · '+(b.intl?'🌍 ':'')+b.from
               + ' <span style="opacity:.65">('+when+' · ЦАС '+hm(b.cas)+')</span></div>';
        }).join('');
        html = '<div style="margin-top:7px;padding:7px 9px;border-radius:7px;background:'
             + (urgent?'rgba(234,88,12,.14)':'rgba(56,189,248,.10)')
             + ';border-left:3px solid '+(urgent?'#ea580c':'#38bdf8')+';font-size:12px">'
             + '<b style="font-size:12px">🚌 Слизане на '+si.n+'</b>'+rows+'</div>';
      }
      if(el.dataset) el.dataset.eta='1';
      el.insertAdjacentHTML('beforeend', html);
    }catch(e){}
  }

  function scan(){
    document.querySelectorAll('.leaflet-popup-content').forEach(enrich);
    document.querySelectorAll('[data-stop],.stop-card,.zone-detail').forEach(enrich);
  }
  scan();
  setInterval(scan, 4000);
  try{ new MutationObserver(function(){ scan(); })
        .observe(document.body,{childList:true,subtree:true}); }catch(e){}
})();
"""
    rep.append('OK   часове на спирките (popup ETA по коридор)')

open('/tmp/app.c.js', 'w', encoding='utf-8').write(cand)
r = subprocess.run(['node', '--check', '/tmp/app.c.js'], capture_output=True, text=True)
if r.returncode == 0:
    shutil.move('/tmp/app.c.js', 'app.js')
    idx = open('index.html', encoding='utf-8').read()
    idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260723v12', idx)
    open('index.html', 'w', encoding='utf-8').write(idx)
    ids = re.findall(r'\{\s*id:"([^"]+)"\s*,\s*name:', cand)
    rep.append('зони: %d' % len(ids))
    rep.append('OK v12 + node --check + cache-bust v12')
else:
    rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])

os.makedirs('debug', exist_ok=True)
open('debug/v12-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
open('flights-rain-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

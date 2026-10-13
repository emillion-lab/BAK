#!/usr/bin/env python3
"""🚻 Слой „бързи тоалетни“ в BAK: чете toilets.json, бутон под zoom-а за
вкл./изкл. и бутон „най-близката отворена“. Идемпотентен."""
import sys

MARK = 'toilet-layer-v1'
LAYER = r"""

// ------ toilet-layer-v1: 🚻 бързи тоалетни (toilets.json) ------
// Моловете не влизат нарочно — паркиране + влизане/излизане отнема много.
// Нови места се добавят само в toilets.json, кодът не се пипа.
(function(){
  var KIND = { kaufland:['#e10915','K','#fff'], praktiker:['#f7c600','P','#111'], decathlon:['#0082c3','D','#fff'],
               office:['#64748b','10','#fff'], other:['#16a34a','•','#fff'] };
  var DAYS = {Mo:1,Tu:2,We:3,Th:4,Fr:5,Sa:6,Su:0};
  var esc = function(s){ return String(s||'').replace(/[&<>"]/g,function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); };

  // Отворено ли е сега по OSM часове ("Mo-Su 07:00-22:00; Fr 07:00-21:00").
  // null = часовете не са известни. По-късно правило за същия ден печели (както в OSM).
  function openNow(h){
    if(!h) return null;
    var now = new Date(), d = now.getDay(), m = now.getHours()*60 + now.getMinutes(), res = null;
    h.split(';').forEach(function(rule){
      var r = rule.trim().match(/^([A-Za-z,\-]+)\s+(\d\d):(\d\d)-(\d\d):(\d\d)$/); if(!r) return;
      var today = false;
      r[1].split(',').forEach(function(part){
        var ab = part.split('-'), a = DAYS[ab[0]], b = ab.length > 1 ? DAYS[ab[1]] : a;
        if(a === undefined || b === undefined) return;
        for(var i = a, k = 0; k < 7; k++, i = (i+1)%7){ if(i === d){ today = true; break; } if(i === b) break; }
      });
      if(today) res = (m >= (+r[2])*60 + (+r[3]) && m < (+r[4])*60 + (+r[5]));
    });
    return res === null ? false : res;
  }

  function icon(p, open){
    var k = KIND[p.kind] || KIND.other;
    return L.divIcon({ className:'', iconSize:[26,26], iconAnchor:[13,13], popupAnchor:[0,-12],
      html: '<div style="position:relative;width:26px;height:26px;border-radius:50%;background:#fff;border:2px solid '+k[0]
          + ';display:flex;align-items:center;justify-content:center;font-size:14px;box-shadow:0 1px 4px rgba(0,0,0,.45);'
          + (open === false ? 'opacity:.45;filter:grayscale(1);' : '') + '">🚻'
          + '<span style="position:absolute;right:-6px;bottom:-4px;background:'+k[0]+';color:'+k[2]
          + ';font:900 8px/1 system-ui;border-radius:6px;padding:2px 3px">'+k[1]+'</span></div>' });
  }

  function popup(p, open, km){
    var nm = esc(p.name).replace(/'/g, "\\'");
    var st = open === null ? '<span style="color:#64748b">часове неизвестни</span>'
           : open ? '<b style="color:#16a34a">отворено сега</b>' : '<b style="color:#dc2626">затворено сега</b>';
    var b = 'flex:1;padding:6px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;color:#0f172a;font:700 12px system-ui;cursor:pointer';
    return '<div style="font-family:system-ui;min-width:190px"><b style="font-size:14px">🚻 '+esc(p.name)+'</b>'
      + (p.addr ? '<div style="color:#64748b;font-size:12px">'+esc(p.addr)+'</div>' : '')
      + '<div style="font-size:12px;margin:4px 0">'+st+(p.hours ? ' · <span style="color:#64748b">'+esc(p.hours)+'</span>' : '')
      + (km != null ? ' · ≈'+km.toFixed(1)+' км' : '') + '</div>'
      + (p.note ? '<div style="font-size:11.5px;color:#b45309">'+esc(p.note)+'</div>' : '')
      + '<div style="display:flex;gap:6px;margin-top:6px">'
      + '<button onclick="openWaze(\''+nm+'\','+p.lat+','+p.lng+')" style="'+b+'">🚗 Waze</button>'
      + '<button onclick="openGoogleMaps(\''+nm+'\','+p.lat+','+p.lng+')" style="'+b+'">📍 Google</button></div></div>';
  }

  function ready(cb){
    var t = setInterval(function(){ if(window.map && window.L){ clearInterval(t); cb(); } }, 500);
    setTimeout(function(){ clearInterval(t); }, 30000);
  }

  ready(function(){
    fetch('toilets.json?v='+Date.now()).then(function(r){ return r.json(); }).then(function(d){
      var P = (d && d.places) || []; if(!P.length) return;
      var M = window.map, layer = L.layerGroup(), marks = [], on = true, btn = null;
      try{ on = localStorage.getItem('bak_wc') !== '0'; }catch(e){}

      P.forEach(function(p){
        var o = openNow(p.hours);
        var mk = L.marker([p.lat, p.lng], { icon: icon(p, o), zIndexOffset: 300 }).bindPopup(popup(p, o));
        marks.push({ p:p, mk:mk }); layer.addLayer(mk);
      });

      function refresh(){
        marks.forEach(function(x){ var o = openNow(x.p.hours); x.mk.setIcon(icon(x.p, o)); x.mk.setPopupContent(popup(x.p, o)); });
      }
      setInterval(refresh, 5*60000);

      function setOn(v){
        on = v;
        if(on) layer.addTo(M); else M.removeLayer(layer);
        if(btn){ btn.style.background = on ? '#dcfce7' : '#fff'; btn.style.opacity = on ? '1' : '.6'; }
        try{ localStorage.setItem('bak_wc', on ? '1' : '0'); }catch(e){}
      }

      // най-близката отворена (или с неизвестни часове) спрямо GPS-а, иначе центъра на картата
      function nearest(){
        var me = (typeof userLat !== 'undefined' && userLat !== null) ? [userLat, userLng] : [M.getCenter().lat, M.getCenter().lng];
        var cosLat = Math.cos(me[0]*Math.PI/180), best = null;
        marks.forEach(function(x){
          if(openNow(x.p.hours) === false) return;
          var dy = (x.p.lat - me[0])*111.2, dx = (x.p.lng - me[1])*111.2*cosLat, km = Math.sqrt(dx*dx + dy*dy);
          if(!best || km < best.km) best = { x:x, km:km };
        });
        if(!best){ alert('🚻 Няма отворена тоалетна от списъка в момента'); return; }
        setOn(true);
        M.setView([best.x.p.lat, best.x.p.lng], Math.max(M.getZoom(), 15));
        best.x.mk.setPopupContent(popup(best.x.p, openNow(best.x.p.hours), best.km)).openPopup();
      }

      var Ctl = L.Control.extend({ options:{ position:'topleft' }, onAdd:function(){
        var c = L.DomUtil.create('div', 'leaflet-bar');
        var a = 'display:block;width:34px;height:32px;line-height:32px;text-align:center;background:#fff;color:#111;text-decoration:none;';
        c.innerHTML = '<a href="#" title="Тоалетни: вкл./изкл." style="'+a+'font-size:17px">🚻</a>'
                    + '<a href="#" title="Най-близката отворена тоалетна" style="'+a+'font:900 10.5px/32px system-ui">📍WC</a>';
        L.DomEvent.disableClickPropagation(c);
        var l = c.querySelectorAll('a'); btn = l[0];
        l[0].onclick = function(e){ e.preventDefault(); setOn(!on); };
        l[1].onclick = function(e){ e.preventDefault(); nearest(); };
        return c;
      }});
      M.addControl(new Ctl());
      setOn(on);
    }).catch(function(e){ console.warn('[WC] toilets.json', e); });
  });
})();
"""

s = open('app.js', encoding='utf-8').read()
log = []
if MARK in s:
    log.append('слой тоалетни: вече е приложено')
else:
    s = s.rstrip('\n') + LAYER
    log.append('слой тоалетни: OK')
open('app.js', 'w', encoding='utf-8').write(s)

h = open('index.html', encoding='utf-8').read()
OLD_V, NEW_V = 'app.js?v=20261013v168', 'app.js?v=20261013v169'
if NEW_V in h: log.append('версия: вече е приложено')
elif h.count(OLD_V) == 1:
    h = h.replace(OLD_V, NEW_V); log.append('версия: OK')
else: log.append('версия: ГРЕШКА — очаквах ' + OLD_V)
open('index.html', 'w', encoding='utf-8').write(h)

open('toilets-report.txt', 'w', encoding='utf-8').write('\n'.join(log) + '\n')
print('\n'.join(log))
if any('ГРЕШКА' in l for l in log): sys.exit(1)

// inline-closer-v23 — работещи реализации за inline хендлъри от index.html
(function(){
  function hideOwner(){
    try{
      var ev = window.event;
      var t = ev && (ev.target || ev.srcElement);
      if(t){
        var n = t;
        for(var i = 0; i < 7 && n; i++){
          n = n.parentElement;
          if(!n) break;
          var cls = (n.className || '').toString();
          if(n.id || /alert|event|banner|toast|popup|hint|modal|box/i.test(cls)){
            n.style.display = 'none';
            return true;
          }
        }
        if(t.parentElement){ t.parentElement.style.display = 'none'; return true; }
      }
      var ids = ['event-alert','eventAlert','event-banner','alert-box',
                 'bakshish-box','direction-hint','karyk-banner','rain-banner'];
      for(var k = 0; k < ids.length; k++){
        var e = document.getElementById(ids[k]);
        if(e && e.offsetParent !== null){ e.style.display = 'none'; return true; }
      }
    }catch(err){}
    return false;
  }
  var N = ["closeDirHint", "closeEventAlert", "closeNav", ];
  N.forEach(function(n){
    if(typeof window[n] === 'function') return;
    window[n] = hideOwner;
  });
})();

// inline-fallback-v21 — предпазни заглушки, за да не гърми inline onclick
(function(){ var N = ["function"];
  N.forEach(function(n){
    if(typeof window[n] === 'function') return;
    window[n] = function(){
      try{
        var ids = ['event-alert','eventAlert','event-banner','alert-box'];
        ids.forEach(function(id){ var e=document.getElementById(id); if(e) e.style.display='none'; });
      }catch(e){}
    };
  });
})();

// __leafletMap-hook (v20) — прихваща Leaflet картата при създаване
(function(){
  try{
    if(window.L && typeof L.map === 'function'){
      var _origMap = L.map;
      L.map = function(){
        var m = _origMap.apply(this, arguments);
        try{ window.__leafletMap = m; }catch(e){}
        return m;
      };
      for(var k in _origMap){ try{ L.map[k] = _origMap[k]; }catch(e){} }
    }
  }catch(e){}
  // фокусиране на зона от списъка — вика се от inline onclick
  window.__focusZone = function(lat, lng, zoom){
    try{
      var el = document.getElementById('map');
      if(el && el.scrollIntoView) el.scrollIntoView({behavior:'smooth', block:'center'});
      var m = window.__leafletMap;
      if(!m || typeof m.setView !== 'function') return;
      setTimeout(function(){
        try{
          if(typeof m.invalidateSize === 'function') m.invalidateSize();
          m.setView([lat, lng], zoom || 15);
        }catch(e){}
      }, 220);
    }catch(e){}
  };
})();

// bak-rescue-v16 — ловец на грешки (вмъкнат НАЙ-ОТГОРЕ)
(function(){
  var shown = 0;
  function show(msg, extra){
    if (shown >= 3) return;
    shown++;
    try{
      var d = document.createElement('div');
      d.style.cssText = 'position:fixed;left:0;right:0;top:0;z-index:99999;'
        + 'background:#7f1d1d;color:#fff;font:12px/1.35 monospace;padding:8px 30px 8px 10px;'
        + 'white-space:pre-wrap;word-break:break-word;box-shadow:0 2px 8px rgba(0,0,0,.6)';
      d.textContent = '⚠ ' + msg + (extra ? ('\n' + extra) : '');
      var x = document.createElement('span');
      x.textContent = '✕';
      x.style.cssText = 'position:absolute;right:8px;top:6px;cursor:pointer;font-size:16px';
      x.onclick = function(){ d.remove(); };
      d.appendChild(x);
      (document.body || document.documentElement).appendChild(d);
    }catch(e){}
  }
  window.addEventListener('error', function(ev){
    var f = (ev.filename||'').split('/').pop();
    show((ev.message||'грешка'), f + ':' + ev.lineno + ':' + ev.colno);
  });
  window.addEventListener('unhandledrejection', function(ev){
    var r = ev.reason;
    show('Promise: ' + ((r && (r.message||r)) || 'отхвърлен'), '');
  });
  // защита: грешка в един DOMContentLoaded хендлър да не спира другите
  var origAdd = document.addEventListener.bind(document);
  document.addEventListener = function(ev, fn, opt){
    if (ev === 'DOMContentLoaded' && typeof fn === 'function'){
      var wrapped = function(e){
        try { return fn.call(this, e); }
        catch(err){
          show('DOMContentLoaded: ' + (err && err.message),
               ((err && err.stack)||'').split('\n')[1] || '');
          throw err;
        }
      };
      return origAdd(ev, wrapped, opt);
    }
    return origAdd(ev, fn, opt);
  };
})();

document.addEventListener('DOMContentLoaded', function() {

if (typeof L === 'undefined') {
  document.getElementById('map').innerHTML =
    '<div style="color:#ef4444;padding:20px;font-family:monospace">Leaflet не се зареди.</div>';
  return;
}

// ═══════════════════════════════════════════════
// GLOBAL STATE
// ═══════════════════════════════════════════════
let currentHour       = 16;
let karykMode         = false;
let autoTime          = true;
let weatherBoost      = 0;
let userLat           = null;
let userLng           = null;
let watchId           = null;
let userMarker        = null;
let navTarget         = null;
let deviceHeading     = null;
let dirHintZid        = null;
let dirHintSuppressed = false;
let flightHours       = Array(24).fill(0);
let flightDetails     = []; // [{from, exitFrom, exitTo, fn, nonSchengen}]
let airportStatus     = 'offline';
let demandCurve       = [];
let alertedEvents     = new Set();

// ═══════════════════════════════════════════════
// ZONE DEFINITIONS
// ═══════════════════════════════════════════════
const ZONES = window.__ZONES = [
  { id:"airport",        name:"Летище София (СОФ)",                     icon:"✈️",  lat:42.6885, lng:23.4082, radius:600, type:"airport",          wazeName:"Летище София" },
  { id:"bpark",          name:"Business Park Sofia",                    icon:"🏢", lat:42.6269, lng:23.3784, radius:380, type:"office",           wazeName:"Business Park Sofia" },
  { id:"garitage",       name:"Garitage Park",                          icon:"🏢", lat:42.6227, lng:23.3735, radius:320, type:"office",           wazeName:"Garitage Park Sofia" },
  { id:"polygraphia",    name:"Polygraphia Office Center (Цариградско 47)",              icon:"🏢", lat:42.6874, lng:23.344, radius:260, type:"office",           wazeName:"Polygraphia Office Center Sofia" },
  { id:"capital_fort",   name:"Capital Fort",                           icon:"🏢", lat:42.6464, lng:23.3958, radius:230, type:"office",           wazeName:"Capital Fort Sofia" },
  { id:"megapark",       name:"Megapark / The Mall офиси",              icon:"🏢", lat:42.661, lng:23.38, radius:260, type:"office",           wazeName:"Megapark Sofia" },
  { id:"advance_bc",     name:"Advance Business Center",                icon:"🏢", lat:42.6294, lng:23.3747, radius:230, type:"office",           wazeName:"Advance Business Center Sofia" },
  { id:"expo2000",       name:"Ellipse Center (Цариградско шосе)",             icon:"🏢", lat:42.6458, lng:23.3972, radius:280, type:"office",           wazeName:"Expo 2000 Sofia" },
  { id:"iec",            name:"IEC / Интер Експо Център (Цариградско 147)",               icon:"🏢", lat:42.6491, lng:23.3952, radius:280, type:"office",           wazeName:"Inter Expo Center Sofia" },
  { id:"office_center",  name:"Офис Център (пл.Патриарх Евтимий)",     icon:"🏢", lat:42.6883, lng:23.3285, radius:230, type:"office",           wazeName:"площад Патриарх Евтимий София" },
  { id:"sopharma_bc",    name:"Sopharma Business Towers (Лъчезар Станчев 5)",               icon:"🏢", lat:42.6661, lng:23.3571, radius:200, type:"office",           wazeName:"Sopharma Business Towers Sofia" },
  { id:"sopharma_rozhen", name:"Sopharma Trading (бул.Рожен 16)", icon:"🏢", lat:42.7289, lng:23.3133, radius:180, type:"office", wazeName:"Sopharma Trading бул Рожен 16 София" },
  { id:"telus",          name:"Telus Tower / пл.Македония",             icon:"🏢", lat:42.6947, lng:23.3154, radius:180, type:"office",           wazeName:"Telus Tower Sofia" },
  { id:"millennium",     name:"Millennium Center (бул.Витоша)",         icon:"🏢", lat:42.6822, lng:23.3147, radius:200, type:"office",           wazeName:"Millennium Center Sofia" },
  { id:"oval",           name:"Oval Business Center (Лозенец)",         icon:"🏢", lat:42.6640, lng:23.3340, radius:180, type:"office",           wazeName:"Oval Business Center Sofia" },

  { id:"serdika",        name:"Мол Сердика (бул.Ситняково 48)",                            icon:"🛍", lat:42.6918, lng:23.3532, radius:240, type:"mall",             wazeName:"Serdika Center Sofia" },
  { id:"paradise",       name:"Paradise Center",                        icon:"🛍", lat:42.6578, lng:23.3144, radius:290, type:"mall",             wazeName:"Paradise Center Sofia" },
  { id:"mall_sofia",     name:"Mall of Sofia",                          icon:"🛍", lat:42.6981, lng:23.3086, radius:210, type:"mall",             wazeName:"Mall of Sofia" },
  { id:"ring_mall",      name:"Ring Mall / IKEA",                       icon:"🛍", lat:42.6246, lng:23.3519, radius:340, type:"mall",             wazeName:"Ring Mall Sofia" },
  { id:"the_mall",       name:"The Mall Sofia",                         icon:"🛍", lat:42.6605, lng:23.3822, radius:290, type:"mall",             wazeName:"The Mall Sofia" },
  { id:"bulgaria_mall",  name:"България Мол",                           icon:"🛍", lat:42.6641, lng:23.2885, radius:240, type:"mall",             wazeName:"Bulgaria Mall Sofia" },
  { id:"park_center",    name:"Park Center (бул.Арсеналски 2)",    icon:"🛍", lat:42.6788, lng:23.3208, radius:190, type:"mall",             wazeName:"Park Center Sofia" },

  { id:"hotels_ctr",     name:"Хотели Център (Radisson/Hilton)",        icon:"🏨", lat:42.6953, lng:23.3242, radius:280, type:"hotel",            wazeName:"Radisson Blu Sofia" },
  { id:"hotels_ndk",     name:"Kempinski / InterContinental НДК",       icon:"🏨", lat:42.6855, lng:23.3188, radius:180, type:"hotel",            wazeName:"Kempinski Hotel Zografski Sofia" },
  { id:"hotel_marinela", name:"Хотел Маринела (Джеймс Баучер 100)",    icon:"🏨", lat:42.6724, lng:23.319, radius:160, type:"hotel",            wazeName:"Hotel Marinela Sofia" },

  { id:"cjp",            name:"Централна ЖП гара",                      icon:"🚂", lat:42.7121, lng:23.3210, radius:240, type:"transit",          wazeName:"Централна жп гара София" },
  { id:"cab_north",      name:"Централна автогара",                     icon:"🚌", lat:42.7103, lng:23.3233, radius:200, type:"transit",          wazeName:"Централна автогара София" },
  { id:"cas_intl", name:"🌍 Междунар. автогара Сердика / FlixBus", icon:"🌍", lat:42.7108, lng:23.3224, radius:150, type:"transit", wazeName:"Международна автогара Сердика София" },
  { id:"ag_yug",         name:"Автогара Юг (бул.Драган Цанков)",        icon:"🚌", lat:42.6689, lng:23.3526, radius:190, type:"transit",          wazeName:"Автогара Юг София" },
  { id:"ag_pod",         name:"Автогара Подуяне",                       icon:"🚌", lat:42.7034, lng:23.3601, radius:190, type:"transit",          wazeName:"Автогара Подуяне София" },

  { id:"arena",          name:"Арена 8888",                             icon:"🎸", lat:42.6711, lng:23.3692, radius:290, type:"venue",            wazeName:"Arena Sofia 8888" },
  { id:"ndk",            name:"НДК",                                    icon:"🎭", lat:42.6855, lng:23.3188, radius:260, type:"venue",            wazeName:"Национален дворец на културата НДК" },
  { id:"borisova",       name:"Борисова градина (парк)",      icon:"🌳", lat:42.6748, lng:23.3394, radius:750, type:"leisure",          wazeName:"Борисова градина София" },
  { id:"vl_stadium", name:"Нац. стадион Васил Левски", icon:"🏟️", lat:42.6882, lng:23.3346, radius:320, type:"leisure", wazeName:"Национален стадион Васил Левски София" },
  { id:"nat_theatre",    name:"Народен театър Иван Вазов",              icon:"🎭", lat:42.6944, lng:23.3261, radius:180, type:"theatre",          wazeName:"Народен театър Иван Вазов София" },
  { id:"opera",          name:"Национална опера и балет",               icon:"🎶", lat:42.6975, lng:23.3305, radius:180, type:"theatre",          wazeName:"Национална опера и балет София" },
  { id:"ndk_theatre",    name:"Театри / НДК зона",                      icon:"🎭", lat:42.6843, lng:23.3196, radius:200, type:"theatre",          wazeName:"НДК театри София" },

  { id:"pirogov",        name:"УМБАЛ Пирогов (бул.Тотлебен 21)",        icon:"🏥", lat:42.6901, lng:23.3072, radius:190, type:"hospital",         wazeName:"УМБАЛСМ Пирогов бул Тотлебен 21 София" },
  { id:"alexand",        name:"Александровска болница",                 icon:"🏥", lat:42.6854, lng:23.3114, radius:190, type:"hospital",         wazeName:"УМБАЛ Александровска болница София" },
  { id:"vma",            name:"ВМА (Георги Софийски 3)",         icon:"🏥", lat:42.6842, lng:23.3045, radius:170, type:"hospital",         wazeName:"ВМА Военномедицинска академия София" },
  { id:"sv_anna",        name:"УМБАЛ Света Анна",                       icon:"🏥", lat:42.6605, lng:23.3734, radius:160, type:"hospital",         wazeName:"УМБАЛ Света Анна Sofia" },
  { id:"sv_ekaterina",   name:"УМБАЛ Света Екатерина",                  icon:"🏥", lat:42.6851, lng:23.3125, radius:160, type:"hospital",         wazeName:"УМБАЛ Света Екатерина Sofia" },
  { id:"acibadem_ortho", name:"Acibadem Ортопедия (Околовръстен 127)", icon:"🏥", lat:42.64, lng:23.3181, radius:150, type:"hospital",         wazeName:"Acibadem Ортопедия Околовръстен Sofia" },
  { id:"isul",           name:"ИСУЛ – Царица Йоанна (Бяло море 8)",                 icon:"🏥", lat:42.7008, lng:23.3391, radius:160, type:"hospital",         wazeName:"ИСУЛ болница Sofia" },

  { id:"unss",           name:"УНСС",                                   icon:"🎓", lat:42.6513, lng:23.349, radius:240, type:"university",       wazeName:"УНСС София" },
  { id:"nbu",            name:"НБУ (ул.Монтевидео 21)",                 icon:"🎓", lat:42.6782, lng:23.2527, radius:190, type:"university",       wazeName:"Нов Български Университет НБУ" },
  { id:"tu",             name:"Технически университет",                 icon:"🎓", lat:42.657, lng:23.3554, radius:210, type:"university",       wazeName:"Технически университет София" },
  { id:"su",             name:"Софийски университет",                   icon:"🎓", lat:42.6936, lng:23.3349, radius:200, type:"university",       wazeName:"Софийски университет Св Климент Охридски" },
  { id:"studentski",     name:"Студентски град",                        icon:"🎓", lat:42.6475, lng:23.3530, radius:380, type:"university",       wazeName:"Студентски град Sofia" },

  { id:"simenovo",       name:"Симеоново / Hill Side",                  icon:"🌲", lat:42.6395, lng:23.3310, radius:380, type:"residential_lux",  wazeName:"Hill Side Sofia Симеоновско шосе 97" },
  { id:"manast",         name:"Манастирски ливади",                     icon:"🏘", lat:42.6637, lng:23.2910, radius:380, type:"residential_lux",  wazeName:"Манастирски ливади София" },
  { id:"boyana",         name:"Бояна / Драгалевци",                     icon:"🌳", lat:42.6348, lng:23.2889, radius:430, type:"residential_lux",  wazeName:"Бояна квартал София" },
  { id:"kambanite",      name:"ЖК Камбаните / Малинова долина",         icon:"⛰️",  lat:42.6155, lng:23.3780, radius:380, type:"residential_lux",  wazeName:"ЖК Камбаните Sofia" },

  { id:"lyulin",         name:"жк Люлин",                               icon:"🏘", lat:42.7050, lng:23.2650, radius:400, type:"residential",      wazeName:"жк Люлин Sofia" },
  { id:"nadezhda",       name:"жк Надежда",                             icon:"🏘", lat:42.7200, lng:23.2900, radius:350, type:"residential",      wazeName:"жк Надежда Sofia" },
  { id:"ovcha_kupel",    name:"жк Овча купел",                          icon:"🏘", lat:42.6617, lng:23.2878, radius:300, type:"residential",      wazeName:"жк Овча купел Sofia" },
  { id:"druzhba",        name:"жк Дружба / Горубляне",                  icon:"🏘", lat:42.6590, lng:23.4230, radius:380, type:"residential",      wazeName:"жк Дружба Sofia" },
  { id:"mladost",        name:"жк Младост 1/2/3",                       icon:"🏘", lat:42.6500, lng:23.3700, radius:350, type:"residential",      wazeName:"жк Младост Sofia" },

  // Карък зони — невидими в нормален мод
  { id:"k_borovo",       name:"жк Борово",                              icon:"🥉", lat:42.6710, lng:23.2960, radius:300, type:"karyk",            wazeName:"жк Борово Sofia" },
  { id:"k_krasno",       name:"жк Красно село",                         icon:"🥉", lat:42.6890, lng:23.2990, radius:300, type:"karyk",            wazeName:"жк Красно село Sofia" },
  { id:"k_pavlovo",      name:"жк Павлово",                             icon:"🥉", lat:42.6770, lng:23.2820, radius:280, type:"karyk",            wazeName:"жк Павлово Sofia" },
  { id:"k_izgrev",       name:"жк Изгрев",                              icon:"🥉", lat:42.6720, lng:23.3500, radius:260, type:"karyk",            wazeName:"жк Изгрев Sofia" },
  { id:"k_geo_milev",    name:"жк Гео Милев",                           icon:"🥉", lat:42.6860, lng:23.3680, radius:260, type:"karyk",            wazeName:"жк Гео Милев Sofia" },
  { id:"k_iztok",        name:"жк Изток (жилищна зона)",                icon:"🥉", lat:42.6820, lng:23.3620, radius:280, type:"karyk",            wazeName:"жк Изток Sofia" },

  // ── ТЕАТРИ ──
  { id:"youth_theatre",  name:"Младежки театър (бул.Дондуков 8)",       icon:"🎭", lat:42.6978, lng:23.3269, radius:150, type:"theatre",          wazeName:"Младежки театър Николай Бинев София" },
  { id:"satira",         name:"Сатиричен театър Алеко Константинов",                       icon:"🎭", lat:42.6917, lng:23.3263, radius:140, type:"theatre",          wazeName:"Театър Сатирикон София" },
  { id:"theatre_199",    name:"Театър 199 Валентин Стойчев",   icon:"🎭", lat:42.6932, lng:23.3279, radius:140, type:"theatre",          wazeName:"Театър 199 Sofia" },

  // ── КИНА ──
  { id:"cinema_city_ml", name:"Cinema City Mall of Sofia",              icon:"🎬", lat:42.6981, lng:23.3086, radius:160, type:"cinema",           wazeName:"Cinema City Mall of Sofia" },
  { id:"cinema_city_ser",name:"Cinema City Сердика",                    icon:"🎬", lat:42.6918, lng:23.3532, radius:160, type:"cinema",           wazeName:"Cinema City Serdika Center Sofia" },
  { id:"cinema_arena",   name:"Кино Арена (Ring Mall)",                 icon:"🎬", lat:42.6246, lng:23.3519, radius:160, type:"cinema",           wazeName:"Кино Арена Grand Cinema Ring Mall Sofia" },
  { id:"cineland",       name:"Cineland (Paradise Center)",             icon:"🎬", lat:42.6578, lng:23.3144, radius:150, type:"cinema",           wazeName:"Cineland Paradise Center Sofia" },
  { id:"dom_kinoto",     name:"Дом на киното (ул.Екзарх Йосиф 37)",    icon:"🎬", lat:42.7003, lng:23.324, radius:130, type:"cinema",           wazeName:"Дом на киното Sofia" },

  // ── РЕСТОРАНТИ / НОЩЕН ЖИВОТ ──
  { id:"vitosha_bar",    name:"Бул.Витоша – ресторанти/барове",         icon:"🍷", lat:42.6890, lng:23.3220, radius:250, type:"nightlife",        wazeName:"булевард Витоша ресторанти София" },
  { id:"lozenets_rest",  name:"Ресторанти Лозенец (Водна кула)",        icon:"🍽", lat:42.6713, lng:23.3382, radius:220, type:"nightlife",        wazeName:"ресторанти Лозенец Водна кула София" },
  { id:"center_bars",    name:"Барове / клубове Център (ул.Раковски)",  icon:"🍺", lat:42.6960, lng:23.3310, radius:200, type:"nightlife",        wazeName:"улица Раковски Sofia" },

  // ── ДОПЪЛНИТЕЛНИ БОЛНИЦИ ──
  { id:"acibadem_tokuda",name:"Acibadem Токуда (Н.Вапцаров 51Б)",  icon:"🏥", lat:42.665, lng:23.3252, radius:160, type:"hospital",         wazeName:"Acibadem City Clinic Токуда Sofia" },
  { id:"acibadem_cardio",name:"Acibadem Сърдечно-съдов (Окол.път/Драгалевци)",icon:"🏥",lat:42.6387,lng:23.3174,radius:140,type:"hospital",       wazeName:"Acibadem City Clinic Сърдечно-съдов Sofia" },
  { id:"acibadem_mladost",name:"Acibadem Младост (Цариградско шосе)",   icon:"🏥", lat:42.6553, lng:23.3857, radius:160, type:"hospital",         wazeName:"Acibadem City Clinic Младост Sofia" },
  
  { id:"pool_madara", name:"Басейн Мадара (НСА) ☀лято", icon:"🏊", lat:42.6873, lng:23.3114, radius:180, type:"leisure", wazeName:"Плувен басейн Мадара София" },
  { id:"pool_vazrazhdane", name:"Аква парк Възраждане ☀лято", icon:"🏊", lat:42.6953, lng:23.3055, radius:200, type:"leisure", wazeName:"Аква парк Възраждане София" },
  { id:"pool_varadero", name:"Комплекс Варадеро ☀лято", icon:"🏊", lat:42.7124, lng:23.382, radius:220, type:"leisure", wazeName:"Варадеро басейни София" },
  { id:"pool_thebeach", name:"Басейн The Beach (бул.Рожен 25Е) ☀лято", icon:"🏊", lat:42.7361, lng:23.3144, radius:200, type:"leisure", wazeName:"Pool The Beach бул Рожен 25Е София" },
  { id:"pool_silvercity", name:"Басейн Silver City (Хладилника) ☀до 22ч", icon:"🏊", lat:42.6558, lng:23.3131, radius:180, type:"leisure", wazeName:"Silver City басейн София" },
  { id:"pool_sportpalace", name:"Sport Palace Pool (В.Левски 75) 🏠целогодишен", icon:"🏊", lat:42.6903, lng:23.3312, radius:160, type:"leisure", wazeName:"Sport Palace Pool София" },
  { id:"pool_hearts", name:"Hearts in Love Pool Club ☀лято", icon:"🏊", lat:42.6271, lng:23.4238, radius:200, type:"leisure", wazeName:"Hearts in Love Pool Club София" },
  { id:"pool_korali", name:"Басейн Корали (Панчарево) ☀лято", icon:"🏊", lat:42.6027, lng:23.4039, radius:200, type:"leisure", wazeName:"Korali Pool Самоковско шосе 211 Панчарево" },
  { id:"pool_infinity", name:"Infinity SPA (Панчарево)", icon:"🏊", lat:42.6019, lng:23.4035, radius:180, type:"leisure", wazeName:"Infinity SPA Самоковско шосе 211 Панчарево" },
  { id:"pool_spartak",    name:"Басейн Спартак (бул.Арсеналски 4) ☀лято",        icon:"🏊", lat:42.675, lng:23.3132, radius:200, type:"leisure", wazeName:"Спортен комплекс Спартак София" },
  { id:"pool_diana",      name:"Басейни Диана (Дианабад) ☀лято",          icon:"🏊", lat:42.6657, lng:23.3458, radius:220, type:"leisure", wazeName:"Басейн Диана София" },
  { id:"pool_akademika",  name:"Басейн Академика (4-ти км) ☀лято",        icon:"🏊", lat:42.6756, lng:23.366, radius:200, type:"leisure", wazeName:"Спортен център Академика София" },
  { id:"lozenets_h",     name:"УБ Лозенец (към СУ)",                    icon:"🏥", lat:42.6644, lng:23.3113, radius:150, type:"hospital",         wazeName:"Университетска болница Лозенец Sofia" },
  { id:"kardiologia",    name:"Национална кардиологична болница",       icon:"🏥", lat:42.7062, lng:23.2874, radius:150, type:"hospital",         wazeName:"Национална кардиологична болница Sofia" },
  { id:"sv_sofia_h",     name:"МБАЛ Св.София (бул.България 104)",       icon:"🏥", lat:42.6599, lng:23.2849, radius:160, type:"hospital",         wazeName:"МБАЛ Света София Sofia" },

  // ── ЗАДРЪСТВАНИЯ ──
  { id:"jam_orl",        name:"⚠ Задръстване Орлов мост",               icon:"🚦", lat:42.6906, lng:23.3374, radius:150, type:"traffic",          wazeName:"Орлов мост София" },
  { id:"jam_tsar",       name:"⚠ Задръстване Цариградско (при хотел Плиска)",   icon:"🚦", lat:42.6752, lng:23.3587, radius:200, type:"traffic",          wazeName:"Цариградско шосе Армейски Sofia" },
  { id:"jam_ndk",        name:"⚠ Задръстване бул.България (НДК → Мол България)",             icon:"🚦", lat:42.6745, lng:23.3028, radius:160, type:"traffic",          wazeName:"булевард България Sofia" },
  { id:"jam_serdika",    name:"⚠ Задръстване бул.Сливница (при Лъвов мост)",   icon:"🚦", lat:42.7049, lng:23.3239, radius:160, type:"traffic",          wazeName:"Сердика бул Сливница Sofia" },
];

// ═══════════════════════════════════════════════
// BASE DEMAND
// ═══════════════════════════════════════════════
const BASE = {
  airport:1.4,
  bpark:0.5, garitage:0.4, polygraphia:0.4, capital_fort:0.4, megapark:0.4,
  advance_bc:0.4, expo2000:0.4, iec:0.4, office_center:0.6,
  sopharma_bc:0.4, telus:0.5, millennium:0.4, oval:0.4,
  serdika:0.8, paradise:0.7, mall_sofia:0.6, ring_mall:0.6,
  the_mall:0.6, bulgaria_mall:0.6, park_center:0.5,
  hotels_ctr:0.9, hotels_ndk:0.7, hotel_marinela:0.6,
  cjp:0.9, cab_north:0.8, ag_yug:0.7, ag_pod:0.5,
  arena:0.3, ndk:0.7, borisova:0.3,
  nat_theatre:0.3, youth_theatre:0.2, satira:0.2, opera:0.3, theatre_199:0.2,
  cinema_city_ml:0.3, cinema_city_ser:0.3, cinema_arena:0.3, cineland:0.3, dom_kinoto:0.2,
  vitosha_bar:0.6, lozenets_rest:0.5, center_bars:0.5,
  pirogov:1.0, alexand:0.9, vma:0.8, tokuda:0.7, sv_anna:0.7,
  pool_marialuiza:0.5, pool_spartak:0.5, pool_diana:0.5, pool_akademika:0.4,
  acibadem_tokuda:0.8, acibadem_cardio:0.7, acibadem_mladost:0.7, acibadem_ortho:0.6,
  sv_ekaterina:0.7, lozenets_h:0.6, kardiologia:0.6, sv_sofia_h:0.6, isul:0.8,
  unss:0.5, nbu:0.4, tu:0.4, su:0.5, studentski:0.6,
  simenovo:0.4, manast:0.5, boyana:0.4, kambanite:0.4,
  lyulin:0.5, nadezhda:0.4, ovcha_kupel:0.4, druzhba:0.4, mladost:0.5,
  k_borovo:0.3, k_krasno:0.3, k_pavlovo:0.3,
  k_izgrev:0.3, k_geo_milev:0.3, k_iztok:0.3,
  ndk_theatre:0.3, nat_theatre:0.3,
  jam_orl:0, jam_tsar:0, jam_ndk:0, jam_serdika:0,
};

// ═══════════════════════════════════════════════
// EVENTS
// ═══════════════════════════════════════════════
const EVENTS = [
  // Airport events injected dynamically from flight-cache.json

  // Офиси — пик 16:30–18:00
  { zone:"polygraphia",   name:"Polygraphia – изход",          endHour:17.5, boost:3.0, repeat:"mon-fri" },
  { zone:"capital_fort",  name:"Capital Fort – изход",          endHour:17.5, boost:2.8, repeat:"mon-fri" },
  { zone:"megapark",      name:"Megapark – изход",              endHour:17.5, boost:2.5, repeat:"mon-fri" },
  { zone:"bpark",         name:"Business Park – изход",         endHour:17.5, boost:3.0, repeat:"mon-fri" },
  { zone:"garitage",      name:"Garitage Park – изход",         endHour:17.0, boost:2.8, repeat:"mon-fri" },
  { zone:"advance_bc",    name:"Advance BC – изход",            endHour:17.5, boost:2.5, repeat:"mon-fri" },
  { zone:"expo2000",      name:"Expo 2000 – изход",             endHour:17.5, boost:2.5, repeat:"mon-fri" },
  { zone:"iec",           name:"IEC – изход / конференции",     endHour:18.0, boost:2.2, repeat:"mon-fri" },
  { zone:"office_center", name:"Офис Център – изход",           endHour:17.0, boost:2.2, repeat:"mon-fri" },

  // Молове — 2 вълни
  { zone:"serdika",      name:"Мол Сердика – следобед",         endHour:17.5, boost:1.6, repeat:"daily" },
  { zone:"paradise",     name:"Paradise – следобед",            endHour:17.0, boost:1.5, repeat:"daily" },
  { zone:"ring_mall",    name:"Ring Mall – следобед",           endHour:17.5, boost:1.5, repeat:"daily" },
  { zone:"the_mall",     name:"The Mall – следобед",            endHour:17.0, boost:1.5, repeat:"daily" },
  { zone:"serdika",      name:"Мол Сердика – затваряне",        endHour:21.0, boost:2.0, repeat:"daily" },
  { zone:"paradise",     name:"Paradise – затваряне",           endHour:21.5, boost:2.2, repeat:"daily" },
  { zone:"ring_mall",    name:"Ring Mall – затваряне",          endHour:21.0, boost:1.8, repeat:"daily" },
  { zone:"the_mall",     name:"The Mall – затваряне",           endHour:21.0, boost:2.0, repeat:"daily" },
  { zone:"mall_sofia",   name:"Mall of Sofia – затваряне",      endHour:21.0, boost:1.8, repeat:"daily" },

  // Хотели
  { zone:"hotels_ctr",   name:"Late checkout / трансфери",      endHour:13.0, boost:1.8, repeat:"daily" },
  { zone:"hotels_ctr",   name:"Check-in wave",                  endHour:16.0, boost:1.5, repeat:"daily" },
  { zone:"hotels_ctr",   name:"Бизнес вечеря",                  endHour:21.5, boost:1.6, repeat:"mon-fri" },
  { zone:"hotels_ctr",   name:"Уикенд бар",                     endHour:23.0, boost:1.8, repeat:"fri-sat" },

  // Концерти
  { zone:"arena",        name:"SCORPIONS – Coming Home 60г.",   endHour:22.5, boost:3.5, date:"2026-06-27" },
  { zone:"ndk",          name:"НДК – концерт",                  endHour:22.0, boost:2.2, repeat:"fri-sat" },
  { zone:"borisova",     name:"Стадион – мач",                  endHour:21.5, boost:2.5, repeat:"fri-sat" },
  { zone:"nat_theatre",  name:"Народен театър – спектакъл",     endHour:21.5, boost:2.5, repeat:"tue-sat" },
  { zone:"opera",        name:"Опера / Балет – край",           endHour:22.0, boost:2.5, repeat:"tue-sun" },

  // Транзит
  { zone:"cjp",          name:"Влак Варна→София",               endHour:18.5, boost:2.2, repeat:"daily" },
  { zone:"cjp",          name:"Влак Пловдив→София",             endHour:20.0, boost:1.8, repeat:"daily" },
  { zone:"ag_yug",       name:"Автобуси от Пловдив",            endHour:19.5, boost:2.0, repeat:"daily" },
  { zone:"ag_yug",       name:"Нощни автобуси",                 endHour:22.0, boost:1.5, repeat:"daily" },

  // Болници — меки вълни
  { zone:"pirogov",      name:"Пирогов – прегледи",             endHour:9.0,  boost:1.4, repeat:"daily" },
  { zone:"pirogov",      name:"Пирогов – вечерни посещения",    endHour:18.5, boost:1.2, repeat:"daily" },
  { zone:"alexand",      name:"Александровска – прегледи",      endHour:9.0,  boost:1.3, repeat:"daily" },
  { zone:"sv_anna",      name:"Св.Анна – прегледи",             endHour:9.0,  boost:1.1, repeat:"daily" },
  { zone:"isul",         name:"ИСУЛ – прегледи",                endHour:9.0,  boost:1.1, repeat:"daily" },

  // Университети
  { zone:"unss",         name:"УНСС – края на лекции",          endHour:13.5, boost:2.0, repeat:"mon-fri" },
  { zone:"unss",         name:"УНСС – вечерни",                 endHour:18.0, boost:1.8, repeat:"mon-fri" },
  { zone:"studentski",   name:"Студентски – обяд към Центъра",  endHour:13.5, boost:2.2, repeat:"mon-fri" },
  { zone:"studentski",   name:"Студентски – вечер към Гарата",  endHour:19.0, boost:2.5, repeat:"mon-fri" },

  // Луксозни жилища
  { zone:"manast",       name:"Ман.ливади – сутрешно тръгване", endHour:8.5,  boost:2.0, repeat:"mon-fri" },
  { zone:"simenovo",     name:"Симеоново – сутрешно тръгване",  endHour:8.0,  boost:1.8, repeat:"mon-fri" },
  { zone:"boyana",       name:"Бояна – сутрешно тръгване",      endHour:8.5,  boost:1.6, repeat:"mon-fri" },
  { zone:"manast",       name:"Ман.ливади – прибиране",         endHour:22.5, boost:1.6, repeat:"fri-sat" },
  { zone:"simenovo",     name:"Симеоново – прибиране",          endHour:23.0, boost:1.8, repeat:"fri-sat" },

  // Нощен живот
  { zone:"ndk",          name:"НДК / Витоша – след вечеря",     endHour:22.0, boost:1.8, repeat:"daily" },
  { zone:"borisova",     name:"Борисова – летно кино",          endHour:23.0, boost:2.0, repeat:"fri-sat" },

  // Театри
  { zone:"nat_theatre",  name:"Народен театър – спектакъл",     endHour:21.5, boost:2.5, repeat:"tue-sat" },
  { zone:"nat_theatre",  name:"Народен театър – матине",        endHour:13.0, boost:1.5, repeat:"sat" },
  { zone:"opera",        name:"Опера / Балет – край",           endHour:22.0, boost:2.5, repeat:"tue-sun" },
  { zone:"youth_theatre",name:"Младежки театър – край",         endHour:21.5, boost:2.0, repeat:"tue-sat" },
  { zone:"satira",       name:"Театър Сатирикон – край",        endHour:22.0, boost:1.8, repeat:"thu-sat" },
  { zone:"theatre_199",  name:"Театър 199 – край",              endHour:22.0, boost:2.0, repeat:"thu-sat" },

  // Кина — последна прожекция ~22:30
  { zone:"cinema_city_ml",  name:"Cinema City Mall of Sofia – последна прожекция", endHour:22.5, boost:2.0, repeat:"daily" },
  { zone:"cinema_city_ser", name:"Cinema City Сердика – последна прожекция",       endHour:22.5, boost:2.0, repeat:"daily" },
  { zone:"cinema_arena",    name:"Кино Арена Ring Mall – последна прожекция",      endHour:22.5, boost:1.8, repeat:"daily" },
  { zone:"cineland",        name:"Cineland Paradise – последна прожекция",         endHour:22.5, boost:1.8, repeat:"daily" },
  { zone:"dom_kinoto",      name:"Дом на киното – последна прожекция",             endHour:22.0, boost:1.5, repeat:"daily" },
  // Следобедни прожекции
  { zone:"cinema_city_ml",  name:"Cinema City – следобедна прожекция",             endHour:17.5, boost:1.2, repeat:"daily" },
  { zone:"cinema_city_ser", name:"Cinema City Сердика – следобед",                 endHour:17.5, boost:1.2, repeat:"daily" },

  // Ресторанти / нощен живот
  { zone:"vitosha_bar",  name:"Бул.Витоша – след вечеря",       endHour:22.0, boost:2.2, repeat:"daily" },
  { zone:"vitosha_bar",  name:"Бул.Витоша – след клуб",         endHour:24.0, boost:2.5, repeat:"fri-sat" },
  { zone:"lozenets_rest",name:"Лозенец – след вечеря",          endHour:22.0, boost:2.0, repeat:"daily" },
  { zone:"center_bars",  name:"Центъра – барове след вечеря",   endHour:22.0, boost:1.8, repeat:"daily" },
  { zone:"center_bars",  name:"Центъра – след клуб",            endHour:24.0, boost:2.2, repeat:"fri-sat" },

  // Допълнителни болници
  
  { zone:"pool_spartak",    name:"Басейн Спартак – лятно изтичане",    endHour:18.5, boost:1.5, repeat:"daily" },
  { zone:"pool_diana",      name:"Басейни Диана – лятно изтичане",     endHour:19.0, boost:1.5, repeat:"daily" },
  { zone:"pool_akademika",  name:"Басейн Академика – лятно изтичане",  endHour:18.0, boost:1.4, repeat:"daily" },
  { zone:"acibadem_tokuda",  name:"Acibadem Токуда – прегледи",        endHour:9.0,  boost:1.1, repeat:"daily" },
  { zone:"acibadem_cardio",  name:"Acibadem Сърдечно-съдов – прегледи",endHour:9.0,  boost:1.0, repeat:"daily" },
  { zone:"acibadem_mladost", name:"Acibadem Младост – прегледи",       endHour:9.0,  boost:1.1, repeat:"daily" },
  { zone:"sv_ekaterina",     name:"Св.Екатерина – прегледи",           endHour:9.0,  boost:1.1, repeat:"daily" },
  { zone:"lozenets_h",       name:"УБ Лозенец – прегледи",             endHour:9.0,  boost:1.0, repeat:"daily" },
  { zone:"kardiologia",      name:"Кардиологична – прегледи",          endHour:9.0,  boost:1.0, repeat:"daily" },
  { zone:"sv_sofia_h",       name:"МБАЛ Св.София – прегледи",          endHour:9.0,  boost:1.0, repeat:"daily" },
  { zone:"acibadem_tokuda",  name:"Acibadem Токуда – вечерни",         endHour:18.5, boost:1.0, repeat:"daily" },
  { zone:"acibadem_mladost", name:"Acibadem Младост – вечерни",        endHour:18.5, boost:1.0, repeat:"daily" },

  // Задръствания
  { zone:"jam_orl",    name:"🚦 Задръстване СУТРИН – Орлов мост",     endHour:9.0,  boost:1.8, repeat:"mon-fri" },
  { zone:"jam_tsar",   name:"🚦 Задръстване СУТРИН – Цариградско",    endHour:9.0,  boost:2.0, repeat:"mon-fri" },
  { zone:"jam_ndk",    name:"🚦 Задръстване СУТРИН – бул.България",   endHour:9.0,  boost:1.6, repeat:"mon-fri" },
  { zone:"jam_serdika",name:"🚦 Задръстване СУТРИН – Сердика",        endHour:9.0,  boost:1.5, repeat:"mon-fri" },
  { zone:"jam_orl",    name:"🚦 Задръстване СЛЕДОБЕД – Орлов мост",   endHour:19.0, boost:2.2, repeat:"mon-fri" },
  { zone:"jam_tsar",   name:"🚦 Задръстване СЛЕДОБЕД – Цариградско",  endHour:18.5, boost:2.5, repeat:"mon-fri" },
  { zone:"jam_ndk",    name:"🚦 Задръстване СЛЕДОБЕД – бул.България", endHour:18.5, boost:2.0, repeat:"mon-fri" },
  { zone:"jam_serdika",name:"🚦 Задръстване СЛЕДОБЕД – Сердика",      endHour:18.5, boost:1.8, repeat:"mon-fri" },
];

// ═══════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════
window.demandColor = function demandColor(score, type) {
  if (type === 'hospital')
    return score>=2.0 ? {fill:"#ff2020",fillAlpha:0.75,stroke:"#ff6060",label:"🏥 Активно"}
         : score>=1.3 ? {fill:"#ef4444",fillAlpha:0.60,stroke:"#ff5555",label:"🏥"}
         :              {fill:"#991b1b",fillAlpha:0.40,stroke:"#cc3333",label:"🏥"};
  if (type === 'karyk')
    return {fill:"#f97316",fillAlpha:0.0,stroke:"transparent",label:"🥉"};
  if (score>=3.8) return {fill:"#ef4444",fillAlpha:0.62,stroke:"#ff8f8f",label:"ПИК 🔥"};
  if (score>=3.0) return {fill:"#f97316",fillAlpha:0.56,stroke:"#ffb070",label:"Висок ▲"};
  if (score>=2.4) return {fill:"#f59e0b",fillAlpha:0.52,stroke:"#ffd060",label:"Добър"};
  if (score>=1.8) return {fill:"#a3c23a",fillAlpha:0.48,stroke:"#cbe860",label:"Среден"};
  if (score>=1.2) return {fill:"#4cba52",fillAlpha:0.44,stroke:"#84e88f",label:"Нормален"};
  if (score>=0.7) return {fill:"#2fa88a",fillAlpha:0.40,stroke:"#63dcb8",label:"Слаб шанс"};
  if (score>=0.35) return {fill:"#3d8fb5",fillAlpha:0.34,stroke:"#74c4e2",label:"Минимален"};
  return               {fill:"#33415c",fillAlpha:0.15,stroke:"#4d5f80",label:"Тих"};
}

function karykColor(ks) {
  if (ks>=4.0) return {fill:"#ff6b00",stroke:"#ff9040",label:"🔥 Карък ПИК"};
  if (ks>=3.0) return {fill:"#f97316",stroke:"#ffaa55",label:"▲ Отлично"};
  if (ks>=2.0) return {fill:"#fbbf24",stroke:"#ffd060",label:"Добро"};
  if (ks>=1.0) return {fill:"#a3a300",stroke:"#d4d400",label:"Слабо"};
  return              {fill:"#1a1030",stroke:"#2a2050",label:"Избягвай"};
}

function fmtHour(h) {
  return String(Math.floor(h)).padStart(2,'0') + ':' + (h%1===0.5?'30':'00');
}

const TODAY    = new Date();
const todayStr = TODAY.toISOString().slice(0,10);
const todayDay = TODAY.getDay();

function dayMatches(ev) {
  if (ev.date    && ev.date    !== todayStr)  return false;
  if (ev.endDate && todayStr   >  ev.endDate) return false;
  const r = ev.repeat;
  if (!r || r==="daily")    return true;
  if (r==="mon-fri")        return todayDay>=1 && todayDay<=5;
  if (r==="fri-sat")        return [5,6].includes(todayDay);
  if (r==="tue-sat")        return todayDay>=2 && todayDay<=6;
  if (r==="tue-sun")        return todayDay>=2 || todayDay===0;
  if (r==="thu-sat")        return [4,5,6].includes(todayDay);
  if (r==="wed-sat")        return todayDay>=3 && todayDay<=6;
  return true;
}

function deadZoneFactor(h) {
  if (h>=20 && h<=21) {
    const m=20.5;
    return 0.42 + 0.58*Math.pow(Math.abs(h-m)/0.5, 2);
  }
  return 1.0;
}

function computeScores(hour) {
  const scores={}, activeEvents={};
  ZONES.forEach(z => { scores[z.id]=BASE[z.id]||0.3; activeEvents[z.id]=[]; });
  const dz = deadZoneFactor(hour);
  for (const ev of EVENTS) {
    if (!dayMatches(ev)) continue;
    const diff = hour - ev.endHour;
    let f = 0;
    if (diff>=-0.75 && diff<=0)   f = (diff+0.75)/0.75;
    else if (diff>0 && diff<=1.5) f = 1 - diff/1.5;
    if (f>0.05) {
      scores[ev.zone] = (scores[ev.zone]||0) + ev.boost*f*dz;
      (activeEvents[ev.zone] = activeEvents[ev.zone] || []).push({name:ev.name, f});
    }
  }
  // Weather boost
  if (weatherBoost>0) {
    ZONES.forEach(z => {
      if (['residential','residential_lux','hospital','karyk'].includes(z.type))
        scores[z.id] += weatherBoost*0.6;
      else if (['mall','hotel'].includes(z.type))
        scores[z.id] += weatherBoost*0.3;
    });
  }
  if (dz<1) ZONES.forEach(z => { if(z.id!=='airport') scores[z.id]*=(0.7+0.3*dz); });
  // Летищна вълна: излизащи полети вдигат скора на летището (силно — 10 полета≈3.6)
  try{ var _ax = window.__airportExiting|0; if(_ax>0 && scores['airport']!==undefined){ scores['airport'] += Math.min(4.0, _ax*0.36); } }catch(e){}
  return {scores, activeEvents};
}

function totalDemand(hour) {
  const {scores}=computeScores(hour);
  return Object.values(scores).reduce((a,b)=>a+b,0);
}

function computeKarykScore(zid, scores) {
  const z = ZONES.find(x=>x.id===zid);
  if (!z) return 0;
  const demand = scores[zid]||0;
  const typeBonus = {
    karyk:1.8, residential_lux:1.2, residential:1.0,
    hospital:0.8, leisure:0.5,
    university:-0.3, theatre:-0.2, venue:-0.2,
    office:-0.5, mall:-0.8, hotel:-0.8,
    airport:-1.5, transit:-0.6,
  };
  let ks = demand + (typeBonus[z.type]||0);
  if (demand<1.0) ks += 0.8;
  return Math.max(0, Math.min(5, ks));
}

// ═══════════════════════════════════════════════
// TRAFFIC JAM INFO
// ═══════════════════════════════════════════════
const TRAFFIC_INFO = {
  jam_orl:    { jamDir:'← КЪМ ЦЕНТЪРА', freeDir:'→ НАВЪН', freeArrow:'→',
                tip:'Задръстено КЪМ ЦЕНТЪРА. Ти върви → НАВЪН (свободно!)', time:'07:30–09:30 и 17:00–19:00' },
  jam_tsar:   { jamDir:'→ КЪМ ЛЕТИЩЕТО', freeDir:'← КЪМ ЦЕНТЪРА', freeArrow:'←',
                tip:'Задръстено → КЪМ ЛЕТИЩЕТО. Ти върви ← КЪМ ЦЕНТЪРА (свободно!)', time:'07:00–09:00 и 17:00–19:30' },
  jam_ndk:    { jamDir:'↑↓ ДВЕ ПОСОКИ', freeDir:'↔ СТРАНИЧНИ УЛ.', freeArrow:'↔',
                tip:'Задръстено по бул.България. Използвай странични улици!', time:'17:00–19:30 делнични' },
  jam_serdika:{ jamDir:'← КЪМ ЗАПАДА', freeDir:'→ КЪМ ИЗТОКА', freeArrow:'→',
                tip:'Задръстено ← КЪМ ЗАПАДА. Ти върви → КЪМ ИЗТОКА (свободно!)', time:'07:30–09:30 делнични' },
};

const trafficMarkers={};
function makeTrafficIcon(info,active){
  const op=active?'1':'0.35', sz=active?14:10;
  const glow=active?`0 0 8px #a855f7`:'none';
  return L.divIcon({className:'',
    html:`<div style="width:${sz}px;height:${sz}px;border-radius:50%;background:#a855f7;box-shadow:${glow};opacity:${op};${active?'animation:jam-blink 2s ease-in-out infinite':''}"></div>`,
    iconSize:[sz,sz],iconAnchor:[sz/2,sz/2]});
}

// ═══════════════════════════════════════════════
// HOSPITAL CROSS ICON
// ═══════════════════════════════════════════════
function makeHospitalIcon(score){
  const bright=score>=2.0?'#ff2020':score>=1.3?'#ef4444':'#cc2222';
  const sz=score>=2.0?26:score>=1.3?22:18;
  const glow=score>=1.3?`drop-shadow(0 0 5px ${bright})`:'none';
  return L.divIcon({className:'',
    html:`<div style="width:${sz}px;height:${sz}px;position:relative;filter:${glow}">
      <div style="position:absolute;left:50%;top:20%;transform:translateX(-50%);width:30%;height:60%;background:${bright};border-radius:2px"></div>
      <div style="position:absolute;top:50%;left:15%;transform:translateY(-50%);width:70%;height:28%;background:${bright};border-radius:2px"></div>
    </div>`,iconSize:[sz,sz],iconAnchor:[sz/2,sz/2]});
}

// ═══════════════════════════════════════════════
// KARYK SCORE ALGORITHM
// ═══════════════════════════════════════════════
const KARYK_PREFER=['hospital','residential','residential_lux','karyk','leisure'];
const KARYK_AVOID =['airport','mall','hotel','office','university','nightlife','transit','venue','theatre','cinema','traffic'];

function computeKarykScore(zid,scores){
  const z=ZONES.find(x=>x.id===zid); if(!z) return 0;
  const demand=scores[zid]||0;
  const typeBonus={
    karyk:1.8, residential_lux:1.2, residential:1.0,
    hospital:0.8, leisure:0.5,
    university:-0.3, theatre:-0.2, cinema:-0.1, venue:-0.2, nightlife:-0.2,
    office:-0.5, mall:-0.8, hotel:-0.8,
    airport:-1.5, transit:-0.6, traffic:0,
  };
  let ks=demand+(typeBonus[z.type]||0);
  if(demand<1.0) ks+=0.8;
  if(!['airport','serdika','bpark','the_mall','hotels_ctr'].includes(zid)) ks+=0.3;
  return Math.max(0,Math.min(5,ks));
}

// ═══════════════════════════════════════════════
// NOMINATIM GEOCODING (кешира за 7 дни)
// ═══════════════════════════════════════════════
const NOMINATIM_QUERIES={
  airport:'Летище София SOF Bulgaria', bpark:'Business Park Sofia Mladost Bulgaria',
  garitage:'Garitage Park Sofia Bulgaria', polygraphia:'Polygraphia Office Center Tsarigradsko 47 Sofia Bulgaria',
  capital_fort:'Capital Fort Tsarigradsko 90 Sofia Bulgaria', megapark:'Megapark Sofia Bulgaria',
  serdika:'Serdika Center Sitnyakovo Sofia Bulgaria', paradise:'Paradise Center Cherni vrah Sofia Bulgaria',
  ring_mall:'Sofia Ring Mall Okolovrasten Bulgaria', the_mall:'The Mall Sofia Tsarigradsko 115 Bulgaria',
  mall_sofia:'Mall of Sofia Stamboliyski Bulgaria', cjp:'Central Railway Station Sofia Bulgaria',
  cab_north:'Central Bus Station Sofia Bulgaria', ag_yug:'Автогара Юг Sofia Bulgaria',
  arena:'Arena Sofia 8888 Asen Yordanov Bulgaria', ndk:'National Palace Culture Sofia Bulgaria',
  pirogov:'UMBALSM Pirogov Totleben 21 Sofia Bulgaria', alexand:'UMBAL Aleksandrovska Sofia Bulgaria',
  vma:'Voenno-medicinska akademia Sofia Bulgaria', isul:'ISUL Konyovitsa 65 Sofia Bulgaria',
  acibadem_tokuda:'Acibadem Tokuda bul Nikola Vaptsarov 51B Sofia Bulgaria',
  acibadem_ortho:'Acibadem Ortopedia Okolovrasten 127 Sofia Bulgaria',
  sv_anna:'УМБАЛ Света Анна Sofia Bulgaria', nat_theatre:'Naroden teatar Ivan Vazov Sofia Bulgaria',
  opera:'Natsionalna opera i balet Sofia Bulgaria', unss:'UNSS Sofia Bulgaria',
  nbu:'Нов Български Университет Sofia Bulgaria', simenovo:'Hill Side Sofia Simeonovsko shose 97 Bulgaria',
  manast:'Manastirski livadi Sofia Bulgaria', boyana:'Boyana Sofia Bulgaria',
  kambanite:'ЖК Камбаните Sofia Bulgaria',
};

const CACHE_KEY='sofia_taxi_coords_v4', CACHE_TTL=7*24*3600*1000;

async function geocodeZones(){
  let cache={};
  try{
    const raw=localStorage.getItem(CACHE_KEY);
    if(raw){const p=JSON.parse(raw);if(Date.now()-p.ts<CACHE_TTL)cache=p.coords;}
  }catch(e){}
  const zMap={}; ZONES.forEach(z=>{zMap[z.id]=z;});
  const missing=ZONES.filter(z=>!cache[z.id]&&NOMINATIM_QUERIES[z.id]);
  if(!missing.length){applyGeoCache(cache,zMap);return;}
  const badge=document.getElementById('airport-badge');
  const orig=badge.textContent;
  let i=0;
  for(const z of missing){
    try{
      const r=await fetch(`https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(NOMINATIM_QUERIES[z.id])}`,
        {headers:{'User-Agent':'SofiaTaxiDemand/1.0'}});
      const d=await r.json();
      if(d&&d[0]) cache[z.id]={lat:parseFloat(d[0].lat),lng:parseFloat(d[0].lon)};
    }catch(e){}
    badge.textContent=`📡 ${++i}/${missing.length}`;
    await new Promise(r=>setTimeout(r,1100));
  }
  try{localStorage.setItem(CACHE_KEY,JSON.stringify({ts:Date.now(),coords:cache}));}catch(e){}
  badge.textContent=orig;
  applyGeoCache(cache,zMap);
}

function applyGeoCache(cache,zMap){
  let n=0;
  for(const[id,coords]of Object.entries(cache)){
    if(zMap[id]&&coords){zMap[id].lat=coords.lat;zMap[id].lng=coords.lng;n++;}
  }
  if(n>0){
    ZONES.forEach(z=>{circleMap[z.id]?.setLatLng?.([z.lat,z.lng]);});
    Object.values(hospitalMarkers).forEach(({marker,circle},id)=>{
      const z=ZONES.find(x=>x.id===id); if(!z) return;
      marker?.setLatLng([z.lat,z.lng]); circle?.setLatLng([z.lat,z.lng]);
    });
    render(currentHour);
  }
}

// ═══════════════════════════════════════════════
// NEXT 90 MINUTES PANEL
// ═══════════════════════════════════════════════
let next90Open=false;
document.getElementById('next90-btn')?.addEventListener('click',()=>{
  next90Open=!next90Open;
  document.getElementById('next90-btn').classList.toggle('active',next90Open);
  const panel=document.getElementById('next90-panel');
  if(next90Open){buildNext90();panel.style.display='block';}
  else panel.style.display='none';
});
window.closeNext90=function(){
  next90Open=false;
  document.getElementById('next90-btn')?.classList.remove('active');
  document.getElementById('next90-panel').style.display='none';
};

function buildNext90(){
  const h=currentHour; // следва slider-а
  const end=Math.min(24,h+1.5);
  const zMap={}; ZONES.forEach(z=>{zMap[z.id]=z;});
  const upcoming=EVENTS.filter(ev=>dayMatches(ev)&&!ev._fromFlight)
    .filter(ev=>ev.endHour>h&&ev.endHour<=end)
    .sort((a,b)=>a.endHour-b.endHour);
  const list=document.getElementById('next90-list');
  if(!list) return;
  if(!upcoming.length){
    list.innerHTML='<div style="padding:14px;color:var(--muted);font-size:15px">Няма значими events в следващите 90 мин</div>';
    return;
  }
  list.innerHTML=upcoming.map(ev=>{
    const z=zMap[ev.zone]; if(!z) return '';
    const min=Math.round((ev.endHour-h)*60);
    const c=demandColor(ev.boost,z.type);
    return `<div class="n90-item">
      <div class="n90-time">${fmtHour(ev.endHour)}</div>
      <div class="n90-icon">${z.icon}</div>
      <div class="n90-info">
        <div class="n90-name">${ev.name}</div>
        <div class="n90-zone">${z.name.split('(')[0].trim()} · след ${min} мин</div>
      </div>
      <div class="n90-score" style="color:${c.fill}">+${ev.boost.toFixed(1)}</div>
    </div>`;
  }).join('');
}

// ═══════════════════════════════════════════════
const map = L.map('map', {center:[42.698,23.322], zoom:13, zoomControl:true, attributionControl:false});
L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
  maxZoom:19, subdomains:['a','b','c','d']
}).addTo(map);
document.getElementById('map').style.filter='brightness(0.85) saturate(0.6)';
setTimeout(()=>map.invalidateSize(), 300);
setTimeout(()=>map.invalidateSize(), 800);

const circleMap={}, hospitalMarkers={};

function makeHospitalIcon(score) {
  const bright = score>=2.0?'#ff2020':score>=1.3?'#ef4444':'#cc2222';
  const sz = score>=2.0?26:score>=1.3?22:18;
  const glow = score>=1.3?`drop-shadow(0 0 5px ${bright})`:'none';
  return L.divIcon({
    className:'',
    html:`<div style="width:${sz}px;height:${sz}px;position:relative;filter:${glow}">
      <div style="position:absolute;left:50%;top:20%;transform:translateX(-50%);width:30%;height:60%;background:${bright};border-radius:2px"></div>
      <div style="position:absolute;top:50%;left:15%;transform:translateY(-50%);width:70%;height:28%;background:${bright};border-radius:2px"></div>
    </div>`,
    iconSize:[sz,sz], iconAnchor:[sz/2,sz/2],
  });
}

function buildCircles() {
  ZONES.forEach(z => {
    if (z.type==='traffic') {
      const info=TRAFFIC_INFO[z.id];
      if(info){
        const m=L.marker([z.lat,z.lng],{icon:makeTrafficIcon(info,false),zIndexOffset:600}).addTo(map);
        m.on('click',()=>showZonePopup(z.id));
        trafficMarkers[z.id]=m; circleMap[z.id]=m;
      }
      return;
    }
    if (z.type==='karyk') {
      const c=L.circle([z.lat,z.lng],{radius:z.radius,fillOpacity:0,opacity:0,weight:0});
      c.on('click',()=>z.type==='airport'?showAirportSchedule():z.type==='transit'?showTransitPopup(z.id):showZonePopup(z.id)); c.addTo(map); circleMap[z.id]=c;
      return;
    }
    if (z.type==='hospital') {
      const hm=L.marker([z.lat,z.lng],{icon:makeHospitalIcon(BASE[z.id]||0.5),zIndexOffset:400}).addTo(map);
      hm.on('click',()=>showZonePopup(z.id));
      const hc=L.circle([z.lat,z.lng],{radius:z.radius,color:'#991b1b',fillColor:'#991b1b',fillOpacity:0.12,weight:1}).addTo(map);
      hc.on('click',()=>showZonePopup(z.id));
      hospitalMarkers[z.id]={marker:hm,circle:hc};
      circleMap[z.id]={setStyle:(o)=>hc.setStyle({fillColor:o.fillColor||'#991b1b',fillOpacity:o.fillOpacity||0.12,color:o.color||'#cc2222'}),_hm:hm,_hc:hc};
      return;
    }
    const c=L.circle([z.lat,z.lng],{radius:z.radius,...getScoreStyle(BASE[z.id]||0.3,z.type)});
    c.on('click',()=>z.type==='airport'?showAirportSchedule():z.type==='transit'?showTransitPopup(z.id):showZonePopup(z.id)); c.addTo(map); circleMap[z.id]=c;
  });
}

function getScoreStyle(score, type) {
  const c=demandColor(score,type);
  return {color:c.stroke, fillColor:c.fill, fillOpacity:c.fillAlpha, weight:1.5, opacity:0.85};
}

function updateCircles() {
  const {scores}=computeScores(currentHour); if(window.__applyLive)window.__applyLive(scores);
  ZONES.forEach(z => {
    const s=scores[z.id]||0;
    if (z.type==='traffic') {
      const info=TRAFFIC_INFO[z.id];
      const marker=trafficMarkers[z.id];
      if(marker&&info) marker.setIcon(makeTrafficIcon(info,s>=1.5));
      return;
    }
    if (z.type==='hospital') {
      const cm=circleMap[z.id];
      if(cm?._hm) cm._hm.setIcon(makeHospitalIcon(s));
      cm?.setStyle(getScoreStyle(s,z.type));
      return;
    }
    if (z.type==='karyk') {
      if (karykMode) {
        const ks=computeKarykScore(z.id,scores);
        const kc=karykColor(ks);
        circleMap[z.id]?.setStyle({color:kc.stroke,fillColor:kc.fill,fillOpacity:ks>=1?0.6:0.1,weight:2,opacity:ks>=1?0.9:0.2});
      } else {
        circleMap[z.id]?.setStyle({fillOpacity:0,opacity:0,weight:0});
      }
      return;
    }
    if (karykMode) {
      const ks=computeKarykScore(z.id,scores);
      const kc=karykColor(ks);
      circleMap[z.id]?.setStyle({color:kc.stroke,fillColor:kc.fill,fillOpacity:Math.max(0.08,0.1+ks*0.08),weight:ks>=3?2:1,opacity:ks>=2?0.8:0.3});
      return;
    }
    circleMap[z.id]?.setStyle(getScoreStyle(s,z.type));
  });
}


// (дублираната bus система е премахната — виж BUS SCHEDULE по-долу)
function showTransitPopup(zid){
  const z = ZONES.find(x=>x.id===zid);
  if(!z) return;

  const fmt = (h,m) => String(h).padStart(2,'0')+':'+String(m).padStart(2,'0');

  let html = '<div style="font-size:14px;max-height:60vh;overflow-y:auto">';
  html += `<div style="font-weight:800;font-size:15px;margin-bottom:10px;color:var(--cyan)">${z.icon||'🚌'} ${z.name}</div>`;

  // Plovdiv buses arriving at Central Autogara (cab_north)
  if(zid === 'cab_north'){
    const arrivals = getSofiaArrivals(12);
    if(arrivals.length){
      html += '<div style="font-size:12px;font-weight:800;color:var(--muted);letter-spacing:.6px;margin-bottom:8px">🚌 ПРИСТИГАЩИ НА ЦЕНТРАЛНА АВТОГАРА</div>';
      arrivals.forEach(b=>{
        const untilArr = b.arrMin - b.nowMin; // минути до пристигане
        const isSoon = untilArr>=-5 && untilArr<=40;
        const bg = isSoon?'rgba(239,68,68,.1)':'transparent';
        const col = untilArr<=0?'var(--muted)':untilArr<=40?'#ef4444':untilArr<=90?'var(--amber)':'var(--muted)';
        const label = untilArr<=0?`пристигнал ~${b.arrTime}`:
                      untilArr<=90?`~${b.arrTime} · след ${untilArr} мин`:
                      `~${b.arrTime}`;
        const origin = b.route.name.replace(' → София','');
        html += `<div style="padding:6px 8px;border-radius:7px;background:${bg};margin-bottom:3px;display:flex;justify-content:space-between;gap:8px">
          <span style="font-weight:800;color:var(--text)">${origin} <span style="font-weight:400;color:var(--muted);font-size:11px">(${b.dep}${b.route.approx?' ≈':''})</span></span>
          <span style="font-size:12px;color:${col};text-align:right;white-space:nowrap">${label}</span>
        </div>`;
      });
    } else {
      html += '<div style="color:var(--muted);padding:8px">Няма пристигащи в следващите часове / зареждане…</div>';
    }
    html += '<div style="font-size:11px;color:var(--muted);margin-top:8px;padding-top:6px;border-top:1px solid var(--border)">≈ разписание по модел на превозвача (Пловдив — точно). Сортирано по час на пристигане.</div>';
  }

  // Expo Center bus stop
  if(zid === 'iec' || zid === 'expo2000'){
    // Автобуси по Тракия, минаващи през Expo/Цариградско, по route stops offset
    const data = busSchedule;
    const now = new Date();
    const nowMin = now.getHours()*60 + now.getMinutes();
    const rows = [];
    for(const route of (data?.routes||[])){
      const expo = (route.stops||[]).find(s=>s.name.includes('Expo'));
      if(!expo || !route.to || !route.to.includes('Централна автогара София')) continue;
      for(const dep of route.departures){
        const [h,m] = dep.split(':').map(Number);
        const atExpo = h*60+m+(expo.offset_min||0);
        let delta = atExpo - nowMin;
        if(delta < -10) continue;
        if(delta > 240) continue;
        rows.push({route, dep, atExpo, delta});
      }
    }
    rows.sort((a,b)=>a.atExpo-b.atExpo);
    if(rows.length){
      html += '<div style="font-size:12px;font-weight:800;color:var(--muted);letter-spacing:.6px;margin-bottom:8px">🚌 Минаващи през Expo/Цариградско</div>';
      rows.slice(0,6).forEach(b=>{
        const t = `${String(Math.floor((b.atExpo%1440)/60)).padStart(2,'0')}:${String(b.atExpo%60).padStart(2,'0')}`;
        const origin = (b.route.name||'').replace(' → София','');
        const col = b.delta<40?'#ef4444':'var(--amber)';
        html += `<div style="padding:6px 8px;border-radius:7px;margin-bottom:3px;display:flex;justify-content:space-between">
          <span>${origin} <span style="color:var(--muted);font-size:11px">${b.dep}${b.route.approx?' ≈':''}</span></span>
          <span style="font-weight:800;color:${col}">~${t}</span>
        </div>`;
      });
    }
  }

  // Generic transit info
  if(!['cab_north','iec','expo2000'].includes(zid)){
    html += '<div style="color:var(--muted);padding:8px 0">Транспортен хъб.</div>';
  }

  html += '</div>';

  L.popup({maxWidth:Math.min(340,window.innerWidth-30), className:'transit-popup'})
    .setLatLng([z.lat, z.lng])
    .setContent(html)
    .openOn(map);
}

// ═══ AIRPORT SCHEDULE POPUP ═══
function showAirportSchedule() {
  const now = new Date();
  const nowMin = ((now.getUTCHours()+3)%24)*60 + now.getUTCMinutes();

  const fmt = (h,m) => String(h).padStart(2,'0')+':'+String(m).padStart(2,'0');
  const flag = f => f.nonSchengen ? '🛂' : '🇪🇺';

  // Всички полети по абсолютно време (кешът носи датата — никакви среднощни трикове)
  const nowTs = Date.now();
  const all = [...flightDetails]
    .filter(f=>f.exitFromTs)
    .sort((a,b)=>a.exitFromTs-b.exitFromTs);

  // Крие излезли преди >2ч; класифицира останалите
  const visible = [];
  all.forEach(f=>{
    if(f.exitToTs < nowTs - 120*60000) return;      // >2ч назад — вън
    const graceTs = f.exitToTs + 15*60000; // грейс: все още може да излизат
    f._state = (nowTs >= f.exitFromTs && nowTs <= graceTs) ? 'now'
             : (f.exitToTs < nowTs) ? 'done' : 'future';
    visible.push(f);
  });

  let html='<div style="font-size:14px">';
  html+='<div style="font-weight:800;font-size:15px;margin-bottom:8px;color:var(--cyan)">✈️ Излизане на пасажери — СОФ</div>';

  const nowCount = visible.filter(f=>f._state==='now').length;
  if(nowCount){
    html+=`<div style="background:rgba(239,68,68,.14);border:1px solid #ef4444;border-radius:8px;padding:6px 10px;margin-bottom:8px;font-weight:800;color:#ef4444;font-size:13px">🔴 В момента излизат: ${nowCount} полет${nowCount===1?'':'а'}</div>`;
  } else {
    const next = visible.find(f=>f._state==='future');
    if(next){
      html+=`<div style="background:rgba(2,132,199,.1);border:1px solid var(--cyan);border-radius:8px;padding:6px 10px;margin-bottom:8px;font-size:13px;color:var(--cyan)"><b>Следващ: ${fmt(next.exitFromH,next.exitFromM)}</b> · ${next.fn} от ${(next.depAirport||'').slice(0,18)} ${flag(next)}</div>`;
    } else if(visible.length===0){
      if(airportStatus==='fallback'){
        html+='<div style="color:#f59e0b;padding:10px 0;text-align:center;font-size:12px">⚠️ Няма живи полетни данни — прогнозен режим</div>';
      } else {
        html+='<div style="color:var(--muted);padding:16px 0;text-align:center">Няма повече полети в кеша за днес</div>';
      }
    }
  }

  // Скролируем списък: терминали → часове → полети
  // ═ Терминал табове (изборът се помни) ═
  let flTerm = 'all';
  try{ flTerm = localStorage.getItem('bak_fl_term') || 'all'; }catch(e){}
  if(flTerm!=='all' && !visible.some(f=>f.term===flTerm)) flTerm='all';
  window.__setFlTerm = t => { try{ localStorage.setItem('bak_fl_term', t); }catch(e){} showAirportSchedule(); };
  const cnt = t => visible.filter(f=>f.term===t).length;
  const tabs = [['all','Всички',visible.length],['2','Т2',cnt('2')],['1','Т1',cnt('1')]];
  html+='<div style="display:flex;gap:6px;margin-bottom:8px">';
  tabs.forEach(([id,label,n])=>{
    const on = flTerm===id;
    html+=`<button onclick="window.__setFlTerm('${id}')" style="flex:1;padding:7px 4px;border-radius:9px;font-weight:900;font-size:13px;cursor:pointer;border:1px solid ${on?'var(--cyan)':'var(--border)'};background:${on?'rgba(2,132,199,.18)':'transparent'};color:${on?'var(--cyan)':'var(--muted)'}">${label} <span style="font-weight:700;font-size:11px">${n}</span></button>`;
  });
  html+='</div>';

  const shownList = flTerm==='all' ? visible : visible.filter(f=>f.term===flTerm);
  const nowCnt = shownList.filter(f=>f._state==='now').length;
  try{ window.__airportExiting = visible.filter(f=>f._state==='now').length; }catch(e){}
  html+='<div style="display:flex;align-items:center;gap:8px;padding:8px 10px;margin-bottom:8px;border-radius:10px;'
    +'background:'+(nowCnt?'rgba(239,68,68,.18)':'rgba(255,255,255,.04)')+';'
    +'border:1px solid '+(nowCnt?'#ef4444':'var(--border)')+'">'
    +'<span style="font-size:20px">🔴</span>'
    +'<span style="font-weight:900;font-size:16px;color:'+(nowCnt?'#ef4444':'var(--muted)')+'">'
    +(nowCnt?('Сега излизат: '+nowCnt+' полет'+(nowCnt===1?'':'а')):'Няма излизащи в момента')
    +'</span></div>';
  html+='<div id="fl-scroll" style="max-height:48vh;overflow-y:auto;-webkit-overflow-scrolling:touch;padding-right:2px">';
  let anchorSet = false;
  {
    const grp = shownList;
    let lastHour = -1;
    grp.forEach(f=>{
      if(f.exitFromH !== lastHour){
        lastHour = f.exitFromH;
        html+=`<div style="font-size:11px;font-weight:800;color:var(--muted);margin:7px 0 3px;padding-left:4px">— ${String(lastHour).padStart(2,'0')}:00 —</div>`;
      }
      const isNow  = f._state==='now';
      const isDone = f._state==='done';
      const bg  = isNow ? 'rgba(239,68,68,.16)' : 'transparent';
      const brd = isNow ? '1px solid #ef4444'    : '1px solid transparent';
      const col = isNow ? '#ef4444' : isDone ? 'var(--muted)' : 'var(--amber)';
      const op  = isDone ? 'opacity:.45;' : '';
      const anchor = (!anchorSet && (isNow || f._state==='future')) ? (anchorSet=true, ' id="fl-now-anchor"') : '';
      html+=`<div${anchor} style="display:flex;align-items:center;gap:6px;padding:6px 8px;border-radius:8px;background:${bg};border:${brd};margin-bottom:2px;${op}">
        <span style="font-weight:800;font-size:16px;min-width:48px;color:var(--text)">${f.fn}</span>
        ${flTerm==='all'?`<span style="font-size:12px;font-weight:900;color:var(--cyan);border:1px solid var(--border);border-radius:5px;padding:1px 5px">${'Т'+f.term}</span>`:''}
        <span style="flex:1;font-size:14px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${(f.depAirport||'').slice(0,22)}</span>
        <span style="font-size:13px">${flag(f)}</span>
        ${isNow?'<span style="font-size:12px;font-weight:900;color:#ef4444;white-space:nowrap">ИЗЛИЗАТ</span>':''}
        <span style="font-weight:800;font-size:15px;color:${col};white-space:nowrap">${fmt(f.exitFromH,f.exitFromM)}–${fmt(f.exitToH,f.exitToM)}</span>
      </div>`;
    });
    if(!grp.length) html+='<div style="color:var(--muted);text-align:center;padding:14px 0;font-size:13px">Няма полети за този терминал</div>';
  }
  html+='</div>';

  html+='<div style="font-size:11px;color:var(--muted);margin-top:8px;padding-top:8px;border-top:1px solid var(--border)">🇪🇺 Шенген: +5–15 мин &nbsp;|&nbsp; 🛂 Извън Шенген: +10–30 мин &nbsp;|&nbsp; 🔴 = излизат сега</div>';
  html+='</div>';

  const airportZone=ZONES.find(z=>z.id==='airport');
  if(airportZone){
    L.popup({maxWidth:Math.min(340,window.innerWidth-30),maxHeight:Math.min(420,window.innerHeight*0.6),className:'airport-popup',autoPan:true})
      .setLatLng([airportZone.lat,airportZone.lng])
      .setContent(html)
      .openOn(map);
    setTimeout(()=>{
      const box=document.getElementById('fl-scroll'), el=document.getElementById('fl-now-anchor');
      if(box && el) box.scrollTop = Math.max(0, el.offsetTop - box.offsetTop - 34);
    }, 120);
  }
}

function showZonePopup(zid) {
  const z=ZONES.find(x=>x.id===zid); if(!z) return;
  const {scores,activeEvents}=computeScores(currentHour); if(window.__applyLive)window.__applyLive(scores);
  const s=scores[zid]||0;
  const isTraffic=z.type==='traffic';
  const ti=TRAFFIC_INFO[zid];
  let c, label, evHtml;
  if (karykMode&&!isTraffic) {
    const ks=computeKarykScore(zid,scores);
    c=karykColor(ks); label=`К:${ks.toFixed(1)} ${c.label}`;
  } else {
    c=demandColor(s,z.type); label=c.label;
  }
  if (isTraffic&&ti) {
    const active=s>=1.5;
    const sc=active?'#ef4444':'#22c55e';
    evHtml=`<div style="background:${active?'#1a0808':'#081a0d'};border:1px solid ${sc};border-radius:5px;padding:5px 8px;margin-bottom:5px;color:${sc};font-size:15px;font-weight:600">${active?'🔴 ЗАДРЪСТЕНО СЕГА':'🟢 В МОМЕНТА СВОБОДНО'}</div>
      <div style="font-size:15px;color:#a855f7;margin-bottom:3px">🚦 ${ti.jamDir}</div>
      <div style="font-size:15px;color:#00e5ff;margin-bottom:5px">✅ Свободно: ${ti.freeDir}</div>
      ${active?`<div style="background:#1a0a2e;border:1px solid #a855f7;border-radius:5px;padding:5px 8px;font-size:15px;color:#d08dff;margin-bottom:4px">💡 Карай ${ti.freeArrow} обратно — стигаш по-бързо!</div>`:''}
      <div style="font-size:14px;color:#4a6080">⏰ Пик: ${ti.time}</div>`;
  } else {
    const evs=(activeEvents[zid]||[]).slice(0,3);
    evHtml=evs.length?evs.map(e=>`<div>• ${e.name}</div>`).join(''):'<div style="color:#4a6080">Базово търсене</div>';
  }
  const pct=Math.min(100,(s/4.5)*100);
  L.popup({maxWidth:240}).setLatLng([z.lat,z.lng]).setContent(`
    <div style="font-family:'Share Tech Mono',monospace;font-size:16px;color:#00e5ff;margin-bottom:5px">${z.icon} ${z.name}</div>
    <div style="font-size:18px;font-weight:bold;color:${c.fill};margin-bottom:4px">${s.toFixed(1)} <span style="font-size:15px">${label}</span></div>
    <div style="height:4px;background:#182d47;border-radius:2px;margin:5px 0"><div style="width:${pct}%;height:100%;background:${c.fill};border-radius:2px"></div></div>
    <div style="font-size:15px;color:#c8daf0;margin:6px 0">${evHtml}</div>
    ${!isTraffic?`<button onclick="startNav('${zid}')" style="width:100%;background:#00e5ff;color:#000;border:none;border-radius:4px;padding:5px;font-size:15px;cursor:pointer;margin-top:4px">🧭 Навигирай</button>
    <div style="display:flex;gap:5px;margin-top:5px">
      <a href="https://waze.com/ul?q=${encodeURIComponent(z.wazeName||z.name)}&navigate=yes" target="_blank"
         style="flex:1;text-align:center;font-size:14px;color:#00e5ff;padding:4px;background:#0d1929;border:1px solid #182d47;border-radius:4px;text-decoration:none">🚗 Waze</a>
      <a href="https://www.google.com/maps?q=${z.lat},${z.lng}" target="_blank"
         style="flex:1;text-align:center;font-size:14px;color:#4a6080;padding:4px;background:#0d1929;border:1px solid #182d47;border-radius:4px;text-decoration:none">📍 Google</a>
    </div>`:''}
  `).openOn(map);
}
window.startNav=function(zid){
  const z=ZONES.find(x=>x.id===zid); if(!z) return;
  navTarget=z; map.closePopup();
  window.open(`https://waze.com/ul?q=${encodeURIComponent(z.wazeName||z.name)}&navigate=yes`,'_blank');
};

// ═══════════════════════════════════════════════
// SPARKLINE
// ═══════════════════════════════════════════════
const canvas=document.getElementById('demand-canvas');
const ctx=canvas.getContext('2d');
const MIN_H=6, MAX_H=24, STEPS=72;

function buildCurve() {
  demandCurve=[];
  for(let i=0;i<=STEPS;i++) demandCurve.push(totalDemand(MIN_H+(i/STEPS)*(MAX_H-MIN_H)));
}

function drawSparkline(h) {
  const dpr=window.devicePixelRatio||1;
  const W=Math.max(canvas.offsetWidth,canvas.parentElement?.offsetWidth||300);
  const H=40;
  canvas.width=W*dpr; canvas.height=H*dpr; ctx.scale(dpr,dpr);
  if(!demandCurve.length) return;
  const maxD=Math.max(...demandCurve), minD=Math.min(...demandCurve)*0.85;
  const xOf=i=>(i/STEPS)*W;
  const yOf=v=>H-3-((v-minD)/(maxD-minD))*(H-8);
  // Dead zone shade
  const x20=((20-MIN_H)/(MAX_H-MIN_H))*W;
  const x21=((21-MIN_H)/(MAX_H-MIN_H))*W;
  ctx.fillStyle='rgba(239,68,68,0.08)'; ctx.fillRect(x20,0,x21-x20,H);
  // Red bands for airport exit windows
  if(flightDetails && flightDetails.length) {
    flightDetails.forEach(f=>{
      const x1=((f.exitFromH + f.exitFromM/60 - MIN_H)/(MAX_H-MIN_H))*W;
      const x2=((f.exitToH   + f.exitToM/60   - MIN_H)/(MAX_H-MIN_H))*W;
      if(x2>0 && x1<W) {
        ctx.fillStyle='rgba(239,68,68,0.18)';
        ctx.fillRect(Math.max(0,x1),0,Math.min(W,x2)-Math.max(0,x1),H);
      }
    });
  }
  // Fill
  const grad=ctx.createLinearGradient(0,0,0,H);
  grad.addColorStop(0,'rgba(239,68,68,0.28)');
  grad.addColorStop(0.5,'rgba(245,158,11,0.14)');
  grad.addColorStop(1,'rgba(34,197,94,0.02)');
  ctx.beginPath(); ctx.moveTo(xOf(0),yOf(demandCurve[0]));
  for(let i=1;i<=STEPS;i++) ctx.lineTo(xOf(i),yOf(demandCurve[i]));
  ctx.lineTo(W,H); ctx.lineTo(0,H); ctx.closePath();
  ctx.fillStyle=grad; ctx.fill();
  ctx.beginPath(); ctx.moveTo(xOf(0),yOf(demandCurve[0]));
  for(let i=1;i<=STEPS;i++) ctx.lineTo(xOf(i),yOf(demandCurve[i]));
  ctx.strokeStyle='#f59e0b99'; ctx.lineWidth=1.5; ctx.stroke();
  // Cursor
  const cx=((h-MIN_H)/(MAX_H-MIN_H))*W;
  ctx.beginPath(); ctx.moveTo(cx,0); ctx.lineTo(cx,H);
  ctx.strokeStyle='#00e5ff'; ctx.lineWidth=1.5; ctx.setLineDash([3,3]); ctx.stroke(); ctx.setLineDash([]);
  const ci=Math.round(((h-MIN_H)/(MAX_H-MIN_H))*STEPS);
  ctx.beginPath(); ctx.arc(cx,yOf(demandCurve[Math.min(ci,STEPS)]),4,0,Math.PI*2);
  ctx.fillStyle='#00e5ff'; ctx.fill();
}

// ═══════════════════════════════════════════════
// RENDER
// ═══════════════════════════════════════════════
function render(hour) {
  const {scores,activeEvents}=computeScores(hour); if(window.__applyLive)window.__applyLive(scores);
  const dead=hour>=19.8&&hour<=21.2;
  document.getElementById('tl-dead').style.display=dead?'inline':'none';
  updateCircles();
  drawSparkline(hour);
  // Sidebar
  const sorted=Object.entries(scores).sort((a,b)=>b[1]-a[1]);
  const top=sorted[0];
  const tz=ZONES.find(z=>z.id===top[0]);
  document.getElementById('tl-hint').textContent=
    dead?'— мъртва зона, почини':`Топ: ${tz?.icon||''} ${tz?.name||top[0]} (${top[1].toFixed(1)})`;
  const zList=document.getElementById('zone-list');
  if (zList && !karykMode) {
    zList.innerHTML=sorted
      .filter(([zid])=>{ const z=ZONES.find(x=>x.id===zid); return z&&z.type!=='karyk'; })
      .map(([zid,score])=>{
        const z=ZONES.find(x=>x.id===zid); if(!z) return '';
        const c=demandColor(score,z.type);
        const sub=(activeEvents[zid]||[])[0]?.name||'';
        return `<div class="zone-item" onclick="(function(){if(document.body.classList.contains('list-view'))toggleMapView();setTimeout(()=>{window.__focusZone(${z.lat},${z.lng},'${zid}'==='airport'?14:15);'${zid}'==='airport'?showAirportSchedule():showZonePopup('${zid}');},150);})()">
          <div class="zone-dot" style="background:${c.fill}"></div>
          <div style="flex:1;min-width:0">
            <div class="zone-name">${z.icon} ${z.name}</div>
            ${sub?`<div class="zone-sub">${sub}</div>`:''}
          </div>
          <div style="text-align:right">
            <div class="zone-score" style="color:${c.fill};font-size:16px;font-weight:800">${score.toFixed(1)}</div>
            <div style="font-size:11px;color:${c.fill}">${c.label}</div>
          </div>
        </div>`;
      }).join('');
  }
  const kList=document.getElementById('karyk-list');
  if (kList && karykMode) {
    const ranked=ZONES
      .filter(z=>z.type!=='hospital')
      .map(z=>({z,ks:computeKarykScore(z.id,scores),ev:(activeEvents[z.id]||[])[0]?.name||''}))
      .filter(({ks})=>ks>=1.0)
      .sort((a,b)=>b.ks-a.ks).slice(0,20);
    kList.innerHTML=ranked.map(({z,ks,ev},i)=>{
      const c=karykColor(ks);
      const reason=ev||(z.type==='karyk'?'Тих квартал':z.type==='residential_lux'?'Луксозен жк':'');
      return `<div class="karyk-item" onclick="(function(){if(document.body.classList.contains('list-view'))toggleMapView();setTimeout(function(){map.invalidateSize();map.setView([${z.lat},${z.lng}],15);showZonePopup('${z.id}');},200);})()">
        <div class="karyk-rank" style="color:${c.fill}">#${i+1}</div>
        <div class="karyk-dot" style="background:${c.fill}"></div>
        <div style="flex:1;min-width:0">
          <div class="karyk-name">${z.icon} ${z.name.split('(')[0].trim()}</div>
          <div class="karyk-sub">${c.label}${reason?' · '+reason:''}</div>
        </div>
        <div style="text-align:right">
          <div class="karyk-score" style="color:${c.fill}">К:${ks.toFixed(1)}</div>
          <div style="font-size:14px;color:#5a3a10">↑${scores[z.id]?.toFixed(1)||'0.0'}</div>
        </div>
      </div>`;
    }).join('');
  }
}

// ═══════════════════════════════════════════════
// GPS
// ═══════════════════════════════════════════════
function deg2rad(d){return d*Math.PI/180;}
function haversine(lat1,lng1,lat2,lng2){
  const R=6371000,dLat=deg2rad(lat2-lat1),dLng=deg2rad(lng2-lng1);
  const a=Math.sin(dLat/2)**2+Math.cos(deg2rad(lat1))*Math.cos(deg2rad(lat2))*Math.sin(dLng/2)**2;
  return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
}
function bearing(lat1,lng1,lat2,lng2){
  const dLng=deg2rad(lng2-lng1);
  const y=Math.sin(dLng)*Math.cos(deg2rad(lat2));
  const x=Math.cos(deg2rad(lat1))*Math.sin(deg2rad(lat2))-Math.sin(deg2rad(lat1))*Math.cos(deg2rad(lat2))*Math.cos(dLng);
  return (Math.atan2(y,x)*180/Math.PI+360)%360;
}
const ARROWS=['⬆️','↗️','➡️','↘️','⬇️','↙️','⬅️','↖️'];
const DIRS  =['С','СИ','И','ЮИ','Ю','ЮЗ','З','СЗ'];

if(window.DeviceOrientationEvent){
  window.addEventListener('deviceorientationabsolute',e=>{deviceHeading=e.alpha;},true);
  window.addEventListener('deviceorientation',e=>{if(e.webkitCompassHeading)deviceHeading=e.webkitCompassHeading;},true);
}

function updateDirectionHint(scores) {
  if(userLat===null||dirHintSuppressed) return;
  let best=null,bestW=Infinity;
  ZONES.forEach(z=>{
    const s=scores[z.id]||0; if(s<1.3) return;
    const d=haversine(userLat,userLng,z.lat,z.lng);
    const w=d/(s*s);
    if(w<bestW){bestW=w;best=z;}
  });
  const panel=document.getElementById('direction-hint');
  if(!best){panel.style.display='none';return;}
  if(best.id===dirHintZid&&panel.style.display!=='none') return;
  dirHintZid=best.id;
  const {scores:sc}=computeScores(currentHour);
  const bs=sc[best.id]||0;
  const dist=haversine(userLat,userLng,best.lat,best.lng);
  const bear=bearing(userLat,userLng,best.lat,best.lng);
  let relBear=bear;
  if(deviceHeading!==null) relBear=(bear-deviceHeading+360)%360;
  const c=demandColor(bs,best.type);
  const distTxt=dist<1000?`${Math.round(dist)} м`:`${(dist/1000).toFixed(1)} км`;
  document.getElementById('dh-arrow').textContent=ARROWS[Math.round(relBear/45)%8];
  document.getElementById('dh-name').textContent=`${best.icon} ${best.name}`;
  document.getElementById('dh-addr').textContent=`\u{1F697} Карай ${DIRS[Math.round(bear/45)%8]} · ${distTxt} · скор ${bs.toFixed(1)}`;
  document.getElementById('dh-score').textContent=bs.toFixed(1);
  document.getElementById('dh-score').style.color=c.fill;
  panel.style.display='block';
  panel.style.borderTopColor=c.fill;
  if(window._dirLine) map.removeLayer(window._dirLine);
  window._dirLine=L.polyline([[userLat,userLng],[best.lat,best.lng]],{color:c.fill,weight:2,dashArray:'6,4',opacity:0.9}).addTo(map);
}

function startGPS(){
  const btn=document.getElementById('gps-btn');
  btn.classList.add('active');
  if(!navigator.geolocation){return;}
  if(watchId) return;
  document.getElementById('direction-hint').style.display='block';
  document.getElementById('dh-name').textContent='🛰 Изчакай GPS…';
  document.getElementById('dh-arrow').textContent='📡';
  watchId=navigator.geolocation.watchPosition(pos=>{
    userLat=pos.coords.latitude; userLng=pos.coords.longitude;
    if(!userMarker){
      const icon=L.divIcon({className:'',
        html:`<div style="position:relative;width:24px;height:24px">
          <div style="position:absolute;inset:0;border-radius:50%;background:rgba(0,229,255,.2);animation:pulse-ring 3s ease-out infinite"></div>
          <div style="position:absolute;inset:5px;border-radius:50%;background:#00e5ff;border:2px solid #fff;box-shadow:0 0 8px #00e5ff"></div>
        </div>`,iconSize:[24,24],iconAnchor:[12,12]});
      userMarker=L.marker([userLat,userLng],{icon,zIndexOffset:1000}).addTo(map);
      map.setView([userLat,userLng],14);
    } else {
      userMarker.setLatLng([userLat,userLng]);
    }
    // Update airport badge to show GPS is active
    document.getElementById('gps-btn').title=`📍 ${userLat.toFixed(4)}, ${userLng.toFixed(4)}`;
    const {scores}=computeScores(currentHour); if(window.__applyLive)window.__applyLive(scores);
    updateDirectionHint(scores);
  },()=>{btn.classList.remove('active');},{enableHighAccuracy:true,maximumAge:5000,timeout:15000});
}

document.getElementById('gps-btn').addEventListener('click',()=>{
  if(watchId){
    navigator.geolocation.clearWatch(watchId); watchId=null;
    document.getElementById('gps-btn').classList.remove('active');
    if(userMarker){map.removeLayer(userMarker);userMarker=null;}
    if(window._dirLine){map.removeLayer(window._dirLine);window._dirLine=null;}
    document.getElementById('direction-hint').style.display='none';
    userLat=null; userLng=null;
  } else { startGPS(); }
});
document.getElementById('direction-hint').querySelector('.dh-close').addEventListener('click',()=>{
  dirHintSuppressed=true;
  document.getElementById('direction-hint').style.display='none';
});

// ═══════════════════════════════════════════════
// FULLSCREEN
// ═══════════════════════════════════════════════
let isFullscreen=false;
document.getElementById('fs-btn').addEventListener('click',()=>{
  isFullscreen=!isFullscreen;
  document.body.classList.toggle('map-fullscreen',isFullscreen);
  document.getElementById('fs-btn').textContent=isFullscreen?'✕':'⛶';
  setTimeout(()=>{map.invalidateSize();drawSparkline(currentHour);},200);
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&isFullscreen)document.getElementById('fs-btn').click();});

// ═══════════════════════════════════════════════
// КАРЪК MODE
// ═══════════════════════════════════════════════
const karykBtn=document.getElementById('karyk-btn');
karykBtn.addEventListener('click',()=>{
  karykMode=!karykMode;
  karykBtn.classList.toggle('active',karykMode);
  document.body.classList.toggle('karyk-active',karykMode);
  document.getElementById('karyk-banner').style.display=karykMode?'block':'none';
  if(karykMode){
    const {scores}=computeScores(currentHour); if(window.__applyLive)window.__applyLive(scores);
    const gems=ZONES.filter(z=>z.type==='karyk'||z.type==='residential_lux'||z.type==='residential'||(window.__liveDemand&&window.__liveDemand.hub&&window.__liveDemand.hub[z.id]!==undefined))
      .map(z=>({z,ks:(window.__karykLive?window.__karykLive(z,computeKarykScore(z.id,scores),typeof userLat==='number'?userLat:null,typeof userLng==='number'?userLng:null):computeKarykScore(z.id,scores))})).sort((a,b)=>b.ks-a.ks);
    if(gems[0]){
      const c=karykColor(gems[0].ks);
      document.getElementById('karyk-hint').innerHTML=
        `🥉 Иди при <span style="color:${c.fill}">${gems[0].z.icon} ${gems[0].z.name.split('(')[0].trim()}</span> (К:${gems[0].ks.toFixed(1)})`;
    }
  }
  render(currentHour);
});

// ═══════════════════════════════════════════════
// TICKER
// ═══════════════════════════════════════════════
function buildTicker(){
  const zMap={}; ZONES.forEach(z=>{zMap[z.id]=z;});
  const items=EVENTS.filter(dayMatches).sort((a,b)=>a.endHour-b.endHour).map(ev=>{
    const z=zMap[ev.zone]; if(!z) return '';
    return `<span class="tick-item"><span class="ev-time">${fmtHour(ev.endHour)}</span> ${ev.name} <span class="ev-loc">@ ${z.name.split('(')[0].trim()}</span> <span style="color:#0f2040"> ·· </span></span>`;
  }).filter(Boolean);
  const el=document.getElementById('ticker');
  el.innerHTML=items.join('')+items.join('');
  el.style.animation='none'; el.offsetHeight; el.style.animation='';
}

// ═══════════════════════════════════════════════
// FLIGHT-CACHE.JSON
// ═══════════════════════════════════════════════
function injectAirportEvents(){
  const keep=EVENTS.filter(e=>!e._fromFlight);
  for(let h=0;h<24;h++){
    const c=flightHours[h]; if(!c) continue;
    keep.push({zone:'airport',name:`✈ ${c} рейса ~${String(h).padStart(2,'0')}:00`,
      endHour:h+0.25,boost:Math.min(3.8,c*0.42),repeat:'daily',_fromFlight:true});
  }
  EVENTS.length=0; keep.forEach(e=>EVENTS.push(e));
}

function applyFallbackAirport(){
  airportStatus='fallback';
  [[6,2],[7,4],[8,5],[9,5],[10,4],[11,4],[12,3],[13,4],[14,3],[15,4],[16,6],
   [17,5],[18,7],[19,8],[20,6],[21,5],[22,5],[23,4]].forEach(([h,c])=>{flightHours[h]=c;});
  injectAirportEvents();
}

function updateAirportBadge(){
  const b=document.getElementById('airport-badge');
  if(airportStatus==='live')        {b.textContent='✈ LIVE';     b.style.color='#22c55e';}
  else if(airportStatus==='fallback'){b.textContent='✈ ПРОГНОЗА';b.style.color='#f59e0b';}
  else                              {b.textContent='✈ ОФЛАЙН';  b.style.color='#ef4444';}
}

function loadFlights(){
  fetch('flight-cache.json?v='+Date.now())
    .then(r=>{if(!r.ok)throw 0;return r.json();})
    .then(data=>{
      const fl=data.data||[]; if(!fl.length) throw 0;
      flightHours=Array(24).fill(0); flightDetails=[];
      fl.forEach(f=>{
        if(!f.arrival?.scheduled) return;
        if(!f.arrival?.terminal) return; // без терминал = частни/военни/карго — без пътници за такси
        const t=new Date(f.arrival.estimated||f.arrival.scheduled);
        const dep=(f.departure?.airport||f.departure?.country_name||'').toLowerCase();
        const nonSchengen=dep.match(/tur|istanbul|sabiha|ankar|israel|ben.gurion|dubai|abu.dhabi|egypt|cairo|morocco|casablanca|london|heathrow|gatwick|stansted|luton|manchester|birmingham|usa|jfk|lax|china|beijing|shanghai|russia|moscow|georgia|tbilisi|armenia|yerevan|jordan|amman|serbia|belgrade|ukraine|kyiv|north.mac/);
        // Exit window (наблюдения): ЕС/Шенген ~10 мин, извън ~15–20 мин след кацане
        const exitFirst = nonSchengen ? 10 : 5;
        const exitLast  = nonSchengen ? 30 : 15;
        const tFirst = new Date(t.getTime() + exitFirst*60000);
        const tLast  = new Date(t.getTime() + exitLast*60000);
        const hFirst = (tFirst.getUTCHours()+3)%24;
        const hLast  = (tLast.getUTCHours()+3)%24;
        const mFirst = tFirst.getUTCMinutes();
        const mLast  = tLast.getUTCMinutes();
        // Spread passengers across exit window (3 slots: start, mid, end)
        const hMid = (new Date(t.getTime()+(exitFirst+exitLast)/2*60000).getUTCHours()+3)%24;
        flightHours[hFirst] = (flightHours[hFirst]||0) + 0.3;
        flightHours[hMid]   = (flightHours[hMid]||0)   + 0.5;
        flightHours[hLast]  = (flightHours[hLast]||0)  + 0.2;
        // Store for popup
        const fn = (f.flight?.iata||'??');
        const depAirport = f.departure?.airport||dep;
        flightDetails.push({
          fn, depAirport, nonSchengen:!!nonSchengen,
          term: (f.arrival && f.arrival.terminal) ? String(f.arrival.terminal) : '?',
          exitFromTs: tFirst.getTime(), exitToTs: tLast.getTime(),
          landH:(t.getUTCHours()+3)%24, landM:t.getUTCMinutes(),
          exitFromH:hFirst, exitFromM:mFirst,
          exitToH:hLast,   exitToM:mLast
        });
      });
      console.log('[SOF] flightDetails populated:', flightDetails.length, 'flights');
      airportStatus='live';
      injectAirportEvents(); updateAirportBadge();
      buildCurve(); buildTicker(); render(currentHour);
    })
    .catch(e=>{
      window.__flErr = (e && (e.stack||e.message)) ? String(e.stack||e.message).slice(0,160) : ('код '+String(e));
      console.error('[SOF] flights failed:', e);
      applyFallbackAirport(); updateAirportBadge();
      buildCurve(); buildTicker(); render(currentHour);
    });
}

// ═══════════════════════════════════════════════
// WEATHER
// ═══════════════════════════════════════════════
let OWM_KEY = '';

async function loadConfig(){
  try {
    const r = await fetch('config.json');
    const d = await r.json();
    OWM_KEY = d.owm_key || '';
  } catch(e) {}
}

async function loadWeather(){
  const bar=document.getElementById('weather-bar');
  if(!OWM_KEY){
    bar.style.display='flex';
    document.getElementById('wb-desc').textContent='Добави OWM ключ в config.json';
    return;
  }
  try{
    const r=await fetch(`https://api.openweathermap.org/data/2.5/weather?lat=42.6977&lon=23.3219&units=metric&lang=bg&appid=${OWM_KEY}`);
    const d=await r.json();
    if(d.cod!==200) throw 0;
    const w=d.weather[0], temp=Math.round(d.main.temp), wind=d.wind?.speed||0;
    const icons={'Rain':'🌧','Drizzle':'🌦','Thunderstorm':'⛈','Snow':'❄️','Fog':'🌫','Mist':'🌫'};
    const wIcon=icons[w.main]||'☀️';
    const boost=w.main==='Rain'?2.0:w.main==='Thunderstorm'?2.8:w.main==='Snow'?1.8:w.main==='Drizzle'?1.2:wind>10?0.5:0;
    weatherBoost=boost;
    bar.style.display='flex';
    document.getElementById('wb-icon').textContent=wIcon;
    document.getElementById('wb-temp').textContent=`${temp}°C`;
    document.getElementById('wb-desc').textContent=w.description;
    document.getElementById('wb-boost').textContent=boost>0?`+${boost.toFixed(1)} demand 🌧`:'';
    if(boost>0){bar.style.borderBottomColor='#00e5ff'; buildCurve(); render(currentHour);}
  }catch(e){console.warn('Weather error',e);}
}

// ═══════════════════════════════════════════════
// SLIDER + AUTO TIME
// ═══════════════════════════════════════════════
const slider=document.getElementById('time-slider');
slider.addEventListener('input',()=>{
  autoTime=false; clearTimeout(slider._t);
  slider._t=setTimeout(()=>{autoTime=true;},10*60000);
  currentHour=parseFloat(slider.value);
  const td=document.getElementById('time-display');
  td.textContent=fmtHour(currentHour);
  // Показва дали е реален час или симулация
  const realH=new Date().getHours()+new Date().getMinutes()/60;
  const isSim=Math.abs(currentHour-realH)>0.4;
  td.style.color = isSim ? '#f59e0b' : 'var(--cyan)';
  td.title = isSim ? '⏱ Симулация — не е реалното време' : '';
  render(currentHour);
  // Обновява панелите ако са отворени
  if(bakshishOpen) buildBakshishPanel();
  if(next90Open) buildNext90();
  checkEventAlerts();
});

function syncTime(){
  if(!autoTime) return;
  const h=new Date().getHours()+new Date().getMinutes()/60;
  const sn=Math.round(h*2)/2;
  if(Math.abs(sn-currentHour)>=0.25){
    currentHour=sn; slider.value=sn;
    document.getElementById('time-display').textContent=fmtHour(sn);
    render(sn);
  }
}
setInterval(syncTime,60000);

// ═══════════════════════════════════════════════
// EVENT ALERT — 15-30 мин преди голям event
// ═══════════════════════════════════════════════
function checkEventAlerts(){
  // Event alerts използват реалния час (не slider) - за реални предупреждения
  const realH=new Date().getHours()+new Date().getMinutes()/60;
  // Но ако slider е близо до реалния час (±30мин), показваме и preview
  const h=Math.abs(currentHour-realH)<0.5 ? realH : currentHour;
  const upcoming=EVENTS.filter(ev=>dayMatches(ev)&&!ev._fromFlight).filter(ev=>{
    const diff=ev.endHour-h;
    return diff>=0.25&&diff<=0.5&&ev.boost>=2.0&&!alertedEvents.has(ev.name+ev.endHour);
  }).sort((a,b)=>a.endHour-b.endHour);
  const panel=document.getElementById('event-alert');
  if(!upcoming.length){panel.style.display='none';return;}
  const ev=upcoming[0], z=ZONES.find(x=>x.id===ev.zone);
  if(!z) return;
  const min=Math.round((ev.endHour-h)*60);
  document.getElementById('ea-icon').textContent=z.icon;
  document.getElementById('ea-title').textContent=`${ev.name} — след ${min} мин!`;
  document.getElementById('ea-sub').textContent=`${z.name.split('(')[0].trim()} · ${fmtHour(ev.endHour)}`;
  document.getElementById('ea-dist').textContent=userLat?`📏 ${(haversine(userLat,userLng,z.lat,z.lng)/1000).toFixed(1)} км`:'';
  document.getElementById('ea-waze').onclick=()=>window.open(`https://waze.com/ul?q=${encodeURIComponent(z.wazeName||z.name)}&navigate=yes`,'_blank');
  panel.style.display='block';
}
setInterval(checkEventAlerts,60000);
document.getElementById('event-alert').querySelector('.ea-close').addEventListener('click',()=>{
  const h=currentHour;
  EVENTS.filter(ev=>dayMatches(ev)&&!ev._fromFlight).filter(ev=>{
    const diff=ev.endHour-h; return diff>=0.25&&diff<=0.5&&ev.boost>=2.0;
  }).forEach(ev=>alertedEvents.add(ev.name+ev.endHour));
  document.getElementById('event-alert').style.display='none';
});

// ═══════════════════════════════════════════════
// 🎩 БАКШИШ РАДАР
// Смени и бакшиш score по тип клиент/зона/час

// ═══════════════════════════════════════════════
// BUS SCHEDULE
// ═══════════════════════════════════════════════
let busSchedule = null;

async function loadBuses(){
  try{
    const r = await fetch('bus-schedule.json');
    if(!r.ok) return;
    busSchedule = await r.json();
    renderBusPanel();
    addBusZones();
  }catch(e){ console.warn('Bus schedule:', e.message); }
}

function getNextBuses(routeId, count=5){
  if(!busSchedule) return [];
  const route = busSchedule.routes.find(r => r.id === routeId);
  if(!route) return [];
  const now = new Date();
  const nowMin = now.getHours()*60 + now.getMinutes();
  const results = [];
  for(const dep of route.departures){
    const [h,m] = dep.split(':').map(Number);
    const depMin = h*60+m;
    const diff = depMin - nowMin;
    if(diff >= -10){ // include buses that left up to 10min ago (may still be picking up)
      const arrMin = depMin + route.duration_min;
      results.push({
        dep, depMin,
        arr: `${Math.floor(arrMin/60).toString().padStart(2,'0')}:${(arrMin%60).toString().padStart(2,'0')}`,
        diffMin: diff,
        route
      });
    }
    if(results.length >= count) break;
  }
  return results;
}

// Всички пристигащи на ЦАС от всички маршрути, сортирани по час на пристигане
let liveArrivals = null;

async function loadLiveArrivals(){
  try{
    const r = await fetch('bus-arrivals.json?v='+Date.now());
    if(!r.ok) return;
    const d = await r.json();
    // валидни само ако са свежи (<100 мин)
    if(d.updated && (Date.now()-new Date(d.updated).getTime()) < 100*60000){
      liveArrivals = d;
    }
  }catch(e){ /* няма live файл — оставаме на разписание */ }
}

function getLiveArrivals(count){
  if(!liveArrivals) return [];
  const now = new Date();
  const nowMin = now.getHours()*60 + now.getMinutes();
  const out = [];
  for(const a of (liveArrivals.arrivals||[])){
    const [h,m] = a.time.split(':').map(Number);
    if(isNaN(h)||isNaN(m)) continue;
    let delta = h*60+m - nowMin;
    if(delta < -20) continue;
    out.push({origin:a.from, operator:a.operator, sector:a.sector||'', intl:!!a.intl, arrTime:a.time, until:delta, live:true});
  }
  return out.slice(0, count||10);
}

function getSofiaArrivals(count){
  const data = busSchedule;
  if(!data) return [];
  const now = new Date();
  const nowMin = now.getHours()*60 + now.getMinutes();
  const fmt2 = mm => String(Math.floor((mm%1440)/60)).padStart(2,'0')+':'+String(mm%60).padStart(2,'0');
  const out = [];
  for(const route of (data.routes||[])){
    if(!route.to || !route.to.includes('Централна автогара София')) continue;
    const dur = route.duration_min || 120;
    for(const dep of route.departures){
      const [h,m] = dep.split(':').map(Number);
      const depMin = h*60+m;
      const arrAbs = depMin + dur;
      let delta = arrAbs - nowMin;
      if(delta < -15) delta += 1440; // след полунощ / утрешен
      if(delta <= 360){ // от -15 мин до +6 часа
        out.push({dep, depMin, route, nowMin, arrMin: nowMin+delta, arrTime: fmt2(arrAbs)});
      }
    }
  }
  out.sort((a,b)=>a.arrMin-b.arrMin);
  return out.slice(0, count||10);
}

function renderBusPanel(){
  // Find or create bus panel in sidebar
  let panel = document.getElementById('bus-panel');
  if(!panel){
    const sidebar = document.getElementById('sidebar') || document.querySelector('.sidebar') || document.querySelector('.panel-list');
    if(!sidebar) return;
    panel = document.createElement('div');
    panel.id = 'bus-panel';
    panel.style.cssText = 'background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px;margin:8px 0;';
    sidebar.appendChild(panel);
  }

  const live = getLiveArrivals(14);
  const arrivals = getSofiaArrivals(live.length ? 4 : 8);

  let html = '<div style="font-size:14px;font-weight:800;color:var(--cyan);margin-bottom:8px">🚌 Пристигащи на ЦАС</div>';

  if(live.length){
    const busRow = b => {
      const urgency = b.until <= 15 ? 'color:#ef4444;font-weight:800' : 'color:var(--text)';
      const sec = b.sector ? `<span style="color:#f5c518;font-size:11px;font-weight:800;white-space:nowrap"> → Сектор ${b.sector}</span>` : '';
      return `<div style="display:flex;justify-content:space-between;gap:8px;padding:4px 0;border-bottom:1px solid var(--border);font-size:13px">
        <span>${b.intl?'🌍':'🚌'} ${b.origin}${sec} <span style="color:var(--muted);font-size:11px">${b.operator||''}</span></span>
        <span style="${urgency};white-space:nowrap">${b.arrTime}${b.until>=0?' · след '+b.until+' мин':''}</span>
      </div>`;
    };
    const dom = live.filter(b=>!b.intl), intl = live.filter(b=>b.intl);
    html += '<div style="font-size:11px;font-weight:800;color:#ef4444;margin-bottom:4px">🔴 LIVE — centralnaavtogara.bg</div>';
    html += '<div style="max-height:32vh;overflow-y:auto;-webkit-overflow-scrolling:touch">';
    for(const b of dom) html += busRow(b);
    if(intl.length){
      html += '<div style="font-size:11px;font-weight:800;color:#22c3a6;margin:6px 0 3px">🌍 МЕЖДУНАРОДНИ</div>';
      for(const b of intl) html += busRow(b);
    }
    html += '</div>';
    html += '<div style="font-size:11px;font-weight:800;color:var(--muted);margin:8px 0 4px">📋 По разписание</div>';
  }

  if(arrivals.length){
    for(const b of arrivals){
      const until = b.arrMin - b.nowMin;
      const urgency = until <= 0 ? 'color:#ef4444;font-weight:800' : until < 40 ? 'color:#f59e0b;font-weight:800' : 'color:var(--text)';
      const origin = (b.route.name||'').replace(' → София','');
      const label = until <= 0 ? `пристигнал ~${b.arrTime}` :
                    until < 90 ? `~${b.arrTime} · след ${until} мин` :
                    `~${b.arrTime}`;
      html += `<div style="display:flex;justify-content:space-between;gap:8px;padding:4px 0;border-bottom:1px solid var(--border);font-size:13px">
        <span>${b.route.intl?'🌍':'🚌'} ${origin} <span style="color:var(--muted);font-size:11px">${b.dep}${b.route.approx?' ≈':''}</span></span>
        <span style="${urgency};white-space:nowrap">${label}</span>
      </div>`;
    }
  } else {
    html += '<div style="color:var(--muted);font-size:12px">Няма пристигащи в следващите 6 часа</div>';
  }

  html += '<div style="margin-top:8px;font-size:11px;color:var(--muted)">≈ разписание по модел на превозвача · Пловдив е точно</div>';
  panel.innerHTML = html;

  // Update every minute
  setTimeout(renderBusPanel, 60000);
}

function addBusZones(){
  var M = (typeof map!=='undefined' && map && typeof map.addLayer==='function') ? map : null;
  if(!busSchedule || !M) return;
  // Add Expo Center bus stop as zone marker
  const expoStop = {lat:42.6497, lng:23.3940, name:'🚌 Expo Center (спирка при метро Цариградско шосе)'};
  const icon = L.divIcon({
    className:'',
    html:`<div style="background:#0284c7;color:#fff;border-radius:6px;padding:3px 7px;font-size:12px;font-weight:800;white-space:nowrap;box-shadow:0 2px 6px #0004">🚌 Expo</div>`,
    iconAnchor:[25,15]
  });
  L.marker([expoStop.lat, expoStop.lng], {icon})
    .addTo(M)
    .bindPopup(`<b style="color:#0284c7">🚌 Expo Center / метро Цариградско шосе</b><br><small>Слизане от Тракия: Пловдив · Пазарджик · Ст. Загора · Бургас — спирката е при метростанцията</small>`);
  // Коридорни входове — къде влизат междуградските автобуси в София
  const corridors = [
    {lat:42.7208, lng:23.4085, short:'🚌 Хемус', pop:'<b style="color:#0284c7">🚌 Ботевградско шосе</b><br><small>Вход от Хемус: Варна · В. Търново · Плевен · Русе</small>'},
    {lat:42.6520, lng:23.2800, short:'🚌 Струма', pop:'<b style="color:#0284c7">🚌 Бул. България</b><br><small>Вход от Струма: Благоевград · ЮЗ България</small>'},
  ];
  corridors.forEach(c=>{
    const ci = L.divIcon({className:'',
      html:`<div style="background:#0284c7;color:#fff;border-radius:6px;padding:3px 7px;font-size:12px;font-weight:800;white-space:nowrap;box-shadow:0 2px 6px #0004">${c.short}</div>`,
      iconAnchor:[25,15]});
    L.marker([c.lat, c.lng], {icon:ci}).addTo(M).bindPopup(c.pop);
  });
}

// ═══════════════════════════════════════════════

const SHIFTS = {
  morning:   { name:"🌅 Сутрешна смяна (08–11)",    hours:[8,11],
    tip:"Бизнес пътници, летищни трансфери, хора за прегледи. Луксозните квартали тръгват.",
    clientType:"бизнес / турист / пациент" },
  midday:    { name:"☀️ Обедна смяна (11–16)",       hours:[11,16],
    tip:"Туристи разхождат се, бизнес обяди, след прегледи. Хотелски клиенти с чемодан. Корпоративни карти.",
    clientType:"турист / бизнес обяд" },
  afternoon: { name:"🌆 Следобедна смяна (16–20)",  hours:[16,20],
    tip:"Офисите излизат. Театри и опера след 19ч. В дъжд се удвоява.",
    clientType:"офис работник / театрал" },
  evening:   { name:"🌙 Вечерна смяна (20–02)",     hours:[20,26],
    tip:"След ресторант. След концерт — емоционален пик. Хотели 5* вечер — корпоративни.",
    clientType:"ресторант гост / нощен" },
  night:     { name:"🌃 Нощна смяна (02–08)",       hours:[2,8],
    tip:"Последни гости от клубове. Летище — ранни полети. Хотелски пристигания.",
    clientType:"нощен гост / ранен полет" },
};

function getCurrentShift(h) {
  if (h >= 8  && h < 11) return 'morning';
  if (h >= 11 && h < 16) return 'midday';
  if (h >= 16 && h < 20) return 'afternoon';
  if (h >= 20 || h <  2) return 'evening';
  return 'night';
}

// Бакшиш фактори по тип зона за всяка смяна
const BAKSHISH_WEIGHTS = {
  morning: {
    airport:3.5, hotel:3.0, residential_lux:2.8, hospital:2.2,
    office:1.5, transit:2.0, mall:1.0, university:0.8,
    theatre:0.5, cinema:0.5, nightlife:0.2, karyk:1.8,
  },
  midday: {
    airport:2.8, hotel:3.2, restaurant:2.5, mall:1.8,
    hospital:1.8, office:1.2, transit:1.5, residential_lux:1.5,
    university:1.0, theatre:0.8, nightlife:0.5, karyk:1.2,
  },
  afternoon: {
    office:3.0, theatre:3.5, airport:2.5, hotel:2.0,
    mall:2.0, residential_lux:2.2, transit:1.8,
    hospital:1.5, university:1.5, nightlife:1.0, karyk:2.0,
  },
  evening: {
    theatre:4.0, nightlife:3.5, hotel:3.5, airport:2.8,
    restaurant:3.8, residential_lux:2.5, mall:1.5,
    transit:1.5, hospital:1.0, office:0.5, karyk:2.5,
  },
  night: {
    nightlife:4.5, airport:4.0, hotel:3.5, transit:2.0,
    residential_lux:2.0, theatre:0.5, mall:0.2,
    hospital:1.5, office:0.2, karyk:1.5,
  },
};

// Причини защо дадена зона е добра за бакшиш
const BAKSHISH_REASONS = {
  airport:         "✈️ Чужденци с багаж — летищни трансфери",
  hotel:           "🏨 Бизнес гости — корпоративни карти",
  residential_lux: "💎 Луксозни квартали — висок клас клиенти",
  hospital:        "🏥 Болнични клиенти — редовен поток",
  theatre:         "🎭 След спектакъл — емоционален пик",
  nightlife:       "🍷 Ресторанти и нощен живот",
  office:          "💼 Офис работници след работа",
  mall:            "🛍 Пазаруващи с багаж",
  transit:         "🚌 Пристигащи с багаж — нужда от такси",
  university:      "🎓 Много на брой — компенсира с обем",
  karyk:           "🥉 Тих квартал — без конкуренция",
};

// Дъжд мултипликатор
function rainMultiplier() {
  if (weatherBoost >= 2.0) return 1.6; // дъжд
  if (weatherBoost >= 1.0) return 1.3; // ситен дъжд
  return 1.0;
}

function computeBakshishScore(zid, scores, shiftKey) {
  const z = ZONES.find(x=>x.id===zid); if(!z) return 0;
  const demand  = scores[zid] || 0;
  const weights = BAKSHISH_WEIGHTS[shiftKey] || {};
  const w = weights[z.type] || 0.5;
  const rain = rainMultiplier();
  // Score = demand × тип_тежест × дъжд_бонус
  return Math.min(5, demand * w * rain * 0.6);
}

function bakshishColor(bs) {
  if (bs >= 4.0) return '#ffd700'; // злато
  if (bs >= 3.0) return '#d4af37'; // тъмно злато
  if (bs >= 2.0) return '#c8a000'; // amber
  if (bs >= 1.0) return '#8a7000'; // тъмен amber
  return '#3a3000';
}

let bakshishOpen = false;

document.getElementById('bakshish-btn')?.addEventListener('click', () => {
  bakshishOpen = !bakshishOpen;
  document.getElementById('bakshish-btn').classList.toggle('active', bakshishOpen);
  const panel = document.getElementById('bakshish-panel');
  if (bakshishOpen) { buildBakshishPanel(); panel.style.display = 'block'; }
  else panel.style.display = 'none';
});

window.closeBakshish = function() {
  bakshishOpen = false;
  document.getElementById('bakshish-btn')?.classList.remove('active');
  document.getElementById('bakshish-panel').style.display = 'none';
};

function buildBakshishPanel() {
  const h = currentHour; // следва slider-а, не реалния часовник
  const shiftKey = getCurrentShift(h);
  const shift = SHIFTS[shiftKey];
  const {scores} = computeScores(currentHour);
  const rain = rainMultiplier();

  // Shift banner
  document.getElementById('bp-shift-label').textContent = shift.clientType;
  document.getElementById('bp-shift-name').textContent  = shift.name;
  let tip = shift.tip;
  if (rain > 1.0) tip = `🌧 ДЪЖД БОНУС ×${rain.toFixed(1)}! ` + tip;
  document.getElementById('bp-shift-tip').textContent = tip;

  // Rank all zones by bakshish score
  const ranked = ZONES
    .filter(z => z.type !== 'traffic')
    .map(z => ({
      z,
      bs: computeBakshishScore(z.id, scores, shiftKey),
      demand: scores[z.id] || 0,
    }))
    .filter(({bs}) => bs >= 0.5)
    .sort((a,b) => b.bs - a.bs)
    .slice(0, 15);

  const list = document.getElementById('bakshish-list');
  if (!ranked.length) {
    list.innerHTML = '<div style="padding:14px;color:#6a5000;font-family:Share Tech Mono,monospace">Няма активни бакшиш зони в момента</div>';
    return;
  }

  list.innerHTML = ranked.map(({z, bs, demand}, i) => {
    const color = bakshishColor(bs);
    const reason = BAKSHISH_REASONS[z.type] || '🚖 Потенциален клиент';
    const rainTxt = rain > 1.0 ? ` 🌧×${rain.toFixed(1)}` : '';
    const stars = '⭐'.repeat(Math.min(5, Math.round(bs)));
    return `<div class="bp-item" onclick="(function(){closeBakshish();if(document.body.classList.contains('list-view'))toggleMapView();setTimeout(function(){map.invalidateSize();map.setView([${z.lat},${z.lng}],'${z.id}'==='airport'?14:15);'${z.id}'==='airport'?showAirportSchedule():showZonePopup('${z.id}');},200);})()">
      <div class="bp-rank">#${i+1}</div>
      <div class="bp-dot" style="background:${color};box-shadow:0 0 5px ${color}66"></div>
      <div class="bp-info">
        <div class="bp-name">${z.icon} ${z.name.split('(')[0].trim()}</div>
        <div class="bp-why">${reason}${rainTxt}</div>
        <div style="font-size:14px;color:#5a4000;margin-top:1px">${stars}</div>
      </div>
      <div class="bp-score-wrap">
        <div class="bp-score" style="color:${color}">${bs.toFixed(1)}</div>
        <div class="bp-multiplier">demand ${demand.toFixed(1)}</div>
      </div>
    </div>`;
  }).join('') + '<div style="padding:12px 12px 16px;text-align:center"><button onclick="closeBakshish()" style="background:#d4af37;color:#0d0e00;border:none;border-radius:8px;padding:10px 32px;font-weight:800;font-size:14px;cursor:pointer">✕ Затвори</button></div>';
}

// Rebuild bakshish panel when time changes (via setInterval, not render override)
setInterval(()=>{ if(bakshishOpen) buildBakshishPanel(); }, 60000);


const nowH=new Date().getHours()+new Date().getMinutes()/60;
currentHour=Math.min(24,Math.max(6,Math.round(nowH*2)/2));
slider.value=currentHour;
document.getElementById('time-display').textContent=fmtHour(currentHour);

applyFallbackAirport(); // зарежда веднага с fallback
buildCurve();
buildCircles();
buildTicker();
render(currentHour);
loadFlights(); loadBuses(); loadLiveArrivals(); setInterval(loadLiveArrivals, 10*60000);
loadConfig().then(()=>{ loadWeather(); setInterval(loadWeather,10*60000); });
checkEventAlerts();
geocodeZones();     // async — прецизира координатите от OSM

setTimeout(()=>{drawSparkline(currentHour); map.invalidateSize();},300);
window.addEventListener('resize',()=>{drawSparkline(currentHour); map.invalidateSize();});

}); // end DOMContentLoaded


function toggleMapView(){
  const listView = document.body.classList.toggle('list-view');
  const btn = document.getElementById('toggle-map-btn');
  if(btn) btn.textContent = listView ? '🗺️ Карта' : '📋 Списък';
  if(!listView && window.map) setTimeout(()=>map.invalidateSize(), 100);
}


// ------ Дъжд-аларма: Open-Meteo 15-мин прогноза ------
(function(){
  async function checkRain(){
    try{
      const r=await fetch('https://api.open-meteo.com/v1/forecast?latitude=42.6977&longitude=23.3219&minutely_15=precipitation&forecast_hours=4&timezone=Europe%2FSofia');
      const d=await r.json();
      const t=(d.minutely_15&&d.minutely_15.time)||[], p=(d.minutely_15&&d.minutely_15.precipitation)||[];
      const now=Date.now();
      let hit=null, stop=null;
      for(let i=0;i<t.length;i++){
        const ts=new Date(t[i]).getTime();
        if(ts<now-15*60000) continue;
        if(p[i]>=0.1 && !hit) hit={ts:ts};
        else if(hit && p[i]<0.1){ stop=ts; break; }
      }
      let el=document.getElementById('rain-banner');
      if(!hit){ if(el) el.remove(); return; }
      const hhmm=function(x){return new Date(x).toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'});};
      const started=hit.ts<=now;
      const txt=started
        ? ('🌧️ Вали сега'+(stop?(' до ~'+hhmm(stop)):'')+' — търсенето расте')
        : ('🌧️ Дъжд около '+hhmm(hit.ts)+(stop?(' до '+hhmm(stop)):''));
      if(!el){
        el=document.createElement('div');
        el.id='rain-banner';
        el.style.cssText='position:fixed;top:8px;left:50%;transform:translateX(-50%);z-index:9999;background:rgba(30,58,138,.92);color:#dbeafe;font-weight:900;font-size:15px;padding:9px 16px;border-radius:12px;border:1px solid #3b82f6;box-shadow:0 4px 14px rgba(0,0,0,.4);pointer-events:none;white-space:nowrap';
        document.body.appendChild(el);
      }
      el.textContent=txt;
    }catch(e){}
  }
  checkRain();
  setInterval(checkRain, 15*60000);
})();


// ------ Театрални събития (events.json): 🎭 маркери + чип "кога свършват" ------
// theatre-events-layer
(function(){
  function ready(cb){
    var t=setInterval(function(){ if(window.map&&window.L){clearInterval(t);cb();} },500);
    setTimeout(function(){clearInterval(t)},30000);
  }
  ready(function(){
    fetch('events.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var today=new Date().toISOString().slice(0,10);
      if(d.date!==today || !d.events || !d.events.length) return;
      var layer=L.layerGroup();
      d.events.forEach(function(e){
        var mk=L.marker([e.lat,e.lng],{icon:L.divIcon({className:'',html:'<div style="font-size:22px;filter:drop-shadow(0 1px 2px rgba(0,0,0,.6))">🎭</div>',iconSize:[24,24],iconAnchor:[12,12]})});
        mk.bindPopup('<div style="font-family:sans-serif;min-width:180px"><b style="font-size:14px">'+e.t+'</b>'+
          '<div style="color:#64748b;font-size:12px;margin:3px 0">'+e.v+'</div>'+
          '<div style="font-size:13px">Начало: '+e.start+' · Край: ~'+e.end+'</div>'+
          '<div style="font-size:14px;font-weight:900;color:#f59e0b;margin-top:4px">🚕 Бъди там: '+e.target+'</div></div>');
        layer.addLayer(mk);
      });
      layer.addTo(window.map);
      var chip=document.createElement('div');
      chip.style.cssText='position:fixed;left:8px;bottom:130px;z-index:1500;background:#1a1029f0;color:#e9d5ff;border:1px solid #a855f7;border-radius:10px;padding:7px 11px;font-family:sans-serif;font-size:13px;font-weight:900;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5)';
      chip.textContent='🎭 '+d.events.length+' довечера';
      chip.onclick=function(){
        alert(d.events.map(function(e){return e.target+' → '+e.t+' ('+e.v+')'}).join('\n')+'\n\n🚕 Час = кога да си там (12 мин преди края)');
      };
      document.body.appendChild(chip);
    }).catch(function(e){});
  });
})();


// ------ SEV събития (/SEV/events.json): 🎫 маркери + чип с demand прозорци ------
// sev-events-layer
(function(){
  function ready(cb){
    var t=setInterval(function(){ if(window.map&&window.L){clearInterval(t);cb();} },500);
    setTimeout(function(){clearInterval(t)},30000);
  }
  function hm(d){return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'});}
  ready(function(){
    fetch('/SEV/events.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      if(!d.events||!d.events.length) return;
      var now=Date.now(), DUR=150*60000, POST=45*60000, PRE=2*3600000;
      var todayEnd=new Date(); todayEnd.setHours(23,59,59,999);
      var evs=d.events.map(function(e){
        var s=new Date(e.start).getTime();
        return {n:e.name,v:e.venue,lat:e.lat,lon:e.lon,cap:e.cap||600,s:s,e:s+DUR,src:e.src};
      }).filter(function(e){
        return e.e+POST>now && e.s<=todayEnd.getTime()+36*3600000; // до утре вечер
      }).sort(function(a,b){return a.s-b.s});
      if(!evs.length) return;
      var layer=L.layerGroup();
      evs.forEach(function(e){
        if(!e.lat) return;
        var big=e.cap>=8000, mid=e.cap>=2500;
        var col=big?'#f85149':(mid?'#d29922':'#3fb950');
        var mk=L.marker([e.lat,e.lon],{icon:L.divIcon({className:'',
          html:'<div style=\"font-size:'+(big?26:20)+'px;filter:drop-shadow(0 1px 3px rgba(0,0,0,.7))\">🎫</div>',
          iconSize:[26,26],iconAnchor:[13,13]})});
        var s=new Date(e.s),en=new Date(e.e);
        mk.bindPopup('<div style=\"font-family:sans-serif;min-width:190px\">'+
          '<b style=\"font-size:14px\">'+e.n+'</b>'+
          '<div style=\"color:#64748b;font-size:12px;margin:3px 0\">'+e.v+' · ~'+e.cap.toLocaleString('bg')+' души</div>'+
          '<div style=\"font-size:13px\">Начало '+hm(s)+' · Край ~'+hm(en)+'</div>'+
          '<div style=\"font-size:13px;color:'+col+';font-weight:900;margin-top:4px\">'+
          '🚕 Dropoff '+hm(new Date(e.s-PRE))+'–'+hm(s)+'<br>🚕 Pickup '+hm(en)+'–'+hm(new Date(e.e+POST))+'</div></div>');
        layer.addLayer(mk);
      });
      layer.addTo(window.map);
      var chip=document.createElement('div');
      chip.style.cssText='position:fixed;left:8px;bottom:154px;z-index:1500;background:#0c1f2ef0;color:#bae6fd;border:1px solid #38bdf8;border-radius:10px;padding:7px 11px;font-family:sans-serif;font-size:13px;font-weight:900;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5)';
      chip.textContent='🎫 '+evs.length+' събития';
      chip.onclick=function(){
        alert(evs.map(function(e){
          var en=new Date(e.e);
          return hm(new Date(e.s))+' '+e.n.slice(0,40)+' @ '+(e.v||'?')+'\\n   🚕 pickup '+hm(en)+'–'+hm(new Date(e.e+45*60000));
        }).join('\\n')+'\\n\\nИзточник: SEV ('+(d.sources_ok||[]).join('+')+')');
      };
      document.body.appendChild(chip);
    }).catch(function(e){});
  });
})();


// ------ ☔ Прогноза за дъжд (следващите 12ч, Open-Meteo) ------
// rain-forecast-chip
(function(){
  function hm(d){return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'});}
  fetch('https://api.open-meteo.com/v1/forecast?latitude=42.695&longitude=23.406&hourly=precipitation_probability,precipitation&forecast_days=2&timezone=Europe%2FSofia')
  .then(function(r){return r.json()}).then(function(d){
    var t=d.hourly.time,p=d.hourly.precipitation,pp=d.hourly.precipitation_probability;
    var now=Date.now(), hit=null;
    for(var i=0;i<t.length;i++){
      var ts=new Date(t[i]+':00+03:00').getTime();
      if(ts<now-3600000) continue;
      if(ts>now+12*3600000) break;
      if((pp[i]>=50&&p[i]>=0.1)||p[i]>=0.4){ hit={ts:ts,pr:pp[i],mm:p[i]}; break; }
    }
    var chip=document.createElement('div');
    chip.style.cssText='position:fixed;left:8px;bottom:112px;z-index:1500;border-radius:10px;padding:6px 10px;font-family:sans-serif;font-size:12px;font-weight:900;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5)';
    if(hit){
      var mins=Math.round((hit.ts-now)/60000);
      var when=mins<=0?'сега':(mins<60?('след '+mins+' мин'):('след '+Math.floor(mins/60)+'ч '+(mins%60)+'м'));
      chip.textContent='☔ Дъжд от '+hm(new Date(hit.ts))+' ('+when+')';
      var urgent=mins<90;
      chip.style.background=urgent?'#3a2510f0':'#10233af0';
      chip.style.color=urgent?'#fbbf24':'#93c5fd';
      chip.style.border='1px solid '+(urgent?'#f59e0b':'#3b82f6');
    } else {
      chip.textContent='☀️ Без дъжд 12ч';
      chip.style.background='#111827d0'; chip.style.color='#9ca3af'; chip.style.border='1px solid #374151';
    }
    chip.onclick=function(){ chip.style.display='none'; };
    document.body.appendChild(chip);
  }).catch(function(e){});
})();

// ------ 🛬 Излизат сега: кацане -> изходен прозорец (кацане+15 до +40 мин) ------
// exit-now-panel exit-now-v2
(function(){
  function hm(d){return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'});}
  var chip=document.createElement('div');
  chip.style.cssText='position:fixed;left:8px;bottom:70px;z-index:1500;background:#0f2818f0;color:#86efac;border:1px solid #22c55e;border-radius:10px;padding:7px 11px;font-family:sans-serif;font-size:13px;font-weight:900;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5);display:none';
  document.body.appendChild(chip);
  var panel=document.createElement('div');
  panel.style.cssText='position:fixed;left:8px;right:8px;bottom:80px;max-height:55vh;overflow-y:auto;z-index:2500;background:#0b1220f8;color:#e5e7eb;border:1px solid #334155;border-radius:14px;padding:12px;font-family:sans-serif;font-size:13px;display:none;box-shadow:0 6px 30px rgba(0,0,0,.7)';
  document.body.appendChild(panel);
  chip.onclick=function(){ panel.style.display = panel.style.display==='none'?'block':'none'; };
  function refresh(){
    fetch('flight-cache.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var now=Date.now(), out=[], soon=[];
      (d.data||[]).forEach(function(f){
        if(f.flight_status==='cancelled') return;
        var a=f.arrival||{}, land=a.estimated||a.scheduled;
        if(!land) return;
        var lt=new Date(land).getTime();
        if(isNaN(lt)) return;
        var NS=/(лондон|london|luton|stansted|manchester|edinburgh|birmingham|bristol|liverpool|glasgow|leeds|дъблин|dublin|истанбул|istanbul|sabiha|анталия|antalya|tel aviv|тел авив|dubai|дубай|abu dhabi|doha|доха|cairo|кайро|hurghada|хургада|sharm|шарм|belgrade|белград|skopje|скопие|chisinau|кишинев|tbilisi|тбилиси|kutaisi|кутаиси|yerevan|ереван|baku|баку|larnaca|ларнака|paphos|пафос|amman|аман|jeddah|riyadh|new york|ню йорк|kuwait|beirut|бейрут|tirana|тирана|podgorica|подгорица|sarajevo|сараево|amman)/i;var nonsch=NS.test((f.departure&&f.departure.airport)||'');var xs=lt+(nonsch?20:10)*60000, xe=lt+(nonsch?50:30)*60000;
        var item={land:lt,xs:xs,xe:xe,from:(f.departure&&f.departure.airport)||'?',
                  num:(f.flight&&f.flight.iata)||'', term:a.terminal||'', st:f.flight_status, ns:nonsch};
        if(now>=xs&&now<=xe) out.push(item);
        else if(xs>now&&xs<=now+60*60000) soon.push(item);
      });
      out.sort(function(a,b){return a.xe-b.xe}); soon.sort(function(a,b){return a.xs-b.xs});
      if(!out.length&&!soon.length){ chip.style.display='none'; panel.style.display='none'; return; }
      chip.style.display='block';
      chip.textContent='🛬 '+(out.length?out.length+' излизат СЕГА':'')+(out.length&&soon.length?' · ':'')+(soon.length?soon.length+' до 1ч':'');
      var html='<div style=\"font-weight:900;font-size:14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center\"><span>🛬 Изходи Терминал 1/2</span><span style=\"cursor:pointer;padding:2px 10px;font-size:16px;color:#94a3b8\" onclick=\"this.parentElement.parentElement.style.display=&quot;none&quot;\">✕</span></div>';
      out.forEach(function(f){
        html+='<div style=\"background:#14532d80;border-left:3px solid #22c55e;border-radius:6px;padding:6px 8px;margin:5px 0\">'+
          '<b>ИЗЛИЗАТ СЕГА</b> '+(f.ns?'🛂':'🇪🇺')+' · '+f.from+' '+(f.term?('· T'+f.term):'')+'<br>'+
          '<span style=\"color:#9ca3af\">Кацна '+hm(new Date(f.land))+'</span> → изход <b>'+hm(new Date(f.xs))+'–'+hm(new Date(f.xe))+'</b> · '+f.num+'</div>';
      });
      soon.forEach(function(f){
        html+='<div style=\"background:#1e293b80;border-left:3px solid #64748b;border-radius:6px;padding:6px 8px;margin:5px 0\">'+
          f.from+' '+(f.term?('· T'+f.term):'')+'<br>'+
          '<span style=\"color:#9ca3af\">Кацане '+hm(new Date(f.land))+(f.st==='landed'?' ✓':'')+'</span> → изход <b>'+hm(new Date(f.xs))+'–'+hm(new Date(f.xe))+'</b> · '+f.num+'</div>';
      });
      html+='<div style=\"color:#64748b;font-size:11px;margin-top:6px\">🇪🇺 Шенген: изход +10–30 мин · 🛂 не-Шенген: +20–50 мин · опресн. на 60 сек</div>';
      panel.innerHTML=html;
    }).catch(function(e){});
  }
  refresh(); setInterval(refresh, 60000);
})();


// ------ rain-banner: ✕ бутон + авто-скриване след края на дъжда ------
// ui-fix-v3 rain-toast-x
(function(){
  function tend(txt){
    var m=/до\s+(\d{1,2}):(\d{2})/.exec(txt||'');
    if(!m) return null;
    var d=new Date(); d.setHours(+m[1],+m[2],0,0);
    return d.getTime();
  }
  function tick(){
    var el=document.getElementById('rain-banner');
    if(!el) return;
    var end=tend(el.textContent);
    if(end && Date.now()>end+10*60000){ el.remove(); return; }
    if(!el.dataset.rx){
      el.dataset.rx='1';
      var x=document.createElement('span');
      x.textContent=' ✕';
      x.style.cssText='cursor:pointer;padding:0 4px 0 10px;opacity:.85';
      x.onclick=function(ev){ev.stopPropagation();el.remove();};
      el.appendChild(x);
    }
  }
  tick(); setInterval(tick, 30000);
})();


// ------ bak-v4 ------
// (1) старият rain-banner: премахване (ненадеждни данни, дублира прогнозата)
(function(){
  function kill(){ var el=document.getElementById('rain-banner'); if(el) el.remove(); }
  kill(); setInterval(kill, 5000);
})();

// (2) rain chip v2: сегашно състояние + следващ дъжд от един източник (Open-Meteo)
(function(){
  Array.prototype.slice.call(document.querySelectorAll('div')).forEach(function(el){
    var t=el.textContent||'';
    if((t.indexOf('☔ Дъжд от')===0||t.indexOf('☀️ Без дъжд')===0)&&el.style.position==='fixed') el.remove();
  });
  function hm(d){return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'});}
  fetch('https://api.open-meteo.com/v1/forecast?latitude=42.695&longitude=23.406&hourly=precipitation_probability,precipitation&forecast_days=2&timezone=Europe%2FSofia')
  .then(function(r){return r.json()}).then(function(d){
    var t=d.hourly.time,p=d.hourly.precipitation,pp=d.hourly.precipitation_probability;
    var now=Date.now(), idxNow=-1;
    for(var i=0;i<t.length;i++){
      var ts=new Date(t[i]+':00+03:00').getTime();
      if(ts<=now&&now<ts+3600000){ idxNow=i; break; }
    }
    var chip=document.createElement('div');
    chip.style.cssText='position:fixed;left:8px;bottom:112px;z-index:1500;border-radius:10px;padding:6px 10px;font-family:sans-serif;font-size:12px;font-weight:900;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5)';
    var rainingNow = idxNow>=0 && p[idxNow]>=0.15;
    if(rainingNow){
      var j=idxNow; while(j<t.length&&p[j]>=0.15) j++;
      var stop=new Date(new Date(t[Math.min(j,t.length-1)]+':00+03:00').getTime());
      chip.textContent='🌧️ Вали · спира ~'+hm(stop);
      chip.style.background='#0f2a3af0'; chip.style.color='#7dd3fc'; chip.style.border='1px solid #0ea5e9';
    } else {
      var hit=null;
      for(var i=Math.max(idxNow,0);i<t.length;i++){
        var ts=new Date(t[i]+':00+03:00').getTime();
        if(ts>now+12*3600000) break;
        if(ts>now&&((pp[i]>=50&&p[i]>=0.1)||p[i]>=0.4)){ hit=ts; break; }
      }
      if(hit){
        var mins=Math.round((hit-now)/60000);
        var when=mins<60?('след '+mins+' мин'):('след '+Math.floor(mins/60)+'ч '+(mins%60)+'м');
        chip.textContent='☔ Дъжд от '+hm(new Date(hit))+' ('+when+')';
        var urgent=mins<90;
        chip.style.background=urgent?'#3a2510f0':'#10233af0';
        chip.style.color=urgent?'#fbbf24':'#93c5fd';
        chip.style.border='1px solid '+(urgent?'#f59e0b':'#3b82f6');
      } else {
        chip.textContent='☀️ Без дъжд 12ч';
        chip.style.background='#111827d0'; chip.style.color='#9ca3af'; chip.style.border='1px solid #374151';
      }
    }
    chip.onclick=function(){ chip.style.display='none'; };
    document.body.appendChild(chip);
  }).catch(function(e){});
})();

// (3) 🚌 входящи автобуси с ETA на първите спирки по коридор
(function(){
  function hm(d){return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'});}
  var HEMUS=/(ВАРНА|ШУМЕН|РУСЕ|РАЗГРАД|ТЪРГОВИЩЕ|ВЕЛИКО ТЪРНОВО|В\. ?ТЪРНОВО|ГАБРОВО|ПЛЕВЕН|ЛОВЕЧ|СЕВЛИЕВО|БЯЛА|ДОБРИЧ|СИЛИСТРА|БОТЕВГРАД|ПРАВЕЦ)/i;
  var TRAKIA=/(ПЛОВДИВ|БУРГАС|СТАРА ЗАГОРА|СЛИВЕН|ЯМБОЛ|ХАСКОВО|КЪРДЖАЛИ|ДИМИТРОВГРАД|ПАЗАРДЖИК|АСЕНОВГРАД|НЕСЕБЪР|СЛЪНЧЕВ|ПОМОРИЕ|СОЗОПОЛ)/i;
  var YUG=/(БЛАГОЕВГРАД|САНДАНСКИ|ПЕТРИЧ|ДУПНИЦА|КЮСТЕНДИЛ|БАНСКО|РАЗЛОГ|ГОЦЕ|СОЛУН|АТИНА|КАВАЛА|ДРАМА|СКОПИЕ|СТРУМИЦА|ОХРИД|БИТОЛЯ)/i;
  function corridor(from){
    var f=(from||'').toUpperCase();
    if(HEMUS.test(f)) return {n:'Хемус',stops:[['Експо/Цариградско',-18],['Ботевградско шосе',-12]]};
    if(TRAKIA.test(f)) return {n:'Тракия',stops:[['Експо Център',-15],['Цариградско шосе',-10]]};
    if(YUG.test(f)) return {n:'Юг',stops:[['бул. България',-14],['Хладилника',-9]]};
    return null;
  }
  var chip=document.createElement('div');
  chip.style.cssText='position:fixed;left:8px;bottom:28px;z-index:1500;border-radius:10px;padding:7px 11px;font-family:sans-serif;font-size:13px;font-weight:900;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5);display:none';
  document.body.appendChild(chip);
  var panel=document.createElement('div');
  panel.style.cssText='position:fixed;left:8px;right:8px;bottom:80px;max-height:55vh;overflow-y:auto;z-index:2500;background:#0b1220f8;color:#e5e7eb;border:1px solid #334155;border-radius:14px;padding:12px;font-family:sans-serif;font-size:13px;display:none;box-shadow:0 6px 30px rgba(0,0,0,.7)';
  document.body.appendChild(panel);
  chip.onclick=function(){ panel.style.display=panel.style.display==='none'?'block':'none'; };
  function refresh(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var now=new Date(), list=[];
      (d.arrivals||[]).forEach(function(a){
        var m=/^(\d{2}):(\d{2})$/.exec(a.time); if(!m) return;
        var cas=new Date(); cas.setHours(+m[1],+m[2],0,0);
        var diff=(cas-now)/60000;
        if(diff<-25||diff>120) return;
        list.push({cas:cas,diff:diff,from:a.from,intl:a.intl,cor:corridor(a.from)});
      });
      list.sort(function(a,b){return a.cas-b.cas});
      var hot=list.filter(function(x){return x.diff>=-20&&x.diff<=20}).length;
      if(!list.length){ chip.style.display='none'; panel.style.display='none'; return; }
      chip.style.display='block';
      chip.textContent='🚌 '+list.length+' до 2ч'+(hot?' · '+hot+' СЕГА':'');
      if(hot){ chip.style.background='#3a2510f0'; chip.style.color='#fb923c'; chip.style.border='1px solid #ea580c'; }
      else { chip.style.background='#10233af0'; chip.style.color='#93c5fd'; chip.style.border='1px solid #3b82f6'; }
      var html='<div style=\"font-weight:900;font-size:14px;margin-bottom:8px;display:flex;justify-content:space-between\"><span>🚌 Входящи автобуси</span><span style=\"cursor:pointer;padding:2px 10px;color:#94a3b8\" onclick=\"this.parentElement.parentElement.style.display=&quot;none&quot;\">✕</span></div>';
      list.forEach(function(x){
        var urgent=x.diff>=-20&&x.diff<=20;
        var stops='';
        if(x.cor){
          stops=x.cor.stops.map(function(s){
            return s[0]+' ~<b>'+hm(new Date(x.cas.getTime()+s[1]*60000))+'</b>';
          }).join(' → ')+' → ';
        }
        html+='<div style=\"background:'+(urgent?'#3a251080':'#1e293b80')+';border-left:3px solid '+(urgent?'#ea580c':'#64748b')+';border-radius:6px;padding:6px 8px;margin:5px 0\">'+
          (x.intl?'🌍 ':'')+x.from+(x.cor?' <span style=\"color:#64748b\">('+x.cor.n+')</span>':'')+'<br>'+
          '<span style=\"font-size:12px\">'+stops+'ЦАС <b>'+hm(x.cas)+'</b></span></div>';
      });
      html+='<div style=\"color:#64748b;font-size:11px;margin-top:6px\">ETA на спирките = ЦАС час − типичен пробег · оранжево = в прозорец ±20 мин</div>';
      panel.innerHTML=html;
    }).catch(function(e){});
  }
  refresh(); setInterval(refresh, 120000);
})();


// ------ bak-v5 ------
// (2) Централна автогара: реален деманд от пристигащите автобуси
(function(){
  var busState = {recent:0, soon:0, ts:0};

  function pull(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 100*60000;
      if(!fresh){ busState={recent:0,soon:0,ts:Date.now()}; return; }
      var now=new Date(), nowMin=now.getHours()*60+now.getMinutes();
      var recent=0, soon=0;
      (d.arrivals||[]).forEach(function(a){
        var m=/^(\d{1,2}):(\d{2})$/.exec(a.time||''); if(!m) return;
        var delta=(+m[1])*60+(+m[2])-nowMin;
        if(delta<=0 && delta>=-15) recent++;        // слезли са преди <=15 мин
        else if(delta>0 && delta<=25) soon++;       // идват до 25 мин
      });
      busState={recent:recent, soon:soon, ts:Date.now()};
    }).catch(function(e){});
  }
  pull(); setInterval(pull, 120000);

  if(typeof computeScores === 'function'){
    var _origCompute = computeScores;
    computeScores = function(h){
      var s = _origCompute(h);
      try{
        if(s && typeof s['cab_north'] === 'number'){
          // всеки току-що слязъл автобус тежи най-много (хората са на място СЕГА)
          var boost = Math.min(2.6, busState.recent*0.85 + busState.soon*0.65);
          if(boost>0) s['cab_north'] = s['cab_north'] + boost;
        }
      }catch(e){}
      return s;
    };
  }

  // видим маркер защо е горещо — малък надпис в списъка на автогарата
  setInterval(function(){
    var items=document.querySelectorAll('#zone-list .zone-item');
    Array.prototype.slice.call(items).forEach(function(it){
      var nm=it.querySelector('.zone-name');
      if(!nm || nm.textContent.indexOf('Централна автогара')<0) return;
      var sub=it.querySelector('.zone-sub');
      var txt='';
      if(busState.recent) txt='🚌 '+busState.recent+' слезли <15 мин';
      if(busState.soon) txt+=(txt?' · ':'')+busState.soon+' идват <25 мин';
      if(!txt) return;
      if(!sub){
        sub=document.createElement('div');
        sub.className='zone-sub';
        nm.parentElement.appendChild(sub);
      }
      sub.textContent=txt;
    });
  }, 15000);
})();

// (3) ЖП гара: честен статус, докато няма разписание
(function(){
  if(typeof showTransitPopup !== 'function') return;
  var _origTransit = showTransitPopup;
  showTransitPopup = function(zid){
    var r = _origTransit(zid);
    if(zid==='cjp'){
      setTimeout(function(){
        var pops=document.querySelectorAll('.leaflet-popup-content');
        if(!pops.length) return;
        var p=pops[pops.length-1];
        if(p.innerHTML.indexOf('bdz-note')>=0) return;
        p.innerHTML += '<div class="bdz-note" style="margin-top:8px;padding:7px 9px;border-radius:7px;'+
          'background:rgba(56,189,248,.08);border-left:3px solid #38bdf8;font-size:12px;color:#94a3b8">'+
          '🚂 Живо разписание на БДЖ — предстои.<br>Засега: пиковете са ~07:30, 13:00, 18:30, 21:40 '+
          '(пристигания от Пловдив/Варна/Бургас).</div>';
      }, 200);
    }
    return r;
  };
})();


// ------ bak-v6: жив мост към вътрешния scope ------
(function(){
  window.__liveDemand = {hub:{}, boost:{}};

  function num(x){ return typeof x==='number' && isFinite(x) ? x : 0; }

  function pullFlights(){
    fetch('flight-cache.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var now=Date.now(), soon=0;
      (d.data||[]).forEach(function(f){
        if(f.flight_status==='cancelled') return;
        var a=f.arrival||{}, land=a.estimated||a.scheduled;
        if(!land) return;
        var lt=new Date(land).getTime(); if(isNaN(lt)) return;
        var xs=lt+12*60000;                       // начало на изходния прозорец
        if(xs>now-20*60000 && xs<now+75*60000) soon++;
      });
      window.__liveDemand.hub.airport = soon ? Math.min(5, 1.0 + soon*0.6) : 0;
      window.__liveDemand.flights = soon;
    }).catch(function(e){});
  }

  function pullBuses(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 100*60000;
      if(!fresh){ window.__liveDemand.hub.cab_north=0; window.__liveDemand.boost.cab_north=0; return; }
      var now=new Date(), nowMin=now.getHours()*60+now.getMinutes(), recent=0, soon=0;
      (d.arrivals||[]).forEach(function(a){
        var m=/^(\d{1,2}):(\d{2})$/.exec(a.time||''); if(!m) return;
        var delta=(+m[1])*60+(+m[2])-nowMin;
        if(delta<=0 && delta>=-15) recent++;
        else if(delta>0 && delta<=25) soon++;
      });
      window.__liveDemand.boost.cab_north = Math.min(2.6, recent*0.85 + soon*0.65);
      window.__liveDemand.hub.cab_north   = (recent+soon) ? Math.min(4.5, 1.0 + recent*0.9 + soon*0.7) : 0;
      window.__liveDemand.buses = {recent:recent, soon:soon};
    }).catch(function(e){});
  }

  function pullTrains(){
    fetch('train-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 120*60000;
      if(!fresh){ window.__liveDemand.hub.cjp=0; window.__liveDemand.boost.cjp=0; return; }
      var now=new Date(), nowMin=now.getHours()*60+now.getMinutes(), w=0, n=0;
      (d.arrivals||[]).forEach(function(a){
        var m=/^(\d{1,2}):(\d{2})$/.exec(a.time||''); if(!m) return;
        var delta=(+m[1])*60+(+m[2])+num(a.delay)-nowMin;
        if(delta>=-15 && delta<=30){ w += num(a.weight)||0.5; n++; }
      });
      window.__liveDemand.boost.cjp = Math.min(2.4, w*1.05);
      window.__liveDemand.hub.cjp   = n ? Math.min(4.5, 1.0 + w*1.15) : 0;
      window.__liveDemand.trains = n;
    }).catch(function(e){});
  }

  function pull(){ pullFlights(); pullBuses(); pullTrains(); }
  pull(); setInterval(pull, 120000);

  // прилага живите boost-ове върху нормалните demand точки
  window.__applyLive = function(scores){
    try{
      var b = window.__liveDemand.boost || {};
      if(typeof scores.cab_north === 'number' && b.cab_north) scores.cab_north += b.cab_north;
      if(typeof scores.cjp === 'number' && b.cjp) scores.cjp += b.cjp;
    }catch(e){}
  };

  // КЪРК: хъбовете се състезават с кварталите + наказание за разстояние
  window.__karykLive = function(z, baseKs, ulat, ulng){
    var ks = num(baseKs);
    try{
      var h = (window.__liveDemand.hub||{})[z.id];
      if(typeof h === 'number' && h > 0) ks = Math.max(ks, h);
      if(typeof ulat === 'number' && typeof ulng === 'number'){
        var dx=(z.lat-ulat)*111, dy=(z.lng-ulng)*82;
        var km=Math.sqrt(dx*dx+dy*dy);
        if(km > 5) ks -= Math.min(1.3, (km-5)*0.11);   // далече = губиш време на празно
      }
    }catch(e){}
    return ks;
  };

  // подсказка защо е горещо — в КЪРК банера
  setInterval(function(){
    var el=document.getElementById('karyk-hint');
    if(!el || !document.body.classList.contains('karyk-active')) return;
    var L=window.__liveDemand||{}, bits=[];
    if(L.flights) bits.push('✈️ '+L.flights+' изхода');
    if(L.buses && (L.buses.recent+L.buses.soon)) bits.push('🚌 '+(L.buses.recent+L.buses.soon));
    if(L.trains) bits.push('🚂 '+L.trains);
    if(!bits.length) return;
    if(el.dataset.live === bits.join()) return;
    el.dataset.live = bits.join();
    var tag=el.querySelector('.live-tag');
    if(!tag){ tag=document.createElement('span'); tag.className='live-tag';
              tag.style.cssText='margin-left:8px;font-size:12px;opacity:.85'; el.appendChild(tag); }
    tag.textContent='· '+bits.join(' · ');
  }, 10000);
})();


// ------ bak-v7: rain-banner окончателно ------
// Предишният опит търсеше само #rain-banner. Ако е клас или без id,
// не го хващаше. Сега: по id, по клас И по текстово съдържание.
(function(){
  var RX = /Дъжд\s+около|Дъжд\s+\d{1,2}:\d{2}\s+до/;
  function kill(){
    var hits = [];
    var byId = document.getElementById('rain-banner');
    if(byId) hits.push(byId);
    Array.prototype.push.apply(hits, document.querySelectorAll('.rain-banner,#rain-banner,[data-rain]'));
    // текстов лов: fixed елемент в горната част на екрана с дъждовен текст
    Array.prototype.slice.call(document.querySelectorAll('div,span,section')).forEach(function(el){
      if(el.children.length > 2) return;
      var t = el.textContent || '';
      if(t.length > 90 || !RX.test(t)) return;
      var cs = window.getComputedStyle(el);
      if(cs.position === 'fixed' || cs.position === 'absolute' ||
         (el.parentElement && window.getComputedStyle(el.parentElement).position === 'fixed')) {
        hits.push(el);
      }
    });
    hits.forEach(function(el){ try{ el.remove(); }catch(e){ el.style.display='none'; } });
  }
  kill();
  setInterval(kill, 3000);
  // и при всяка промяна в DOM-а (ако се пресъздава)
  try{
    new MutationObserver(function(){ kill(); })
      .observe(document.body, {childList:true, subtree:true});
  }catch(e){}
})();


// ------ stop-eta-v12: ЧАСОВЕ на крайпътните спирки ------
// Инжектира ETA направо в popup-а на спирката, вместо в отделен панел.
(function(){
  var BUS = {list:[], ts:0};
  var HEMUS=/(ВАРНА|ШУМЕН|РУСЕ|РАЗГРАД|ТЪРГОВИЩЕ|ТЪРНОВО|ГАБРОВО|ПЛЕВЕН|ЛОВЕЧ|СЕВЛИЕВО|БЯЛА|ДОБРИЧ|СИЛИСТРА|БОТЕВГРАД|ПРАВЕЦ)/i;
  var TRAKIA=/(ПЛОВДИВ|БУРГАС|СТАРА ЗАГОРА|СТ\. ?ЗАГОРА|СЛИВЕН|ЯМБОЛ|ХАСКОВО|КЪРДЖАЛИ|ДИМИТРОВГРАД|ПАЗАРДЖИК|АСЕНОВГРАД|НЕСЕБЪР|СЛЪНЧЕВ|ПОМОРИЕ|СОЗОПОЛ)/i;
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
          var m=/^(\d{1,2}):(\d{2})$/.exec(a.time||''); if(!m) return;
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
    if(/бул\.? ?България|Хладилника/i.test(t)) return {n:'бул. България', off:14};
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
      if(!/Слизане от|Експо|Ботевградско|бул\.? ?България|Цариградско/i.test(txt)) return;
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
    /* v12 изключен от v18 */
    /* v12 изключен от v18 */
  }
  scan();
  setInterval(scan, 4000);
  try{ new MutationObserver(function(){ scan(); })
        .observe(document.body,{childList:true,subtree:true}); }catch(e){}
})();


// ------ pool-weather-v15: работно време + температура + изход при дъжд ------
(function(){
  // [делник_отваря, делник_затваря, уикенд_отваря, уикенд_затваря, закрит?]
  var POOLS = {
    pool_spartak:     [7,   21,   8.5, 18,   0],
    pool_diana:       [9.5, 18.5, 9.5, 18.5, 0],
    pool_akademika:   [7,   21,   8,   20,   0],
    pool_madara:      [7,   21.7, 7,   18,   0],
    pool_vazrazhdane: [9,   19,   9,   19,   0],
    pool_varadero:    [9,   19,   9,   19,   0],
    pool_thebeach:    [9,   22,   9,   23.7, 0],
    pool_silvercity:  [7,   22,   7,   22,   0],
    pool_hearts:      [10,  18,   9,   19,   0],
    pool_korali:      [9,   19,   9,   19,   0],
    pool_infinity:    [9,   20,   9,   20,   1],
    pool_sportpalace: [6.5, 19.5, 8,   17,   1]   // ЗАКРИТ — при дъжд печели
  };

  var W = {t:null, rainNow:0, rainSoon:null, cloud:0, ts:0};

  function pullWeather(){
    fetch('https://api.open-meteo.com/v1/forecast?latitude=42.6977&longitude=23.3219'
        + '&current=temperature_2m,precipitation,cloud_cover'
        + '&hourly=precipitation,precipitation_probability,cloud_cover'
        + '&forecast_days=2&timezone=Europe%2FSofia')
    .then(function(r){return r.json()}).then(function(d){
      var c = d.current || {};
      W.t = c.temperature_2m;
      W.rainNow = c.precipitation || 0;
      W.cloud = c.cloud_cover || 0;
      var t=d.hourly.time, p=d.hourly.precipitation, pp=d.hourly.precipitation_probability;
      var now=Date.now(); W.rainSoon=null;
      for(var i=0;i<t.length;i++){
        var ts=new Date(t[i]+':00+03:00').getTime();
        if(ts<=now) continue;
        if(ts>now+3*3600000) break;
        if((pp[i]>=55 && p[i]>=0.1) || p[i]>=0.4){ W.rainSoon=ts; break; }
      }
      W.ts=now;
    }).catch(function(e){});
  }
  pullWeather(); setInterval(pullWeather, 900000);   // на 15 мин

  function poolScore(zid){
    var h = POOLS[zid]; if(!h) return null;
    var now = new Date();
    var wknd = (now.getDay()===0 || now.getDay()===6);
    var open = wknd ? h[2] : h[0], close = wknd ? h[3] : h[1];
    var indoor = !!h[4];
    var hh = now.getHours() + now.getMinutes()/60;

    // Sport Palace не работи в неделя
    if(zid==='pool_sportpalace' && now.getDay()===0) return 0;
    // затворено -> мъртва зона (но 30 мин преди затваряне има изход)
    if(hh < open - 0.25) return 0;
    if(hh > close + 0.3) return 0;

    if(W.t === null) return null;   // без данни -> не пипаме

    // --- база по температура ---
    var s;
    if(indoor){
      s = 1.0;                                   // закритият е стабилен целогодишно
    } else {
      if(W.t < 22) s = 0.2;
      else if(W.t < 25) s = 0.7;
      else if(W.t < 28) s = 1.3;
      else if(W.t < 32) s = 2.0;
      else s = 2.5;
    }

    // --- следобеден пик ---
    if(hh >= 12 && hh <= 18) s *= 1.25;

    // --- изход в края на деня (последните 45 мин) ---
    if(hh >= close - 0.75 && hh <= close + 0.3) s += indoor ? 0.6 : 1.4;

    if(indoor){
      // при дъжд закритият печели — хората се прехвърлят
      if(W.rainNow >= 0.15) s += 0.8;
      return s;
    }

    // --- ⛈️ ИЗХОД ПРИ ДЪЖД (ключовото) ---
    if(W.rainNow >= 0.15){
      s += 3.2;                                  // валят навън -> масово бягство СЕГА
    } else if(W.rainSoon){
      var mins = (W.rainSoon - Date.now())/60000;
      if(mins <= 20) s += 2.8;                   // първите капки, всички станаха
      else if(mins <= 45) s += 1.9;              // небето почерня, започват да се прибират
      else if(mins <= 90) s += 0.9;
    } else if(W.cloud >= 75 && W.t < 27){
      s += 0.7;                                  // заоблачи се и застудя -> изтичане
    }
    return s;
  }

  // закачаме се към живия мост от v6
  var prev = window.__applyLive;
  window.__applyLive = function(scores){
    try{ if(prev) prev(scores); }catch(e){}
    try{
      for(var zid in POOLS){
        if(typeof scores[zid] !== 'number') continue;
        var ps = poolScore(zid);
        if(ps === null) continue;
        scores[zid] = (ps === 0) ? 0 : Math.max(scores[zid], ps);
      }
    }catch(e){}
  };

  // --- предупреждение: басейните всеки момент ще се изпразнят ---
  var chip=document.createElement('div');
  chip.style.cssText='position:fixed;left:8px;bottom:196px;z-index:1500;border-radius:10px;'
    +'padding:7px 11px;font-family:sans-serif;font-size:13px;font-weight:900;cursor:pointer;'
    +'box-shadow:0 2px 10px rgba(0,0,0,.5);display:none;background:#3a1a10f0;color:#fdba74;'
    +'border:1px solid #ea580c';
  chip.onclick=function(){ chip.style.display='none'; };
  document.body.appendChild(chip);

  function alertTick(){
    if(W.t === null) return;
    var now=new Date(), hh=now.getHours()+now.getMinutes()/60;
    var wknd=(now.getDay()===0||now.getDay()===6);
    // има ли изобщо отворени открити басейни сега?
    var openCnt=0;
    for(var zid in POOLS){
      var h=POOLS[zid]; if(h[4]) continue;
      var o=wknd?h[2]:h[0], c=wknd?h[3]:h[1];
      if(hh>=o && hh<=c) openCnt++;
    }
    if(!openCnt || W.t < 23){ chip.style.display='none'; return; }

    if(W.rainNow >= 0.15){
      chip.textContent='⛈️ Вали — басейните се изпразват СЕГА';
      chip.style.display='block';
    } else if(W.rainSoon){
      var m=Math.round((W.rainSoon-Date.now())/60000);
      if(m<=45){
        chip.textContent='🌧️ Дъжд след '+m+'м — '+openCnt+' басейна ще излязат';
        chip.style.display='block';
      } else chip.style.display='none';
    } else chip.style.display='none';
  }
  alertTick(); setInterval(alertTick, 60000);
})();


// ------ stop-eta-v18: часове от РАЗПИСАНИЕ + живи данни като бонус ------
(function(){
  var SCHED = null, BUS = [], TRAINS = null;

  function hm(d){ return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'}); }
  function mins(d){ return Math.round((d.getTime()-Date.now())/60000); }
  function whenTxt(m){
    if(m <= 0) return 'сега';
    if(m < 60) return 'след '+m+'м';
    return 'след '+Math.floor(m/60)+'ч '+(m%60)+'м';
  }

  // ── коя спирка е (от текста на popup-а и от името в разписанието) ──
  function keyOf(t){
    t = t || '';
    if(/expo|цариградско/i.test(t)) return 'expo';
    if(/ботевградско/i.test(t)) return 'botev';
    if(/бул\.? ?[Бб]ългария|струма|околовръстен/i.test(t)) return 'bulgaria';
    return null;
  }
  var LABEL = { expo:'Експо / Цариградско', botev:'Ботевградско шосе', bulgaria:'бул. България' };

  fetch('bus-schedule.json?v='+Date.now()).then(function(r){return r.json()})
    .then(function(d){ SCHED = d; }).catch(function(){});

  function pullLive(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 4*3600000;
      BUS = [];
      if(!fresh) return;
      (d.arrivals||[]).forEach(function(a){
        var m=/^(\d{1,2}):(\d{2})$/.exec(a.time||''); if(!m) return;
        var t=new Date(); t.setHours(+m[1],+m[2],0,0);
        if(t.getTime() < Date.now()-3*3600000) t.setDate(t.getDate()+1);
        BUS.push({t:t, from:a.from, intl:a.intl});
      });
    }).catch(function(){});
  }
  function pullTrains(){
    fetch('train-arrivals.json?v='+Date.now()).then(function(r){return r.json()})
      .then(function(d){ TRAINS = d; }).catch(function(){});
  }
  pullLive(); pullTrains();
  setInterval(function(){ pullLive(); pullTrains(); }, 180000);

  // ── пристигания на дадена спирка по разписание ──
  function fromSchedule(key){
    if(!SCHED || !SCHED.routes) return [];
    var out = [], now = Date.now();
    SCHED.routes.forEach(function(rt){
      if(!/София/i.test(rt.to || '')) return;           // само входящи
      (rt.stops || []).forEach(function(st){
        if(keyOf(st.name) !== key) return;
        (rt.departures || []).forEach(function(dep){
          var m = /^(\d{1,2}):(\d{2})$/.exec(dep); if(!m) return;
          var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
          t = new Date(t.getTime() + (st.offset_min||0)*60000);
          if(t.getTime() < now - 10*60000) t = new Date(t.getTime() + 864e5);
          if(t.getTime() > now + 5*3600000) return;
          out.push({ t:t, name:(rt.name||'').replace(/\s*→.*/,''), approx:!!rt.approx });
        });
      });
    });
    out.sort(function(a,b){ return a.t - b.t; });
    return out.slice(0, 5);
  }

  function busHTML(key){
    var list = fromSchedule(key);
    if(!list.length){
      return '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;'
           + 'background:rgba(148,163,184,.12);border-left:3px solid #94a3b8;'
           + 'font-size:12px;color:#64748b">🚌 Няма курсове в следващите 5ч</div>';
    }
    var first = mins(list[0].t), urgent = first <= 20;
    var rows = list.map(function(x){
      var m = mins(x.t);
      // има ли живо потвърждение от ЦАС (пристига ~15-20 мин след спирката)
      var conf = BUS.some(function(b){
        return Math.abs((b.t.getTime() - x.t.getTime())/60000 - 18) < 14;
      });
      return '<div style="margin:2px 0"><b>' + hm(x.t) + '</b> · ' + x.name
           + (x.approx ? ' <span style="opacity:.55">≈</span>' : '')
           + (conf ? ' <span style="color:#22c55e">●</span>' : '')
           + ' <span style="opacity:.65">(' + whenTxt(m) + ')</span></div>';
    }).join('');
    return '<div style="margin-top:7px;padding:7px 9px;border-radius:7px;background:'
         + (urgent ? 'rgba(234,88,12,.14)' : 'rgba(56,189,248,.10)')
         + ';border-left:3px solid ' + (urgent ? '#ea580c' : '#38bdf8') + ';font-size:12px">'
         + '<b>🚌 Слизане на ' + LABEL[key] + '</b>' + rows
         + '<div style="opacity:.55;font-size:11px;margin-top:4px">по разписание · ≈ ориентировъчно'
         + (BUS.length ? ' · <span style="color:#22c55e">●</span> потвърдено от ЦАС' : '') + '</div></div>';
  }

  function trainHTML(){
    if(!TRAINS || !TRAINS.arrivals || !TRAINS.arrivals.length){
      return '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;'
           + 'background:rgba(148,163,184,.12);border-left:3px solid #94a3b8;'
           + 'font-size:12px;color:#64748b">🚂 Няма данни от БДЖ в момента</div>';
    }
    var now = Date.now(), list = [];
    TRAINS.arrivals.forEach(function(a){
      var m = /^(\d{1,2}):(\d{2})$/.exec(a.time||''); if(!m) return;
      var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
      t = new Date(t.getTime() + (a.delay||0)*60000);
      if(t.getTime() < now - 20*60000) t = new Date(t.getTime() + 864e5);
      if(t.getTime() > now + 5*3600000) return;
      list.push({ t:t, from:a.from, train:a.train, delay:a.delay||0, tier:a.tier });
    });
    list.sort(function(a,b){ return a.t - b.t; });
    list = list.slice(0, 5);
    if(!list.length){
      return '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;'
           + 'background:rgba(148,163,184,.12);border-left:3px solid #94a3b8;'
           + 'font-size:12px;color:#64748b">🚂 Няма влакове в следващите 5ч</div>';
    }
    var far = list.filter(function(x){ return x.tier === 'far'; }).length;
    var urgent = mins(list[0].t) <= 20 && list[0].tier === 'far';
    var rows = list.map(function(x){
      var ic = x.tier === 'far' ? '🧳' : (x.tier === 'near' ? '·' : '•');
      return '<div style="margin:2px 0">' + ic + ' <b>' + hm(x.t) + '</b> · ' + x.from
           + ' <span style="opacity:.6">' + x.train + '</span>'
           + (x.delay ? ' <span style="color:#f59e0b">+' + x.delay + 'м</span>' : '')
           + ' <span style="opacity:.65">(' + whenTxt(mins(x.t)) + ')</span></div>';
    }).join('');
    return '<div style="margin-top:7px;padding:7px 9px;border-radius:7px;background:'
         + (urgent ? 'rgba(234,88,12,.14)' : 'rgba(56,189,248,.10)')
         + ';border-left:3px solid ' + (urgent ? '#ea580c' : '#38bdf8') + ';font-size:12px">'
         + '<b>🚂 Пристигащи влакове</b>' + rows
         + '<div style="opacity:.55;font-size:11px;margin-top:4px">🧳 = далечен (багаж) · '
         + far + ' от ' + list.length + ' са далечни</div></div>';
  }

  function enrich(el){
    try{
      if(!el || (el.dataset && el.dataset.eta18)) return;
      var txt = el.textContent || '';
      var html = null;

      // ЖП гара
      if(/[Жж][Пп] гара|Централна ЖП|железопът/i.test(txt) || el.querySelector('.bdz-note')){
        html = trainHTML();
        var old = el.querySelector('.bdz-note');
        if(old) old.remove();
      }
      // крайпътни спирки
      if(!html){
        if(!/Слизане от|Вход от/i.test(txt)) return;
        var k = keyOf(txt);
        if(!k) return;
        html = busHTML(k);
      }
      if(el.dataset) el.dataset.eta18 = '1';
      // махаме стария блок от v12, ако е останал
      var prev = el.querySelector('[data-eta12]');
      if(prev) prev.remove();
      el.insertAdjacentHTML('beforeend', html);
    }catch(e){}
  }

  function scan(){
    try{
      document.querySelectorAll('.leaflet-popup-content').forEach(enrich);
      document.querySelectorAll('[data-stop],.stop-card,.zone-detail').forEach(enrich);
    }catch(e){}
  }
  scan();
  setInterval(scan, 4000);
  try{ new MutationObserver(scan).observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();


// ------ cas-sched-v19: Централна автогара смята деманд от РАЗПИСАНИЕТО ------
(function(){
  var SCHED = null;
  fetch('bus-schedule.json?v='+Date.now()).then(function(r){return r.json()})
    .then(function(d){ SCHED = d; }).catch(function(){});

  // пристигания на ЦАС по разписание в прозорец [-20, +30] мин
  function casNow(){
    if(!SCHED || !SCHED.routes) return {recent:0, soon:0, names:[]};
    var now = Date.now(), recent = 0, soon = 0, names = [];
    SCHED.routes.forEach(function(rt){
      if(!/София/i.test(rt.to || '')) return;
      var dur = rt.duration_min || 0;
      (rt.departures || []).forEach(function(dep){
        var m = /^(\d{1,2}):(\d{2})$/.exec(dep); if(!m) return;
        var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
        t = new Date(t.getTime() + dur*60000);
        var diff = (t.getTime() - now) / 60000;
        if(diff < -180) diff += 1440;          // за вчерашни нощни курсове
        if(diff <= 0 && diff >= -20){ recent++; names.push((rt.name||'').replace(/\s*→.*/,'')); }
        else if(diff > 0 && diff <= 30){ soon++; names.push((rt.name||'').replace(/\s*→.*/,'')); }
      });
    });
    return {recent:recent, soon:soon, names:names.slice(0,4)};
  }

  var prev = window.__applyLive;
  window.__applyLive = function(scores){
    try{ if(prev) prev(scores); }catch(e){}
    try{
      var c = casNow();
      if(typeof scores.cab_north === 'number' && (c.recent || c.soon)){
        // слезлите преди малко тежат най-много — те са на място СЕГА
        var boost = Math.min(3.0, c.recent*0.9 + c.soon*0.55);
        scores.cab_north = Math.max(scores.cab_north, 1.0 + boost);
        window.__casInfo = c;
      }
    }catch(e){}
  };

  // подсказка в списъка защо гори
  setInterval(function(){
    try{
      var c = window.__casInfo; if(!c) return;
      var items = document.querySelectorAll('#zone-list .zone-item, .zone-item');
      Array.prototype.slice.call(items).forEach(function(it){
        var nm = it.querySelector('.zone-name') || it;
        if((nm.textContent||'').indexOf('Централна автогара') < 0) return;
        if(it.dataset && it.dataset.cas === (c.recent+'/'+c.soon)) return;
        if(it.dataset) it.dataset.cas = c.recent+'/'+c.soon;
        var sub = it.querySelector('.cas-sub');
        if(!sub){
          sub = document.createElement('div');
          sub.className = 'cas-sub';
          sub.style.cssText = 'font-size:11px;opacity:.75;margin-top:2px';
          nm.parentElement.appendChild(sub);
        }
        var bits = [];
        if(c.recent) bits.push('🚌 ' + c.recent + ' слезли <20м');
        if(c.soon) bits.push(c.soon + ' идват <30м');
        sub.textContent = bits.join(' · ') + (c.names.length ? ' (' + c.names.join(', ') + ')' : '');
      });
    }catch(e){}
  }, 12000);
})();


// ------ color-scale-v24: цвят още при малък шанс за клиент ------
(function(){
  return; // изключен от v33 — цветовете са в източника
  var orig = window.demandColor;

  // праг -> цвят. Сиво САМО при реално нула.
  var SCALE = [
    [0.35, '#8b95a5', 0.10],   // мъртво — бледо сиво, да не прави каша
    [0.80, '#4aa3c7', 0.20],   // минимален шанс — студено синьо
    [1.30, '#2fa88a', 0.28],   // има шанс — тюркоаз
    [1.90, '#4cba52', 0.34],   // приличен — зелено
    [2.50, '#a3c23a', 0.40],   // добър — жълто-зелено
    [3.10, '#e0a020', 0.46],   // силен — кехлибар
    [3.80, '#ef7a1a', 0.54],   // много силен — оранж
    [99,   '#e33b2e', 0.62]    // пик — червено
  ];

  function pick(s){
    for(var i = 0; i < SCALE.length; i++){
      if(s < SCALE[i][0]) return SCALE[i];
    }
    return SCALE[SCALE.length - 1];
  }

  window.demandColor = function(s, type){
    var out;
    try{ out = orig.apply(this, arguments); }catch(e){ out = {}; }
    try{
      var num = (typeof s === 'number') ? s : parseFloat(s) || 0;
      var p = pick(num), col = p[1], op = p[2];
      if(!out || typeof out !== 'object') out = {};
      // болниците си пазят собствения червен код
      if(type === 'hospital') return out;
      ['fill','color','stroke','border','fillColor','bg'].forEach(function(k){
        if(k in out) out[k] = col;
      });
      if(!('fill' in out)) out.fill = col;
      ['op','opacity','fillOpacity','alpha'].forEach(function(k){
        if(k in out && typeof out[k] === 'number') out[k] = op;
      });
    }catch(e){}
    return out;
  };
})();


// ------ karyk-shrink-v24: КЪРК бутонът да не закрива картата ------
(function(){
  try{
    var st = document.createElement('style');
    st.textContent = '#karyk-banner,#karyk-btn{transform:scale(.6)!important;transform-origin:left bottom!important;opacity:.85!important}#karyk-list,#karyk-sidebar,.karyk-item,.karyk-name,.karyk-score,.karyk-rank,.karyk-sub,.karyk-dot,#karyk-hint{transform:none!important;opacity:1!important}';
    document.head.appendChild(st);
  }catch(e){}
})();


// ------ cas-intl-v26: пристигащи на Централна автогара, вкл. МЕЖДУНАРОДНИ ------
(function(){
  var SCHED = null, LIVE = [];
  var FLAG = {
    'скопие':'🇲🇰','ниш':'🇷🇸','белград':'🇷🇸','солун':'🇬🇷','атина':'🇬🇷',
    'букурещ':'🇷🇴','истанбул':'🇹🇷','одрин':'🇹🇷','киев':'🇺🇦','кишинев':'🇲🇩',
    'виена':'🇦🇹','мюнхен':'🇩🇪','берлин':'🇩🇪','прага':'🇨🇿','будапеща':'🇭🇺'
  };
  function flagFor(name){
    var n = (name||'').toLowerCase();
    for(var k in FLAG){ if(n.indexOf(k) >= 0) return FLAG[k]; }
    return '🌍';
  }
  function hm(d){ return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'}); }
  function whenTxt(m){
    if(m <= 0) return 'сега';
    if(m < 60) return 'след ' + m + 'м';
    return 'след ' + Math.floor(m/60) + 'ч ' + (m%60) + 'м';
  }

  fetch('bus-schedule.json?v='+Date.now()).then(function(r){return r.json()})
    .then(function(d){ SCHED = d; }).catch(function(){});

  function pullLive(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 4*3600000;
      LIVE = [];
      if(!fresh) return;
      (d.arrivals||[]).forEach(function(a){
        var m = /^(\d{1,2}):(\d{2})$/.exec(a.time||''); if(!m) return;
        var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
        if(t.getTime() < Date.now()-3*3600000) t.setDate(t.getDate()+1);
        LIVE.push({t:t, from:a.from, intl:!!a.intl, sector:a.sector||''});
      });
    }).catch(function(){});
  }
  pullLive(); setInterval(pullLive, 180000);

  function casArrivals(){
    var out = [], now = Date.now();
    // 1) живи данни от ЦАС (най-точни)
    LIVE.forEach(function(b){
      var diff = (b.t.getTime()-now)/60000;
      if(diff < -25 || diff > 180) return;
      out.push({t:b.t, name:b.from, intl:b.intl, sector:b.sector, live:true});
    });
    // 2) разписание (винаги налично)
    if(SCHED && SCHED.routes){
      SCHED.routes.forEach(function(rt){
        if(!/София/i.test(rt.to||'')) return;
        var dur = rt.duration_min || 0;
        (rt.departures||[]).forEach(function(dep){
          var m = /^(\d{1,2}):(\d{2})$/.exec(dep); if(!m) return;
          var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
          t = new Date(t.getTime() + dur*60000);
          var diff = (t.getTime()-now)/60000;
          if(diff < -180) { t = new Date(t.getTime()+864e5); diff += 1440; }
          if(diff < -20 || diff > 180) return;
          var nm = (rt.name||'').replace(/\s*→.*/,'');
          // без дублиране с живите
          var dup = out.some(function(o){
            return o.live && Math.abs((o.t-t)/60000) < 25
                   && o.name.toUpperCase().indexOf(nm.toUpperCase().slice(0,4)) >= 0;
          });
          if(dup) return;
          out.push({t:t, name:nm, intl:!!rt.intl, approx:!!rt.approx, live:false});
        });
      });
    }
    out.sort(function(a,b){ return a.t - b.t; });
    return out;
  }

  function casHTML(){
    var list = casArrivals();
    if(!list.length){
      return '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;'
           + 'background:rgba(148,163,184,.12);border-left:3px solid #94a3b8;'
           + 'font-size:12px;color:#64748b">🚌 Няма пристигащи в следващите 3ч</div>';
    }
    var intl = list.filter(function(x){ return x.intl; });
    var top = list.slice(0, 6);
    var first = Math.round((top[0].t-Date.now())/60000);
    var urgent = first <= 20;
    var rows = top.map(function(x){
      var m = Math.round((x.t-Date.now())/60000);
      return '<div style="margin:2px 0">' + (x.intl ? flagFor(x.name)+' ' : '🚌 ')
           + '<b>' + hm(x.t) + '</b> · ' + x.name
           + (x.approx ? ' <span style="opacity:.5">≈</span>' : '')
           + (x.live ? ' <span style="color:#22c55e">●</span>' : '')
           + (x.sector ? ' <span style="opacity:.6">сек.' + x.sector + '</span>' : '')
           + ' <span style="opacity:.65">(' + whenTxt(m) + ')</span></div>';
    }).join('');
    var intlNote = intl.length
      ? '<div style="margin-top:5px;padding-top:5px;border-top:1px solid rgba(148,163,184,.25);'
        + 'font-size:11px;color:#93c5fd">🌍 <b>' + intl.length + ' международни</b> в следващите 3ч — '
        + 'багаж, дълъг път, почти сигурен курс</div>'
      : '';
    return '<div style="margin-top:7px;padding:7px 9px;border-radius:7px;background:'
         + (urgent ? 'rgba(234,88,12,.14)' : 'rgba(56,189,248,.10)')
         + ';border-left:3px solid ' + (urgent ? '#ea580c' : '#38bdf8') + ';font-size:12px">'
         + '<b>🚌 Пристигащи на ЦАС</b>' + rows + intlNote
         + '<div style="opacity:.5;font-size:11px;margin-top:4px">● живо от ЦАС · ≈ ориентировъчно</div></div>';
  }

  function enrich(el){
    try{
      if(!el || (el.dataset && el.dataset.cas26)) return;
      var txt = el.textContent || '';
      if(!/Централна автогара/i.test(txt)) return;
      // приложението вече си има списък с пристигащи -> не дублираме
      if(/по час на пристигане|модел на превозвача|Пристигащи на ЦАС/i.test(txt)) return;
      if(/Слизане от|Вход от/i.test(txt)) return;   // това е спирка, не автогарата
      if(el.dataset) el.dataset.cas26 = '1';
      el.insertAdjacentHTML('beforeend', casHTML());
    }catch(e){}
  }
  function scan(){
    try{
      document.querySelectorAll('.leaflet-popup-content').forEach(enrich);
      document.querySelectorAll('.zone-detail,[data-stop]').forEach(enrich);
    }catch(e){}
  }
  scan(); setInterval(scan, 4000);
  try{ new MutationObserver(scan).observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();


// ------ popup-scroll-v28: popup-ите да не заемат целия екран ------
(function(){
  try{
    var st = document.createElement('style');
    st.textContent = '/*popup-scroll-v28*/.leaflet-popup-content{max-height:52vh!important;overflow-y:auto!important;overflow-x:hidden!important;-webkit-overflow-scrolling:touch;}.leaflet-popup-content::-webkit-scrollbar{width:5px}.leaflet-popup-content::-webkit-scrollbar-thumb{background:rgba(120,140,170,.55);border-radius:3px}.leaflet-popup-content-wrapper{max-height:56vh!important;}';
    document.head.appendChild(st);
  }catch(e){}
})();


// ------ cas-intl-score-v28: скор на международната зона ------
(function(){
  var SCHED = null, LIVE = [];
  fetch('bus-schedule.json?v='+Date.now()).then(function(r){return r.json()})
    .then(function(d){ SCHED = d; }).catch(function(){});
  function pullLive(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 4*3600000;
      LIVE = fresh ? (d.arrivals||[]).filter(function(a){ return a.intl; }) : [];
    }).catch(function(){});
  }
  pullLive(); setInterval(pullLive, 180000);

  function intlNow(){
    var now = new Date(), nowMin = now.getHours()*60 + now.getMinutes();
    var recent = 0, soon = 0, names = [];
    LIVE.forEach(function(a){
      var m = /^(\d{1,2}):(\d{2})$/.exec(a.time||''); if(!m) return;
      var d = (+m[1])*60 + (+m[2]) - nowMin;
      if(d <= 0 && d >= -25){ recent++; names.push(a.from); }
      else if(d > 0 && d <= 40){ soon++; names.push(a.from); }
    });
    if(SCHED && SCHED.routes){
      SCHED.routes.forEach(function(rt){
        if(!rt.intl && !/СКОПИЕ|НИШ|БЕЛГРАД|СОЛУН|АТИНА|БУКУРЕЩ|ИСТАНБУЛ|ОДРИН|ЧОРЛУ|АНКАРА|БУРСА|КИЕВ|КИШИНЕВ|ВИЕНА|МЮНХЕН|БЕРЛИН|ПРАГА|БУДАПЕЩА|ЗАГРЕБ|ЛЮБЛЯНА|ТИРАНА|ПОДГОРИЦА|САРАЕВО|ОХРИД|БИТОЛЯ|СТРУМИЦА|КАВАЛА|ДРАМА/i.test(rt.name||"")) return;
        var dur = rt.duration_min || 0;
        (rt.departures||[]).forEach(function(dep){
          var m = /^(\d{1,2}):(\d{2})$/.exec(dep); if(!m) return;
          var t = (+m[1])*60 + (+m[2]) + dur;
          var d = t - nowMin;
          if(d < -180) d += 1440;
          var nm = (rt.name||'').replace(/\s*→.*/,'');
          if(d <= 0 && d >= -25){ recent++; names.push(nm); }
          else if(d > 0 && d <= 40){ soon++; names.push(nm); }
        });
      });
    }
    return {recent:recent, soon:soon, names:names.slice(0,3)};
  }

  var prev = window.__applyLive;
  window.__applyLive = function(scores){
    try{ if(prev) prev(scores); }catch(e){}
    try{
      if(typeof scores.cas_intl !== 'number') return;
      var c = intlNow();
      // международните носят багаж и почти винаги взимат такси
      var s = c.recent*1.5 + c.soon*0.9;
      scores.cas_intl = s > 0 ? Math.min(5, 0.6 + s) : 0.3;
      window.__intlInfo = c;
    }catch(e){}
  };
})();


// ------ intl-list-v29: международни автобуси + бележка за Подуяне ------
(function(){
  var SCHED = null, LIVE = [];
  var FLAG = {
    'скопие':'🇲🇰','ниш':'🇷🇸','белград':'🇷🇸','солун':'🇬🇷','атина':'🇬🇷',
    'букурещ':'🇷🇴','истанбул':'🇹🇷','одрин':'🇹🇷','киев':'🇺🇦','кишинев':'🇲🇩',
    'виена':'🇦🇹','мюнхен':'🇩🇪','берлин':'🇩🇪','прага':'🇨🇿','будапеща':'🇭🇺',
    'загреб':'🇭🇷','любляна':'🇸🇮','тирана':'🇦🇱','подгорица':'🇲🇪','сараево':'🇧🇦'
  };
  function flagFor(n){
    n = (n||'').toLowerCase();
    for(var k in FLAG){ if(n.indexOf(k) >= 0) return FLAG[k]; }
    return '🌍';
  }
  function hm(d){ return d.toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'}); }
  function whenTxt(m){
    if(m <= 0) return 'сега';
    if(m < 60) return 'след ' + m + 'м';
    return 'след ' + Math.floor(m/60) + 'ч ' + (m%60) + 'м';
  }

  fetch('bus-schedule.json?v='+Date.now()).then(function(r){return r.json()})
    .then(function(d){ SCHED = d; }).catch(function(){});
  function pullLive(){
    fetch('bus-arrivals.json?v='+Date.now()).then(function(r){return r.json()}).then(function(d){
      var fresh = d.updated && (Date.now()-new Date(d.updated).getTime()) < 4*3600000;
      LIVE = fresh ? (d.arrivals||[]).filter(function(a){ return a.intl; }) : [];
    }).catch(function(){});
  }
  pullLive(); setInterval(pullLive, 180000);

  function intlList(){
    var out = [], now = Date.now();
    LIVE.forEach(function(a){
      var m = /^(\d{1,2}):(\d{2})$/.exec(a.time||''); if(!m) return;
      var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
      if(t.getTime() < now-3*3600000) t.setDate(t.getDate()+1);
      var d = (t-now)/60000;
      if(d < -30 || d > 360) return;
      out.push({t:t, name:a.from, live:true, sector:a.sector||''});
    });
    if(SCHED && SCHED.routes){
      SCHED.routes.forEach(function(rt){
        if(!rt.intl && !/СКОПИЕ|НИШ|БЕЛГРАД|СОЛУН|АТИНА|БУКУРЕЩ|ИСТАНБУЛ|ОДРИН|ЧОРЛУ|АНКАРА|БУРСА|КИЕВ|КИШИНЕВ|ВИЕНА|МЮНХЕН|БЕРЛИН|ПРАГА|БУДАПЕЩА|ЗАГРЕБ|ЛЮБЛЯНА|ТИРАНА|ПОДГОРИЦА|САРАЕВО|ОХРИД|БИТОЛЯ|СТРУМИЦА|КАВАЛА|ДРАМА/i.test(rt.name||"")) return;
        var dur = rt.duration_min || 0;
        (rt.departures||[]).forEach(function(dep){
          var m = /^(\d{1,2}):(\d{2})$/.exec(dep); if(!m) return;
          var t = new Date(); t.setHours(+m[1], +m[2], 0, 0);
          t = new Date(t.getTime() + dur*60000);
          if(t.getTime() < now-3*3600000) t = new Date(t.getTime()+864e5);
          var d = (t-now)/60000;
          if(d < -30 || d > 360) return;
          var nm = (rt.name||'').replace(/\s*→.*/,'');
          var dup = out.some(function(o){
            return o.live && Math.abs((o.t-t)/60000) < 40
                && o.name.toUpperCase().slice(0,4) === nm.toUpperCase().slice(0,4);
          });
          if(!dup) out.push({t:t, name:nm, approx:true});
        });
      });
    }
    out.sort(function(a,b){ return a.t-b.t; });
    return out.slice(0, 7);
  }

  function intlHTML(){
    var list = intlList();
    if(!list.length){
      return '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;'
           + 'background:rgba(148,163,184,.12);border-left:3px solid #94a3b8;'
           + 'font-size:12px;color:#64748b">🌍 Няма международни в следващите 6ч</div>';
    }
    var first = Math.round((list[0].t-Date.now())/60000);
    var urgent = first <= 30;
    var rows = list.map(function(x){
      return '<div style="margin:3px 0">' + flagFor(x.name) + ' <b>' + hm(x.t) + '</b> · ' + x.name
           + (x.approx ? ' <span style="opacity:.5">≈</span>' : '')
           + (x.live ? ' <span style="color:#22c55e">●</span>' : '')
           + (x.sector ? ' <span style="opacity:.6">сек.' + x.sector + '</span>' : '')
           + ' <span style="opacity:.65">(' + whenTxt(Math.round((x.t-Date.now())/60000)) + ')</span></div>';
    }).join('');
    return '<div style="margin-top:7px;padding:7px 9px;border-radius:7px;background:'
         + (urgent ? 'rgba(234,88,12,.14)' : 'rgba(56,189,248,.10)')
         + ';border-left:3px solid ' + (urgent ? '#ea580c' : '#38bdf8') + ';font-size:12px">'
         + '<b>🌍 Международни пристигания</b>' + rows
         + '<div style="opacity:.55;font-size:11px;margin-top:5px">Дълъг път + багаж = почти сигурен курс<br>'
         + '● живо от ЦАС · ≈ по разписание на превозвача</div></div>';
  }

  function enrich(el){
    try{
      if(!el || (el.dataset && el.dataset.intl29)) return;
      var txt = el.textContent || '';
      if(/Междунар|Сердика \/ FlixBus|FlixBus/i.test(txt)){
        if(el.dataset) el.dataset.intl29 = '1';
        el.insertAdjacentHTML('beforeend', intlHTML());
        return;
      }
      if(/Автогара Подуяне/i.test(txt)){
        if(el.dataset) el.dataset.intl29 = '1';
        el.insertAdjacentHTML('beforeend',
          '<div style="margin-top:7px;padding:6px 8px;border-radius:6px;'
          + 'background:rgba(148,163,184,.12);border-left:3px solid #94a3b8;'
          + 'font-size:12px;color:#64748b">🚌 Северно/източно направление.<br>'
          + 'Няма публично разписание.</div>');
      }
    }catch(e){}
  }
  function scan(){
    try{
      document.querySelectorAll('.leaflet-popup-content').forEach(enrich);
      document.querySelectorAll('.zone-detail').forEach(enrich);
    }catch(e){}
  }
  scan(); setInterval(scan, 4000);
  try{ new MutationObserver(scan).observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();


// ------ ticker-future-v30: само предстоящи точки (напред ~5ч) ------
(function(){
  var HORIZON_H = 5;      // колко часа напред показваме
  var GRACE_MIN = 10;     // толкова минути след часа още се брои за "сега"

  function nowMin(){ var d = new Date(); return d.getHours()*60 + d.getMinutes(); }

  function ahead(hhmm){
    var m = /^(\d{1,2}):(\d{2})$/.exec(hhmm);
    if(!m) return null;
    var t = (+m[1])*60 + (+m[2]);
    var d = t - nowMin();
    if(d < -180) d += 1440;          // явно е за утре
    return d;
  }

  function keep(seg){
    var times = seg.match(/\b\d{1,2}:\d{2}\b/g);
    if(!times || !times.length) return true;      // без час — оставяме
    for(var i = 0; i < times.length; i++){
      var a = ahead(times[i]);
      if(a === null) continue;
      if(a >= -GRACE_MIN && a <= HORIZON_H*60) return true;
    }
    return false;
  }

  function findTicker(){
    var best = null, bestLen = 0;
    var sel = ['#ticker','.ticker','#event-ticker','.event-ticker','#marquee','.marquee',
               '#scroll-text','.scroll-text','#event-strip','.event-strip'];
    for(var i = 0; i < sel.length; i++){
      var el = document.querySelector(sel[i]);
      if(el && (el.textContent||'').length > bestLen){ best = el; bestLen = el.textContent.length; }
    }
    if(best) return best;
    var all = document.querySelectorAll('div,span,p');
    for(var j = 0; j < all.length; j++){
      var e = all[j], t = e.textContent || '';
      if(t.length < 40 || t.length > 3000) continue;
      if(e.children.length > 3) continue;
      var dots = (t.match(/·/g)||[]).length, tm = (t.match(/\b\d{1,2}:\d{2}\b/g)||[]).length;
      if(dots >= 2 && tm >= 2 && t.length > bestLen){ best = e; bestLen = t.length; }
    }
    return best;
  }

  function clean(){
    try{
      var el = findTicker();
      if(!el) return;
      var raw = el.dataset.tickerRaw;
      if(!raw){
        raw = el.textContent || '';
        if(raw.length < 30) return;
        el.dataset.tickerRaw = raw;
      }
      var parts = raw.split(/\s*·\s*/).filter(function(s){ return s.trim().length; });
      if(parts.length < 2) return;
      var kept = parts.filter(keep);
      if(!kept.length) kept = ['— няма събития в следващите ' + HORIZON_H + 'ч —'];
      var out = kept.join('  ·  ');
      if(el.textContent.trim() !== out.trim()) el.textContent = out;
    }catch(e){}
  }

  clean();
  setInterval(clean, 60000);
  try{
    var mo = new MutationObserver(function(muts){
      for(var i = 0; i < muts.length; i++){
        var t = muts[i].target;
        if(t && t.dataset && t.dataset.tickerRaw && t.textContent &&
           t.textContent.indexOf('·') >= 0 &&
           t.textContent.length > (t.dataset.tickerRaw.length * 0.9)){
          t.dataset.tickerRaw = t.textContent;
        }
      }
      clean();
    });
    mo.observe(document.body, {childList:true, subtree:true, characterData:true});
  }catch(e){}
})();


// ------ jam-status-v31: "ЗАДРЪСТЕНО СЕГА" само ако наистина е пиков час ------
(function(){
  function inPeak(txt){
    // чете реда "⏰ Пик: 07:30–09:30 делнични" от самия popup
    var m = txt.match(/Пик:\s*([\d:–\-\s и]+)/);
    if(!m) return null;
    var now = new Date();
    var wknd = (now.getDay() === 0 || now.getDay() === 6);
    if(/делнич/i.test(txt) && wknd) return false;      // само в делник
    var cur = now.getHours()*60 + now.getMinutes();
    var ranges = m[1].match(/(\d{1,2}):(\d{2})\s*[–\-]\s*(\d{1,2}):(\d{2})/g) || [];
    if(!ranges.length) return null;
    for(var i = 0; i < ranges.length; i++){
      var p = ranges[i].match(/(\d{1,2}):(\d{2})\s*[–\-]\s*(\d{1,2}):(\d{2})/);
      var a = (+p[1])*60 + (+p[2]), b = (+p[3])*60 + (+p[4]);
      if(cur >= a && cur <= b) return true;
    }
    return false;
  }

  function fix(el){
    try{
      if(!el || (el.dataset && el.dataset.jam31)) return;
      var txt = el.textContent || '';
      if(txt.indexOf('Пик:') < 0) return;
      if(!/ЗАДРЪСТЕНО СЕГА|В МОМЕНТА СВОБОДНО/.test(txt)) return;
      var peak = inPeak(txt);
      if(peak === null) return;
      if(el.dataset) el.dataset.jam31 = '1';
      var html = el.innerHTML;
      if(!peak){
        // извън пиков час: статусът става зелен, а съветът за обратна посока пада
        html = html.replace(/🔴\s*ЗАДРЪСТЕНО СЕГА/g, '🟢 СВОБОДНО (извън пиков час)');
        html = html.replace(/<div[^>]*>💡[^<]*<\/div>/g, '');
      } else {
        html = html.replace(/🟢\s*В МОМЕНТА СВОБОДНО/g, '🔴 ЗАДРЪСТЕНО СЕГА');
        html = html.replace(/💡\s*Карай\s*([←→↔↑↓])\s*обратно\s*—\s*стигаш по-бързо!/g,
                            '💡 Насрещното платно $1 е свободно');
      }
      // отсечка, не точка
      if(html.indexOf('отсечка') < 0){
        html = html.replace(/(⏰\s*Пик:)/,
          '<div style="font-size:11px;color:#64748b;margin:3px 0">'
          + '📍 Маркерът е ориентир за цялата отсечка, не точно място</div>$1');
      }
      el.innerHTML = html;
    }catch(e){}
  }
  function scan(){
    try{ document.querySelectorAll('.leaflet-popup-content').forEach(fix); }catch(e){}
  }
  scan(); setInterval(scan, 3000);
  try{ new MutationObserver(scan).observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();


// ------ flags-ticker-v32: истински знамена + четим тикер ------
(function(){
  // --- 1) emoji флагчета -> картинки (устройството ги рисува като букви) ---
  var RI_LOW = 0x1F1E6, RI_HIGH = 0x1F1FF;
  function pairToCode(s){
    try{
      var a = s.codePointAt(0), b = s.codePointAt(2);
      if(a < RI_LOW || a > RI_HIGH || b < RI_LOW || b > RI_HIGH) return null;
      return String.fromCharCode(97 + (a - RI_LOW)) + String.fromCharCode(97 + (b - RI_LOW));
    }catch(e){ return null; }
  }
  var FLAG_RX = /[\uD83C][\uDDE6-\uDDFF][\uD83C][\uDDE6-\uDDFF]/g;

  function imgFor(code){
    return '<img src="https://flagcdn.com/20x15/' + code + '.png" '
         + 'width="20" height="15" alt="' + code.toUpperCase() + '" '
         + 'style="vertical-align:-2px;border-radius:2px;box-shadow:0 0 0 1px rgba(0,0,0,.25)" '
         + 'onerror="this.replaceWith(document.createTextNode(this.alt))">';
  }

  function swapFlags(root){
    try{
      var sel = '.leaflet-popup-content, .zone-detail, [data-eta18], [data-intl29], '
              + '[data-cas26], .exit-panel, .bus-panel';
      var nodes = (root || document).querySelectorAll(sel);
      Array.prototype.forEach.call(nodes, function(el){
        if(el.dataset && el.dataset.flagged === '1') return;
        var h = el.innerHTML;
        if(!h || !FLAG_RX.test(h)) return;
        FLAG_RX.lastIndex = 0;
        el.innerHTML = h.replace(FLAG_RX, function(m){
          var c = pairToCode(m);
          return c ? imgFor(c) : m;
        });
        if(el.dataset) el.dataset.flagged = '1';
      });
    }catch(e){}
  }

  // --- 2) тикерът: четим текст ---
  function styleTicker(){
    try{
      if(document.getElementById('ticker-style-v32')) return;
      var st = document.createElement('style');
      st.id = 'ticker-style-v32';
      st.textContent =
        '[data-ticker-raw]{color:#e2ecf8!important;font-weight:600!important;'
        + 'text-shadow:0 1px 2px rgba(0,0,0,.55)!important;opacity:1!important;'
        + 'letter-spacing:.2px!important;}'
        + '[data-ticker-raw] *{color:inherit!important;opacity:1!important;}';
      document.head.appendChild(st);
    }catch(e){}
  }

  function tick(){ styleTicker(); swapFlags(); }
  tick();
  setInterval(tick, 2500);
  try{ new MutationObserver(function(){ tick(); })
        .observe(document.body, {childList:true, subtree:true}); }catch(e){}
})();


// ------ zones-tune-v33 ------
(function(){
  var MALLS = {
    paradise:1.18, ring_mall:1.12, the_mall:1.10, serdika:1.10,
    mall_sofia:1.0, bulgaria_mall:1.0, park_center:0.85
  };

  // моловете имат постоянен поток — под по часове (отваряне 10:00, затваряне 22:00)
  function mallFloor(zid){
    var w = MALLS[zid]; if(!w) return null;
    var d = new Date(), h = d.getHours() + d.getMinutes()/60;
    var wknd = (d.getDay() === 0 || d.getDay() === 6);
    var s;
    if(h < 9.5) s = 0.25;                        // затворен
    else if(h < 12) s = 0.9;                     // отваряне, рядко
    else if(h < 15) s = 1.35;                    // обедна вълна
    else if(h < 17.5) s = 1.5;
    else if(h < 20) s = 2.0;                     // следобеден/вечерен пик
    else if(h < 21.5) s = 2.3;                   // преди затваряне — най-силно
    else if(h < 22.4) s = 2.6;                   // изходната вълна
    else s = 0.3;
    if(wknd && h >= 11 && h <= 21) s *= 1.25;    // уикендът е по-силен
    return s * w;
  }

  // Студентски град: жилищен профил, не сесиен.
  // Живущи без коли (нови и чужденци) — като Кръстова вада.
  function studentskiScore(){
    var d = new Date(), h = d.getHours() + d.getMinutes()/60, day = d.getDay();
    var fri = (day === 5), sat = (day === 6), sun = (day === 0);
    var s;
    if(h < 6) s = (fri || sat) ? 1.9 : 0.8;      // нощем навън само в края на седмицата
    else if(h < 9.5) s = 1.5;                    // сутрин на работа/лекции
    else if(h < 16) s = 0.9;
    else if(h < 19) s = 1.3;                     // прибиране
    else if(h < 22) s = fri ? 2.1 : (sat ? 1.9 : 1.35);
    else s = fri ? 2.4 : (sat ? 2.2 : 1.2);      // излизане навън
    if(sun && h > 16) s += 0.4;                  // връщане в неделя вечер
    return s;
  }

  var prev = window.__applyLive;
  window.__applyLive = function(scores){
    try{ if(prev) prev(scores); }catch(e){}
    try{
      for(var zid in MALLS){
        if(typeof scores[zid] !== 'number') continue;
        var f = mallFloor(zid);
        if(f !== null) scores[zid] = Math.max(scores[zid], f);
      }
      if(typeof scores.studentski === 'number'){
        scores.studentski = studentskiScore();
      }
    }catch(e){}
  };

  // ---- надписи върху големите кръгове ----
  function shortName(z){
    var n = (z.name || '').replace(/\([^)]*\)/g, '').trim();
    n = n.replace(/^(жк|ЖК)\s+/, '').replace(/^Мол\s+/i, '').replace(/^Хотели\s+/i, '');
    n = n.replace(/\s*[–—-]\s*.*$/, '');
    var words = n.split(/\s+/).filter(Boolean);
    var out = words.slice(0, 2).join(' ');
    if(out.length > 15) out = words[0];
    if(out.length > 15) out = out.slice(0, 14) + '…';
    return out;
  }
  var LABEL_TYPES = {airport:1, transit:1, mall:1, residential:1, residential_lux:1,
                     hospital:1, university:1, venue:1};

  function addLabels(){
    try{
      var map = window.__leafletMap, Z = window.__ZONES;
      if(!map || !Z || !window.L) return;
      if(map.getZoom() < 12){ 
        if(window.__labelLayer){ map.removeLayer(window.__labelLayer); window.__labelLayer = null; }
        return;
      }
      if(window.__labelLayer) return;                 // вече са сложени
      var lg = L.layerGroup();
      Z.forEach(function(z){
        if(!z.radius || z.radius < 240) return;       // само големите
        if(!LABEL_TYPES[z.type]) return;
        var txt = shortName(z);
        if(!txt) return;
        lg.addLayer(L.marker([z.lat, z.lng], {
          interactive: false,
          icon: L.divIcon({
            className: '',
            html: '<div style="white-space:nowrap;font:600 11px/1.1 system-ui,sans-serif;'
                + 'color:#f2f6fc;text-shadow:0 1px 3px #000,0 0 6px #000;'
                + 'transform:translate(-50%,-50%);pointer-events:none">'
                + (z.icon || '') + ' ' + txt + '</div>',
            iconSize: [0, 0]
          })
        }));
      });
      lg.addTo(map);
      window.__labelLayer = lg;
    }catch(e){}
  }
  function refreshLabels(){
    try{
      var map = window.__leafletMap;
      if(!map) return;
      if(window.__labelLayer){ map.removeLayer(window.__labelLayer); window.__labelLayer = null; }
      addLabels();
    }catch(e){}
  }
  var t = setInterval(function(){
    if(window.__leafletMap && window.__ZONES){
      clearInterval(t);
      addLabels();
      try{ window.__leafletMap.on('zoomend', refreshLabels); }catch(e){}
    }
  }, 700);

  // ---- десктоп/телефон ----
  try{
    var st = document.createElement('style');
    st.id = 'responsive-v33';
    st.textContent =
      '@media (min-width:1024px){'
      + 'body{max-width:1400px;margin:0 auto;}'
      + '#map{height:62vh!important;min-height:520px!important;}'
      + '.leaflet-popup-content{font-size:14px!important;max-height:60vh!important;}'
      + '}'
      + '@media (max-width:480px){'
      + '.leaflet-popup-content{font-size:12.5px!important;}'
      + '.leaflet-popup-content-wrapper{border-radius:12px!important;}'
      + '}'
      + '@media (min-width:1400px){ #map{height:68vh!important;} }';
    document.head.appendChild(st);
  }catch(e){}
})();

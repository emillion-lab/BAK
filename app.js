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
let airportStatus     = 'offline';
let demandCurve       = [];
let alertedEvents     = new Set();

// ═══════════════════════════════════════════════
// ZONE DEFINITIONS
// ═══════════════════════════════════════════════
const ZONES = [
  { id:"airport",        name:"Летище София (СОФ)",                     icon:"✈️",  lat:42.6950, lng:23.4083, radius:600, type:"airport",          wazeName:"Летище София" },
  { id:"bpark",          name:"Business Park Sofia",                    icon:"🏢", lat:42.6292, lng:23.3731, radius:380, type:"office",           wazeName:"Business Park Sofia" },
  { id:"garitage",       name:"Garitage Park",                          icon:"🏢", lat:42.6227, lng:23.3735, radius:320, type:"office",           wazeName:"Garitage Park Sofia" },
  { id:"polygraphia",    name:"Polygraphia Office Center",              icon:"🏢", lat:42.6700, lng:23.3820, radius:260, type:"office",           wazeName:"Polygraphia Office Center Sofia" },
  { id:"capital_fort",   name:"Capital Fort",                           icon:"🏢", lat:42.6464, lng:23.3958, radius:230, type:"office",           wazeName:"Capital Fort Sofia" },
  { id:"megapark",       name:"Megapark / The Mall офиси",              icon:"🏢", lat:42.6600, lng:23.3840, radius:260, type:"office",           wazeName:"Megapark Sofia" },
  { id:"advance_bc",     name:"Advance Business Center",                icon:"🏢", lat:42.6290, lng:23.3720, radius:230, type:"office",           wazeName:"Advance Business Center Sofia" },
  { id:"expo2000",       name:"Expo 2000 / Ellipse Center",             icon:"🏢", lat:42.6535, lng:23.3958, radius:280, type:"office",           wazeName:"Expo 2000 Sofia" },
  { id:"iec",            name:"IEC / Интер Експо Център",               icon:"🏢", lat:42.6710, lng:23.4020, radius:280, type:"office",           wazeName:"Inter Expo Center Sofia" },
  { id:"office_center",  name:"Офис Център (пл.Патриарх Евтимий)",     icon:"🏢", lat:42.6883, lng:23.3285, radius:230, type:"office",           wazeName:"площад Патриарх Евтимий София" },
  { id:"sopharma_bc",    name:"Sopharma Business Towers",               icon:"🏢", lat:42.7195, lng:23.3142, radius:200, type:"office",           wazeName:"Sopharma Business Towers Sofia" },
  { id:"telus",          name:"Telus Tower / пл.Македония",             icon:"🏢", lat:42.6947, lng:23.3154, radius:180, type:"office",           wazeName:"Telus Tower Sofia" },
  { id:"millennium",     name:"Millennium Center (бул.Витоша)",         icon:"🏢", lat:42.6822, lng:23.3147, radius:200, type:"office",           wazeName:"Millennium Center Sofia" },
  { id:"oval",           name:"Oval Business Center (Лозенец)",         icon:"🏢", lat:42.6640, lng:23.3340, radius:180, type:"office",           wazeName:"Oval Business Center Sofia" },

  { id:"serdika",        name:"Мол Сердика",                            icon:"🛍", lat:42.6976, lng:23.3243, radius:240, type:"mall",             wazeName:"Serdika Center Sofia" },
  { id:"paradise",       name:"Paradise Center",                        icon:"🛍", lat:42.6578, lng:23.3144, radius:290, type:"mall",             wazeName:"Paradise Center Sofia" },
  { id:"mall_sofia",     name:"Mall of Sofia",                          icon:"🛍", lat:42.6981, lng:23.3086, radius:210, type:"mall",             wazeName:"Mall of Sofia" },
  { id:"ring_mall",      name:"Ring Mall / IKEA",                       icon:"🛍", lat:42.6246, lng:23.3519, radius:340, type:"mall",             wazeName:"Ring Mall Sofia" },
  { id:"the_mall",       name:"The Mall Sofia",                         icon:"🛍", lat:42.6605, lng:23.3822, radius:290, type:"mall",             wazeName:"The Mall Sofia" },
  { id:"bulgaria_mall",  name:"България Мол",                           icon:"🛍", lat:42.6641, lng:23.2885, radius:240, type:"mall",             wazeName:"Bulgaria Mall Sofia" },
  { id:"park_center",    name:"Park Center (бул.Черни връх до НДК)",    icon:"🛍", lat:42.6869, lng:23.3182, radius:190, type:"mall",             wazeName:"Park Center Sofia" },

  { id:"hotels_ctr",     name:"Хотели Център (Radisson/Hilton)",        icon:"🏨", lat:42.6953, lng:23.3242, radius:280, type:"hotel",            wazeName:"Radisson Blu Sofia" },
  { id:"hotels_ndk",     name:"Kempinski / InterContinental НДК",       icon:"🏨", lat:42.6855, lng:23.3188, radius:180, type:"hotel",            wazeName:"Kempinski Hotel Zografski Sofia" },
  { id:"hotel_marinela", name:"Хотел Маринела (бул.Черни връх 100)",    icon:"🏨", lat:42.6623, lng:23.3175, radius:160, type:"hotel",            wazeName:"Hotel Marinela Sofia" },

  { id:"cjp",            name:"Централна ЖП гара",                      icon:"🚂", lat:42.7121, lng:23.3210, radius:240, type:"transit",          wazeName:"Централна жп гара София" },
  { id:"cab_north",      name:"Централна автогара",                     icon:"🚌", lat:42.7103, lng:23.3233, radius:200, type:"transit",          wazeName:"Централна автогара София" },
  { id:"ag_yug",         name:"Автогара Юг (бул.Драган Цанков)",        icon:"🚌", lat:42.6784, lng:23.3405, radius:190, type:"transit",          wazeName:"Автогара Юг София" },
  { id:"ag_pod",         name:"Автогара Подуяне",                       icon:"🚌", lat:42.7015, lng:23.3758, radius:190, type:"transit",          wazeName:"Автогара Подуяне София" },

  { id:"arena",          name:"Арена 8888",                             icon:"🎸", lat:42.6711, lng:23.3692, radius:290, type:"venue",            wazeName:"Arena Sofia 8888" },
  { id:"ndk",            name:"НДК",                                    icon:"🎭", lat:42.6855, lng:23.3188, radius:260, type:"venue",            wazeName:"Национален дворец на културата НДК" },
  { id:"borisova",       name:"Борисова градина / Стадион Левски",      icon:"🌳", lat:42.6838, lng:23.3450, radius:340, type:"leisure",          wazeName:"Борисова градина София" },
  { id:"nat_theatre",    name:"Народен театър Иван Вазов",              icon:"🎭", lat:42.6951, lng:23.3297, radius:180, type:"theatre",          wazeName:"Народен театър Иван Вазов София" },
  { id:"opera",          name:"Национална опера и балет",               icon:"🎶", lat:42.6946, lng:23.3229, radius:180, type:"theatre",          wazeName:"Национална опера и балет София" },
  { id:"ndk_theatre",    name:"Театри / НДК зона",                      icon:"🎭", lat:42.6843, lng:23.3196, radius:200, type:"theatre",          wazeName:"НДК театри София" },

  { id:"pirogov",        name:"УМБАЛ Пирогов (бул.Тотлебен 21)",        icon:"🏥", lat:42.6933, lng:23.3177, radius:190, type:"hospital",         wazeName:"УМБАЛСМ Пирогов бул Тотлебен 21 София" },
  { id:"alexand",        name:"Александровска болница",                 icon:"🏥", lat:42.6958, lng:23.3093, radius:190, type:"hospital",         wazeName:"УМБАЛ Александровска болница София" },
  { id:"vma",            name:"ВМА (бул.Св.Георги Софийски 3)",         icon:"🏥", lat:42.6856, lng:23.3192, radius:170, type:"hospital",         wazeName:"ВМА Военномедицинска академия София" },
  { id:"tokuda",         name:"Acibadem Токуда (бул.Н.Вапцаров 51Б)",  icon:"🏥", lat:42.6600, lng:23.3230, radius:160, type:"hospital",         wazeName:"Acibadem City Clinic Токуда Sofia" },
  { id:"sv_anna",        name:"УМБАЛ Света Анна",                       icon:"🏥", lat:42.6618, lng:23.3732, radius:160, type:"hospital",         wazeName:"УМБАЛ Света Анна Sofia" },
  { id:"sv_ekaterina",   name:"УМБАЛ Света Екатерина",                  icon:"🏥", lat:42.6856, lng:23.3148, radius:160, type:"hospital",         wazeName:"УМБАЛ Света Екатерина Sofia" },
  { id:"acibadem_ortho", name:"Acibadem Ортопедия (Околовръстен 127)", icon:"🏥", lat:42.6355, lng:23.3510, radius:150, type:"hospital",         wazeName:"Acibadem Ортопедия Околовръстен Sofia" },
  { id:"isul",           name:"ИСУЛ (ул.Коньовица 65)",                 icon:"🏥", lat:42.7008, lng:23.3445, radius:160, type:"hospital",         wazeName:"ИСУЛ болница Sofia" },

  { id:"unss",           name:"УНСС",                                   icon:"🎓", lat:42.6796, lng:23.3127, radius:240, type:"university",       wazeName:"УНСС София" },
  { id:"nbu",            name:"НБУ (ул.Монтевидео 21)",                 icon:"🎓", lat:42.6580, lng:23.2968, radius:190, type:"university",       wazeName:"Нов Български Университет НБУ" },
  { id:"tu",             name:"Технически университет",                 icon:"🎓", lat:42.6569, lng:23.3532, radius:210, type:"university",       wazeName:"Технически университет София" },
  { id:"su",             name:"Софийски университет",                   icon:"🎓", lat:42.6943, lng:23.3318, radius:200, type:"university",       wazeName:"Софийски университет Св Климент Охридски" },
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
  { id:"nat_theatre",    name:"Народен театър Иван Вазов",              icon:"🎭", lat:42.6951, lng:23.3297, radius:180, type:"theatre",          wazeName:"Народен театър Иван Вазов София" },
  { id:"youth_theatre",  name:"Младежки театър (бул.Дондуков 8)",       icon:"🎭", lat:42.6985, lng:23.3254, radius:150, type:"theatre",          wazeName:"Младежки театър Николай Бинев София" },
  { id:"satira",         name:"Театър Сатирикон",                       icon:"🎭", lat:42.6945, lng:23.3285, radius:140, type:"theatre",          wazeName:"Театър Сатирикон София" },
  { id:"opera",          name:"Национална опера и балет",               icon:"🎶", lat:42.6946, lng:23.3229, radius:180, type:"theatre",          wazeName:"Национална опера и балет София" },
  { id:"theatre_199",    name:"Театър 199 (бул.Евлоги Георгиев 199)",   icon:"🎭", lat:42.6804, lng:23.3470, radius:140, type:"theatre",          wazeName:"Театър 199 Sofia" },

  // ── КИНА ──
  { id:"cinema_city_ml", name:"Cinema City Mall of Sofia",              icon:"🎬", lat:42.6981, lng:23.3086, radius:160, type:"cinema",           wazeName:"Cinema City Mall of Sofia" },
  { id:"cinema_city_ser",name:"Cinema City Сердика",                    icon:"🎬", lat:42.6976, lng:23.3243, radius:160, type:"cinema",           wazeName:"Cinema City Serdika Center Sofia" },
  { id:"cinema_arena",   name:"Кино Арена (Ring Mall)",                 icon:"🎬", lat:42.6246, lng:23.3519, radius:160, type:"cinema",           wazeName:"Кино Арена Grand Cinema Ring Mall Sofia" },
  { id:"cineland",       name:"Cineland (Paradise Center)",             icon:"🎬", lat:42.6578, lng:23.3144, radius:150, type:"cinema",           wazeName:"Cineland Paradise Center Sofia" },
  { id:"dom_kinoto",     name:"Дом на киното (ул.Екзарх Йосиф 37)",    icon:"🎬", lat:42.6978, lng:23.3331, radius:130, type:"cinema",           wazeName:"Дом на киното Sofia" },

  // ── РЕСТОРАНТИ / НОЩЕН ЖИВОТ ──
  { id:"vitosha_bar",    name:"Бул.Витоша – ресторанти/барове",         icon:"🍷", lat:42.6890, lng:23.3220, radius:250, type:"nightlife",        wazeName:"булевард Витоша ресторанти София" },
  { id:"lozenets_rest",  name:"Ресторанти Лозенец (Водна кула)",        icon:"🍽", lat:42.6713, lng:23.3382, radius:220, type:"nightlife",        wazeName:"ресторанти Лозенец Водна кула София" },
  { id:"center_bars",    name:"Барове / клубове Център (ул.Раковски)",  icon:"🍺", lat:42.6960, lng:23.3310, radius:200, type:"nightlife",        wazeName:"улица Раковски Sofia" },

  // ── ДОПЪЛНИТЕЛНИ БОЛНИЦИ ──
  { id:"acibadem_tokuda",name:"Acibadem Токуда (бул.Н.Вапцаров 51Б)",  icon:"🏥", lat:42.6600, lng:23.3230, radius:160, type:"hospital",         wazeName:"Acibadem City Clinic Токуда Sofia" },
  { id:"acibadem_cardio",name:"Acibadem Сърдечно-съдов (бул.Н.Вапцаров 53)",icon:"🏥",lat:42.6593,lng:23.3225,radius:140,type:"hospital",       wazeName:"Acibadem City Clinic Сърдечно-съдов Sofia" },
  { id:"acibadem_mladost",name:"Acibadem Младост (Цариградско шосе)",   icon:"🏥", lat:42.6430, lng:23.3780, radius:160, type:"hospital",         wazeName:"Acibadem City Clinic Младост Sofia" },
  { id:"sv_ekaterina",   name:"УМБАЛ Света Екатерина",                  icon:"🏥", lat:42.6856, lng:23.3148, radius:160, type:"hospital",         wazeName:"УМБАЛ Света Екатерина Sofia" },
  { id:"lozenets_h",     name:"УБ Лозенец (към СУ)",                    icon:"🏥", lat:42.6748, lng:23.3307, radius:150, type:"hospital",         wazeName:"Университетска болница Лозенец Sofia" },
  { id:"kardiologia",    name:"Национална кардиологична болница",       icon:"🏥", lat:42.6882, lng:23.3262, radius:150, type:"hospital",         wazeName:"Национална кардиологична болница Sofia" },
  { id:"sv_sofia_h",     name:"МБАЛ Св.София (бул.България 104)",       icon:"🏥", lat:42.6790, lng:23.2980, radius:160, type:"hospital",         wazeName:"МБАЛ Света София Sofia" },

  // ── ЗАДРЪСТВАНИЯ ──
  { id:"jam_orl",        name:"⚠ Задръстване Орлов мост",               icon:"🚦", lat:42.6838, lng:23.3345, radius:150, type:"traffic",          wazeName:"Орлов мост София" },
  { id:"jam_tsar",       name:"⚠ Задръстване Цариградско (Армейски)",   icon:"🚦", lat:42.6662, lng:23.3795, radius:200, type:"traffic",          wazeName:"Цариградско шосе Армейски Sofia" },
  { id:"jam_ndk",        name:"⚠ Задръстване бул.България",             icon:"🚦", lat:42.6820, lng:23.3050, radius:160, type:"traffic",          wazeName:"булевард България Sofia" },
  { id:"jam_serdika",    name:"⚠ Задръстване Сердика / бул.Сливница",   icon:"🚦", lat:42.7012, lng:23.3228, radius:160, type:"traffic",          wazeName:"Сердика бул Сливница Sofia" },
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
  { zone:"cjp",          name:"Влак София–Варна",               endHour:18.5, boost:2.2, repeat:"daily" },
  { zone:"cjp",          name:"Влак Sofia–Пловдив",             endHour:20.0, boost:1.8, repeat:"daily" },
  { zone:"ag_yug",       name:"Автобуси от Пловдив",            endHour:19.5, boost:2.0, repeat:"daily" },
  { zone:"ag_yug",       name:"Нощни автобуси",                 endHour:22.0, boost:1.5, repeat:"daily" },

  // Болници — меки вълни
  { zone:"pirogov",      name:"Пирогов – прегледи",             endHour:9.0,  boost:1.4, repeat:"daily" },
  { zone:"pirogov",      name:"Пирогов – вечерни посещения",    endHour:18.5, boost:1.2, repeat:"daily" },
  { zone:"alexand",      name:"Александровска – прегледи",      endHour:9.0,  boost:1.3, repeat:"daily" },
  { zone:"tokuda",       name:"Токуда – прегледи",              endHour:9.0,  boost:1.1, repeat:"daily" },
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
function demandColor(score, type) {
  if (type === 'hospital')
    return score>=2.0 ? {fill:"#ff2020",fillAlpha:0.75,stroke:"#ff6060",label:"🏥 Активно"}
         : score>=1.3 ? {fill:"#ef4444",fillAlpha:0.60,stroke:"#ff5555",label:"🏥"}
         :              {fill:"#991b1b",fillAlpha:0.40,stroke:"#cc3333",label:"🏥"};
  if (type === 'karyk')
    return {fill:"#f97316",fillAlpha:0.0,stroke:"transparent",label:"🥉"};
  if (score>=3.2) return {fill:"#ef4444",fillAlpha:0.55,stroke:"#ff7777",label:"ПИК 🔥"};
  if (score>=2.4) return {fill:"#f97316",fillAlpha:0.50,stroke:"#ffaa55",label:"Висок ▲"};
  if (score>=1.6) return {fill:"#f59e0b",fillAlpha:0.45,stroke:"#ffd060",label:"Среден"};
  if (score>=0.8) return {fill:"#22c55e",fillAlpha:0.35,stroke:"#55ee88",label:"Нормален"};
  return               {fill:"#1a3050",fillAlpha:0.20,stroke:"#2a4870",label:"Тих"};
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
      activeEvents[ev.zone].push({name:ev.name, f});
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
      c.on('click',()=>showZonePopup(z.id)); c.addTo(map); circleMap[z.id]=c;
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
    c.on('click',()=>showZonePopup(z.id)); c.addTo(map); circleMap[z.id]=c;
  });
}

function getScoreStyle(score, type) {
  const c=demandColor(score,type);
  return {color:c.stroke, fillColor:c.fill, fillOpacity:c.fillAlpha, weight:1.5, opacity:0.85};
}

function updateCircles() {
  const {scores}=computeScores(currentHour);
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

function showZonePopup(zid) {
  const z=ZONES.find(x=>x.id===zid); if(!z) return;
  const {scores,activeEvents}=computeScores(currentHour);
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
  const {scores,activeEvents}=computeScores(hour);
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
        return `<div class="zone-item" onclick="(function(){map.setView([${z.lat},${z.lng}],15);showZonePopup('${zid}')})()">
          <div class="zone-dot" style="background:${c.fill}"></div>
          <div style="flex:1;min-width:0">
            <div class="zone-name">${z.icon} ${z.name}</div>
            ${sub?`<div class="zone-sub">${sub}</div>`:''}
          </div>
          <div class="zone-score" style="color:${c.fill}">${score.toFixed(1)}</div>
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
      return `<div class="karyk-item" onclick="(function(){map.setView([${z.lat},${z.lng}],15);showZonePopup('${z.id}')})()">
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
    const s=scores[z.id]||0; if(s<1.6) return;
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
  document.getElementById('dh-addr').textContent=`${DIRS[Math.round(bear/45)%8]} · ${distTxt}`;
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
    const {scores}=computeScores(currentHour);
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
    const {scores}=computeScores(currentHour);
    const gems=ZONES.filter(z=>z.type==='karyk'||z.type==='residential_lux'||z.type==='residential')
      .map(z=>({z,ks:computeKarykScore(z.id,scores)})).sort((a,b)=>b.ks-a.ks);
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

function loadFlights(); loadBuses(){
  fetch('flight-cache.json')
    .then(r=>{if(!r.ok)throw 0;return r.json();})
    .then(data=>{
      const fl=data.data||[]; if(!fl.length) throw 0;
      flightHours=Array(24).fill(0);
      fl.forEach(f=>{
        if(!f.arrival?.scheduled) return;
        const t=new Date(f.arrival.estimated||f.arrival.scheduled);
        const nonEU=(f.departure?.airport||'').toLowerCase().match(/tur|israel|uk/);
        const ready=new Date(t.getTime()+(nonEU?20:10)*60000);
        // Sofia = EEST = UTC+3 in summer
        const sofiaH=(ready.getUTCHours()+3)%24;
        flightHours[sofiaH]++;
      });
      airportStatus='live';
      injectAirportEvents(); updateAirportBadge();
      buildCurve(); buildTicker(); render(currentHour);
    })
    .catch(()=>{
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

  const nextPlov = getNextBuses('plovdiv_sofia', 4);
  const nextSof  = getNextBuses('sofia_plovdiv', 3);

  let html = '<div style="font-size:14px;font-weight:800;color:var(--cyan);margin-bottom:8px">🚌 Автобуси</div>';

  if(nextPlov.length){
    html += '<div style="font-size:12px;color:var(--muted);font-weight:700;margin-bottom:4px">Пловдив → София (пристигане)</div>';
    for(const b of nextPlov){
      const urgency = b.diffMin < 0 ? 'color:#ef4444' : b.diffMin < 30 ? 'color:#f59e0b;font-weight:800' : 'color:var(--text)';
      const label = b.diffMin < 0 ? `тръгнал (пристига ~${b.arr})` :
                    b.diffMin < 60 ? `след ${b.diffMin} мин → пристига ${b.arr}` :
                    `${b.dep} → пристига ${b.arr}`;
      html += `<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border);font-size:13px">
        <span>🚌 ${b.dep}</span>
        <span style="${urgency}">${label}</span>
      </div>`;
    }
  }

  html += '<div style="margin-top:8px;font-size:11px;color:var(--muted)">Expo Center спирка: ~100 мин след тръгване от Пловдив</div>';
  panel.innerHTML = html;

  // Update every minute
  setTimeout(renderBusPanel, 60000);
}

function addBusZones(){
  if(!busSchedule || !window.map) return;
  // Add Expo Center bus stop as zone marker
  const expoStop = {lat:42.6543, lng:23.4012, name:'🚌 Expo Center (автобусна спирка)'};
  const icon = L.divIcon({
    className:'',
    html:`<div style="background:#0284c7;color:#fff;border-radius:6px;padding:3px 7px;font-size:12px;font-weight:800;white-space:nowrap;box-shadow:0 2px 6px #0004">🚌 Expo</div>`,
    iconAnchor:[25,15]
  });
  L.marker([expoStop.lat, expoStop.lng], {icon})
    .addTo(window.map)
    .bindPopup(`<b style="color:#0284c7">🚌 Expo Center</b><br><small>Спирка Пловдив↔София</small>`);
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
    return `<div class="bp-item" onclick="(function(){map.setView([${z.lat},${z.lng}],15);showZonePopup('${z.id}');closeBakshish()})()">
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
  }).join('');
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
loadFlights(); loadBuses();
loadConfig().then(()=>{ loadWeather(); setInterval(loadWeather,10*60000); });
checkEventAlerts();
geocodeZones();     // async — прецизира координатите от OSM

setTimeout(()=>{drawSparkline(currentHour); map.invalidateSize();},300);
window.addEventListener('resize',()=>{drawSparkline(currentHour); map.invalidateSize();});

}); // end DOMContentLoaded

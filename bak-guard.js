/* BAK · пазач за демо режима (12.11.2026)
 *
 * Зарежда се в <head>, ПРЕДИ app.js. Ако няма вход (няма bak_access в localStorage),
 * спира заявките, които харчат пари или квоти, и тези с живи данни:
 *   - mvr-proxy (полети през AeroDataBox, трафик през TomTom, КАТ риск, /track в KV)
 *   - OpenWeatherMap и Nominatim
 *   - живите json-и: полети, автобуси, влакове, събития, седмична статистика
 * Остават: картата, зоните, времевата линия, времето от open-meteo (безплатно), тоалетните.
 *
 * Входът (access-gate.js) презарежда страницата и тогава пазачът не се включва.
 * ЧЕСТНО: и това е на клиента — пести квоти от случайни посетители, не спира хакер.
 */
(function () {
  'use strict';
  var rec = null;
  try { rec = JSON.parse(localStorage.getItem('bak_access') || 'null'); } catch (e) {}
  var locked = !rec;
  window.BAK_LOCKED = locked;
  if (!locked) return;

  document.documentElement.classList.add('bak-locked');

  var RX = [
    /\.workers\.dev/i,
    /openweathermap\.org/i,
    /nominatim\.openstreetmap\.org/i,
    /(flight-cache|bus-arrivals|bus-schedule|train-arrivals|events|eventim|sof-weekly)\.json/i,
    /\/SEV\//
  ];
  function blocked(u) {
    u = String((u && u.url) || u || '');
    for (var i = 0; i < RX.length; i++) if (RX[i].test(u)) return true;
    return false;
  }
  var n = 0;
  window.BAK_BLOCKED = function () { return n; };

  var of = window.fetch;
  if (of) window.fetch = function (input) {
    if (blocked(input)) { n++; return Promise.reject(new TypeError('BAK: демо, без живи данни')); }
    return of.apply(this, arguments);
  };

  if (navigator.sendBeacon) {
    var sb = navigator.sendBeacon.bind(navigator);
    navigator.sendBeacon = function (u, d) { if (blocked(u)) { n++; return true; } return sb(u, d); };
  }

  if (window.XMLHttpRequest) {
    var XP = XMLHttpRequest.prototype, XO = XP.open, XS = XP.send;
    XP.open = function (m, u) { this.__bakBlock = blocked(u); return XO.apply(this, arguments); };
    XP.send = function () {
      if (!this.__bakBlock) return XS.apply(this, arguments);
      n++; var x = this;
      setTimeout(function () { try { x.dispatchEvent(new Event('error')); } catch (e) {} }, 0);
    };
  }

  // блокираните заявки не трябва да пълнят конзолата с „Uncaught (in promise)“
  window.addEventListener('unhandledrejection', function (e) {
    if (e.reason && /BAK: демо/.test(String(e.reason.message || e.reason))) e.preventDefault();
  });
})();

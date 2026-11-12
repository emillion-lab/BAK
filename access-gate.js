/* BAK · заключване на достъпа с код
 *
 * Самостоятелен файл — не пипа app.js.
 * Чете списъка от fish.taxi (cross-origin, GitHub Pages праща CORS *).
 *
 * ЧЕСТНО: това е обфускация, не защита. Списъкът е публичен, проверката
 * е на клиента. Спира случайно споделяне и дава лесно отнемане.
 * Истинската проверка идва с api/ (D1 + Worker).
 *
 * Заключени в демо: полети, събития, трафик, автобуси и влакове.
 * Свободни: карта, зони, време, КАТ индекс, времева линия.
 *
 * 12.11.2026: bak-guard.js (в <head>, преди app.js) спира и самите заявки в демо,
 * за да не се харчат квоти. Затова след вход страницата се презарежда.
 * Изгледът е като fish.taxi v3: тъмно стъкло и жълт акцент.
 */

(function () {
  'use strict';

  var PEPPER = 'fishtaxi-access-v1';
  var LIST_URL = 'https://fish.taxi/data/access.json';
  var LS_KEY = 'bak_access';
  var CACHE_KEY = 'bak_access_cache';
  var RECHECK_MS = 3600 * 1000;          // 1 час
  var DEMO_MS = 30 * 60 * 1000;
  var DEMO_KEY = 'bak_demo_until';

  function sha256hex(s) {
    return crypto.subtle.digest('SHA-256', new TextEncoder().encode(s))
      .then(function (buf) {
        return Array.prototype.map.call(new Uint8Array(buf), function (b) {
          return b.toString(16).padStart(2, '0');
        }).join('');
      });
  }

  function hashCode(c) {
    var n = String(c || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
    return sha256hex(PEPPER + ':' + n).then(function (h) { return h.slice(0, 16); });
  }

  function ls(k, v) {
    try {
      if (v === undefined) return JSON.parse(localStorage.getItem(k) || 'null');
      if (v === null) { localStorage.removeItem(k); return null; }
      localStorage.setItem(k, JSON.stringify(v));
      return v;
    } catch (e) { return null; }
  }

  function fetchList() {
    return fetch(LIST_URL + '?t=' + Math.floor(Date.now() / 60000))
      .then(function (r) { return r.json(); })
      .then(function (j) { ls(CACHE_KEY, { at: Date.now(), list: j }); return j; })
      .catch(function () {
        var c = ls(CACHE_KEY);
        return c ? c.list : null;
      });
  }

  function applyLevel(level, rec) {
    var b = document.body;
    if (!b) return;
    b.classList.remove('ft-demo', 'ft-full', 'ft-admin');
    b.classList.add(level === 'demo' ? 'ft-demo'
      : (rec && rec.role === 'admin' ? 'ft-admin' : 'ft-full'));
    window.BAKAccess.level = level;
    window.BAKAccess.driver = rec || null;
    try {
      document.dispatchEvent(new CustomEvent('bak:access',
        { detail: { level: level, driver: rec || null } }));
    } catch (e) {}
  }

  function check() {
    var rec = ls(LS_KEY);
    if (!rec) return Promise.resolve({ level: 'demo', driver: null });
    if (Date.now() - (rec.checked || 0) < RECHECK_MS)
      return Promise.resolve({ level: 'full', driver: rec });

    return fetchList().then(function (list) {
      if (!list) return { level: 'full', driver: rec };
      var hit = (list.drivers || []).filter(function (d) { return d.hash === rec.hash; })[0];
      if (!hit || hit.status !== 'active') {
        ls(LS_KEY, null);
        return { level: 'demo', driver: null, revoked: true };
      }
      hit.hash = rec.hash; hit.checked = Date.now();
      ls(LS_KEY, hit);
      return { level: 'full', driver: hit };
    });
  }

  function redeem(code) {
    return hashCode(code).then(function (h) {
      return fetchList().then(function (list) {
        if (!list) return { ok: false, reason: 'Няма връзка. Опитай пак.' };
        var hit = (list.drivers || []).filter(function (d) { return d.hash === h; })[0];
        if (!hit) return { ok: false, reason: 'Непознат код.' };
        if (hit.status !== 'active') return { ok: false, reason: 'Кодът е спрян.' };
        hit.hash = h; hit.checked = Date.now();
        ls(LS_KEY, hit);
        return { ok: true, driver: hit };
      });
    });
  }

  function demoLeft() {
    var until = ls(DEMO_KEY);
    return until ? Math.max(0, until - Date.now()) : null;
  }

  function startDemo() {
    var until = ls(DEMO_KEY);
    if (!until || until < Date.now() - 24 * 3600 * 1000) {
      until = Date.now() + DEMO_MS;
      ls(DEMO_KEY, until);
    }
    return until;
  }

  // ─── Стилове ──────────────────────────────────────────────────────────

  function css() {
    if (document.getElementById('bak-gate-css')) return;
    var s = document.createElement('style');
    s.id = 'bak-gate-css';
    s.textContent = [

      /* ── входният екран (fish.taxi v3) ── */
      '#bak-gate{position:fixed;inset:0;z-index:99999;background:rgba(10,12,14,.62);',
      'backdrop-filter:blur(22px) saturate(140%);-webkit-backdrop-filter:blur(22px) saturate(140%);',
      'display:flex;align-items:center;justify-content:center;padding:24px;',
      'font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,sans-serif;animation:bakIn .45s cubic-bezier(.2,.9,.25,1)}',
      '@keyframes bakIn{from{opacity:0}to{opacity:1}}',
      '@keyframes bakUp{from{opacity:0;transform:translateY(18px) scale(.98)}to{opacity:1;transform:none}}',
      '#bak-gate .bx{width:100%;max-width:360px;text-align:center;color:#eef0ee;padding:26px 22px 20px;',
      'border-radius:26px;background:rgba(24,28,32,.42);border:1px solid rgba(255,255,255,.12);',
      'box-shadow:0 20px 50px rgba(0,0,0,.45);animation:bakUp .5s .05s both cubic-bezier(.2,.9,.25,1)}',
      '#bak-gate .lk{width:54px;height:54px;margin:0 auto 12px;border-radius:50%;display:grid;place-items:center;',
      'font-size:24px;background:rgba(230,195,106,.14);border:1px solid rgba(230,195,106,.4)}',
      '#bak-gate h2{font-size:1.3rem;margin:0 0 6px;font-weight:700;letter-spacing:-.01em}',
      '#bak-gate p{font-size:.93rem;color:#a3abb1;margin:0 0 18px;line-height:1.5}',
      '#bak-gate input{width:100%;padding:14px;font-size:1.2rem;text-align:center;',
      'letter-spacing:.2em;text-transform:uppercase;border-radius:14px;border:1px solid rgba(255,255,255,.14);',
      'background:rgba(0,0,0,.28);color:#eef0ee;outline:none;font-family:inherit;transition:border-color .2s}',
      '#bak-gate input:focus{border-color:rgba(230,195,106,.65)}',
      '#bak-gate .go{width:100%;margin-top:12px;height:50px;border-radius:14px;cursor:pointer;',
      'background:rgba(230,195,106,.18);border:1px solid rgba(230,195,106,.55);color:#e6c36a;',
      'font-size:1rem;font-weight:700;font-family:inherit;transition:transform .18s cubic-bezier(.3,1.5,.5,1)}',
      '#bak-gate .go:active{transform:scale(.96)}',
      '#bak-gate .demo{margin-top:14px;background:none;border:none;color:#a3abb1;',
      'font-size:.88rem;font-family:inherit;cursor:pointer;padding:8px}',
      '#bak-gate .demo u{text-decoration-color:rgba(163,171,177,.5)}',
      '#bak-gate .er{color:#ef8f86;font-size:.86rem;min-height:1.2em;margin-top:10px;font-weight:600}',

      /* ── лентата долу в демо ── */
      '#bak-demobar{position:fixed;left:10px;bottom:calc(env(safe-area-inset-bottom,0px) + 10px);',
      'z-index:3900;max-width:calc(100% - 84px);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;',
      'background:rgba(24,28,32,.55);border:1px solid rgba(230,195,106,.45);color:#eef0ee;',
      'backdrop-filter:blur(18px) saturate(160%);-webkit-backdrop-filter:blur(18px) saturate(160%);',
      'padding:10px 16px;border-radius:999px;box-shadow:0 8px 24px rgba(0,0,0,.4);',
      'font:600 .85rem -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;text-align:center;cursor:pointer}',
      '#bak-demobar b{color:#e6c36a}',

      /* ── КРЪГОВЕТЕ: черни, наполовина прозрачни ── */
      'body.ft-demo .leaflet-overlay-pane path{',
      'fill:#000 !important;fill-opacity:.5 !important;',
      'stroke:#000 !important;stroke-opacity:.5 !important}',
      'body.ft-demo .leaflet-marker-pane{opacity:.35 !important;filter:grayscale(1)}',

      /* ── СПИСЪЦИТЕ: само надпис ── */
      'body.ft-demo #airport-modal-body,body.ft-demo #next90-list,',
      'body.ft-demo .leaflet-popup-content{position:relative;min-height:132px}',
      'body.ft-demo #airport-modal-body>*,body.ft-demo #next90-list>*,',
      'body.ft-demo .leaflet-popup-content>*{visibility:hidden !important}',
      'body.ft-demo #airport-modal-body::after,body.ft-demo #next90-list::after,',
      'body.ft-demo .leaflet-popup-content::after{',
      'content:"🔒 Не си влязъл\\A\\A Това е демо без живи данни.\\A Влез с кода си, за да ги видиш.";',
      'white-space:pre-wrap;position:absolute;inset:0;display:flex;flex-direction:column;',
      'align-items:center;justify-content:center;text-align:center;padding:18px;',
      'font:600 13px/1.6 -apple-system,system-ui,sans-serif;color:#a3abb1;letter-spacing:0}',

      /* ── тикерът и значката на летището ── */
      'body.ft-demo .ticker-wrap{visibility:hidden}',
      'body.ft-demo .ticker-bar{position:relative}',
      'body.ft-demo .ticker-bar::after{content:"🔒 Не си влязъл · живите данни са скрити";',
      'position:absolute;inset:0;display:flex;align-items:center;justify-content:center;',
      'font:600 11.5px -apple-system,system-ui,sans-serif;color:#a3abb1}',
      'body.ft-demo #airport-badge{filter:blur(5px);opacity:.6}'

    ].join('');
    document.head.appendChild(s);
  }

  // ─── Изглед ───────────────────────────────────────────────────────────

  function showGate() {
    css();
    if (document.getElementById('bak-gate')) return;
    var d = document.createElement('div');
    d.id = 'bak-gate';
    d.innerHTML =
      '<div class="bx">' +
        '<div class="lk">🔒</div>' +
        '<h2>Не си влязъл</h2>' +
        '<p>BAK е за шофьорите на fish.taxi. Въведи кода, който получи по Viber или WhatsApp.</p>' +
        '<input id="bak-code" maxlength="9" placeholder="XXXXXXXX" autocomplete="off" ' +
        'autocapitalize="characters" spellcheck="false">' +
        '<div class="er" id="bak-err"></div>' +
        '<button class="go" id="bak-go">Влез</button>' +
        '<button class="demo" id="bak-demo"><u>Разгледай демото</u> — без живи данни</button>' +
      '</div>';
    document.body.appendChild(d);

    var inp = d.querySelector('#bak-code');
    var er = d.querySelector('#bak-err');
    setTimeout(function () { inp.focus(); }, 80);

    function submit() {
      er.textContent = '';
      redeem(inp.value).then(function (r) {
        if (!r.ok) { er.textContent = r.reason; return; }
        if (window.BAK_LOCKED) { location.reload(); return; }   // данните са били спрени → зареди наново
        d.remove();
        var bar = document.getElementById('bak-demobar');
        if (bar) bar.remove();
        applyLevel('full', r.driver);
      });
    }

    d.querySelector('#bak-go').onclick = submit;
    inp.addEventListener('keydown', function (e) { if (e.key === 'Enter') submit(); });

    d.querySelector('#bak-demo').onclick = function () {
      startDemo();
      d.remove();
      applyLevel('demo', null);
      showDemoBar();
    };
  }

  function showDemoBar() {
    css();
    if (document.getElementById('bak-demobar')) return;
    var b = document.createElement('div');
    b.id = 'bak-demobar';
    b.innerHTML = '🔒 Не си влязъл · демо · <b>Влез</b>';
    b.onclick = showGate;
    document.body.appendChild(b);
  }

  function boot() {
    css();
    check().then(function (r) {
      if (r.revoked && !window.BAK_LOCKED) { location.reload(); return; }
      applyLevel(r.level, r.driver);
      if (r.level === 'demo') {
        var left = demoLeft();
        if (left === null || left <= 0) showGate();
        else showDemoBar();
      }
    });
  }

  window.BAKAccess = {
    redeem: redeem,
    check: check,
    showGate: showGate,
    signOut: function () { ls(LS_KEY, null); location.reload(); },
    isAdmin: function () { var r = ls(LS_KEY); return !!(r && r.role === 'admin'); }
  };

  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();

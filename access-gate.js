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

      /* ── входният екран ── */
      '#bak-gate{position:fixed;inset:0;z-index:99999;background:rgba(8,10,16,.95);',
      'backdrop-filter:blur(10px);display:flex;align-items:center;justify-content:center;',
      'padding:24px;font-family:-apple-system,system-ui,sans-serif}',
      '#bak-gate .bx{width:100%;max-width:340px;text-align:center;color:#f2f0ea}',
      '#bak-gate h2{font-size:1.25rem;margin:0 0 8px;font-weight:800;letter-spacing:.5px}',
      '#bak-gate p{font-size:.92rem;color:#9aa4b2;margin:0 0 20px;line-height:1.55}',
      '#bak-gate input{width:100%;padding:15px;font-size:1.25rem;text-align:center;',
      'letter-spacing:.2em;text-transform:uppercase;border-radius:12px;border:2px solid #2c3546;',
      'background:#141a26;color:#f2f0ea;outline:none;font-family:inherit}',
      '#bak-gate input:focus{border-color:#22d3ee}',
      '#bak-gate .go{width:100%;margin-top:12px;padding:15px;border:none;border-radius:12px;',
      'background:#22d3ee;color:#04121a;font-size:1rem;font-weight:800;font-family:inherit;cursor:pointer}',
      '#bak-gate .demo{margin-top:14px;background:none;border:none;color:#9aa4b2;',
      'font-size:.88rem;text-decoration:underline;font-family:inherit;cursor:pointer}',
      '#bak-gate .er{color:#ff6b6b;font-size:.86rem;min-height:1.2em;margin-top:10px;font-weight:600}',

      /* ── лентата долу в демо ── */
      '#bak-demobar{position:fixed;left:0;right:0;bottom:0;z-index:3900;background:#22d3ee;',
      'color:#04121a;padding:10px 14px;font:700 .85rem -apple-system,system-ui,sans-serif;',
      'text-align:center;cursor:pointer}',
      '#bak-demobar b{text-decoration:underline}',

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
      'content:"🔒 НЯМА ДОСТЪП\\A\\A Демо акаунт.\\A Въведи код, за да видиш данните.";',
      'white-space:pre-wrap;position:absolute;inset:0;display:flex;flex-direction:column;',
      'align-items:center;justify-content:center;text-align:center;padding:18px;',
      'font:700 13px/1.6 -apple-system,system-ui,sans-serif;color:#94a3b8;letter-spacing:.3px}',

      /* ── тикерът и значката на летището ── */
      'body.ft-demo .ticker-wrap{visibility:hidden}',
      'body.ft-demo .ticker-bar{position:relative}',
      'body.ft-demo .ticker-bar::after{content:"🔒 живите данни са скрити в демо режим";',
      'position:absolute;inset:0;display:flex;align-items:center;justify-content:center;',
      'font:700 11.5px -apple-system,system-ui,sans-serif;color:#94a3b8}',
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
        '<h2>🚕 БАКШИШ</h2>' +
        '<p>Въведи кода, който получи по Viber или WhatsApp.</p>' +
        '<input id="bak-code" maxlength="9" placeholder="XXXXXXXX" autocomplete="off" ' +
        'autocapitalize="characters" spellcheck="false">' +
        '<div class="er" id="bak-err"></div>' +
        '<button class="go" id="bak-go">Влез</button>' +
        '<button class="demo" id="bak-demo">Разгледай в демо режим</button>' +
      '</div>';
    document.body.appendChild(d);

    var inp = d.querySelector('#bak-code');
    var er = d.querySelector('#bak-err');
    setTimeout(function () { inp.focus(); }, 80);

    function submit() {
      er.textContent = '';
      redeem(inp.value).then(function (r) {
        if (!r.ok) { er.textContent = r.reason; return; }
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
    b.innerHTML = 'Демо · полети, събития и трафик са скрити · <b>въведи код</b>';
    b.onclick = showGate;
    document.body.appendChild(b);
  }

  function boot() {
    css();
    check().then(function (r) {
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
